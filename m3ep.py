"""The M3epbuggin channel of the SCDA Launcher: fetch, add, upload, check, build, publish.

    python m3ep.py fetch                        download every file the catalogue names
    python m3ep.py add <file> [--as NAME]       put a new or changed file under sources/ and upload it
    python m3ep.py upload                       upload every locked file the store does not have yet
    python m3ep.py check [--local]              every named file present, locked and uploaded
    python m3ep.py next                         the next free M3epbuggin version
    python m3ep.py status                       what is published here
    python m3ep.py build --version V [--notes "..."] [--dry-run]
    python m3ep.py publish [--version V] --notes "..." [--dry-run]
    python m3ep.py claims --main <slots.json> --experimental <slots-experimental.json>

Players' launchers read latest.json on the `main` branch of this repository
(M3epmeep/SCDA-M3epbuggin). It names a bundle attached to the pre-release
`m3ep-v<version>` here. There is no mirror: the repository is public and the
launcher downloads from it directly.

Needs Python 3.8+, git, and the GitHub CLI (`gh auth login`) with write access
to this repository. Nothing outside the standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "M3epmeep/SCDA-M3epbuggin"
TRACK = "m3epbuggin"
STORE_TAG = "sources"
CATALOGUE = "slots-m3epbuggin.json"
MAIN_CATALOGUE = "slots.json"
EXP_CATALOGUE = "slots-experimental.json"
LOCK = "sources.lock.json"
DIST = "dist"
TAG_PREFIX = "m3ep-v"
BUNDLE = "scda-ce-m3ep-%s.scdaupd"
VERSION_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}-m(\d+)$")
EXE = "System/SCDA_Online.exe"


# --- small helpers ----------------------------------------------------------

def die(msg):
    raise SystemExit("\n" + msg)


def path_of(rel):
    return os.path.join(HERE, *rel.split("/"))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(rel):
    with open(path_of(rel), encoding="utf-8") as fh:
        return json.load(fh)


def save_json(rel, obj):
    tmp = path_of(rel) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path_of(rel))


def place(src, dest, link=False):
    """Put src's bytes at dest WITHOUT writing into an existing dest.

    sources/ and stock/ may hold hard links to files elsewhere on the disk (the
    builder's own output, a verified stock copy). Writing into such a file
    would change the other name too, so a new file always goes in beside it
    and is renamed over it. With link=True it is a hard link to src (same
    volume only), which costs no disk.
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    if link:
        os.link(src, tmp)
    else:
        shutil.copyfile(src, tmp)
    os.replace(tmp, dest)


def stage(src, folder, name):
    """A file named `name` in `folder` with src's bytes: a hard link if the
    volume allows it (no disk used), else a copy."""
    dest = os.path.join(folder, name)
    try:
        os.link(src, dest)
    except OSError:
        shutil.copyfile(src, dest)
    return dest


def run(cmd, check=True, capture=True):
    proc = subprocess.run(cmd, cwd=HERE, text=True, encoding="utf-8",
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)
    if check and proc.returncode != 0:
        die("command failed: %s\n%s%s" % (" ".join(cmd), proc.stdout or "", proc.stderr or ""))
    return proc


def gh(*args, check=True):
    return run(["gh"] + list(args), check=check)


def gh_json(*args):
    out = gh(*args).stdout
    return json.loads(out) if out.strip() else None


def gh_lines(*args):
    return [line for line in gh(*args).stdout.splitlines() if line.strip()]


# --- what the catalogue names -------------------------------------------------

def _walk(value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            if not k.startswith("_"):
                _walk(v, out)
    elif isinstance(value, list):
        for v in value:
            _walk(v, out)
    elif isinstance(value, str) and (value.startswith("sources/") or value.startswith("stock/")):
        out.add(value)


def _stock_for(addon, baseline):
    """The stock copies an add-on is measured against: its files' `base`s,
    plus the description donor and the .occ stub for a map slot."""
    out = set()
    entries = list(addon.get("files", [])) + list(addon.get("extra_files", []))
    for e in entries:
        if e.get("base") and not e.get("force_full"):
            src = baseline.get(e["base"])
            if src:
                out.add(src)
    if addon.get("kind", "map") == "map":
        if addon.get("level_base") and baseline.get(addon["level_base"]):
            out.add(baseline[addon["level_base"]])
    return out


def named_files():
    """(needed, held): files the enabled add-ons name, with the stock copies
    their deltas are measured against and the stock exe make_release reports
    on; and files only disabled add-ons name.

    Only the stock files this channel uses: main's table lists fifteen (about
    400 MB) and a game change here patches two of them.
    """
    cat, main = load_json(CATALOGUE), load_json(MAIN_CATALOGUE)
    baseline = {k: v for k, v in main.get("baseline_sources", {}).items() if not k.startswith("_")}
    needed, held = set(), set()
    _walk({k: v for k, v in cat.items() if k != "addons"}, needed)
    if EXE in baseline:
        needed.add(baseline[EXE])              # read by make_release, reported as informational
    for addon in cat.get("addons", []):
        bucket = needed if addon.get("enabled") else held
        _walk(addon, bucket)
        bucket.update(_stock_for(addon, baseline))
        if addon.get("enabled") and addon.get("kind", "map") == "map":
            _walk({"d": main.get("mcd_donor"), "s": main.get("sound_occ_stub")}, needed)
    return needed, held - needed


def lock_files():
    return load_json(LOCK)["files"]


def store_assets():
    """sha256 names already uploaded to the store release (empty if there is none yet)."""
    rel = gh("api", "repos/%s/releases/tags/%s" % (REPO, STORE_TAG), "--jq", ".id", check=False)
    if rel.returncode != 0:
        return set()
    return set(gh_lines("api", "--paginate", "repos/%s/releases/%s/assets?per_page=100" % (REPO, rel.stdout.strip()),
                        "--jq", ".[].name"))


def ensure_store():
    if gh("release", "view", STORE_TAG, "--repo", REPO, check=False).returncode != 0:
        gh("release", "create", STORE_TAG, "--repo", REPO, "--prerelease",
           "--title", "Source store (not a build)",
           "--notes", "Every file the M3epbuggin catalogue names, stored under its sha256. "
                      "Read by `python m3ep.py fetch`. Not a release for players.")


def upload_missing(rels):
    """Upload each locked file in `rels` whose sha256 the store lacks. Staged
    under its sha256 by hard link, so a 180 MB sound bank costs no disk."""
    lock = lock_files()
    ensure_store()
    have = store_assets()
    todo = []
    for rel in sorted(rels):
        entry = lock.get(rel)
        if entry and entry["sha256"] not in have and entry["sha256"] not in {e["sha256"] for _, e in todo}:
            p = path_of(rel)
            if not os.path.isfile(p) or os.path.getsize(p) != entry["size"] or sha256_file(p) != entry["sha256"]:
                die("%s is missing or differs from %s; refusing to upload it." % (rel, LOCK))
            todo.append((rel, entry))
    if not todo:
        print("the store already has every file (%d)." % len(rels))
        return
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        for rel, entry in todo:
            staged = stage(path_of(rel), tmp, entry["sha256"])
            print("uploading %s (%.1f MB) as %s ..." % (rel, entry["size"] / 1e6, entry["sha256"][:16]))
            gh("release", "upload", STORE_TAG, staged, "--repo", REPO)
    have = store_assets()
    missing = [rel for rel, e in todo if e["sha256"] not in have]
    if missing:
        die("the store still lacks: %s" % ", ".join(missing))
    print("uploaded %d file(s)." % len(todo))


# --- commands ----------------------------------------------------------------

def cmd_fetch(args):
    lock = lock_files()
    needed, held = named_files()
    want = sorted(needed | (held if args.all else set()))
    todo = []
    for rel in want:
        entry = lock.get(rel)
        if not entry:
            print("  not in %s: %s" % (LOCK, rel))
            continue
        p = path_of(rel)
        if os.path.isfile(p) and os.path.getsize(p) == entry["size"] and sha256_file(p) == entry["sha256"]:
            continue
        todo.append((rel, entry))
    if not todo:
        print("all %d files present and matching." % len(want))
        return
    total = sum(e["size"] for _, e in todo)
    print("downloading %d file(s), %.1f MB ..." % (len(todo), total / 1e6))
    with tempfile.TemporaryDirectory(dir=HERE) as tmp:
        hashes = sorted({e["sha256"] for _, e in todo})
        for i in range(0, len(hashes), 20):
            cmd = ["release", "download", STORE_TAG, "--repo", REPO, "--dir", tmp, "--skip-existing"]
            for h in hashes[i:i + 20]:
                cmd += ["--pattern", h]
            gh(*cmd)
        for rel, entry in todo:
            src = os.path.join(tmp, entry["sha256"])
            if not os.path.isfile(src) or sha256_file(src) != entry["sha256"]:
                die("%s: the store's copy is missing or does not match its hash %s" % (rel, entry["sha256"]))
            place(src, path_of(rel))
            print("  %s" % rel)
    print("done.")


def cmd_add(args):
    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        die("no such file: %s" % src)
    name = (args.as_name or os.path.basename(src)).replace("\\", "/")
    rel = name if name.startswith(("sources/", "stock/")) else "sources/" + name
    dest = path_of(rel)
    if os.path.abspath(dest) != src:
        place(src, dest, link=args.link)
    digest, size = sha256_file(dest), os.path.getsize(dest)

    data = load_json(LOCK)
    old = data["files"].get(rel)
    data["files"][rel] = {"sha256": digest, "size": size}
    data["files"] = dict(sorted(data["files"].items()))
    save_json(LOCK, data)
    print("%s %s  %s  %d B%s" % ("updated" if old else "added", rel, digest[:16], size,
                                 "  (hard link)" if args.link else ""))
    if args.no_upload:
        print("not uploaded (--no-upload): run python m3ep.py upload before publishing.")
    else:
        upload_missing([rel])
    needed, held = named_files()
    if rel not in needed | held:
        print("\nNo add-on names %s yet. Point an entry in %s at it, e.g.\n"
              "  \"source\": \"%s\"" % (rel, CATALOGUE, rel))
    print("Commit %s and %s with your change." % (LOCK, CATALOGUE))


def cmd_upload(args):
    needed, held = named_files()
    rels = needed | (held & set(lock_files()) if args.all else set())
    upload_missing(rels)


def check(remote=True):
    lock = lock_files()
    needed, held = named_files()
    problems, notes = [], []
    assets = store_assets() if remote else None
    if remote and not assets:
        notes.append("%s has no '%s' release yet (or gh cannot read it) -- run: python m3ep.py upload"
                     % (REPO, STORE_TAG))
    for rel in sorted(needed):
        entry = lock.get(rel)
        if not entry:
            problems.append("%s is named by the catalogue but not in %s -- run: python m3ep.py add <file> --as %s"
                            % (rel, LOCK, rel[len("sources/"):] if rel.startswith("sources/") else rel))
            continue
        p = path_of(rel)
        if not os.path.isfile(p):
            problems.append("%s is missing here -- run: python m3ep.py fetch" % rel)
        elif os.path.getsize(p) != entry["size"] or sha256_file(p) != entry["sha256"]:
            problems.append("%s differs from %s -- if the change is meant, run: python m3ep.py add %s --as %s"
                            % (rel, LOCK, rel, rel))
        if assets is not None and entry["sha256"] not in assets:
            problems.append("%s (%s) is not in the store -- run: python m3ep.py upload"
                            % (rel, entry["sha256"][:16]))
    for rel in sorted(held):
        if rel not in lock:
            notes.append("disabled add-on names %s, which is not in the store (fine until it is enabled)" % rel)
    return problems, notes


def cmd_check(args):
    problems, notes = check(remote=not args.local)
    for n in notes:
        print("  note: " + n)
    if problems:
        die("\n".join("  " + p for p in problems))
    print("every named file is present, matches %s%s." % (LOCK, "" if args.local else " and is in the store"))


def channel():
    """latest.json on main, through the API (the raw URL caches for minutes)."""
    live = gh("api", "repos/%s/contents/latest.json?ref=main" % REPO,
              "-H", "Accept: application/vnd.github.raw", check=False)
    return json.loads(live.stdout) if live.returncode == 0 and live.stdout.strip() else None


def published_versions():
    """Every version this repository has a release for, plus the live channel's."""
    tags = gh_lines("api", "--paginate", "repos/%s/releases?per_page=100" % REPO, "--jq", ".[].tag_name")
    seen = {t[len(TAG_PREFIX):] for t in tags if t.startswith(TAG_PREFIX)}
    live = channel()
    if live:
        seen.add(live["version"])
    return seen


def cmd_status(args):
    live = channel()
    if not live:
        print("published: (nothing yet -- no latest.json on main)")
        return
    tag = TAG_PREFIX + live["version"]
    print("published      : %s  (%s)" % (live["version"], live.get("released", "")))
    print("bundle         : %s  %d B  sha256 %s" % (live["bundle_url"], live["size"], live["sha256"][:16]))
    rel = gh("api", "repos/%s/releases/tags/%s" % (REPO, tag), check=False)
    if rel.returncode != 0:
        print("release %s    : MISSING -- players' launchers cannot download this build" % tag)
        return
    rel = json.loads(rel.stdout)
    assets = {a["name"]: a for a in rel.get("assets", [])}
    name = live["bundle_url"].rsplit("/", 1)[-1]
    asset = assets.get(name)
    print("release        : %s, %s, asset %s" % (
        tag, "pre-release" if rel["prerelease"] else "NOT a pre-release (fix it: it takes over releases/latest)",
        "%d B%s" % (asset["size"], "" if asset["size"] == live["size"] else " -- SIZE DIFFERS from latest.json")
        if asset else "MISSING"))


def next_version():
    numbers = [int(m.group(1)) for v in published_versions() for m in [VERSION_RE.match(v)] if m]
    return "%s-m%d" % (time.strftime("%Y.%m.%d", time.gmtime()), max(numbers, default=0) + 1)


def cmd_next(args):
    print(next_version())


def build(version, notes, dry_run):
    cmd = [sys.executable, os.path.join(HERE, "make_release.py"),
           "--track", TRACK, "--catalogue", path_of(CATALOGUE),
           "--out", path_of("%s/%s" % (DIST, TRACK)), "--version", version, "--notes", notes]
    if dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, cwd=HERE)
    if proc.returncode != 0:
        die("make_release failed.")
    print("\n(`python m3ep.py publish` does the PUBLISH steps above, into %s.)" % REPO)


def cmd_build(args):
    if not VERSION_RE.match(args.version):
        die("version %r does not look like 2026.10.02-m1" % args.version)
    problems, _ = check(remote=False)
    if problems:
        die("\n".join("  " + p for p in problems))
    build(args.version, args.notes, args.dry_run)


def cmd_publish(args):
    if not args.notes:
        die("--notes is required: one line saying what this build changes. Players read it.")
    gh("auth", "status")
    run(["git", "fetch", "origin"])
    if run(["git", "status", "--porcelain", "--untracked-files=no"]).stdout.strip():
        die("You have uncommitted changes. Commit and push the catalogue and %s first, so that\n"
            "what is published is what the repository says." % LOCK)
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    upstream = run(["git", "rev-parse", "origin/main"]).stdout.strip()
    if head != upstream:
        die("Your main is not origin/main. Pull (git pull --rebase) and push your commits first.")

    # --no-store: publish the bundle without the source store. The store would put
    # stock game files (the CE exe, the whole MAPS.SM0) into a public release;
    # players never need it, only the bundle.
    problems, _ = check(remote=not args.no_store)
    if problems:
        die("\n".join("  " + p for p in problems))

    version = args.version or next_version()
    if not VERSION_RE.match(version):
        die("version %r does not look like 2026.10.02-m1" % version)
    if version in published_versions():
        die("%s is already published. Take the next one: python m3ep.py next" % version)
    tag = TAG_PREFIX + version
    print("publishing %s ..." % tag)

    build(version, args.notes, dry_run=args.dry_run)
    if args.dry_run:
        print("\n--dry-run: nothing published.")
        return

    out = "%s/%s" % (DIST, TRACK)
    bundle = path_of("%s/%s" % (out, BUNDLE % version))
    latest = load_json("%s/latest.json" % out)
    if latest["version"] != version or latest["sha256"] != sha256_file(bundle) \
            or latest["size"] != os.path.getsize(bundle):
        die("%s/latest.json does not describe the bundle just built." % out)
    want_url = "https://github.com/%s/releases/download/%s/%s" % (REPO, tag, BUNDLE % version)
    if latest["bundle_url"] != want_url:
        die("bundle_url is %s, expected %s" % (latest["bundle_url"], want_url))

    # 1. the release first, as a PRE-release: releases/latest must never resolve to it
    title = "%s (%s)" % (re.split(r"[;.]", args.notes)[0].strip()[:80], version)
    body = "%s\n\nPick M3epbuggin in the modified ScdaLauncher.exe and press PLAY." % args.notes
    gh("release", "create", tag, bundle, "--repo", REPO, "--prerelease", "--title", title, "--notes", body)

    # 2. then the channel file, which names it
    shutil.copyfile(path_of("%s/latest.json" % out), path_of("latest.json"))
    run(["git", "add", "latest.json"])
    run(["git", "commit", "-m", "m3epbuggin %s: %s" % (version, args.notes)])
    if run(["git", "push", "origin", "HEAD:main"], check=False).returncode != 0:
        run(["git", "pull", "--rebase", "origin", "main"])
        if load_json("latest.json")["version"] != version:
            die("Someone else published while you built. Your release %s exists but the channel\n"
                "names theirs. Rebuild on top of theirs with a new version." % tag)
        run(["git", "push", "origin", "HEAD:main"])

    # 3. verify through the API, not the cached raw URL
    live = channel()
    rel = gh_json("api", "repos/%s/releases/tags/%s" % (REPO, tag))
    asset = {a["name"]: a for a in rel.get("assets", [])}.get(BUNDLE % version)
    if not live or live["version"] != version or not rel["prerelease"] or not asset \
            or asset["size"] != latest["size"]:
        die("verification failed: check the release and latest.json by hand.")
    print("\npublished %s. Launchers see it once raw.githubusercontent.com's cache expires (about 5 minutes)."
          % version)


# --- the other channels' catalogues, reduced to what the build checks against ---

KEEP_TOP = ("track", "name", "install_root", "voice_server", "mcd_donor", "sound_occ_stub", "baseline_sources")
KEEP_ADDON = ("enabled", "kind", "code", "title", "map_id", "title_key", "after")
KEEP_FILE = ("install_path", "base", "force_full", "over")


def _claims(cat, source_name):
    out = {"_comment": [
        "CLAIMS COPY of the %s catalogue (%s), written by `python m3ep.py claims`." % (cat.get("track"), source_name),
        "It holds only what make_release.py reads from another channel's catalogue: its add-on codes,",
        "map IDs, menu keys, install paths and overrides (the cross-channel checks), and on main the",
        "stock-file table this channel inherits. Comments and source paths are left out. Never built:",
        "it is locked, and the files it once named are not here."]}
    for key in KEEP_TOP:
        if key in cat:
            value = cat[key]
            if isinstance(value, dict):
                value = {k: v for k, v in value.items() if not k.startswith("_")}
            out[key] = value
    if "install_root" in out:
        out["install_root"] = ""
    out["locked"] = True
    out["locked_because"] = "A claims copy: the cross-channel checks read it; it is never built from here."
    addons = []
    for a in cat.get("addons", []):
        row = {k: a[k] for k in KEEP_ADDON if k in a}
        occ = a.get("sound_occ", "stub")
        if a.get("kind", "map") == "map":
            row["sound_occ"] = occ if occ in (None, "none", "stub") else "own"
        if a.get("kind") == "files":
            row["files"] = [{k: e[k] for k in KEEP_FILE if k in e} for e in a.get("files", [])]
        if a.get("extra_files"):
            row["extra_files"] = [{k: e[k] for k in KEEP_FILE if k in e} for e in a["extra_files"]]
        addons.append(row)
    out["addons"] = addons
    return out


def cmd_claims(args):
    for src, dest in ((args.main, MAIN_CATALOGUE), (args.experimental, EXP_CATALOGUE)):
        with open(src, encoding="utf-8") as fh:
            cat = json.load(fh)
        save_json(dest, _claims(cat, os.path.basename(src)))
        print("wrote %s: %d add-on(s) of the %s catalogue" % (dest, len(cat.get("addons", [])), cat.get("track")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch", help="download every file the catalogue names")
    p.add_argument("--all", action="store_true", help="also the files only disabled add-ons name")
    p.set_defaults(func=cmd_fetch)
    p = sub.add_parser("add", help="store a new or changed file under sources/ (and upload it)")
    p.add_argument("file")
    p.add_argument("--as", dest="as_name", help="name under sources/ (default: the file's own name), "
                                                "or a full stock/... path")
    p.add_argument("--link", action="store_true", help="hard-link instead of copying (same disk only)")
    p.add_argument("--no-upload", action="store_true", help="lock it only; upload later with `upload`")
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("upload", help="upload every named, locked file the store does not have")
    p.add_argument("--all", action="store_true", help="also the files only disabled add-ons name")
    p.set_defaults(func=cmd_upload)
    p = sub.add_parser("check", help="every named file present, locked and uploaded")
    p.add_argument("--local", action="store_true", help="skip the store lookup")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("status", help="what is published here")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("next", help="print the next free M3epbuggin version")
    p.set_defaults(func=cmd_next)
    p = sub.add_parser("build", help="build the bundle into dist/m3epbuggin/ without publishing")
    p.add_argument("--version", required=True)
    p.add_argument("--notes", default="")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_build)
    p = sub.add_parser("publish", help="build, release and point the channel at it")
    p.add_argument("--version", help="default: the next free one")
    p.add_argument("--notes", default="")
    p.add_argument("--dry-run", action="store_true", help="check and build, publish nothing")
    p.add_argument("--no-store", action="store_true",
                   help="do not require the source store (sources stay on this PC)")
    p.set_defaults(func=cmd_publish)
    p = sub.add_parser("claims", help="refresh slots.json / slots-experimental.json from the real catalogues")
    p.add_argument("--main", required=True, help="the main channel's slots.json")
    p.add_argument("--experimental", required=True, help="the experimental channel's slots-experimental.json")
    p.set_defaults(func=cmd_claims)
    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
