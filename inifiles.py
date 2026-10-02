"""Editing the two shared files a map slot has to appear in.

`Packages\\MapPaths.ini` and `Packages\\_Common\\Texts\\ENG\\Menu_text.eng` are
both plain latin-1 INI with CRLF line endings, and both are shared: every slot
the player has -- ours, theirs, anyone's -- lives in the same two files. So the
patcher **merges** them line by line and never ships a copy. A member who added
their own slot keeps it; a member on a different CE build keeps whatever CE gave
them.

That is the whole reason these two are handled here instead of as ordinary
payload files: overwriting either one would take away exactly the thing the
player owns.

Both writers are idempotent, and both have an inverse, so installing an add-on
twice changes nothing and removing one leaves no trace.
"""

from __future__ import annotations

import re
import struct

ENCODING = "latin-1"
EOL = "\r\n"

PATH_LINE = re.compile(
    r'^PathsMapName\[(\d+)\]=\(Directory="([^"]*)",Map="([^"]*)"\)', re.MULTILINE
)
MENU_SECTION = "Menu_ALL_MAP_NAME_MAP_%s"


def decode(data: bytes) -> str:
    return data.decode(ENCODING)


def encode(text: str) -> bytes:
    return text.encode(ENCODING)


# --- MapPaths.ini ---------------------------------------------------------


def read_slots(text: str):
    """[(index, directory, code)] in file order."""
    return [(int(n), d, m) for n, d, m in PATH_LINE.findall(text)]


def _renumber(text: str) -> str:
    """Rewrite only the bracket numbers, in place. Every other byte survives --
    the shipped file mixes LF and CRLF, and re-rendering it would rewrite lines
    nobody asked us to touch."""
    counter = [0]

    def replace(match):
        index = counter[0]
        counter[0] += 1
        return 'PathsMapName[%d]=(Directory="%s",Map="%s")' % (index, match.group(2), match.group(3))

    return PATH_LINE.sub(replace, text)


def _line_end(text: str, pos: int) -> str:
    if text.startswith("\r\n", pos):
        return "\r\n"
    if text.startswith("\n", pos):
        return "\n"
    return EOL


def mappaths_add(text: str, code: str, directory: str = "_Common", after: str = None):
    """Give `code` a slot. Idempotent.

    `after` names the map it should sit behind, so an add-on can land next to
    the map it belongs with -- "Night Waves" directly after "Dawn Waves" --
    rather than always at the bottom of the list. The index is not chosen here:
    every entry is renumbered densely afterwards, because the engine wants a
    0..n-1 run and position in the file is what actually decides order.

    An unknown `after` appends, which is the honest fallback: a player whose
    install does not have that map still gets the slot.
    """
    for index, _d, existing in read_slots(text):
        if existing.upper() == code.upper():
            return text, False, index

    matches = list(PATH_LINE.finditer(text))
    line = 'PathsMapName[0]=(Directory="%s",Map="%s")' % (directory, code)

    anchor = None
    if after:
        for match in matches:
            if match.group(3).upper() == after.upper():
                anchor = match
                break
    if anchor is None and matches:
        anchor = matches[-1]

    if anchor is not None:
        eol = _line_end(text, anchor.end())
        new = text[: anchor.end()] + eol + line + text[anchor.end():]
        position = matches.index(anchor) + 1
    else:
        new = text + ("" if not text or text.endswith(("\n", "\r")) else EOL) + line + EOL
        position = 0
    return _renumber(new), True, position


def mappaths_reorder(text: str, codes):
    """Rewrite the map list in a given order, in place.

    Order is not cosmetic here: the map ID a description carries IS its index in
    this file, and the eight shipped descriptions carry 0-7. So the stock maps
    have to hold the first eight lines, in their own order, or every one of them
    points at somebody else's level. A player who hand-added a map anywhere but
    the end has exactly that, and this is what puts it right.

    Only the `PathsMapName` lines are touched, one substitution per line, so
    every other byte and every line ending survives.
    """
    present = read_slots(text)
    directories = {code.upper(): directory for _index, directory, code in present}
    wanted = [code.upper() for code in codes]
    if sorted(wanted) != sorted(code.upper() for _i, _d, code in present):
        raise ValueError("a reorder must keep exactly the same maps")

    counter = [0]

    def replace(_match):
        index = counter[0]
        counter[0] += 1
        code = wanted[index]
        return 'PathsMapName[%d]=(Directory="%s",Map="%s")' % (index, directories[code], code)

    return PATH_LINE.sub(replace, text)


