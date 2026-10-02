"""The update tracks, defined once and read by everything else.

(This copy adds a third track, `m3epbuggin`, published from its own repository;
see TRACKS below. The text that follows describes the original two.)

The updater ships **two channels**, and a channel is nothing more than a
`latest.json` served from a different branch of the same GitHub repo:

    main          the build the community runs. Finished work only -- new maps
                  and permanent game changes alike.
    experimental  the playground. Whatever is being tried this week, with
                  whoever wants to try it.

They share one repo, one exe and one install. What keeps them from standing on
each other is entirely in this file:

* **Separate branches.** `latest.json` on `main` and `latest.json` on
  `experimental`. Publishing to one cannot touch the other.
* **Separate catalogues.** `slots.json` and `slots-experimental.json`. A release
  builds from exactly one of them and refuses if the file says otherwise, so no
  flag typed at 3am can put a test map into the community release.
* **Separate map-ID and menu-key ranges.** Every slot a track ships is its own
  slot, so a player can hold the finished Kinshasa and an experimental Kinshasa
  at the same time and pick between them in the map list.
* **Experimental releases are GitHub PRE-RELEASES.** This is load-bearing:
  `releases/latest/download/ScdaPatcher.exe` -- the link the community is given
  -- resolves to the newest release that is *not* a pre-release. Publish an
  experimental build as a normal release and that link starts handing out
  whatever exe was attached to a test build, or 404s if none was.

Both `channel_url` values are compiled into the exe, so they are the two values
that cannot be changed later without handing out a new exe.

THE BASE GAME is the one thing that is not a channel. A channel ships
differences against a game the player already owns; `BASE_GAME` is the whole
game, for somebody who has nothing. It is one zip on a fixed release tag and one
descriptor (`base-game.json`) on the main branch naming its size and hash. The
launcher fetches the descriptor, downloads the image, checks the hash, unpacks
it into a folder the player chose, and from then on that folder is an install
like any other -- every version installs on top of it.
"""

from __future__ import annotations

# Renamed from SCDA-Updater on 2026-09-20 (operator: "rename the github repo to
# SCDA-Launcher"). GitHub keeps redirecting the old name for as long as nobody
# creates a repo called SCDA-Updater again -- the exes handed out before the
# rename depend on that, so that name must stay unused.
REPO = "REALSYNCADE/SCDA-Launcher"
RAW = "https://raw.githubusercontent.com/%s/{branch}/latest.json" % REPO
ASSET = "https://github.com/%s/releases/download/{tag}/{bundle}" % REPO

# --- the full game, for somebody who has no game -----------------------------
BASE_ASSET = "https://github.com/%s/releases/download/{tag}/{image}" % REPO
BASE_GAME = {
    "label": "Community Edition",
    # A tag per image version, published as a PRE-release so `releases/latest`
    # keeps resolving to the launcher. The tag carries the version because the
    # image is replaced only when the game itself changes, never per channel
    # release -- 1.1 was the stock game, 1.1-kinshasa the standard game.
    "tag": "base-{version}",
    "descriptor_url": "https://raw.githubusercontent.com/%s/main/base-game.json" % REPO,
    # what the launcher suggests when it has to create the folder itself
    "default_folder": "SCDA Community Edition",
}

# --- SCDA (heartbeat): a second whole game, in a folder of its own ------------
#
# Operator 2026-09-20, with Downloads/SCDA-Online.rar: "this is the vanilla
# heartbeat version. Add that to the launcher so people can start it like the
# CE ... or experimental version", and: "this is the full game and you can
# upload it like that". It is its own build of the game -- its own exe and
# script packages, the maps in Packages/01..08 rather than _Common/MapsPC -- so
# it cannot be a set of files switched on inside a Community Edition folder.
# It is a second image, unpacked into a second folder, and starting it never
# reads or writes the Community Edition install. Nothing is ever patched into
# it: no channel, no add-ons, no profile switch. The image carries every file
# of his archive, unchanged.
HEARTBEAT_GAME = {
    "label": "SCDA (heartbeat)",
    "tag": "heartbeat-{version}",
    "image_template": "scda-heartbeat-{version}.zip",
    "descriptor": "heartbeat-game.json",
    "descriptor_url": "https://raw.githubusercontent.com/%s/main/heartbeat-game.json" % REPO,
    "default_folder": "SCDA Online (heartbeat)",
    # What tells this tree apart from Community Edition: the numbered package
    # folders. CE has `_Common` under Packages and nothing else. It is NOT the
    # absence of _Common/MapsPC -- his heartbeat tree has that folder too (the
    # menu and entry maps, and his Kinshasa and Secret Base files), and a first
    # marker built on its absence let the real image be patched as if it were
    # Community Edition. Found by installing the real image, 2026-09-20; the
    # fake tree in the tests has carried a _Common/MapsPC ever since.
    "marker": "Packages/01/MapsPC",
    "config_key": "heartbeat_install",
}

