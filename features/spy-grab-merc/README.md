# spy-grab-merc

A spy can grab a mercenary during the last 0.5 s of the merc's berserk spin, during the whole stagger after a merc sprinted into a wall, and on stairs (the grab's height limit between the two pawns is 80 uu instead of 30); the grab replaces the merc's animation as a grab of a walking merc does.

Changes A and B (research `research\G-1-state-gates.md`) and change C (the height check on stairs, `research\G-2-geometry.md`, option F1 with 80.0: the operator's decision "F1-80").

State: version 2 (v1 + change C), built and gated offline (gates in `build\gates\`), **run in the game 2026-10-01 and validated by the operator ("it works")**, see "Test log". Test plan: `test\TEST.md`; the one-PC stairs rig (AI mercs held on Blackwing's stairs): `test\rig\STAIRS.md`. Version 1 (`dbfe5d74`, changes A and B) is kept in `build\out\v1-dbfe5d74\` with its papers. New facts for the documentation: `FINDINGS.md`.

| Piece | File | md5 | Installs to |
| --- | --- | --- | --- |
| plugin v2 | `files\System\SpyGrab.asi` (12,800 B) | `ca67503e0c7579c41aeddfa083225f7f` | `System\SpyGrab.asi` (new) |
| its settings | `files\System\SpyGrab.ini` (654 B) | `36c34fa4ea885b5cb6621e6c59811210` | `System\SpyGrab.ini` (new) |

- Built and gated against the main branch exe `System\SCDA_Online.exe` md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6`. No main-build file is replaced: the exe is patched **in memory** by the plugin at load, never on disk. The plugin never checks the exe's md5: it compares the bytes of each of its four sites with the stock bytes (site 4 also the two floats) and leaves a site alone (logged `REFUSED`) when they differ; the other sites still install.
- Its own ini, `System\SpyGrab.ini` (section `[SPYGRAB]`); `Enhanced.ini` is not read or written. A missing file or key means the default.
- The Ultimate ASI Loader (`System\dinput8.dll`) loads the plugin before any exe code runs; the plugin does all its setup inside its `DllMain`. No thread, no sound, no window, no network of its own, no file but its log. Preferred base `0x6EA00000` (free: `0x6E000000`..`0x6E700000` and `0x6E900000` are other plugins', `0x6E800000` is reserved); position-independent, so a relocated load works too.
- **Every player needs it** (see "Mixed installs"). The protocol is unchanged: the plugin changes only local decisions.
- A game started through the launcher checks the game's files and refuses an extra `System\*.asi` until it is part of a published build or add-on (`Deploy\net-tickrate\README.md`); the test loop starts the exe directly.

# Settings

| Key | Default | Does |
| --- | --- | --- |
| `Enabled` | 1 | 0 = the plugin installs nothing (log: `disabled ...`) |
| `Spin` | 1 | change A (below: site 1 spin branch, site 2 for action 180, site 3 for `ARotativeAttack`) |
| `SpinEarly` | 0.5 | seconds before the spin animation's end from which the spin is grabbable; 0.0 to 1.0, a larger value counts as 1.0, a value that is not a plain decimal number counts as 0.5; at most 3 decimals count; a `;` comment after the value is allowed |
| `Wall` | 1 | change B (site 1 wall branch, site 2 for action 124, site 3 for `ASprintWall`) |
| `Stairs` | 1 | change C (site 4): the grab's height test allows abs(dZ) <= 80 instead of 30; 0 = site 4 stays stock (log: `stairs height 0x10BCB00F: not installed (Stairs=0)`) |

`Spin=0` and `Wall=0` together leave sites 1 to 3 stock (log: `Spin=0 and Wall=0: grab gate, host grace and anim-end guard not installed`); site 4 follows `Stairs` alone. `Enabled=0` installs nothing.

# Change log (rule 8)

| # | File | Site | Stock content | New content |
| --- | --- | --- | --- | --- |
| 1 | `System\SpyGrab.asi` | new file | - | the plugin v2, md5 `ca67503e0c7579c41aeddfa083225f7f` |
| 2 | `System\SpyGrab.ini` | new file | - | `[SPYGRAB]` `Enabled=1` `Spin=1` `SpinEarly=0.5` `Wall=1` `Stairs=1` with comments, md5 `36c34fa4ea885b5cb6621e6c59811210` |
| 3 | `SCDA_Online.exe`, **in memory at load** | site 1, grab gate: VA `0x10BCAE97` (file `0x2CAE97`), 11 bytes in `CheckGrabTarget` `0x10BCAE50`, right after the target pawn's `CanBeGrabbed` event: `cmp dword [esp+0x14],0` / `je 0x10BCB1E8` | `83 7C 24 14 00 0F 84 46 03 00 00` | `E9 <rel32 to stub 1> 90 90 90 90 90 90` (at the preferred base `E9 CE 64 E3 5D 90 90 90 90 90 90`, stub 1 at `0x6EA0136A`). Stub 1: `CanBeGrabbed` true -> `0x10BCAEA2` (stock). False -> the target is accepted (`0x10BCAEA2`) when `PawnState` (`Pawn+0x4E0`) is 4 `PawnInRootMotion`, `GrabbingPawn` (`+0x4F0`) is None, and its channel-0 animation is `ASprintWall` (`+0x8B0`, `Wall=1`, any position) or `ARotativeAttack` (`+0x89C`, `Spin=1`) at a position >= end - `SpinEarly` x rate; `ASprintBump` (`+0x8AC`) and every other animation -> `0x10BCB1E8` (stock refusal) |
| 4 | `SCDA_Online.exe`, **in memory at load** | site 2, host grace: VA `0x10BC9F2D` (file `0x2C9F2D`), 6 bytes in `AController::execAskPermissionToGrab` `0x10BC9F00`: `ja 0x10BCA0D7` after `comiss Target.Controller.TimeOfInvulnerabilityForGrab (+0x498), Level.TimeSeconds (+0x5C8)` | `0F 87 A4 01 00 00` | `E9 <rel32 to stub 2> 90` (at the preferred base `E9 BD 74 E3 5D 90`, stub 2 at `0x6EA013EF`). Stub 2: not in the grace -> `0x10BC9F33` (stock). In the grace (the 0.15 s after every entry into `MercWalking`) -> `0x10BC9F33` when the target pawn's `CurrentAction` (`+0x15BC`) is 180 (`Spin=1`) or 124 (`Wall=1`), else `0x10BCA0D7` (stock `CantGrab`) with the stock flags |
| 5 | `SCDA_Online.exe`, **in memory at load** | site 3, anim-end guard: VA `0x10C35FEB` (file `0x335FEB`), 5 bytes in `APawn::execSeqAnimEnd` `0x10C35980`: the `jmp 0x10C3775F` that only the ends of `ARotativeAttack`, `ASprintBump` and `ASprintWall` take (after `push 1 / push 0 / push 1`) | `E9 6F 17 00 00` | `E9 <rel32 to stub 3>` (at the preferred base `E9 8A B4 DC 5D`, stub 3 at `0x6EA0147A`). Stub 3: a pawn in `s_PawnGrabbed` (`PawnState` 12) whose ending animation is `ARotativeAttack` (`Spin=1`) or `ASprintWall` (`Wall=1`) -> drop the three pushed arguments and leave through the function's epilogue `0x10C37798`, so it is not sent to `PawnWalking` / `SetPhysics(1)`; everything else -> `0x10C3775F` (stock). A precaution (see "Site 3") |
| 6 | `SCDA_Online.exe`, **in memory at load** | site 4, stairs height (change C): VA `0x10BCB00F` (file `0x2CB00F`), 6 bytes in `CheckGrabTarget` `0x10BCAE50`, test T7 abs(dZ of the pill centres) <= limit: `fld dword [0x10FA4A68]`; only its operand, the 4 bytes at VA `0x10BCB011` (file `0x2CB011`), changes | `D9 05 68 4A FA 10` (operand -> `.rdata 0x10FA4A68` = `00 00 F0 41` = 30.0) | `D9 05 30 4C FA 10` (operand -> `.rdata 0x10FA4C30` = `00 00 A0 42` = 80.0, the exe's own float). No hook, no cave. Neither float is written: 30.0 keeps its 55 other readers (the merc's terminate test `0x10BBA52C` among them), 80.0 its 23. Before the write: the image at `GetModuleHandleA(0)` is a PE with `SizeOfImage` >= `0x6A4C34`, the site reads `D9 05` + (`0x10FA4A68` + delta), 30.0 is at `0x10FA4A68` + delta and 80.0 at `0x10FA4C30` + delta, delta = load base - `0x10900000` (the operand is a `.reloc` entry, so a relocated exe is patched with base-relative values); any mismatch parks site 4 only. The 4 bytes are written under `VirtualProtect` (old protection restored). By hand on disk: the same 4 bytes at file `0x2CB011`, `68 4A FA 10` -> `30 4C FA 10` |
| 7 | `System\SpyGrab.log` | new, rewritten on every start | - | the config line and one line per site at load; event lines during play (table "Log") |

## Site 1: how the plugin reads the animation

Read as the stock spin-damage code reads it (`0x10BCC4EF`..`0x10BCC521`, `MercRotativeAttack.NotifyBump`):

| Step | Call / field | Notes |
| --- | --- | --- |
| mesh instance | `0x10BE2330` with `esi` = pawn | `UMesh::MeshGetInstance(Mesh +0x70, pawn)`, returns `Actor+0x80`; the stub calls it only with `Mesh != None` and requires the result to be a `SkeletalMeshInstance` (class `0x110406A0`, Super walk, as the engine's own `0x10C2BC10`) |
| channel-0 node | instance `+0x184` count, `+0x188` data[0] | validated before the engine's accessors run on it: a channel node (vtable `0x10F90B30`) with a sequence (`+0x6C` != 0), or a type-2 cross-fade (vtable `0x10F90A90`, `+0x50` == 2, `+0x64` > 1) whose child 1 (`[+0x68]+4`) is such a node; anything else is the stock refusal |
| name | `0x10BB0A80` (`ecx` = instance, `eax` = 0, `esi` = out) | node slot `+0x24` = `[sequence+0]`; a cross-fade answers its child 1 (the animation fading in) |
| position | `0x10ABBB40` (`ecx` = instance + `0x120`, `eax` = 0) | node slot 0 = `+0x60` (0 at the start, `+0x68` at the end); a cross-fade answers its child 1 |
| end, rate | node `+0x68` = 1 - 1/frames, `+0x70` = play rate x seq rate / frames (per second) | read from the resolved node; threshold = max(0, end - `SpinEarly` x rate). Fallback when the node is looping or reversed (`+0x84` bits 0 / 1) or end / rate are not sane: max(0, 1 - `SpinEarly` / 1.367) (G-1: 41 frames at 30 fps) |

For the stock spin `AtakStAlTu` (41 frames, 30 fps, play rate `a_fAnimRate[4]` 1.0): end 0.9756, rate 0.7317/s, so the grab opens at position 0.6098, 0.500 s before the end; the spin's play time is (41 - 1) / 30 = 1.333 s (the node's length slot 4 `0x10AC1CB0`), not 1.367 s. The spin damages a bumping pawn on the host while position <= 0.8 (`0x10FA4958`): the first 0.26 s of the grab window overlap the damage window (a grab granted there moves the merc's controller to `Grabbed`, which ends the damage; only a bump before the grant is hit).

## Site 3: why it is a precaution

The anim-end dispatcher `0x10C2BBF0` (Pawn vtable `0x10F7ECB0 +0x40C`, the only caller of the `SeqAnimEnd` thunk) passes the name of the node **now in the channel slot** (`0x10C2BC2F`..`0x10C2BC44`), not of the node that ended. Action 261 puts the grab animation into channel 0 (with a tween: a type-2 cross-fade whose child 1, the grab animation, answers the name). A late end of the replaced spin or stagger therefore reaches `SeqAnimEnd` with the grab animation's name and never takes the `0x10C35FEB` jump. The guard can only fire if that reading is wrong; `SpyGrab.log` records every firing, so the in-game test answers it. In stock the guard's condition never holds (no grab starts inside `PawnInRootMotion`), and the ends of every other animation, which reach `0x10C3775F` through `0x10C37758`, never pass the site (harness C3).

# Mixed installs

| Spy's machine | Host | Result |
| --- | --- | --- |
| plugin | plugin | A and B as designed |
| plugin | stock | the spy's prompt shows during the late spin / the stagger, the spy starts walking, the host's stock gate answers `CantGrab`: the spy returns to walking (a wasted walk); a spy that bumps a merc still in the spin's first 0.8 on the host takes the spin damage |
| stock | plugin | no prompt during the spin / stagger (the spy's own gate refuses): stock behaviour; the host's site 2 only lets a request through that arrives in the 0.15 s after the animation ended |
| any | any | the merc's own machine decides nothing about his being grabbed; its site 3 is the precaution only |

Change C (site 4) runs the same test on both machines (the spy's for the prompt, the host's for the grant; the host scales only distance and yaw by 1.5, not the height):

| Spy's machine | Host | On stairs (30 < abs(dZ) <= 80) |
| --- | --- | --- |
| plugin (`Stairs=1`) | plugin (`Stairs=1`) | the prompt shows and the host grants |
| plugin | stock | the spy sees the prompt on stairs, walks to the merc, the host answers `CantGrab`: the spy returns to walking |
| stock | plugin | the spy never gets the prompt, so the host never gets a request: stock behaviour |

The host is a player too: when the host plays the spy, both gates run on the same machine. With bots the same gate applies to any pawn with `PawnType` 0 (G-1 open question 5).

# Known limits

- Each machine judges the spin with its own copy of the animation: the spy's machine may show the prompt a few frames before the host's copy reaches the threshold, and the host then answers `CantGrab` (open point of the test).
- Site 2 tests `CurrentAction`, which stays at the last action a machine ran: a `MercWalking` entry that follows a spin or a stagger without any other action in between also loses its 0.15 s grace.
- Between the grant and the spy's arrival the staggering merc is still pushed back by his stagger (about 80 uu), as the host sent his position at the grant (G-1 question 4).
- The first 0.26 s of the spin's grab window overlap its damage window; a spy that bumps the merc before the host grants still takes the spin damage.
- Change C raises the height limit wherever the grab test runs, not only on stairs: a merc on a low step or platform up to 80 uu above or below the spy (pill centres) passes T7 on flat ground too; the walk test T8 still refuses anything the spy's pill cannot walk to (rises above 32 uu per step, walls, railings, floors).
- The merc's own terminate test (`0x10BBA400`) reads the same 30.0 and is unchanged: a merc terminating a spy on stairs is still refused (G-2).
- The grab pose on stairs is untested: while held, the merc is pulled to the spy's height (G-2 Q5 / F4; 47 to 53 uu on the stock `IND08_STM` stair); whether he floats or sinks is an open point of the test, not changed here.

# Log

| Line | When |
| --- | --- |
| `SpyGrab 2 (Deploy\spy-grab-merc): config: Enabled=1 Spin=1 SpinEarly=0.500 s Wall=1 Stairs=1` | at load |
| `... grab gate 0x10BCAE97: installed` / `host grace 0x10BC9F2D: ...` / `anim-end guard 0x10C35FEB: ...` | at load, one per site; `REFUSED - the bytes are not the expected ones (another exe build or another patch)` or `REFUSED - VirtualProtect failed` instead of `installed` |
| `... stairs height 0x10BCB00F: installed (30.0 -> 80.0)` | at load, the last line; `not installed (Stairs=0)`, `REFUSED - the bytes are not the expected ones (...)` (site, operand or a float differs), `REFUSED - VirtualProtect failed` or `REFUSED - GetModuleHandleA(0) gave no exe base` instead |
| `... disabled by SpyGrab.ini [SPYGRAB] Enabled=0, nothing installed` | at load, the only line |
| `... Spin=0 and Wall=0: grab gate, host grace and anim-end guard not installed` | at load instead of the three site lines (the stairs line follows) |
| `t=<ms> ms  first spin grab allowed: position P, end E, rate R/s, threshold T` (+ `(fallback: ...)`) | once, the first time site 1 accepts a spinning merc (spy's machine or host) |
| `t=<ms> ms  first wall-stagger grab allowed: position P` | once, the first time site 1 accepts a staggering merc |
| `t=<ms> ms  host: 0.15 s grab grace skipped, merc action 180` (or 124) | each time site 2 lets a request through (host) |
| `t=<ms> ms  anim-end guard: the late end of a replaced animation was ignored on a grabbed pawn` | each time site 3 fires |

At most 32 event lines per game start; nothing per frame. `t` is `GetTickCount`.

# Install and remove

- By hand: drag the contents of `files\` onto the install root and choose replace (`DEPLOY-NOTICE.txt`). Remove: delete `System\SpyGrab.asi`, `System\SpyGrab.ini` and `System\SpyGrab.log`.
- By script: `patch.ps1 -GameDir "<install>"` (status), `-Apply` (optionally `-Settings "SpinEarly=0.3;Wall=0;Stairs=0"`), `-Revert`. It refuses the main branch's path, a present `System\Running.ini`, a running game, leftovers of an earlier apply, a foreign `SpyGrab.asi`, an installed v1 (`-Revert` removes it first) and an exe whose four sites or two floats are not stock.

# Gates (offline, `build\gates\`)

| Gate | Transcript | Result |
| --- | --- | --- |
| 1 static: PE, the plugin's own code (every memory access, call, branch, the stubs' exits, site 4's installer step by step and its one write), the four sites and everything each stub relies on in main's exe, the animation readers, node and cross-fade layouts, anim-end dispatch, action codes, no branch or pointer into the stolen bytes or the site-4 operand, both floats in read-only `.rdata`, the `.reloc` entry of the operand, the 56 readers of 30.0, simulated install | `build.txt` | 102 PASS, 0 FAIL (determinism: four builds, one md5) |
| 2 harness: the real plugin loaded in an x86 process against the exe's own code (C1 `CheckGrabTarget` from `0x10BCAE50`, C2 `AskPermissionToGrab` from `0x10BC9F00`, C3 `execSeqAnimEnd` from `0x10C35FDD` / `0x10C37752` / `0x10C377A2`, C4 `CheckGrabTarget` run whole through distance, yaw, crouch, height and walk test) in 26 modes (v1's 18; `Stairs=0`, `Stairs=1` alone, all off, a foreign byte in the operand, 30.0 or 80.0 changed, an exe image relocated by `0x20000000` with its own `.reloc` fixups, the same image without the fixups) | `harness.txt` | 26 of 26 runs pass, 793 checks, 0 FAIL |
| 3 `patch.ps1` dry run on a fresh copy of main's `System` folder | `dryrun.txt` | 50 PASS, 0 FAIL |

Rebuild: `build\gates\run.ps1 -Exe <copy of main's SCDA_Online.exe>` (writes `build\out\SpyGrab.asi`, `build.txt`, `harness.txt`), `build\gates\dryrun.ps1`. Sources: `build\src\SpyGrab.cs` (the plugin, assembled with Iced by `build\builder\`), `build\harness\Program.cs`.

# Test log

| # | Date | Build | Result |
| --- | --- | --- | --- |
| - | - | v1 `dbfe5d74` | not run in the game (superseded by v2) |
| 1 | 2026-10-01 01:01-01:05 | v2 `ca67503e`, alone on main `0f1b2d1c` in the working copy | one PC, the operator as host spy by hand, Blackwing `BLKG1_VS` versus match with the lobby's bot fill (3 AI mercs `NPCPawnMerc_Zero`); `SpyGrab.log`: `config: Enabled=1 Spin=1 SpinEarly=0.500 s Wall=1 Stairs=1`, all four sites `installed` (stairs `30.0 -> 80.0`); the rig put two mercs on the detention-block stairs at 01:05:08-01:05:13; the game ended cleanly about 01:05:15 (no crash event, no `Running.ini`). **Operator: "it works".** The rig recorded no grab after its placement; which grabs the operator made (spin, wall, stairs) is not logged. Logs: `test\results\run1-20261001-0101\`. Reset: `patch.ps1 -Revert`, realign list mode 01:07: 0 content differences |