def mappaths_remove(text: str, code: str):
    """Take `code` out and renumber densely -- the indexes must stay a dense
    0..n-1 run, so removing a middle entry has to renumber the ones after it."""
    for match in PATH_LINE.finditer(text):
        if match.group(3).upper() != code.upper():
            continue
        end = match.end()
        for eol in ("\r\n", "\n"):
            if text.startswith(eol, end):
                end += len(eol)
                break
        else:
            # last line with no terminator: take the one in front of it instead
            start = match.start()
            for eol in ("\r\n", "\n"):
                if text.endswith(eol, 0, start):
                    return _renumber(text[: start - len(eol)] + text[end:]), True
        return _renumber(text[: match.start()] + text[end:]), True
    return text, False


# --- Menu_text.eng --------------------------------------------------------


def _menu_pattern(key: str):
    return re.compile(
        r'(\[%s\]\s*\r?\n\s*Text=")([^"]*)(")' % re.escape(MENU_SECTION % key)
    )


def menutext_title(text: str, key: str):
    """The title currently shown for a title key, or None."""
    match = _menu_pattern(key).search(text)
    return match.group(2) if match else None


def menutext_set(text: str, key: str, title: str):
    """Name the slot. Rewrites an existing title rather than leaving it alone:
    CE ships keys 09 and 10 as "Kinshasa" and "Secret Base", so a slot dropped
    on one of those appears in the menu under the name of a different map, and
    a menu entry that lies about what it loads is worse than no entry."""
    section = "[%s]" % (MENU_SECTION % key)
    pattern = _menu_pattern(key)
    match = pattern.search(text)
    if match:
        if match.group(2) == title:
            return text, False, match.group(2)
        was = match.group(2)
        return pattern.sub(lambda g: g.group(1) + title + g.group(3), text, 1), True, was
    if section in text:
        # the section is there but carries no Text= line; leave it alone and say so
        return text, False, None
    lead = "" if (not text or text.endswith(("\n", "\r"))) else EOL
    return text + lead + section + EOL + 'Text="%s"' % title + EOL, True, None


def menutext_remove(text: str, key: str):
    """Drop the whole section again. Only the section's own lines go -- taking
    the newline in front of it with them would eat the previous line's ending."""
    section = re.escape("[%s]" % (MENU_SECTION % key))
    pattern = re.compile(r'%s[ \t]*\r?\n[ \t]*Text="[^"]*"[ \t]*(?:\r?\n)?' % section)
    new = pattern.sub("", text, 1)
    return (new, True) if new != text else (text, False)


# --- key binds in PlayerProfilePC.ini -------------------------------------
#
# The player's own file: name, login, sensitivity, volumes and every key bind
# the in-game menu writes. It is never shipped (make_release refuses it); an
# add-on that needs a key adds ITS OWN `PCBindings=` line, found again by its
# ActionName, and takes exactly that line back out when it goes. Operator
# 2026-09-24: "the launcher can ship keybinds and you will. if someone
# downloads the coop move needs to be ready on N".

#
# The game reads a player's binds from its own copy, one file per profile:
# %ProgramData%\Ubisoft\SplinterCell4\Save\<dir>\PlayerProfilePC_<profile>.ini
# (the exe: SHGetFolderPath CSIDL_COMMON_APPDATA + "\PlayerProfilePC_%s.ini").
# System\PlayerProfilePC.ini is only the template a NEW profile is made from.
# The game writes its copy with every struct field tagged by a name id --
# `ActionName§(8495)="JumpSpy",Command§(447)=...` -- so a line merged into it
# takes the tags from a row the file already has (keybind_dialect).

KEYBIND_LINE = re.compile(r'^PCBindings=\(ActionName[^=]*="([^"]+)"', re.IGNORECASE)
KEYBIND_FIELD = re.compile(r'([(,])([A-Za-z]+)(\xa7\(\d+\))?(?=[\[=])')


def keybind_action(line: str):
    """The ActionName a `PCBindings=(...)` line binds, or None for any other line.
    Plain (`ActionName="X"`) and saved (`ActionName§(8495)="X"`) rows alike."""
    match = KEYBIND_LINE.match(line.strip())
    return match.group(1) if match else None