TRACKS = {
    "main": {
        "label": "Main build",
        "blurb": "The community build. Finished maps and game changes only.",
        "branch": "main",
        "channel_url": RAW.format(branch="main"),
        "tag_template": "v{version}",
        "bundle_template": "scda-ce-{version}.scdaupd",
        "catalogue": "slots.json",
        "prerelease": False,
        "carries_exe": True,
        # A MAP ID IS A POSITION, NOT A NAME. Stock CE lists BLKG1..USSG8 at
        # MapPaths indexes 0-7 and their descriptions carry map IDs 0-7, in that
        # order -- so the ID a slot ends up with is decided by where its line
        # lands, and the updater restamps it every time the list changes. The
        # value in a catalogue is only the seed the description is minted with.
        # 0-7 stay out of reach because added slots go on the END of the list.
        "map_ids": (8, 31),
        # MENU KEYS ARE NOT PARTITIONED BY CHANNEL, because there are only six of
        # them in the whole game. The name a slot shows comes from a key that must
        # exist in the compiled registry `Texts\Menu_Text.ute`, which ships exactly
        # A1-A8 and 09-14 and is never regenerated -- writing a new section into
        # Menu_text.eng does not create one. A1-A8 are the eight stock maps, so
        # 09-14 is the entire supply for every add-on on every channel. Splitting
        # six keys two ways would strand half of them; `make_release` already
        # refuses a key the other catalogue claims, which is the check that was
        # doing the real work anyway.
        "title_keys": ("09", "14"),
        "profile_label": "Community Edition",
        "warn": "",
    },
    "experimental": {
        "label": "Experimental build",
        "blurb": "Work in progress -- maps and game changes. Expected to break.",
        "branch": "experimental",
        "channel_url": RAW.format(branch="experimental"),
        "tag_template": "exp-v{version}",
        "bundle_template": "scda-ce-exp-{version}.scdaupd",
        "catalogue": "slots-experimental.json",
        "prerelease": True,
        "carries_exe": False,
        "map_ids": (8, 31),
        # CHANNEL KEYS (3.17). This channel's maps take their names from keys
        # 20-29, which the stock registry does not define: the channel ships its
        # own Texts/Menu_Text.ute (add-on MAPKEY) that adds exactly these ten.
        # Players' own maps can only point at keys the stock registry defines
        # (09-14), so a local map can never hold one of these -- 2026-09-25, a
        # tester's local "Kinshasa 1.0" on 14 refused Club House on 14.
        "title_keys": ("20", "29"),
        "minted_keys": True,
        # the keys that registry DEFINES: 15-29. Channel maps claim only 20-29;
        # 15-19 are defined so a developer install's own maps on 16/17/18 keep
        # their names while the channel's registry replaces theirs, and a name on
        # any of them is a map name to the game-file check.
        "defined_keys": ("15", "29"),
        "profile_label": "Experimental Build",
        "warn": (
            "These are test builds. They can crash, look wrong, or stop you "
            "joining a normal game until you take them back out. Added maps are "
            "extra entries in the map list; a game change replaces a file, and "
            "your original is kept. Removing everything from this tab puts the "
            "game back either way."
        ),
    },
    # M3EPBUGGIN (2026-10-02): the operator's test version, a third channel in a
    # repository of its own (M3epmeep/SCDA-M3epbuggin). Community Edition plus
    # the community-mods test features as `files` add-ons; no map slots, so its
    # map-ID and menu-key ranges are main's and claim nothing. It is never live
    # together with `experimental` (no version switches on both), but the two
    # ship some of the same files, so an install must hold the add-ons of only
    # one of them at a time.
    "m3epbuggin": {
        "label": "M3epbuggin build",
        "blurb": "M3epmeep's test build: Community Edition plus the community-mods test features.",
        "branch": "main",
        "channel_url": "https://raw.githubusercontent.com/M3epmeep/SCDA-M3epbuggin/main/latest.json",
        "tag_template": "m3ep-v{version}",
        "bundle_template": "scda-ce-m3ep-{version}.scdaupd",
        "catalogue": "slots-m3epbuggin.json",
        "prerelease": True,
        "carries_exe": False,
        "map_ids": (8, 31),
        "title_keys": ("09", "14"),
        "profile_label": "M3epbuggin",
        "warn": (
            "Test builds of community-mods features on top of Community Edition. "
            "They can crash or stop you joining a normal game; every player in a "
            "match needs the same build. Switching back to Community Edition puts "
            "your files back."
        ),
    },
}

