# sniper-headshot-sound

> **In this channel since 2026.10.02-m3: version 3 = the plugin only.** `M3SNHS` ships `System\SniperHeadshotSound.asi` (md5 `9e9dcfc0`) and no sound bank. Community Edition's own `MAPS.SM0` carries the Ding since 2026.10.02-3: the bank that Club House and Warehouse install (`CLUBEX`, md5 `f6f129b7`) holds the Ding as the sample of the cue `Play_Turret_On` (39,670 bytes at offset 4,974,252, md5 `e4f823cd`) and its 10 m range (parameter 7 at offset 8,832 = 10.0), checked byte for byte on an install of 2026.10.02-3. So this channel replaces no file of Community Edition. m1 and m2 shipped `MAPS.SM0` themselves (row 1 below, as a delta on stock `d8e31526`); the launcher held that back once `CLUBEX` owned the bank. The text below is the feature's v2 change log as its builder wrote it.

When a merc kills a spy with a scoped headshot, a short sound (the operator's Ding) plays at the spy's location through the game's own sound engine, heard by every player within 10 metres, quieter with distance and quieter than gunfire and grenades.

**STATE 2026-09-29 00:05: version 2 built, DEPLOYMENT PREPARED, READY FOR THE IN-GAME TEST. Not run in game, nothing installed.** Version 2 follows the operator's order of 2026-09-28 ("find alternatives that are less invasive for playing the ding file", then "do it"): the sound is played by the game, not by the plugin. Version 1 (its own sound output, a plugin on every machine) was removed by Microsoft Defender at its build and is given up; its papers are kept as `*.v1`. Version 2's plugin was built at 23:49 and was not detected (checked 23:49:55 and 00:03).

| Piece | File | md5 | Installs to | Who needs it |
| --- | --- | --- | --- | --- |
| sound bank, patched | `files\Packages\_Common\SoundsDARE\MAPS.SM0` (182,933,888 B) | `e681dfbd4c293290189c78685a2b5d9e` | replaces `Packages\_Common\SoundsDARE\MAPS.SM0`, main build md5 `d8e31526a7a931df4c1108f05ace94c0` | every machine that is to hear the Ding |
| plugin v2 | `files\System\SniperHeadshotSound.asi` (8,704 B) | `9e9dcfc0d0efa9b07062fbcc6b9f4b4f` | `System\SniperHeadshotSound.asi` (new) | the host only |
| the Ding as a bank sample | `bank\Play_Turret_On.ding.pcm` (39,670 B) | `e4f823cdbfcce197eb86150953621358` | written into the bank by `patch.ps1` | - |
| the stock sample | `bank\Play_Turret_On.stock.pcm` (39,670 B) | `521f75480bff410416b1bbad244bd2c5` | written back by `patch.ps1 -Revert` | - |
| ini section (optional, not written by default) | written by `patch.ps1 -Settings "..."` only | - | appended to `System\Enhanced.ini` | the host |

- Built and gated against the main branch exe `SCDA_Online.exe` md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6` and against the build before it, `d94c9137340f3996b5bc9ec361340d1e`; every address below is byte-identical in both. The working copy's bank has the main bank's md5.
- The plugin never checks the exe's md5. It checks the six bytes of the site it takes over; on a mismatch it installs nothing and says so in `System\SniperHeadshotSound.log`.
- No `.u` package, no `.uax` package and no exe file changes. The Ultimate ASI Loader (`System\dinput8.dll`, shipped with CE) loads the plugin at start.
- "From the sniper" is the scoped shot only (operator, 2026-09-28 22:04): damage type 15 `Dmg_Snipe`, which the game assigns when the shooter's controller is in the state `MercBinocular` (or `SpyBinocular`).
- The game's own headshot sound stays what it is: the stock `ClientPlaySound(HeadShotSound)` goes to the shooter and is neither hooked nor changed (operator, 2026-09-28 22:50).
- The launcher checks the game's files before PLAY: a changed `MAPS.SM0` and an `.asi` it does not publish both stop it. For the test the exe is started directly (the test loop does); players get the feature only as a part of the published build.

# Change log (rule 8)

| # | File | Site | Stock content | New content |
| --- | --- | --- | --- | --- |
| 1 | `Packages\_Common\SoundsDARE\MAPS.SM0` | the sample of the cue `Play_Turret_On`: file offset 4,974,252, 39,670 bytes (16-bit PCM, 24,000 Hz, mono, 19,835 frames). Found as: directory entry `FIX` (block at 636, 160,172 B) -> event record A[78] (event 36, group 5, at 8,792) -> resource B[0xD2] (at 59,680) -> data entry of resource `0x800000D2` -> PCM sub-block at 160,808 + 4,813,444 | the turret sample, md5 `521f75480bff410416b1bbad244bd2c5` (`bank\Play_Turret_On.stock.pcm`) | the Ding, md5 `e4f823cdbfcce197eb86150953621358` (`bank\Play_Turret_On.ding.pcm`): 16,223 frames = 0.676 s, then 3,612 frames of silence. 38,579 of the 39,670 bytes differ |
| 2 | `Packages\_Common\SoundsDARE\MAPS.SM0` | file offset 8,832: parameter 7 of A[78] (the A record's parameters start at +12, four bytes each, 16.16 fixed point) | `00 00 0F 00` = 15.0 | `00 00 0A 00` = 10.0. Parameters 4 and 6 (offsets 8,820 and 8,828) keep 2.0 and 6.0. With `-RangeM r` the three become 0.2 r, 0.6 r, r |
| 3 (only with `-VolumeDb`) | `Packages\_Common\SoundsDARE\MAPS.SM0` | file offset 59,700: word 5 of B[0xD2], loudness in dB, 16.16 fixed point, signed | `00 00 00 00` = 0 dB | the given value, e.g. `00 00 FD FF` = -3 dB |
| 4 | `System\SniperHeadshotSound.asi` | new file | - | the plugin (source `build\builder\`) |
| 5 | `SCDA_Online.exe`, **in memory at load** | VA `0x10BD842B` (file `0x2D842B`), 6 bytes, in the PlayerController damage virtual `0x10BD8320` (vtable `0x10F7F740` slot `+0x3E4`), on the branch DamageType == 15, once per death, killer and victim on different teams, right before `PRI.iSnipeKills += 1` | `8B 85 14 16 00 00` mov eax,[ebp+0x1614] | `E9 <rel32>` jmp stub, then 1 x `90`. The stub saves all registers and xmm0..7, calls the kill handler, restores, replays the stock instruction and returns to `0x10BD8431` |
| 6 | `System\SniperHeadshotSound.log` | new, rewritten on every start | - | `SniperHeadshotSound 2 (Deploy\sniper-headshot-sound): kill hook 0x10BD842B: installed`, then `config: Range=1000 Log=1, cue SFO_Equipment.Group_Dare.Play_Turret_On`; with `Log=1` one line per kill: `t=<ms>  sniper headshot kill of a spy at <x> <y> <z>, cue played to <n> player(s) within 1000 uu`; `REFUSED - ...` with the reason when the site does not hold the stock bytes |
| 7 (optional) | `System\Enhanced.ini` | end of file, only when asked for | - | `[SNIPERHEADSHOT]` and the keys of the table "Settings". Without the section the plugin runs on its defaults |

Nothing in the bank moves: the file keeps its length, the sample its place, length and frame count. On a bank of another build the offsets differ; the way in row 1 finds them, and `patch.ps1` walks it on every run and refuses a cue that holds neither the stock sample nor the Ding.

The stub as built on 2026-09-28 23:49 (preferred base `0x6E600000`; `ebx` = the plugin's image base, found by call/pop); the full listing is in `build\gates\build_v2.txt`, the handler in `build\builder\SniperHeadshotSound.cs`:

```
stub (kill), RVA 0x11A2
pusha
sub esp,0x80 / movups [esp+..],xmm0..7
call $+5 / pop ebx / sub ebx,<its own RVA>
mov eax,[esp+0xC8]        ; PillTag
call hKill
movups xmm0..7,[esp+..] / add esp,0x80
popa
mov eax,[ebp+0x1614]      ; stock instruction
push 0x10BD8431 / ret
```

# Mechanism

| Step | Machine | What happens |
| --- | --- | --- |
| 1 detect | host | kill handler at site 5. Live there: `esi` = victim PlayerController, `ebp` = killer pawn, `[esp+0x28]` = PillTag. Gates: PillTag == 0 (`ePN_Head`), victim Role == 4, victim PawnType == 1 (spy), killer pawn team byte `+0x12A0` == 0 (merc), the victim has a pawn and a level |
| 2 cue | host | `StaticLoadObject` (`0x109992F0`, cdecl) with the Sound class (`0x11031250`), the name `L"SFO_Equipment.Group_Dare.Play_Turret_On"` and the flags `0x2002` - the stock call of `0x10A6B31A` with another class. An object in memory is found, one that is not is loaded. The pointer is used for this kill and not kept. No cue: nothing is sent, the log says so |
| 3 send | host | for every player controller of the level (`Level.ControllerList` `+0x7B8`, next `+0x58C`, bIsPlayer `+0x4C8` bit 4, class chain reaching `PlayerController` `0x11030210`) whose pawn (without a pawn: the controller) is within `Range` of the spy: FindFunction(`0x15BA` ClientHearSound, `0x109948D0`) and ProcessEvent (vtable `+0x10`, flags `0x400000`) with the block {Actor = the spy's pawn, Id 4, S = the cue, SoundLocation = the pawn's location, Parameters = (1000, Range, 1000), Attenuate 1, BoneIdx -1}. This is the call the game's own sender `0x10BDCE50` makes for `SLOT_SFX` sounds |
| 4 travel | engine | `UObject::ProcessEvent` `0x1096E1C0` hands a net function to the owning client (vtable `+0x20`) or, for the host's own controller, runs the native directly. The function is unreliable: sent once |
| 5 play | every machine, stock code | `execClientHearSound` `0x10BD3010` plays S on the Actor through the audio subsystem (vtable `+0x90`). DARE looks the cue up in the bank (event 36, group 5), takes the place from the Actor, the fall-off from the event's parameters and the loudness from the resource, and mixes it with the game's own sounds |
| with the stock bank | any machine | the same cue plays the stock turret sample (0.83 s, largest distance 15) |

# Settings

`System\Enhanced.ini`, section `[SNIPERHEADSHOT]`, read by the host's plugin. All keys optional.

| Key | Default | Range | Meaning |
| --- | --- | --- | --- |
| `Enabled` | 1 | 0, 1 | 0 installs nothing |
| `Range` | 1000 | 100..5000 | whom the cue is sent to: players within this many Unreal units of the spy, 100 = 1 m; 1000 = the ordered 10 m |
| `Log` | 1 | 0, 1 | 1 writes the start lines and a line per kill; 0 writes no file |

How far the Ding carries on each machine and how loud it is are values of the bank, set by `patch.ps1`:

| Switch | Default | Range | Written to |
| --- | --- | --- | --- |
| `-RangeM` | 10 | 1..50 | the event's parameters 4 / 6 / 7 = 0.2 r / 0.6 r / r |
| `-VolumeDb` | 0 | -40..0 | the resource's loudness word |

The keys of version 1 (`Volume`, `Pan`, `Route`, `File`) are gone: loudness and direction are the sound engine's.

# The sound

| Step | Fact |
| --- | --- |
| source | `sound\Ding.mp3`, the operator's file (46,080 B, md5 `6e39c95da0849b8c097f3bae4e7f54b3`, MPEG-1 layer 3, 192 kbit/s, 48 kHz stereo, 1.92 s) |
| decoding | `sound\convert.ps1 -Source sound\Ding.mp3` writes `sound\SniperHeadshot-48k-stereo.wav`: Windows' own media transcoder decodes to PCM, `sound\wav_canon.py` cuts the lead-in below -60 dBFS (63.7 ms) and the silent tail (1,169 ms); md5 `2d3d4d5bd30b4813ee15e4f8877ee85c`, 32,446 frames, peak 0 dBFS |
| to the bank's shape | `bank\make_sample.py`: (L + R) / 2, low-pass (63-tap windowed sinc, 10.8 kHz), every second sample (24,000 Hz), gain -9 dB, last 5 ms faded, zeros up to 19,835 frames. Two runs, one md5 |
| loudness | loudest 50 ms of the Ding in the bank: -17.9 dBFS (peak -10.6, rms -25.8). Stock samples of the same group, loudest 50 ms with their loudness word: the seven loudest -1.5 .. -7.5 (drone explosion -1.7, nano drone explosion -3.5, grenade samples), flash grenade explosion -9.0, the turret cue it replaces -15.4. Which samples are the gunshots is not identified |
| why mono, 24 kHz | the cue is placed in the world by the sound engine, which takes one channel; every PCM sample of the merc equipment group is 24,000 Hz mono; at 48 kHz the Ding (64,892 B) would not fit the sample it replaces |
| not done | the sound was not played on this PC, in or out of the game |

# Install and remove

| Way | How |
| --- | --- |
| script | `.\patch.ps1 -GameDir "<install>"` status; `-Apply` (bank and plugin, a host); `-Apply -BankOnly` (a machine that only joins); `-Apply -RangeM 10 -VolumeDb -3` (on an install that carries the Ding already: writes the two values again); `-Apply -Settings "Range=1000;Log=1"`; `-Revert`. It patches the install's own bank in place and notes the bank's md5 and date in `SoundsDARE\MAPS.SM0.<md5>.sniperheadshot.bak` (a few lines of text); `-Revert` writes the stock sample and values back, sets the date back, checks the md5 against the note and removes the note. Refuses the main branch, a running game, a foreign plugin file, a cue another patch changed, a file that is no sound bank, and for the plugin an exe whose site is not stock |
| by hand | drag the contents of `files\` onto the install (`DEPLOY-NOTICE.txt`): replaces the bank, adds the plugin |
| rebuild | the Ding sample: `_tools\python312\python.exe bank\make_sample.py [--gain-db -9]`; the plugin: `dotnet build build\builder\ShsBuild.csproj -c Release -o build\builder\bin`, then `build\builder\bin\ShsBuild.exe build\out\SniperHeadshotSound.asi <exe> [<exe>]`; then the new md5s into `patch.ps1`, this file and the notice, and the stack in `files\` again |

# Tests

| Test | Result |
| --- | --- |
| static gate of the builder (`build\gates\build_v2.txt`), build of 23:49 | ALL PASS, 96 checks, on main `0f1b2d1c` and on `d94c9137`: PE shape (one section, no import directory, 8,704 B), the image names six kernel32 functions and none for threads, memory, file reading, library loading or sound output, the cue's path, the stub decodes and balances, stolen bytes replayed, 6 bytes change and none outside the site, no branch or pointer into the stolen bytes, 31 stock-code facts per exe |
| harness (`build\gates\harness_v2.txt`): the real plugin in an x86 process, the exe's own code page at its own address, stand-ins for `StaticLoadObject`, `FindFunction` and `ProcessEvent` | 16 runs (8 modes x 2 exe builds), 136 of 136: per run 1,512 scenes against a model written from the rule (gates, one loader call per kill with the six expected arguments, the events in list order with the expected block, range edge at exactly `Range`, the walk's stop at 256 controllers), all registers, the stack level and xmm0..7 unchanged at the resume address, the log line per kill; modes: no plugin, default, relocated, `Range=500 Log=0`, `Range=99999` (clamped to 5000), `Enabled=0`, a site another patch changed (refused), a cue that cannot be loaded (nothing sent) |
| bank (`build\gates\stack-bank.txt`, `bank_diff.py`) | the stack's bank against the main bank: same length, 38,580 bytes differ (38,579 in the sample, 1 in parameter 7), 0 elsewhere; all 12 blocks round-trip through the toolbox's `dare_block`; `dare_census` gives the same tallies (1,022 resources with data) and no mismatch on both; no other event and no container of any block plays B[0xD2] |
| `patch.ps1` dry run on a scratch install (`build\gates\test-patch.txt`) | 40 of 40: apply, second apply with other values, bank only, settings; after every revert each file of the install has its name, length, date and md5 of before; 16 refusals, each leaving the install as it was; main never written |
| Microsoft Defender | the plugin v2 lies in `build\out\` and `files\System\` since 23:49 and was loaded 16 times by the harness: no detection (history read 00:03). No exclusion was set |
| network path, sound path | read in the exe, not measured |
| in game, run 1: 2026-09-29 10:08 to 10:12, automated run (test loop, unattended, ONE player: host as merc on Blackwing), working copy equal to main (exe `0f1b2d1c`), defaults; evidence `test\results\` | step 1 PASS: the log reads `kill hook 0x10BD842B: installed` and `config: Range=1000 Log=1, cue SFO_Equipment.Group_Dare.Play_Turret_On`. The game loads the changed bank (`e681dfbd`) and the match runs. Two scoped shots at a wall: no log line (no kill). Defender: no detection, the plugin stayed in `System\`. `-Revert`: bank back at `d8e31526`, plugin and log removed. Steps 2 to 6 (the scoped kill, hearing, range, loudness, the negative cases) WAIT for a second player: not run, nothing faked. A death of the host by the own frag was tried as a negative case and did not happen (the merc survived) |

# Open

| Point | State |
| --- | --- |
| the engine loads the cue by name at the kill | INFERRED. `StaticLoadObject` by name is proven in game for classes and static meshes (BombHud, HackHud, FileScore), not for a Sound. First question of the test: the log line must read "cue played to n player(s)", not "cue NOT FOUND" |
| a client resolves the cue it has not loaded | INFERRED from the engine's design (the package `SFO_Equipment` is loaded by `SC4Inventory.u`, `SC4Specific.u` and `SC4Ingredients.u` on every machine; the object itself is named by nothing). A client that cannot resolve it gets S == NULL and plays nothing. Second question of the test, needs two machines |
| parameter 7 is the largest distance in metres | INFERRED: the toolbox's Club House bank writes a sound's radius there, the values of stock cues fit (flash explosion 18, gun 30.5, mine 6.5). To be heard in the test: silent beyond 10 m |
| loudness | -17.9 dBFS is a first value; `-VolumeDb` lowers it without a rebuild, `make_sample.py --gain-db` raises or lowers the sample itself |
| the spy's pawn as the sound's owner | the Ding lasts 0.68 s. A sound whose owner is destroyed while it plays is the fault class of `formats/audio.md` ("The position callback"); the game plays its own death sounds on pawns the same way |
| test needs a second player | the site runs only on a kill by a scoped shot. A key that plays the cue on the own pawn for a one-player test is not built (it needs a second hook); on the operator's order |
| main replaces the bank | `MAPS.SM0` was rewritten by the launcher on 2026-09-28 19:55. After such a change: `patch.ps1` on the new bank (it finds the cue again), and the stack bank rebuilt |
| the stack's bank is 183 MB | above GitHub's 100 MB limit for one file: a fork takes `patch.ps1` with the two samples, or the bank through the launcher's bundles |
| the cue's name in a published build | every machine with the stock bank hears the turret sample instead; the bank has to go out with the plugin |