def keybind_dialect(text: str, line: str) -> str:
    """`line` spelled the way `text` spells its PCBindings rows.

    A file the game saved tags each field (`Cat§(8498)=`); the tags are copied
    from the file's own first row, never guessed. A plain file, or a field the
    file's rows do not carry, keeps the plain spelling."""
    tags = {}
    for body, _end in _lines(text):
        if body.startswith("PCBindings="):
            for _sep, name, tag in KEYBIND_FIELD.findall(body):
                if tag:
                    tags.setdefault(name.lower(), tag)
            if tags:
                break
    if not tags:
        return line

    def spell(match):
        name = match.group(2)
        return match.group(1) + name + tags.get(name.lower(), match.group(3) or "")

    return KEYBIND_FIELD.sub(spell, line)


def _lines(text: str):
    """(line without its end, its end) in file order; nothing is re-rendered."""
    out, pos = [], 0
    for match in re.finditer(r"\r\n|\n", text):
        out.append((text[pos:match.start()], match.group(0)))
        pos = match.end()
    if pos < len(text):
        out.append((text[pos:], ""))
    return out


def keybind_set(text: str, line: str):
    """Make `line` the bind for its ActionName. Idempotent.

    A line with the same ActionName is replaced in place (and any duplicate of
    it dropped); otherwise the new line goes directly after the last
    `PCBindings=` line, with that line's own ending. Returns (text, changed).
    """
    line = line.strip()
    action = keybind_action(line)
    if action is None:
        raise ValueError("not a PCBindings line: %r" % line)
    line = keybind_dialect(text, line)
    rows = _lines(text)
    mine = [i for i, (body, _end) in enumerate(rows)
            if (keybind_action(body) or "").lower() == action.lower()]
    if mine:
        if len(mine) == 1 and rows[mine[0]][0] == line:
            return text, False
        first = mine[0]
        rows[first] = (line, rows[first][1] or EOL)
        rows = [r for i, r in enumerate(rows) if i == first or i not in mine]
    else:
        binds = [i for i, (body, _end) in enumerate(rows) if body.startswith("PCBindings=")]
        if binds:
            at = binds[-1]
            end = rows[at][1] or EOL
            if not rows[at][1]:
                rows[at] = (rows[at][0], end)
            rows.insert(at + 1, (line, end))
        else:
            if rows and not rows[-1][1]:
                rows[-1] = (rows[-1][0], EOL)
            rows.append((line, EOL))
    return "".join(body + end for body, end in rows), True


def keybind_remove(text: str, action: str):
    """Take every bind for `action` out. The inverse of keybind_set."""
    rows = _lines(text)
    keep = [r for r in rows if (keybind_action(r[0]) or "").lower() != action.lower()]
    if len(keep) == len(rows):
        return text, False
    return "".join(body + end for body, end in keep), True


# --- map IDs, read straight out of a .mcd ---------------------------------

# A .mcd is a tiny package whose MapDescription export starts at a fixed offset
# for a given file size -- every 5-character code clones the same donor, so the
# layout is identical. Measured across all 13 shipped descriptions:
#   465 bytes (5-char codes) -> export at 305, map ID at 307
#   454 bytes (DWG, 3 chars) -> export at 301, map ID at 303
# Reading the byte directly means the frozen exe needs no package parser.
MCD_ID_OFFSETS = {465: 307, 454: 303}


def mcd_id_offset(data: bytes) -> int:
    """Where the map ID byte sits: two bytes into the export's serial data, which
    begins where the name table ends. Derived rather than looked up by file size,
    because `MMap_blocked` makes a description 463 bytes and no size table can
    keep up with that."""
    offset = _name_table_end(data) + 2
    known = MCD_ID_OFFSETS.get(len(data))
    if known is not None and known != offset:
        raise ValueError("description layout disagrees: derived %d, measured %d"
                         % (offset, known))
    return offset


def mcd_map_id(data: bytes):
    """The map ID a description file claims, or None if the layout is unknown."""
    try:
        offset = mcd_id_offset(data)
    except (ValueError, IndexError, struct.error):
        return None
    return data[offset] if offset < len(data) else None


# The eight menu-name keys the game actually defines. `Menu_text.eng` is only the
# ENGLISH TEXT for a key -- the key itself has to exist in the compiled registry
# `Packages\_Common\Texts\Menu_Text.ute`, which ships exactly fourteen and is
# never regenerated. A5..A8 style keys belong to the eight stock maps; 09..14 are
# the only ones an added map can take. Invent a key outside this set and the
# description's GameString import does not resolve, so the slot shows no name of
# its own -- writing the section into the .eng changes nothing.
SHIPPED_TITLE_KEYS = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
                      "09", "10", "11", "12", "13", "14")