def profile_label(name):
    """What the launcher calls this version: the thing you choose before Play."""
    return profile(name)["label"]


DEFAULT_TRACK = "main"
ORDER = ["main", "experimental", "m3epbuggin"]   # the publishable channels, and only those

# --- profiles: what the launcher offers -----------------------------------
#
# A profile is not a channel. `main` and `experimental` are channels: a branch,
# a catalogue, a release, an ID range. `developer` is none of those and never
# will be -- it is a view that also switches on LOCAL content, which belongs to
# no channel and so can never reach anybody else. There is nothing to publish.

LOCAL = "local"                            # hand-built maps that ship nowhere

# The eight maps Community Edition ships, IN MAP ID ORDER -- which is also the
# order they must hold in MapPaths.ini, because a description's map ID is its
# index in that file. These are the only descriptions the updater never rewrites.
STOCK_MAPS = ["BLKG1", "BOSG2", "DWG", "MOTG4", "TERG5", "REDG6", "SLHG7", "USSG8"]

# Maps that are part of the STANDARD game since 2026-09-20 -- operator: "the
# kinshasa i gave you should be in the .ref its a part of the standart version
# now". They ship inside the base image, on the lines right after the stock
# eight, and the launcher treats them like shipped maps: never adopted as a
# player's own map, never parked by a version switch. The main channel carries
# the same bytes as an add-on so an install made before that day catches up;
# on an image install the add-on finds every file already there and does
# nothing. A description shipped this way is the operator's own file, not a
# minted one, so the image and the channel agree byte for byte.
# Secret Base joined the same day, from his second archive: "this secret base
# is part of the base game now like kinshasa". Order here is line order.
BASE_MAPS = ["KIN01", "NSA01"]

# The registry a channel's own menu keys live in (3.17; see TRACKS["minted_keys"]).
MENU_REGISTRY = "Packages/_Common/Texts/Menu_Text.ute"


def defined_title_keys(track):
    """Every map-name key a channel's own registry defines (a superset of the
    ones its maps claim, minted_title_keys), or () for a channel with none."""
    cfg = get(track)
    if not cfg.get("minted_keys"):
        return ()
    low, high = cfg.get("defined_keys") or cfg["title_keys"]
    return tuple("%02d" % n for n in range(int(low), int(high) + 1))


def minted_title_keys(track):
    """The menu keys a channel mints in its own Menu_Text.ute, or () for none."""
    cfg = get(track)
    if not cfg.get("minted_keys"):
        return ()
    low, high = cfg["title_keys"]
    return tuple("%02d" % n for n in range(int(low), int(high) + 1))

