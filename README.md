# SCDA M3epbuggin

**M3epbuggin** is M3epmeep's test version of SCDA (Splinter Cell: Double Agent, PC Community Edition): Community Edition plus the community-mods features that are being tried. Players get it with the **M3eptemp** launcher: pick *M3epbuggin* and press PLAY. This repository holds that channel: the catalogue, the build tool, the published `latest.json` and the release bundles. The base game itself still comes from the Community Edition image; this channel ships only the differences.

## Download the launcher

**[M3eptemp 3.19.20261002](https://github.com/M3epmeep/SCDA-M3epbuggin/releases/tag/m3eptemp-v3.19.20261002)** (its own release in this repository):

- [`M3eptemp.exe`](https://github.com/M3epmeep/SCDA-M3epbuggin/releases/latest/download/M3eptemp.exe): the launcher window
- [`M3eptemp-cli.exe`](https://github.com/M3epmeep/SCDA-M3epbuggin/releases/latest/download/M3eptemp-cli.exe): the same launcher on the command line

M3eptemp is a separate copy of SYNCADE's SCDA Launcher 3.19 with one more version in its list, *M3epbuggin*. It never updates itself and keeps its settings, log and downloads in its own folder, `%LOCALAPPDATA%\M3eptemp`, so the official launcher keeps working as before. The exes are not code-signed; the release page lists their SHA-256.

## What it changes

Version `2026.10.02-m2`, on top of Community Edition:

| Code | Feature | What it does | Files |
| --- | --- | --- | --- |
| `M3CHAT` | Chat as a list, always on | The chat at the bottom left is a plain list of up to 8 messages that works alive, dead, spectating and in the drone and scope views; on the host, dead players' chat reaches everyone. | `System\SCDA_Online.exe` (replaced) |
| `M3QHUD` | HUD stays on in the drone and the scope | A merc looking through the scope or flying the drone keeps the normal HUD (timer, zone name, score, gadgets, messages), drawn on top of the view. | `System\QolHud.asi` (added) |
| `M3SNHS` | Sniper headshot sound | When a merc kills a spy with a scoped headshot, a short ding plays where the spy fell, heard within 10 metres. | `Packages\_Common\SoundsDARE\MAPS.SM0` (replaced), `System\SniperHeadshotSound.asi` (added) |
| `M3SGRB` | Spy grab: end of the spin, wall stagger and stairs | A spy can grab a merc in the last half second of the berserk spin, during the whole stagger after a wall sprint, and on stairs. | `System\SpyGrab.asi`, `System\SpyGrab.ini` (added) |
| `M3NECK` | QOL4Necks | A spy can neck a merc in the middle of a jump and right after he lands, and an interact press next to a light switch or other object necks a merc in reach first. | `System\QOL4Necks.asi`, `System\QOL4Necks.ini` (added) |

**Known issue in m2:** on Community Edition 2026.10.02-3 and later the launcher holds the sniper headshot sound back, because Club House and Warehouse now ship `MAPS.SM0` themselves. The other four install. The next build fixes this: Community Edition's own `MAPS.SM0` already carries the ding, so `M3SNHS` becomes the plugin alone.

Each feature's own change log, as its builder wrote it, is in [`features/`](features/) (`README.md`, and `FINDINGS.md` where there is one). Paths in those files point into the builder's workspace, not into this repository.

## How a player gets it

1. Download `M3eptemp.exe` (above) and start it.
2. Give it a game folder of its own. Press **PLAY** and let it download Community Edition into a new folder you pick, or open **Settings -> Game folder -> Browse** and choose a Community Edition copy that no other launcher looks after. M3eptemp keeps its own records of the files it installs, so it should not share a folder with the official launcher.
3. Under VERSION pick **M3epbuggin** and press **PLAY**. The launcher brings Community Edition up to date, then installs this channel's add-ons, checks the game files and starts the game.

**Every player in a match needs it.** Most of it works across the network: the spy grab needs the file on the host (who grants the grab) and on the spy's machine (which shows the prompt), the headshot ding is sent by the host's plugin and played from every player's own sound bank, and dead players' chat goes out from the host's exe. Only the HUD change is purely on your own screen.

**Your key bindings are shared.** Every SCDA install reads the same player profiles. Like the official launcher 3.19, M3eptemp adds the bindings an add-on needs (for example push-to-talk) and removes the bindings of retired add-ons (`CoopMove`, `CoopKey`, `NoLight`) in those profiles.

## How to go back

- **To Community Edition:** in M3eptemp pick *Community Edition* and press PLAY. The launcher switches M3epbuggin's add-ons off and puts Community Edition's files back; the add-ons stay installed, switched off, for the next time you pick M3epbuggin.
- **To take M3epbuggin out completely:** `M3eptemp-cli.exe --cli remove-track --track m3epbuggin --install "<game folder>"`.

## How a publish reaches players

1. `python m3ep.py publish` builds the bundle from `slots-m3epbuggin.json`, creates the GitHub **pre-release** `m3ep-v<version>` here with the bundle `scda-ce-m3ep-<version>.scdaupd` attached, then commits `latest.json` to `main`.
2. Every M3epbuggin launcher reads `https://raw.githubusercontent.com/M3epmeep/SCDA-M3epbuggin/main/latest.json`. That address caches for about five minutes.
3. The next time a player presses PLAY on M3epbuggin, the launcher downloads the bundle, checks its size and sha256, and updates.

There is no mirror: this repository is public and the launcher downloads from it directly.

## What is in here

| Path | What it is |
| --- | --- |
| `slots-m3epbuggin.json` | The catalogue: every add-on this channel ships. You edit this. |
| `slots.json`, `slots-experimental.json` | Claims copies of the other two channels' catalogues: their add-on codes, map IDs, menu keys, install paths and overrides, and main's table of stock files (`baseline_sources`), which this catalogue inherits. Comments and source paths are left out. Refresh them with `python m3ep.py claims --main <slots.json> --experimental <slots-experimental.json>` when those channels change. |
| `sources.lock.json` | The sha256 and size of every file under `sources/` and `stock/`. |
| `sources/` (not in git) | The files the add-ons ship. |
| `stock/` (not in git) | The verified Community Edition stock files the deltas are measured against (`MAPS.SM0`, and the stock exe the build reports on). |
| `m3ep.py` | The one command you use. |
| `make_release.py`, `channels.py`, `inifiles.py`, `scpatch.py`, `common.py` | The launcher's bundle builder. `channels.py` adds the `m3epbuggin` track and version; `make_release.py` builds three channels instead of two (below). The other three are unchanged. |
| `features/` | Each feature's change log. |

The bytes for `sources/` and `stock/` can live as assets of a pre-release **`sources`**, each named by its sha256. Files are never overwritten: a changed file is a new asset, and the lockfile says which one the catalogue means. **Not uploaded yet:** the store would hold stock game files (the Community Edition exe and the whole 183 MB `MAPS.SM0`) in public, so builds are published with `python m3ep.py publish --no-store` from the machine that holds `sources/` and `stock/`. Players never need the store; they download only the bundle.

## Setup (once)

You need Python 3.8 or newer, git, and the [GitHub CLI](https://cli.github.com/) logged in with an account that has write access:

```
gh auth login
git clone https://github.com/M3epmeep/SCDA-M3epbuggin.git
cd SCDA-M3epbuggin
python m3ep.py fetch
```

`fetch` downloads about 380 MB the first time (two copies of the 183 MB sound bank: stock and ours) and afterwards only what changed.

## Publishing a change

```
git pull --rebase
python m3ep.py fetch                                   # bring sources/ up to what the catalogue names

python m3ep.py add path\to\SpyGrab.asi --as SpyGrab.v3.asi
                                                       # stores and uploads the file as sources/SpyGrab.v3.asi
# edit slots-m3epbuggin.json: point the entry at "sources/SpyGrab.v3.asi"

python m3ep.py check                                   # every named file present, locked and uploaded
python m3ep.py build --version 2026.10.03-m2 --dry-run    # the table of what would ship, nothing written

git add slots-m3epbuggin.json sources.lock.json
git commit -m "m2: what changed"
git push

python m3ep.py publish --notes "One line players read: what this build changes"
python m3ep.py status                                  # what is published and whether the bundle is there
```

`add --link` hard-links the file instead of copying it (same disk only); `add --no-upload` locks it without uploading, and `python m3ep.py upload` uploads every locked file the store lacks. `publish` refuses when the working tree has uncommitted changes, when your `main` is not `origin/main`, when a named file is missing, changed or not uploaded, or when the version is already taken. Without `--version` it takes the next free one (`python m3ep.py next`): today's date and the next `m` number.

### Rules the build enforces

- No code, map ID or menu key may be claimed by two channels, whether the other channel's add-on is enabled or not.
- A file may not be shipped by two channels one version switches on together: main and this channel. The exe is main's (its `SMOKE` add-on), so `M3CHAT` declares `"over": "SMOKE"` and ships the exe whole, exactly as Experimental's `DEVBLD` does; the launcher puts main's exe back when `M3CHAT` goes off.
- Experimental and M3epbuggin are never switched on together, so a file both ship is printed as a note, not refused. Those notes are why a player takes one channel's add-ons out before picking the other.
- A `files` entry uses `"base": "<install path>"` (a small delta against the stock file, which must be in `slots.json`'s `baseline_sources`) or `"force_full": true` (the whole file; for new files and config files players edit). `PlayerProfilePC.ini` is refused.
- Every release is a **pre-release**. `publish` does this for you. A normal release would take over this repository's `releases/latest` link, which belongs to the launcher.

### Rolling back

Every published `latest.json` is in git history. To put players back on an earlier build, restore that file and push:

```
git log --oneline -- latest.json
git checkout <commit> -- latest.json
git commit -m "roll back to <version>"
git push
```

Bundles are complete snapshots measured against stock, so going back needs nothing else.