# Keys a CHANNEL mints in its own copy of the registry (3.17): 20-29, shipped by
# the experimental channel's MAPKEY add-on (channels.TRACKS["experimental"]).
# Never given to a player's own map -- adopt_foreign_maps names stock keys only.
MINTED_TITLE_KEYS = tuple("%02d" % n for n in range(20, 30))


def registry_defines(data: bytes, key: str) -> bool:
    """Whether a Menu_Text.ute's name table carries this map-name key.

    A name-table entry is length-prefixed and NUL-terminated; the export of the
    same name is what the description's GameString import resolves to, and a
    key the registry does not name cannot be exported by it."""
    name = (MENU_SECTION % key).encode(ENCODING)
    return bytes([len(name) + 1]) + name + bytes(1) in data


STOCK_MAP_TITLE_KEYS = {"BLKG1": "A1", "MOTG4": "A2", "TERG5": "A3", "REDG6": "A4",
                        "BOSG2": "A5", "DWG": "A6", "USSG8": "A7", "SLHG7": "A8"}

# The rotating 3D model the lobby draws for a map lives in
# `Packages\_Common\Animations\Menu_anm.ukx` as `MMap_<name>_msh`, and the
# description names which one. There are eight, one per stock map, plus
# `MMap_blocked` for "no preview". A clone that does not rename this field keeps
# the DONOR's model, which is why every Boss House clone drew Boss House.
PREVIEW_FOR = {"BLKG1": "MMap_Ind01_msh", "MOTG4": "MMap_Ind02_msh",
               "TERG5": "MMap_Ind03_msh", "SLHG7": "MMap_Ind04_msh",
               "REDG6": "MMap_Frq01_msh", "BOSG2": "MMap_Frq02_msh",
               "DWG": "MMap_Shp01_msh", "USSG8": "MMap_Shp02_msh",
               # the game's own "no preview" placeholder. It is the honest choice
               # for a map that is not a variant of a stock one -- and it is TWO
               # CHARACTERS SHORTER than every other model, so it cannot be renamed
               # in place. `rename_in_name_table` resizes the package for it.
               "blocked": "MMap_blocked"}
PREVIEW_NAMES = tuple(sorted(set(PREVIEW_FOR.values())))
PREVIEW_PATTERN = re.compile(rb"MMap_(?:[A-Za-z0-9]{5}_msh|blocked)")


def resolve_preview(preview: str) -> str:
    """Accept a stock map code ("DWG"), "blocked", or the model itself."""
    if preview in PREVIEW_FOR:
        return PREVIEW_FOR[preview]
    if preview in PREVIEW_NAMES:
        return preview
    raise ValueError(
        "unknown lobby preview %r -- name a stock map (%s) or a model (%s)"
        % (preview, ", ".join(sorted(PREVIEW_FOR)), ", ".join(PREVIEW_NAMES)))


def mcd_title_key(data: bytes):
    """The menu-name key a description points at, or None."""
    match = re.search(rb"Menu_ALL_MAP_NAME_MAP_(..)", data)
    return match.group(1).decode(ENCODING) if match else None


def mcd_preview(data: bytes):
    """The lobby model a description names, or None."""
    match = PREVIEW_PATTERN.search(data)
    return match.group(0).decode() if match else None


# --- resizing one name-table entry ----------------------------------------
#
# Every rename in `mint_mcd` is same-length on purpose, because a package is a
# web of byte offsets. `MMap_blocked` is the one that cannot be: it is 12
# characters where every other lobby model is 14. Resizing means moving the
# export serial data, so three fields have to follow it -- the import and export
# table offsets in the header, and the export entry's own SerialOffset, which is
# the last compact index in the file.
#
# Gate: renaming a shipped description and renaming it back reproduces the
# original bytes, for all 11 shipped .mcd files. `selftest()` runs it.


def _compact(value: int) -> bytes:
    """Unreal's signed compact index."""
    out = bytearray()
    negative = value < 0
    value = abs(value)
    first = value & 0x3F
    if negative:
        first |= 0x80
    value >>= 6
    if value:
        first |= 0x40
    out.append(first)
    while value:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        out.append(byte)
    return bytes(out)


def _name_table_end(data: bytes) -> int:
    """Also where the export's serial data starts -- the two are adjacent in
    every shipped description, which is what makes the map ID findable without
    a package parser."""
    position = struct.unpack_from("<I", data, 16)[0]
    for _ in range(struct.unpack_from("<I", data, 12)[0]):
        position += 1 + data[position] + 4
    return position