# --- add-ons that must be asked about before they are installed ---------------
#
# Operator 2026-09-22: "before mumble auto installs, it should ask in the
# launcher if the user is ok with installing mumble".
#
# Everything else a channel carries is the game: our maps, our packages, our
# plugin. Proximity voice chat is not -- it puts a 45 MB program somebody else
# wrote into a folder on their PC, and that is a thing to be asked about rather
# than something that arrives because they picked a build.
#
# LAUNCHER-SIDE ON PURPOSE, not a catalogue field like `voice_server`. A
# catalogue that forgot the flag would install it silently, and the whole point
# of this list is that silence is the failure. A new add-on of the same kind
# costs a launcher release, which is the right price for the question.
#
# It only decides whether we INSTALL it. An add-on already on disk is never
# asked about -- it is answered by being there.
CONSENT = {
    "PROXVC": {
        "what": "Mumble",
        "track": "experimental",
        "question": (
            "Proximity voice chat needs Mumble -- the program that places "
            "everyone's voice around you in the map.\n\n"
            "The launcher can install it into your game folder for you: about 45 MB, "
            "no administrator rights, no installer, and no change anywhere else "
            "on your PC. Removing proximity voice chat deletes it again.\n\n"
            "Install Mumble?"
        ),
        "declined": (
            "Proximity voice chat was not installed -- you said no to Mumble. "
            "Everything else in this build is unaffected. Turn it on from "
            "Settings whenever you like."
        ),
    },
}


def needs_consent(code):
    """The consent entry for an add-on code, or None if it just installs."""
    return CONSENT.get((code or "").upper())


def consent_codes(profile):
    """Codes worth asking about before a PLAY on this version.

    Keyed by the track that carries the add-on, so the question is only put to
    somebody who is actually about to be offered it -- asking a Community
    Edition player about Mumble would be a prompt with no consequence, which is
    the fastest way to teach people to click through prompts.
    """
    tracks = profile_tracks(profile)
    return sorted(code for code, entry in CONSENT.items() if entry.get("track") in tracks)


# --- retired add-ons: taken back out of every install, never installed again ---
#
# Operator 2026-09-21, with a player's crash dialog (write fault 0x10A12823 on
# "Loading Secret Base", Community Edition, "mainly the ones that have had the
# experimental before"): "delete and remove all old kinshasa and secret base
# entrys, we have them working now".
#
# What was measured behind that dialog, in a sandbox copy of CE 1.1 that first
# took exp-v2026.09.11-x1 and then pressed PLAY on Community Edition: the main
# channel's Secret Base could not install, because its mesh package
# `StaticMeshes/NSA01_STM.usx` was still owned by the experimental package set
# (PORTPK). The OLD experimental level stayed in the map list -- a BASE_MAPS
# code is live under every version -- while PORTPK itself was switched off,
# which deletes that mesh package and two texture packages the old level
# imports. A level whose imports resolve to nothing dies at exactly that
# address.
#
# A launcher never removes an add-on merely because a newer release stopped
# carrying it, so dropping these from a catalogue repairs nobody. They are
# named here instead, and the launcher acts on the list twice:
#
# * `client.retire_addons` takes an installed one back out -- on every update
#   and every PLAY, online or not;
# * `client.plan` walks past one in ANY bundle, so the experimental releases
#   cut before 2026-09-21, which still carry all four, cannot put them back.
#
# Keyed by the track the add-on was installed FROM: main's KIN01 and NSA01 are
# the working maps and are not touched.
RETIRED = {
    "experimental": {
        "KIN01": "the old experimental port; Community Edition carries the working Kinshasa",
        "NSA01": "the old experimental port; Community Edition carries the working Secret Base",
        "KIN10": "an older Kinshasa build; Community Edition carries the working Kinshasa",
        "PORTPK": "the packages only the old Kinshasa and Secret Base ports imported",
        "LOBBY": "Community Edition carries the Kinshasa and Secret Base lobby models itself",
    },
}

