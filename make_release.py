"""Operator side: turn the add-on catalogue into one publishable update bundle.

    py -3 launcher/make_release.py --version 2026.08.21-2 --dry-run
    py -3 launcher/make_release.py --version 2026.08.21-2 --notes "Blackwing Enhanced"
    py -3 launcher/make_release.py --track experimental --version 2026.08.21-x1

There are THREE channels (`channels.ORDER`: main, experimental, m3epbuggin)
and one of these builds exactly one of them. `--track` picks the catalogue
(`slots.json` / `slots-experimental.json` / `slots-m3epbuggin.json`), the tag
the bundle is published under, and the branch its `latest.json` belongs on. A
catalogue names its own track, and a mismatch is refused rather than guessed at.
Every cross-catalogue check weighs all the other channels' catalogues found
beside the one being built.

Everything a release carries is a file named explicitly in `slots.json`. Nothing
is scraped from the install: the install is only ever *read* for two things --
the description donor to mint from, and the stock bytes a delta is measured
against, both of which are checked by hash against `baseline_sources`.

A release is a list of add-ons, and an add-on is one of two kinds:

* **`map`** -- one new map slot: a level, its sound stub, a minted description
  carrying an unused map ID, loading art, and two merges into files the player
  already owns. It never replaces a shipped map.
* **`files`** -- a game change: any set of files in the install, named one by
  one. The exe, a `.u` script package, an `.asi` plugin, a config file, a
  texture package. Unlike a map slot these usually **replace** shipped files,
  so the player's originals are cached before the first write and put back when
  the add-on is removed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import channels
import inifiles
import scpatch
from common import human, norm, read_file, sha256_bytes, write_json

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_FORMAT = 2
MINTED_KEYS_LAUNCHER = "3.17"     # the first launcher that knows channel-minted menu keys

MAPS = "Packages/_Common/MapsPC"
DESCS = "Packages/_Common/MapDescriptions"
ART = "Packages/_Common/LoadingScreen/PC"


def resolve(path, base=HERE):
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(base, path))


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_catalogue(path):
    """A catalogue, with anything it inherits filled in.

    `"inherit": "slots.json"` lets the experimental catalogue borrow the parts
    that must be identical in both channels -- above all `baseline_sources`, the
    table of verified stock bytes every delta is measured against. Defined twice,
    those two tables drift; defined once, a member's base-game check means the
    same thing whichever tab they used.

    Only keys the child does not set are taken, and `addons` is never inherited.
    """
    cfg = load_json(path)
    parent_name = cfg.pop("inherit", None)
    if not parent_name:
        return cfg
    parent_path = resolve(parent_name, os.path.dirname(os.path.abspath(path)))
    if not os.path.isfile(parent_path):
        raise SystemExit("%s inherits from %s, which does not exist." % (path, parent_path))
    parent = load_catalogue(parent_path)
    for key, value in parent.items():
        # a lock belongs to ONE channel: inheriting it locked experimental too
        if key in ("addons", "track", "name", "_comment", "locked", "locked_because"):
            continue
        cfg.setdefault(key, value)
    cfg["_inherited_from"] = parent_path
    return cfg


class Builder:
    def __init__(self, cfg, install):
        self.cfg = cfg
        self.install = install
        self.payloads = {}
        self.rows = []
        self.baseline = {}
        self._stock_cache = {}
        self.min_launcher = None

    # -- stock lookup ------------------------------------------------------

    def stock(self, rel):
        """The SHIPPED bytes of an install-relative path, from baseline_sources."""
        rel = norm(rel)
        if rel in self._stock_cache:
            return self._stock_cache[rel]
        sources = self.cfg.get("baseline_sources", {})
        source = sources.get(rel)
        if not source or rel.startswith("_"):
            raise SystemExit(
                "%s has no entry in baseline_sources, so there is no verified stock copy to\n"
                "measure a patch against. Add one pointing at the shipped bytes." % rel
            )
        path = resolve(source)
        if not os.path.isfile(path):
            raise SystemExit("baseline_sources[%s] does not exist:\n  %s" % (rel, path))
        data = read_file(path)
        self._stock_cache[rel] = data
        self.baseline.setdefault(rel, {
            "sha256": sha256_bytes(data),
            "size": len(data),
            "role": "required",
        })
        return data

    # -- one payload -------------------------------------------------------

    def add_file(self, install_path, data, base_rel=None, label="", force_full=False):
        """Ship `data` to `install_path`, as a delta from stock when we can.

        `force_full` is about robustness, not size. A delta needs the player's
        copy to still be the shipped bytes, so anything players hand-edit --
        config above all -- ships as a whole file instead, or one edited
        `Default.ini` blocks the entire update on that one file.
        """
        install_path = norm(install_path)
        if force_full:
            base_rel = None
        target_sha = sha256_bytes(data)
        full = zlib.compress(data, 9)
        mode, payload, base_sha = "full", full, None

        if base_rel:
            base = self.stock(base_rel)
            delta = scpatch.diff(base, data)
            if len(delta) < len(full):
                mode, payload, base_sha = "delta", delta, sha256_bytes(base)
                if scpatch.apply(base, delta) != data:
                    raise SystemExit("%s: the delta did not rebuild the file." % install_path)
            elif zlib.decompress(full) != data:
                raise SystemExit("%s: the compressed copy did not round-trip." % install_path)

        name = "payloads/" + install_path.replace("/", "__")
        self.payloads[name] = payload
        entry = {
            "path": install_path,
            "mode": mode,
            "sha256": target_sha,
            "size": len(data),
            "payload": name,
            "payload_sha256": sha256_bytes(payload),
            "payload_size": len(payload),
        }
        if mode == "delta":
            entry["base"] = norm(base_rel)
            entry["base_sha256"] = base_sha
        note = "delta from %s" % norm(base_rel).split("/")[-1] if mode == "delta" else label
        self.rows.append((install_path, mode, len(data), len(payload), note))
        return entry

    def add_copy(self, install_path, source_rel, label=""):
        """Make the file out of one the player already has -- no payload at all."""
        install_path, source_rel = norm(install_path), norm(source_rel)
        self.rows.append((install_path, "copy", 0, 0, label or "copied from %s" % source_rel.split("/")[-1]))
        return {"path": install_path, "mode": "copy_from", "source": source_rel}

    # -- one add-on --------------------------------------------------------

    def add_addon(self, addon):
        code = addon["code"].upper()
        title = addon["title"]
        map_id = int(addon["map_id"])
        key = str(addon["title_key"])

        donor_cfg = self.cfg["mcd_donor"]
        donor_rel = "%s/PKG_%s_Desc.mcd" % (DESCS, donor_cfg["code"])
        donor = self.stock(donor_rel) if donor_rel in self.cfg.get("baseline_sources", {}) \
            else read_file(resolve(donor_cfg["path"]))

        level_path = resolve(addon["level"])
        if not os.path.isfile(level_path):
            raise SystemExit(
                "%s (%s): the level does not exist:\n  %s\n"
                "Point 'level' at the .sds you want shipped." % (code, title, level_path)
            )

        files = [self.add_file("%s/%s_VS.sds" % (MAPS, code), read_file(level_path),
                               addon.get("level_base"), label=os.path.basename(level_path))]

        occ = addon.get("sound_occ", "stub")
        if occ in (None, "none"):
            # No occlusion file at all. The Kinshasa the operator handed over on
            # 2026-09-20 as the community build has none and loads; shipping a
            # stub beside a map that was judged without one is a change nobody
            # judged. A slot says so with "sound_occ": "none".
            pass
        else:
            occ_path = resolve(self.cfg["sound_occ_stub"]) if occ == "stub" else resolve(occ)
            files.append(self.add_file("%s/%s_VS_sound.occ" % (MAPS, code), read_file(occ_path),
                                       label="112-byte stub" if occ == "stub" else os.path.basename(occ_path)))

        preview = addon.get("preview")
        if addon.get("mcd"):
            # A description shipped AS-IS: the operator's own file, so the base
            # image (which carries the same file) and the channel agree byte for
            # byte and an image install finds nothing to rewrite. The catalogue
            # still has to say what the file says, or the two drift apart.
            mcd_path = resolve(addon["mcd"])
            if not os.path.isfile(mcd_path):
                raise SystemExit("%s: the description does not exist:\n  %s" % (code, mcd_path))
            mcd = read_file(mcd_path)
            if inifiles.mcd_map_id(mcd) != map_id:
                raise SystemExit("%s: %s carries map ID %s but the catalogue says %d."
                                 % (code, os.path.basename(mcd_path), inifiles.mcd_map_id(mcd), map_id))
            if inifiles.mcd_title_key(mcd) != key:
                raise SystemExit("%s: %s points at menu key %s but the catalogue says %s."
                                 % (code, os.path.basename(mcd_path), inifiles.mcd_title_key(mcd), key))
            if preview and inifiles.mcd_preview(mcd) != inifiles.resolve_preview(preview):
                raise SystemExit("%s: %s draws %s in the lobby but the catalogue says %s."
                                 % (code, os.path.basename(mcd_path), inifiles.mcd_preview(mcd), preview))
            label = "shipped as-is (%s): map ID %d, title key %s, lobby model %s" % (
                os.path.basename(mcd_path), map_id, key, inifiles.mcd_preview(mcd))
        else:
            mcd = inifiles.mint_mcd(donor, donor_cfg["code"], code, map_id, key, preview=preview)
            if inifiles.mcd_map_id(mcd) != map_id:
                raise SystemExit("%s: the minted description does not read back map ID %d." % (code, map_id))
            if preview and inifiles.mcd_preview(mcd) != inifiles.resolve_preview(preview):
                raise SystemExit("%s: the minted description still draws %s in the lobby."
                                 % (code, inifiles.mcd_preview(mcd)))
            label = "minted: map ID %d, title key %s, lobby model %s" % (map_id, key, inifiles.mcd_preview(mcd))
        files.append(self.add_file("%s/PKG_%s_Desc.mcd" % (DESCS, code), mcd, label=label))
        if key in inifiles.MINTED_TITLE_KEYS:
            # A DESCRIPTION NAMING A CHANNEL-MINTED KEY (3.17). Launchers before 3.17
            # neither know the key (their file check calls its menu name a changed
            # file) nor move a slot from one key to another, so the entry carries a
            # mode of its own: the same zlib payload as `full`, which 3.16 and older
            # refuse before a byte of the update is written (client.build_targets).
            assert files[-1]["mode"] == "full", files[-1]
            files[-1]["mode"] = "keyed"
            self.rows[-1] = (self.rows[-1][0], "keyed", self.rows[-1][2], self.rows[-1][3],
                             self.rows[-1][4] + " -- channel key, launcher 3.17+")
            self.min_launcher = MINTED_KEYS_LAUNCHER

        art = addon.get("loading_art", "copy:BOSG2")
        if isinstance(art, str) and art.startswith("copy:"):
            files.append(self.add_copy("%s/%s_back.dds" % (ART, code),
                                       "%s/%s_back.dds" % (ART, art[5:])))
        elif art:
            files.append(self.add_file("%s/%s_back.dds" % (ART, code), read_file(resolve(art)),
                                       label=os.path.basename(resolve(art))))

        for extra in addon.get("extra_files", []):
            source = resolve(extra["source"])
            if not os.path.isfile(source):
                raise SystemExit("%s: extra file does not exist:\n  %s" % (code, source))
            files.append(self.add_file(extra["install_path"], read_file(source),
                                       extra.get("base"), label=os.path.basename(source)))

        requires = sorted({f["base"] for f in files if f.get("base")})
        return {
            "code": code,
            "title": title,
            "map_id": map_id,
            "title_key": key,
            "notes": addon.get("notes", ""),
            "requires": requires,
            "files": files,
            "mappaths": {"code": code, "directory": "_Common",
                         "after": addon.get("after")},
            "menu_text": {"key": key, "title": title},
        }

    # -- a game change ----------------------------------------------------

    def add_files_addon(self, addon):
        """Any set of files in the install, named one by one -- no slot at all.

        There is no description to mint, no map ID to keep clear and nothing to
        merge, because a game change does not appear in the map list. What it
        does instead is land on files that are already there, which is why every
        entry either declares a stock `base` to patch against or says
        `force_full` and ships whole.
        """
        code = addon["code"].upper()
        entries = addon.get("files", [])
        if not entries:
            raise SystemExit("%s (%s): a 'files' add-on with no files in it."
                             % (code, addon["title"]))

        files = []
        for entry in entries:
            source = resolve(entry["source"])
            if not os.path.isfile(source):
                raise SystemExit("%s: %s does not exist:\n  %s"
                                 % (code, entry.get("install_path", "?"), source))
            data = read_file(source)
            item = self.add_file(
                entry["install_path"], data, entry.get("base"),
                label=os.path.basename(source), force_full=entry.get("force_full", False))
            if entry.get("over"):
                # another add-on's file, replaced while this one is live. Its own
                # mode is what keeps launchers older than 3.10 off it: they refuse
                # an unknown mode before writing a byte (client.under_path).
                assert item["mode"] == "full", item
                item["mode"] = "over"
                item["over"] = str(entry["over"]).upper()
                if norm(entry["install_path"]).startswith(DESCS + "/"):
                    # the launcher stamps a description's map ID from the map
                    # list; this is the ID it was built with, to compare against
                    item["map_id"] = inifiles.mcd_map_id(data)
                self.rows[-1] = (self.rows[-1][0], "over", self.rows[-1][2], self.rows[-1][3],
                                 "%s's file, while this is on" % item["over"])
            files.append(item)

        # KEY BINDS: one `PCBindings=` line each, merged into the player's own
        # PlayerProfilePC.ini by ActionName and taken back out with the add-on.
        # The file itself is never shipped (see check_catalogue). Launchers
        # older than 3.14 ignore the field and install the files without it.
        keybinds = [str(k).strip() for k in addon.get("keybinds", [])]
        actions = [inifiles.keybind_action(k) for k in keybinds]
        if None in actions:
            raise SystemExit("%s: every \"keybinds\" entry must be one PCBindings=(ActionName=\"...\",...) "
                             "line:\n  %s" % (code, keybinds[actions.index(None)]))
        if len({a.lower() for a in actions}) != len(actions):
            raise SystemExit("%s: two \"keybinds\" entries bind the same ActionName" % code)
        out = {
            "code": code,
            "title": addon["title"],
            "kind": "files",
            "notes": addon.get("notes", ""),
            "requires": sorted({f["base"] for f in files if f.get("base")}),
            "files": files,
        }
        if keybinds:
            out["keybinds"] = keybinds
            if addon.get("keybinds_keep"):
                # part of the game from now on: launchers >= 3.16 never take these rows out
                out["keybinds_keep"] = True
        return out

    def add_any(self, addon):
        kind = addon.get("kind", "map")
        if kind == "map":
            return self.add_addon(addon)
        if kind == "files":
            return self.add_files_addon(addon)
        raise SystemExit("%s: unknown add-on kind %r -- known kinds are map, files"
                         % (addon.get("code", "?"), kind))


def live_together(a, b):
    """Whether one version (profile) switches on both channels at once.

    Main is in every version that has a channel, so main and any other channel
    are live together. Experimental and M3epbuggin never are: each is its own
    version on top of main. Two channels that are never live together may ship
    the same install path (each one's add-on replaces the same stock file); the
    launcher still lets only one installed add-on own a file, so a player takes
    one channel's add-ons out before picking the other.
    """
    return any(a in channels.profile_tracks(p) and b in channels.profile_tracks(p)
               for p in channels.PROFILES)


def other_catalogue(track, base_dir=HERE):
    """Every add-on the OTHER channels lay claim to, enabled or not.

    Disabled counts. A slot that is switched off today is one somebody flips on
    next week, and by then the number it wanted is in a hundred installs.

    Sibling catalogues are looked for next to the one being built, not always in
    `launcher/`, so building a throwaway catalogue somewhere else checks against
    its own neighbours -- or against nothing, if it has none.
    """
    rows = []
    for name in channels.ORDER:
        if name == track:
            continue
        path = os.path.join(base_dir, channels.get(name)["catalogue"])
        if not os.path.isfile(path):
            continue
        for addon in load_json(path).get("addons", []):
            rows.append((name, addon))
    return rows


def check_reserved(addons):
    """Code, map ID and menu key must be unique across the WHOLE catalogue.

    `check_catalogue` only sees the enabled entries, because those are what a
    release ships. But a disabled entry is a reservation: switch it on next week
    and its number has to still be free. Two templates quietly sharing map ID 16
    is a slot that silently loads the other map, discovered by a player.
    """
    problems = []
    seen = {}
    for addon in addons:
        code = addon.get("code", "?").upper()
        keys = [("code", code)]
        if addon.get("kind", "map") == "map":
            keys += [("map ID", int(addon["map_id"])), ("menu key", str(addon["title_key"]))]
        for field, value in keys:
            if (field, value) in seen:
                problems.append("%s and %s share a %s (%s) -- one of them is disabled today, "
                                "which is exactly when this goes unnoticed"
                                % (seen[(field, value)], code, field, value))
            seen[(field, value)] = code
    return problems


def check_sources_against_install(addons, install, base_dir=HERE):
    """Warn where a slot's source file is not the file installed under that name.

    THE DEFECT THIS EXISTS FOR, measured 2026-08-26 on this catalogue. A slot's
    `level` is checked when a release is BUILT, and a release only ever builds
    the ENABLED slots -- so a slot that was populated once and then left
    `"enabled": false` is compared to nothing, ever. Two of the four had
    silently diverged from the map the operator was actually playing:

        KIN01  source b2c1f55d  9,548,486 B      installed c31eb343 10,334,235 B
        NSA01  source c2868db0  9,869,947 B      installed e432b8fd  9,869,947 B

    and NSA01 is the shape that matters: **the same byte count to the byte, a
    different hash**. No size check, no date glance and no directory listing
    catches that one. So this prints BOTH numbers on every line -- "same size,
    different hash" is the sentence that would have saved an evening.

    The damage lands at ENABLE time, not build time: flipping the flag ships the
    stale level and the installer writes it over the live map. So this runs over
    EVERY addon, enabled or not, which is the whole point.

    It WARNS and never refuses, for two reasons. A stale source on a disabled
    slot must not block an unrelated release; and the comparison can only be
    made against whatever the BUILDING machine happens to have installed, which
    is evidence about this workstation and not about the catalogue. A slot whose
    code is not installed here is simply not mentioned.
    """
    if not install:
        return []
    notes = []
    for addon, where in addons:
        code = str(addon.get("code", "?")).upper()
        pairs = []
        if addon.get("kind", "map") == "map" and addon.get("level"):
            pairs.append((addon["level"], "%s/%s_VS.sds" % (MAPS, code)))
        for entry in addon.get("extra_files", []) + (
                addon.get("files", []) if addon.get("kind") == "files" else []):
            if entry.get("source"):
                pairs.append((entry["source"], entry["install_path"]))
        for source, install_path in pairs:
            src = resolve(source, base_dir)
            live = os.path.join(install, *install_path.split("/"))
            if not src or not os.path.isfile(src) or not os.path.isfile(live):
                continue                      # a missing source fails loudly at build
            a, b = read_file(src), read_file(live)
            if a == b:
                continue
            notes.append(
                "%s%s%s ships %s\n     source    %s  %s B\n     installed %s  %s B%s"
                % (code, "" if addon.get("enabled") else " (disabled)",
                   "" if where is None else " [%s]" % where, install_path,
                   sha256_bytes(a)[:16], format(len(a), ","),
                   sha256_bytes(b)[:16], format(len(b), ","),
                   "\n     SAME SIZE, DIFFERENT CONTENT -- nothing but a hash catches this"
                   if len(a) == len(b) else ""))
    return notes


def check_catalogue(addons, track=channels.DEFAULT_TRACK, cross=True, base_dir=HERE, notes=None):
    """Every trap, caught here rather than in somebody's game.

    The first two are the original ones from add_slot.py -- a code that is not
    five characters corrupts the renamed description, and a map ID another slot
    already claims makes the slot silently load that other map. The rest exist
    because there are now several channels writing into one install, so a number
    used over here has to stay unused over there.

    Codes, map IDs and menu keys are refused across every channel. A shared
    install path is refused between two channels one version switches on
    together (`live_together`); between two that never are, it is appended to
    `notes` (when given) instead, because the build cannot see which one a
    player has installed and the launcher refuses the second owner itself.
    """
    problems = []
    cfg = channels.get(track)
    seen_code, seen_id, seen_key = {}, {}, {}

    for addon in addons:
        code, title = addon["code"].upper(), addon["title"]
        kind = addon.get("kind", "map")
        if kind not in ("map", "files"):
            problems.append("%s: unknown kind %r -- known kinds are map, files" % (code, kind))
            continue

        if code in seen_code:
            problems.append("%s and %s share a code (%s)" % (seen_code[code], title, code))
        seen_code[code] = title

        if channels.is_retired(track, code):
            # every launcher takes this code back out of an install and walks
            # past it in a bundle, so a release carrying it ships dead weight
            problems.append("%s (%s) is retired on the %s: %s. Launchers remove it on sight "
                            "and never install it -- see channels.RETIRED. Ship it under a "
                            "new code if it has to come back."
                            % (code, title, cfg["label"], channels.RETIRED[track][code]))

        if kind == "files":
            for entry in addon.get("files", []):
                if entry.get("over"):
                    if track == channels.DEFAULT_TRACK:
                        problems.append("%s: %s says \"over\": %s, but the %s outranks every other "
                                        "channel -- only a channel below it can override one of its files"
                                        % (code, entry.get("install_path", "?"), entry["over"], cfg["label"]))
                    if not entry.get("force_full") or entry.get("base"):
                        problems.append("%s: %s overrides %s's file, so it ships whole: set "
                                        "\"force_full\": true and no \"base\""
                                        % (code, entry.get("install_path", "?"), entry["over"]))
                if not entry.get("base") and not entry.get("force_full"):
                    problems.append(
                        "%s: %s declares neither a stock 'base' to patch against nor "
                        "'force_full': true. Say which -- a base keeps the download small, "
                        "force_full survives a player who has edited the file."
                        % (code, entry.get("install_path", "?")))
                if entry.get("install_path", "").lower().endswith("playerprofilepc.ini"):
                    problems.append("%s: PlayerProfilePC.ini is the player's own keybinds and "
                                    "sensitivity. It is never shipped." % code)
            continue

        if len(code) != 5:
            problems.append("%s: code must be exactly 5 characters (the description is renamed in place)" % code)
        if len(str(addon["title_key"])) != 2:
            problems.append("%s: title_key must be 2 characters" % code)
        minted = channels.minted_title_keys(track)
        if str(addon["title_key"]) not in inifiles.SHIPPED_TITLE_KEYS + minted:
            problems.append(
                "%s: menu key %s is not one the game defines. The stock Menu_Text.ute ships "
                "%s%s; with any other key the slot would show no name of its own -- the "
                "Menu_text.eng section alone does nothing."
                % (code, addon["title_key"], ", ".join(inifiles.SHIPPED_TITLE_KEYS),
                   "" if not minted else " and the %s's own registry adds %s-%s"
                   % (cfg["label"], minted[0], minted[-1])))
        elif str(addon["title_key"]) in minted:
            # a minted key exists only in the registry this catalogue ships itself
            registries = [e for a in addons if a.get("kind") == "files"
                          for e in a.get("files", [])
                          if norm(e.get("install_path", "")).lower() == channels.MENU_REGISTRY.lower()]
            src = resolve(registries[0]["source"], base_dir) if len(registries) == 1 else None
            if not src or not os.path.isfile(src):
                problems.append("%s: menu key %s is minted by this channel, so an enabled files "
                                "add-on here must ship %s -- %d do"
                                % (code, addon["title_key"], channels.MENU_REGISTRY, len(registries)))
            elif not inifiles.registry_defines(read_file(src), str(addon["title_key"])):
                problems.append("%s: menu key %s is not defined by the %s this catalogue ships (%s)"
                                % (code, addon["title_key"], channels.MENU_REGISTRY, src))
        if not addon.get("preview"):
            problems.append(
                "%s: no preview -- the lobby draws MMap_<model>_msh from the description, and "
                "without this the slot keeps the donor's model (Boss House). Name a stock map "
                "(%s) or a model token (%s)."
                % (code, ", ".join(sorted(inifiles.PREVIEW_FOR)), ", ".join(inifiles.PREVIEW_NAMES)))
        else:
            try:
                inifiles.resolve_preview(str(addon["preview"]))
            except ValueError as exc:
                problems.append("%s: %s" % (code, exc))
        if int(addon["map_id"]) < 8:
            problems.append("%s: map ID %s is one stock CE already uses (0-7). The slot would "
                            "silently load that map instead." % (code, addon["map_id"]))
        elif not channels.in_map_id_range(track, addon["map_id"]):
            owner = channels.track_of_map_id(addon["map_id"])
            problems.append("%s: map ID %s is outside the %s range %d-%d%s" % (
                code, addon["map_id"], cfg["label"], cfg["map_ids"][0], cfg["map_ids"][1],
                "" if owner is None else " -- it is the %s's" % channels.get(owner)["label"]))
        if not channels.in_title_key_range(track, addon["title_key"]):
            owner = channels.track_of_title_key(addon["title_key"])
            problems.append("%s: menu key %s is outside the %s range %s-%s%s" % (
                code, addon["title_key"], cfg["label"], cfg["title_keys"][0], cfg["title_keys"][1],
                "" if owner is None else " -- it is the %s's" % channels.get(owner)["label"]))

        for field, table, value in (("map ID", seen_id, int(addon["map_id"])),
                                    ("title key", seen_key, str(addon["title_key"]))):
            if value in table:
                problems.append("%s and %s share a %s (%s)" % (table[value], title, field, value))
            table[value] = title

    if cross:
        paths = {}
        overs = {}                        # rel -> the main-channel code it declares it overrides
        for addon in addons:
            for rel in addon_paths(addon):
                paths[rel] = addon["code"].upper()
            if addon.get("kind", "map") == "files":
                for entry in addon.get("files", []):
                    if entry.get("over"):
                        overs[norm(entry["install_path"])] = str(entry["over"]).upper()
        claimed = {}
        for name, addon in other_catalogue(track, base_dir):
            if name == channels.DEFAULT_TRACK and addon.get("enabled"):
                for rel in addon_paths(addon):
                    claimed[rel] = addon["code"].upper()
        for rel, owner in sorted(overs.items()):
            if claimed.get(rel) != owner:
                problems.append("%s: \"over\": %s, but the %s's %s does not ship that file%s"
                                % (rel, owner, channels.get(channels.DEFAULT_TRACK)["label"], owner,
                                   "" if rel not in claimed else " -- %s does" % claimed[rel]))
        for name, addon in other_catalogue(track, base_dir):
            code, label = addon["code"].upper(), channels.get(name)["label"]
            if code in seen_code:
                problems.append("%s: the %s already has an add-on with this code -- it would "
                                "write the same files" % (code, label))
            if addon.get("kind", "map") == "map":
                if int(addon["map_id"]) in seen_id:
                    problems.append("%s: map ID %s is already claimed by %s on the %s"
                                    % (seen_id[int(addon["map_id"])], addon["map_id"], code, label))
                if str(addon["title_key"]) in seen_key:
                    problems.append("%s: menu key %s is already claimed by %s on the %s"
                                    % (seen_key[str(addon["title_key"])], addon["title_key"], code, label))
            theirs = {}
            if addon.get("kind", "map") == "files":
                theirs = {norm(e["install_path"]): str(e.get("over") or "").upper()
                          for e in addon.get("files", []) if e.get("install_path")}
            for rel in addon_paths(addon):
                if rel in paths and paths[rel] != code:
                    if overs.get(rel) == code and name == channels.DEFAULT_TRACK:
                        continue          # we declare an override of this main-channel file
                    if theirs.get(rel) == paths[rel] and track == channels.DEFAULT_TRACK:
                        continue          # they declare an override of our file
                    if not live_together(track, name):
                        # never switched on together: each replaces the same file
                        # in its own version. Reported, not refused.
                        if notes is not None:
                            notes.append("%s and %s (%s%s) both ship %s -- never live together; "
                                         "an install holds only one of them"
                                         % (paths[rel], code, label,
                                            "" if addon.get("enabled") else ", disabled", rel))
                        continue
                    problems.append("%s and %s (%s) both ship %s -- one would overwrite the other"
                                    % (paths[rel], code, label, rel))
    return problems


def addon_paths(addon):
    """Every install-relative path a catalogue entry would write."""
    code = addon["code"].upper()
    if addon.get("kind", "map") == "files":
        return [norm(e["install_path"]) for e in addon.get("files", []) if e.get("install_path")]
    rels = ["%s/%s_VS.sds" % (MAPS, code),
            "%s/PKG_%s_Desc.mcd" % (DESCS, code),
            "%s/%s_back.dds" % (ART, code)]
    if addon.get("sound_occ", "stub") not in (None, "none"):
        # "sound_occ": "none" writes no occlusion file (build_map), so the
        # slot does not claim the path either
        rels.insert(1, "%s/%s_VS_sound.occ" % (MAPS, code))
    rels += [norm(extra["install_path"]) for extra in addon.get("extra_files", [])]
    return rels


def resolve_track(args):
    """Which channel is being built, and which catalogue is allowed to build it.

    The catalogue declares its own track and a mismatch is an error, never a
    warning. This is the whole reason a test map cannot reach the community
    release: it lives in a file that says `experimental`, and the main build
    refuses to read it.
    """
    track = args.track
    catalogue = args.catalogue
    if catalogue:
        declared = load_json(catalogue).get("track")
        if track and declared and declared != track:
            raise SystemExit(
                "\n%s says it is the %r catalogue, but --track %r was asked for.\n"
                "Refusing to guess which one you meant." % (catalogue, declared, track))
        track = track or declared or channels.DEFAULT_TRACK
    else:
        track = track or channels.DEFAULT_TRACK
        catalogue = os.path.join(HERE, channels.get(track)["catalogue"])
        if not os.path.isfile(catalogue):
            raise SystemExit("\nthere is no catalogue for the %s at:\n  %s"
                             % (channels.get(track)["label"], catalogue))
        declared = load_json(catalogue).get("track")
        if declared and declared != track:
            raise SystemExit("\n%s is the %s catalogue but declares track %r."
                             % (catalogue, track, declared))
    channels.get(track)
    return track, catalogue


def _repo_of(url, default=channels.REPO):
    """owner/name of a github.com release URL or a raw.githubusercontent.com URL."""
    for prefix in ("https://github.com/", "https://raw.githubusercontent.com/"):
        if url and url.startswith(prefix):
            parts = url[len(prefix):].split("/")
            if len(parts) >= 2:
                return "%s/%s" % (parts[0], parts[1])
    return default


def publish_checklist(track, version, bundle_name, out, bundle_url=""):
    cfg = channels.get(track)
    print("\nPUBLISH -- %s" % channels.describe(track))
    print("  1. Create release %s in %s and attach:" % (channels.tag(track, version), _repo_of(bundle_url)))
    print("       %s" % bundle_name)
    if cfg["carries_exe"]:
        print("       ScdaLauncher.exe         <- EVERY main release must carry it; the")
        print("                                   community link is releases/latest/download/")
        print("       (nothing else: the console build and the old ScdaPatcher spelling are")
        print("        NOT published since the launcher went public on 2026-09-20)")
    else:
        print("       (no exe -- %s releases do not hand one out)" % cfg["label"])
    if cfg["prerelease"]:
        print("  2. TICK 'Set as a pre-release'. Load-bearing: releases/latest/download/")
        print("     ScdaLauncher.exe must keep resolving to the newest MAIN release.")
    else:
        print("  2. Leave 'Set as a pre-release' UNTICKED.")
    print("  3. THEN, and only then, commit latest.json to the '%s' branch of %s:"
          % (cfg["branch"], _repo_of(cfg["channel_url"])))
    print("       %s" % os.path.join(out, "latest.json"))
    print("     Release first, channel second -- raw.githubusercontent caches for about")
    print("     five minutes, so a channel pointing at a bundle nobody can download yet")
    print("     is the one order that breaks.")


def build(args):
    track, catalogue_path = resolve_track(args)
    cfg = load_catalogue(catalogue_path)
    out = args.out or os.path.join(HERE, "dist", track)
    install = args.install or cfg.get("install_root")
    enabled = [a for a in cfg.get("addons", []) if a.get("enabled")]
    held = [a for a in cfg.get("addons", []) if not a.get("enabled")]

    print("track     : %s" % channels.describe(track))
    print("catalogue : %s" % catalogue_path)

    if cfg.get("locked"):
        raise SystemExit(
            "\n%s IS LOCKED and will not build.\n\n%s\n\n"
            "This is a standing instruction, not a mistake: Community Edition is the stock game."
            "\nA release from this channel would change what every player has by default."
            "\nTo lift it, set \"locked\": false in %s -- deliberately."
            % (channels.get(track)["label"],
               cfg.get("locked_because", "No reason recorded."),
               os.path.basename(catalogue_path)))
    if cfg.get("_inherited_from"):
        print("            stock bytes and donor inherited from %s"
              % os.path.basename(cfg["_inherited_from"]))

    if held:
        print("\nnot enabled (%d):" % len(held))
        for addon in held:
            print("  %-6s %-22s %s" % (addon["code"], addon["title"], addon.get("_status", "")))

    if not enabled:
        raise SystemExit(
            "\nNo add-on is enabled in %s, so there is nothing to release on the %s.\n"
            "Set \"enabled\": true on the ones that should go out, and make sure each\n"
            "one's \"level\" points at the build you want shipped."
            % (os.path.basename(catalogue_path), channels.get(track)["label"])
        )

    problems = check_reserved(cfg.get("addons", []))
    shared = []
    problems += check_catalogue(enabled, track,
                                base_dir=os.path.dirname(os.path.abspath(catalogue_path)),
                                notes=shared)
    if problems:
        raise SystemExit("\n" + "\n".join("  " + p for p in problems))
    if shared:
        print("\nfiles another channel also ships (never live together with this one):")
        for note in shared:
            print("  " + note)
        print("  The launcher lets one installed add-on own a file: a player takes the")
        print("  other channel's add-ons out (remove-track) before picking this one.")

    # EVERY slot, enabled or not -- see check_sources_against_install. A warning,
    # never a refusal: a stale source on a slot nobody is shipping must not block
    # the release of one somebody is.
    #
    # EVERY catalogue, not just this one. The slot that taught us this lives on
    # the main catalogue, which is LOCKED and refuses to build -- so a check that
    # only saw the track being built would never have reported it. The other
    # catalogues' rows are labelled so it is obvious they are not this release's.
    cat_dir = os.path.dirname(os.path.abspath(catalogue_path))
    every = [(a, None) for a in cfg.get("addons", [])]
    every += [(a, channels.get(name)["label"])
              for name, a in other_catalogue(track, cat_dir)]
    drift = check_sources_against_install(every, install, base_dir=cat_dir)
    if drift:
        print("\nsource files that are NOT what this machine has installed:")
        for note in drift:
            print("  " + note)
        print("  A slot's source is only checked when it is BUILT, and only enabled")
        print("  slots build -- so a disabled slot can drift until the day it is")
        print("  enabled, and then the installer writes it over the live map.")
        print("  Refreeze from the build that was actually judged before enabling.")

    builder = Builder(cfg, install)
    addons = [builder.add_any(a) for a in enabled]

    # the engine build is worth reporting on even though nothing is patched from it
    exe = "System/SCDA_Online.exe"
    if exe in cfg.get("baseline_sources", {}):
        builder.stock(exe)
        builder.baseline[exe]["role"] = "informational"

    manifest = {
        "format": MANIFEST_FORMAT,
        "name": cfg.get("name", "SCDA Community Edition"),
        "track": track,
        "version": args.version,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "notes": args.notes,
        "install_marker": "System/SCDA_Online.exe",
        "mcd_id_offsets": {str(k): v for k, v in inifiles.MCD_ID_OFFSETS.items()},
        "baseline": builder.baseline,
        "addons": addons,
        # Catalogue data on purpose: a voice server moves, and moving it must
        # not need a new patcher shipped to everybody.
        "voice_server": cfg.get("voice_server") or None,
    }
    if builder.min_launcher:
        # read by 3.17 and later (scda_launcher.check_track); older ones are held
        # off by the `keyed` entries themselves
        manifest["min_launcher"] = builder.min_launcher

    print("\n%-52s %-6s %10s %10s  %s" % ("file", "mode", "size", "payload", "note"))
    print("-" * 110)
    for addon in addons:
        if addon.get("kind", "map") == "files":
            # "GAME CHANGE" is a warning, so only say it when it is one. An
            # add-on every file of which is new -- no delta base, and no entry
            # in baseline_sources, meaning the game never shipped that path --
            # replaces nothing and cannot desync a match. Derived, not flagged,
            # so a catalogue cannot claim to be harmless.
            shipped = set(cfg.get("baseline_sources", {}))
            adds_only = all(f.get("mode") not in ("delta", "over") and norm(f["path"]) not in shipped
                            for f in addon["files"])
            print("[%s] %s -- %s, %d file(s)" % (
                addon["code"], addon["title"],
                "adds files, replaces nothing" if adds_only else "GAME CHANGE",
                len(addon["files"])))
            wanted = set(f["path"] for f in addon["files"])
        else:
            print("[%s] %s -- map ID %d, menu key %s" % (addon["code"], addon["title"],
                                                         addon["map_id"], addon["title_key"]))
            wanted = None
        for path, mode, size, payload_size, note in builder.rows:
            if wanted is not None:
                if path not in wanted:
                    continue
            elif not (path.split("/")[-1].startswith(addon["code"]) or addon["code"] in path):
                continue
            print("  %-50s %-6s %10s %10s  %s" % (path[-50:], mode, human(size), human(payload_size), note))
        for line in addon.get("keybinds", []):
            print("  %-50s %-6s %10s %10s  %s" % ("System/PlayerProfilePC.ini", "merge", "", "",
                                                  "key bind " + inifiles.keybind_action(line)))
    print("-" * 110)
    total = sum(len(p) for p in builder.payloads.values())
    print("%d add-on(s), %d file(s), %s of payload" % (
        len(addons), sum(len(a["files"]) for a in addons), human(total)))
    print("\nbase game checked before anything is written:")
    for rel, info in sorted(builder.baseline.items()):
        print("  %-52s %-13s %s" % (rel[-52:], info["role"], info["sha256"][:16]))

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return

    os.makedirs(out, exist_ok=True)
    bundle_name = channels.bundle_name(track, args.version)
    bundle_path = os.path.join(out, bundle_name)
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for name, payload in builder.payloads.items():
            zf.writestr(name, payload)

    bundle = read_file(bundle_path)
    template = args.bundle_url or cfg.get("bundle_url_template", "")
    url = template.format(version=args.version, bundle=bundle_name,
                          tag=channels.tag(track, args.version)) if template \
        else channels.bundle_url(track, args.version)
    latest = {
        "track": track,
        "version": args.version,
        "bundle_url": url,
        "sha256": sha256_bytes(bundle),
        "size": len(bundle),
        "notes": args.notes,
        "released": manifest["created"],
        "addons": [{"code": a["code"], "title": a["title"],
                    "kind": a.get("kind", "map")} for a in addons],
        # informational: no launcher reads it. An override entry's own mode is
        # the gate that keeps launchers older than 3.10 off it.
        "min_patcher": 3 if any(f.get("over") for a in addons for f in a.get("files", [])) else 2,
    }
    if builder.min_launcher:
        latest["min_launcher"] = builder.min_launcher
    write_json(os.path.join(out, "latest.json"), latest)

    print("\nbundle      %s  (%s)" % (bundle_path, human(len(bundle))))
    print("latest.json %s" % os.path.join(out, "latest.json"))
    if not latest["bundle_url"]:
        print("\nWARNING: bundle_url is empty -- the patcher has nowhere to download from.")
    publish_checklist(track, args.version, bundle_name, out, latest["bundle_url"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build one SCDA CE add-on bundle.")
    ap.add_argument("--version", required=True, help="release version, e.g. 2026.08.21-2")
    ap.add_argument("--notes", default="", help="one line shown in the patcher")
    ap.add_argument("--notes-file", help="read the notes from a file instead")
    ap.add_argument("--track", choices=channels.ORDER,
                    help="which channel to build (default: main, or whatever the catalogue says)")
    ap.add_argument("--catalogue", help="override the catalogue file for the track")
    ap.add_argument("--install", help="the CE install to read the donor and stock files from")
    ap.add_argument("--out", help="output folder (default: launcher/dist/<track>)")
    ap.add_argument("--bundle-url", help="download URL template, {version} and {bundle} expand")
    ap.add_argument("--dry-run", action="store_true", help="print the table, write nothing")
    args = ap.parse_args(argv)
    if args.notes_file:
        with open(args.notes_file, encoding="utf-8") as fh:
            args.notes = fh.read().strip()
    build(args)


if __name__ == "__main__":
    main()