def rename_in_name_table(data: bytes, old: str, new: str) -> bytes:
    """Rewrite one name-table entry, resizing the package when the lengths differ."""
    out = bytearray(data)
    count, start = struct.unpack_from("<I", out, 12)[0], struct.unpack_from("<I", out, 16)[0]
    position, found = start, None
    for _ in range(count):
        length = out[position]
        if out[position + 1:position + length] == old.encode(ENCODING):
            found = (position, length)
            break
        position += 1 + length + 4
    if found is None:
        raise ValueError("name %r is not in the table" % old)

    position, length = found
    entry = (bytes([len(new) + 1]) + new.encode(ENCODING) + b"\x00"
             + bytes(out[position + 1 + length:position + 1 + length + 4]))
    delta = len(entry) - (1 + length + 4)

    if delta:
        serial = _name_table_end(out)
        export_offset = struct.unpack_from("<I", out, 24)[0]
        import_offset = struct.unpack_from("<I", out, 32)[0]
        was, now = _compact(serial), _compact(serial + delta)
        exports = bytes(out[export_offset:])
        if not exports.endswith(was):
            raise ValueError(
                "the export table does not end with the serial offset %d -- refusing to "
                "resize a layout this code does not recognise" % serial)
        struct.pack_into("<I", out, 24, export_offset + delta)
        struct.pack_into("<I", out, 32, import_offset + delta)
        out = bytearray(out[:export_offset]) + bytearray(exports[:-len(was)] + now)

    out[position:position + 1 + length + 4] = entry
    return bytes(out)


def mint_mcd(donor: bytes, donor_code: str, code: str, map_id: int, title_key: str,
              preview: str = None) -> bytes:
    """Build a slot's description file by renaming a shipped one in place.

    Recipe and both traps from `toolbox/add_slot.py`:

    * **The map ID must be unused.** A description cloned from Boss House keeps
      ID 1 and the new slot silently loads Boss House -- not a rejection, not a
      whitelist, it resolves to whatever ID it carries.
    * **Strings are renamed IN PLACE, so the new code must be the same length as
      the donor's**, and the longest strings must go first or the bare code
      corrupts the longer ones that contain it.
    * **The lobby model is a THIRD identity the donor carries.** `preview` names
      it; leave it out and the slot draws the donor's map in the map-select and
      lobby panels no matter what it is called.
    * **`title_key` must be one the game defines** -- see `SHIPPED_TITLE_KEYS`.
      A key outside that set leaves the slot with no name of its own.
    """
    if len(code) != len(donor_code):
        raise ValueError(
            "map code %r must be %d characters to rename %s's description in place"
            % (code, len(donor_code), donor_code)
        )
    if len(title_key) != 2:
        raise ValueError(
            "title key %r must be 2 characters -- it is renamed in place over the "
            "donor's own key (Boss House ships A5)" % title_key
        )
    if title_key not in SHIPPED_TITLE_KEYS + MINTED_TITLE_KEYS:
        raise ValueError(
            "title key %r is not one the game defines. The stock Menu_Text.ute ships %s "
            "and a channel's own registry adds %s; any other key does not resolve and the "
            "slot shows no name -- adding the section to Menu_text.eng does not help."
            % (title_key, ", ".join(SHIPPED_TITLE_KEYS), ", ".join(MINTED_TITLE_KEYS)))
    data = bytes(donor)
    pairs = [
        (b"Menu_ALL_MAP_NAME_MAP_A5", (MENU_SECTION % title_key).encode()),
        (b"PKG_%s_Desc" % donor_code.encode(), b"PKG_%s_Desc" % code.encode()),
        (b"%s_back.dds" % donor_code.encode(), b"%s_back.dds" % code.encode()),
        (b"%s_Desc" % donor_code.encode(), b"%s_Desc" % code.encode()),
        (donor_code.capitalize().encode() + b"_Wait", code.capitalize().encode() + b"_Wait"),
        (donor_code.encode(), code.encode()),
    ]
    for before, after in pairs:
        if len(before) != len(after):
            raise ValueError("length mismatch %r -> %r" % (before, after))
        data = data.replace(before, after)

    if preview:
        donor_model = mcd_preview(data)
        if donor_model is None:
            raise ValueError("%s's description names no lobby model to rename" % donor_code)
        data = rename_in_name_table(data, donor_model, resolve_preview(preview))

    out = bytearray(data)
    out[mcd_id_offset(data)] = map_id
    return bytes(out)