# Every hash ever published for a retired file (one build each: the three
# releases that carried them, 2026.09.09-x1 to 2026.09.11-x1, agree byte for
# byte). Retirement deletes a file only while its bytes are still these. A
# level somebody has edited since is theirs: it stays on disk and the slot is
# kept as their own local map. Descriptions and copied loading art are not
# listed -- the launcher restamps the first and makes the second out of the
# player's own files -- so they go with the level or stay with it.
RETIRED_SHA256 = {
    "Packages/_Common/MapsPC/KIN01_VS.sds":
        ["ee5cf1cdf18c716e66282a067dc9c263a64815a4f6e2a1d57a6ffd213b5d8b31"],
    "Packages/_Common/MapsPC/KIN01_VS_sound.occ":
        ["37d5b36f27b4a81d67845db726f4c0539d2d55f41846ffb4787844a2c1fa4431"],
    "Packages/_Common/LoadingScreen/PC/KIN01_back.dds":
        ["7766ed73d54be3e137bf1b5fbeee7be8a514fdb048253b18fecb67600d2b2ac7"],
    "Packages/_Common/MapsPC/KIN10_VS.sds":
        ["31553f63babf78d27c58ab80455b514336ec3759a791d5536e5b40b08ab354aa"],
    "Packages/_Common/MapsPC/KIN10_VS_sound.occ":
        ["37d5b36f27b4a81d67845db726f4c0539d2d55f41846ffb4787844a2c1fa4431"],
    "Packages/_Common/LoadingScreen/PC/KIN10_back.dds":
        ["7766ed73d54be3e137bf1b5fbeee7be8a514fdb048253b18fecb67600d2b2ac7"],
    "Packages/_Common/MapsPC/NSA01_VS.sds":
        ["413fa38d6b811a895a55a5ec0490315c0608a9dd4270ab0020d4a9e3764b0117"],
    "Packages/_Common/MapsPC/NSA01_VS_sound.occ":
        ["37d5b36f27b4a81d67845db726f4c0539d2d55f41846ffb4787844a2c1fa4431"],
    "Packages/_Common/StaticMeshes/NSA01_STM.usx":
        ["71282cec56281e6163ed02869650dfc08ae114135a643276851f0bf67cfccd68"],
    "Packages/_Common/StaticMeshes/toleBridge_IND04.usx":
        ["bcf885fa614df0a1a055edb2caf6161d8c7a07e22326d183a3afe37d9e0458f2"],
    "Packages/_Common/Textures/DET_table.utx":
        ["8651f229c2f29b1a489c06d7f3de9732f1cffc588a427a028ac0fdab51cdadae"],
    "Packages/_Common/Textures/FRQ01_WLL.utx":
        ["41809febe5751189bb310fb2221885f982c263c4099aaf72f2194057a3f483a4"],
    "Packages/_Common/Textures/IND03_Metal.utx":
        ["6b2d088ce5903aeaa09143a46394002afd245bd3c3fbb0516894c75734b29eb7"],
    "Packages/_Common/Textures/shp2_wall01.utx":
        ["122924dc2fb35a67c67bbd33d717d3057029e4c00e0498a523a61b6354218d42"],
    "Packages/_Common/Textures/Detention.utx":
        ["91e69b311df32fc3976d61d9b114b2b5a004b3d29e69efd863ac775a8c58020a"],
    "Packages/_Common/Textures/Detention_N.utx":
        ["e3717f36c24ded73f5966de8a73631e2efb9a2aa4c67f55d7d55d24b5fd996c1"],
    "Packages/_Common/Textures/Ind03_Sol.utx":
        ["eb8544586c4358473b01fe5e0c0a88bc8fa9dfde1fd2dd7af0290ee3e441d050"],
    # LOBBY, experimental 2026.09.24-x1 only (launcher 3.12 retires it: main
    # 2026.09.24-1 ships the same lobby models inside KIN01 / NSA01). Its three
    # overrides ARE listed, descriptions included: retiring an override puts the
    # main channel's own copy back only while ours still sits there, and the
    # lobby package the description names goes in the same step. Its loading
    # screen is the old experimental Kinshasa's, already listed above.
    "Packages/_Common/Animations/plateaux.ukx":
        ["956b6caefbb6d698ee41167a86ba958b59aac3e0c06a501a36c0e31549f36527"],
    "Packages/_Common/Animations/plateaux.evtscript":
        ["5e6225d00c6c857c45e3a958122939023930d45024fcd9dfd5acf1c46333ab45"],
    "Packages/_Common/Animations/plateaux.evtsound":
        ["4be6ada48ec1bba9cb8f68f92c8ddb98a59a1bbd0d8b07d51893c49259b98f85"],
    "Packages/_Common/Textures/SHP2_obj_Baril.utx":
        ["ab545bd5b89d1ece69e1c83aa5229937b8fe725150db127c0774d32be4073ae6"],
    "Packages/_Common/MapDescriptions/PKG_KIN01_Desc.mcd":
        ["54a55e7235dc8a8e30c0a9a28f3c0a0b8941caa5ed3eb40634b4b1b2e9308482"],
    "Packages/_Common/MapDescriptions/PKG_NSA01_Desc.mcd":
        ["3241a8649cd98595bcca3292d0ece01feb302c9752413a6407657efc531a373e"],
}


def is_retired(track, code):
    """Whether this add-on, installed from this track, has been retired."""
    return str(code).upper() in RETIRED.get(track or DEFAULT_TRACK, {})


def retired_everywhere():
    """Codes that are retired whatever track installed them -- local included.

    Operator 2026-09-25 (launcher 3.17): "make sure the old files get deleted
    fully, the base game has its 10 maps now and our experimental has 14 total".
    Every retired code except the standard game's own KIN01 / NSA01 (those two
    are retired only as the old EXPERIMENTAL ports; main's are the working maps).
    """
    return sorted({code for table in RETIRED.values() for code in table} - set(BASE_MAPS))


def is_retired_anywhere(track, code):
    """Retired for this track, or retired whatever the track (see retired_everywhere)."""
    return is_retired(track, code) or str(code).upper() in retired_everywhere()


# THE PLAYER'S OWN SETTINGS FILES: written only where the game has none, never
# overwritten -- not by an update, a version switch or a retirement, and by
# Remove or Restore stock only while the add-on's own copy still sits there.
# Operator 2026-09-22 ("for now, the launcher should ignore the default.ini"):
# the Developer add-on shipped his own Default.ini -- 1920x1080 at 75 Hz -- and
# every PLAY copied it back over the player's, so a tester whose screen cannot
# do that mode got a game that would not start, and a resolution changed in
# game was gone next launch. Operator 2026-09-23 ("make sure the launcher
# doesnt change the resolution or any default ini files on launch for
# anyone"): every settings file the base game ships -- the twelve in System
# plus the sound engine's -- because the Developer add-on also carried
# Enhanced.ini (window mode, refresh rate), HudParams.ini, PC_input.ini and
# PlayerProfile.ini, and each Experimental PLAY put those back the same way.
# The map list (Packages/MapPaths.ini) is not one of them: it is how a map
# gets into the game, merged line by line and never replaced (inifiles.py).
# An .ini an add-on brings that the game never had (SC4Specific.ini) is that
# add-on's file and updates with it.
PLAYER_SETTINGS = {
    "system/default.ini", "system/defuser.ini", "system/enhanced.ini", "system/hudparams.ini",
    "system/mapslinearisation.ini", "system/menuparams.ini", "system/pc_input.ini",
    "system/playerprofile.ini", "system/playerprofilepc.ini", "system/shadowstrikesettings.ini",
    "system/ubi.ini", "system/version.ini", "packages/_common/soundsdare/dare.ini",
}

# The file check leaves these unjudged whatever the published list says. Only
# Default.ini (2026-09-22); the other settings files keep the rules the
# published list gives them (integrity_policy.json, T-511). PC_input.ini is free
# there since 2026-09-23 ("leave pc imput ini also alone"); a camera or a server
# address edited by hand is still a finding, and Repair puts it back only when
# the player says yes.
UNCHECKED_SETTINGS = {"system/default.ini"}


def is_player_setting(rel):
    return str(rel).replace("\\", "/").lower() in PLAYER_SETTINGS


def is_unchecked_setting(rel):
    return str(rel).replace("\\", "/").lower() in UNCHECKED_SETTINGS


# What the launcher OFFERS. "heartbeat" was parked for a few hours on
# 2026-09-20 ("ignore heartbeat for now too") and came back the same day as a
# game of its own -- see HEARTBEAT_GAME.
PROFILES = ["main", "heartbeat", "experimental", "m3epbuggin", "developer"]
PARKED_PROFILES = []

PROFILE_INFO = {
    "main": {
        "label": "Community Edition",
        "tracks": ["main"],
        "updates": "main",
        "warn": "",
    },
    # THE VANILLA HEARTBEAT GAME. Not a channel and not a set of add-ons: a
    # separate game in a separate folder (`game` names its image above), so
    # `tracks` is empty and `updates` is None -- nothing is ever fetched for it
    # beyond the one image, and choosing it never touches the Community
    # Edition install. (An earlier archive he called heartbeat turned out to
    # be the 1.1 tree with his settings; SCDA-Online.rar is the real one.)
    "heartbeat": {
        "label": HEARTBEAT_GAME["label"],
        "tracks": [],
        "updates": None,
        "game": "heartbeat",
        "warn": "",
    },
    "experimental": {
        "label": "Experimental Build",
        "tracks": ["main", "experimental"],
        "updates": "experimental",
        "warn": TRACKS["experimental"]["warn"],
    },
    "m3epbuggin": {
        "label": "M3epbuggin",
        "tracks": ["main", "m3epbuggin"],
        "updates": "m3epbuggin",
        "warn": TRACKS["m3epbuggin"]["warn"],
    },
    "developer": {
        "label": "Developer",
        "tracks": ["main", "experimental", LOCAL],
        "updates": "experimental",
        "warn": ("Your own local maps are switched on as well. These are yours only -- "
                 "they are in no channel, so nothing here is ever handed to anybody else."),
    },
}


def profile(name):
    try:
        return PROFILE_INFO[name]
    except KeyError:
        raise KeyError("unknown version %r -- known versions are %s"
                       % (name, ", ".join(PROFILES)))


def standalone_game(name):
    """The separate full game a version starts, or None for a version that
    lives inside the Community Edition install."""
    return HEARTBEAT_GAME if profile(name).get("game") == "heartbeat" else None


def profile_tracks(name):
    """Which sources of content are switched on under this version."""
    return list(profile(name)["tracks"])


def update_track(name):
    """Which channel this version checks for updates -- None for a version that
    has no channel (the original game)."""
    return profile(name)["updates"]


def update_tracks(name):
    """EVERY channel a version is made of, in publish order.

    Experimental Build is the main build PLUS what is being tried, so starting
    it has to bring the main channel up to date as well -- otherwise a tester
    who never pressed PLAY on Community Edition never receives what the
    community has. `update_track` names the channel the version is *for*; this
    names everything it *contains*. Local maps are not a channel.
    """
    return [t for t in ORDER if t in profile_tracks(name)]


def track_label(track):
    """A name for a content source, including the one that is not a channel."""
    if track == LOCAL:
        return "your local maps"
    return get(track)["label"]


def get(track):
    try:
        return TRACKS[track]
    except KeyError:
        raise KeyError("unknown track %r -- known tracks are %s" % (track, ", ".join(ORDER)))


def channel_url(track):
    return get(track)["channel_url"]


def bundle_name(track, version):
    return get(track)["bundle_template"].format(version=version)


def tag(track, version):
    return get(track)["tag_template"].format(version=version)


def bundle_url(track, version):
    return ASSET.format(tag=tag(track, version), bundle=bundle_name(track, version))


def track_of_map_id(map_id):
    """Which track owns this map ID, or None. Used to explain a collision."""
    for name in ORDER:
        low, high = TRACKS[name]["map_ids"]
        if low <= int(map_id) <= high:
            return name
    return None


def in_map_id_range(track, map_id):
    low, high = get(track)["map_ids"]
    return low <= int(map_id) <= high


def in_title_key_range(track, key):
    """Menu keys are two characters. A track owns a numeric range of them.

    Stock CE uses A1-A8 for its own maps plus 09 and 10, so anything non-numeric
    is stock's and belongs to no track.
    """
    key = str(key)
    if len(key) != 2 or not key.isdigit():
        return False
    low, high = get(track)["title_keys"]
    return int(low) <= int(key) <= int(high)


def track_of_title_key(key):
    for name in ORDER:
        if in_title_key_range(name, key):
            return name
    return None


def describe(track):
    cfg = get(track)
    return "%s (%s branch, map IDs %d-%d, menu keys %s-%s%s)" % (
        cfg["label"], cfg["branch"], cfg["map_ids"][0], cfg["map_ids"][1],
        cfg["title_keys"][0], cfg["title_keys"][1],
        ", pre-release" if cfg["prerelease"] else "")
