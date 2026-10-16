# chat-list lean

> **In M3epbuggin 2026.10.16-m10** as `M3CHAT`, together with the dead-chat gates (`features/dead-chat-gate/`): the 21 exe bytes below and in that file are applied to Community Edition 2026.10.11-3's exe (md5 `ceb13a00`), giving md5 `039f3948a11b0ab0093bbf8787f9c941`; none of the 21 lies within 64 bytes of a 10.11-3 change. `Interface_stm.usx` is the stock file with the 18 bytes below (md5 `91c890cd`). The change log below was measured on Community Edition 2026.10.07-1 (exe `4a17634f`), where it ran in game on 2026-10-16. Paths point into the builder's workspace, not into this repository.

The stock bottom-left chat (HUD widget 18) shows each line at once at its final place, as text only (no background box, no icon), newest at the bottom and older lines pushed up at the text's own line step; life, expiry swing, count, width and visibility stay stock.

Built by LEAN-C on 2026-10-16 00:02 PC from the main build Community Edition 2026.10.07-1 (brief `BRIEF-lean.md`, notes `NOTES.md`). No new code, no plugin, no section, no ini: 18 bytes of the game's own code (operands, constants, two opcodes) and 18 one-byte material references in a mesh package. Not run in game.

## Files

| Install path | Main md5 (replaced) | New md5 | Bytes changed |
| --- | --- | --- | --- |
| `System\SCDA_Online.exe` (7,712,768 B) | `4a17634fbebc1cb2c6b550cc35337d9f` | `f166634880f0c2ed1490d271e2f6eaa9` | 18 (rows E1-E16) |
| `Packages\_Common\StaticMeshes\Interface_stm.usx` (5,302,748 B) | `1221f8f9c36143a3b9d87cb751a36aac` | `91c890cdc2b4a07a9ad338c49247e7a7` | 18 (rows U1-U18) |

Drag the contents of `files\` onto the install root and choose replace. Revert: put main's two files back. Same lengths, no header, section, checksum or relocation change; file offset = VA - `0x10900000`.

## How the stock chat works (what the rows change)

Widget 18 holds 3 slots, 3 items (camera-space meshes `UH_mess_0[1-3]_[1-3]L`: section 0 the background `Mat_UH_fond_mess`, section 1 the icon, section 2 the text) and a row table `0, 3, 6, 8, 10, 12, 17` (`[widget+0x118..0x130]`). A new message waits `[widget+0x134]` = 0.5 s, then is appended to the order list. The layout walks that list oldest first, sums the lines below each item and gives the item target Z = table[lines] and its open animation, which swings it in from the closed pose (yaw -4100, off-screen left) along `Open_MessageY/Z`. At expiry the close animation swings it out towards the closed pose (position 0). Detail and addresses: `NOTES.md`, facts 4-13 (`FINDINGS.md` was refused to this agent by the session; its text went to the orchestrator in the hand-back).

## Changes: `System\SCDA_Online.exe`

| # | Site | File offset | B | Stock | New | Effect |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | widget 18 ctor `0x10B81650`, VA `0x10B8173F` (imm byte `0x10B81740`) | `0x281740` | 1 | `BA 03 00 00 00` `mov edx,3` | `BA 02 00 00 00` `mov edx,2` | row table [1] = 2 (its other stores, the free slots' first line counts `+0xBC/+0xD8/+0xF4`, are rewritten before any read) |
| E2 | ctor, VA `0x10B8179A` (imm `0x10B817A0`) | `0x2817A0` | 1 | `C7 86 20 01 00 00 06 00 00 00` `mov dword [esi+0x120],6` | `... 04 00 00 00` `mov dword [esi+0x120],4` | table [2] = 4 |
| E3 | ctor, VA `0x10B817A4` (imm `0x10B817AA`) | `0x2817AA` | 1 | `... 08 00 00 00` `mov dword [esi+0x124],8` | `... 06 00 00 00` `mov dword [esi+0x124],6` | table [3] = 6 |
| E4 | ctor, VA `0x10B817AE` (imm `0x10B817B4`) | `0x2817B4` | 1 | `... 0A 00 00 00` `mov dword [esi+0x128],0xA` | `... 08 00 00 00` `mov dword [esi+0x128],8` | table [4] = 8 |
| E5 | ctor, VA `0x10B817B8` (imm `0x10B817BE`) | `0x2817BE` | 1 | `... 0C 00 00 00` `mov dword [esi+0x12C],0xC` | `... 0A 00 00 00` `mov dword [esi+0x12C],0xA` | table [5] = 10 |
| E6 | ctor, VA `0x10B817C2` (imm `0x10B817C8`) | `0x2817C8` | 1 | `... 11 00 00 00` `mov dword [esi+0x130],0x11` | `... 0C 00 00 00` `mov dword [esi+0x130],0xC` | table [6] = 12: E1-E6 give 2 units per line, the text's own line step (one text line in the 2L/3L meshes = 1.97 units; stock 1-line box pitch 3 units = 28 px at 720 lines) |
| E7 | widget 18 init `0x10B81F20`, open anim, VA `0x10B824C0` | `0x2824C3` | 1 | `8B 54 24 10` `mov edx,[esp+0x10]` (curve `Open_MessageY`) | `8B 54 24 2C` `mov edx,[esp+0x2C]` (a local the init sets to 0 and only reads) | the open anim's rotation channels get no curve |
| E8 | init, open anim, VA `0x10B824C7` | `0x2824CA` | 1 | `8B 4C 24 14` `mov ecx,[esp+0x14]` (curve `Open_MessageZ`) | `8B 4C 24 2C` `mov ecx,[esp+0x2C]` | nor its position channels: E7 + E8 = the item takes its target pose in the first transform after the open starts (the transform starts from the target and only a channel with a curve moves it): no slide-in, rows snap |
| E9 | update `0x10B82930`, show, VA `0x10B83047` | `0x283047` | 1 | `74 11` `je short 0x10B8305A` (after `cmp dword [ebp+0xA4],0`) | `EB 11` `jmp short 0x10B8305A` | the icon skin (mesh skin 1, `call 0x10B9F0E0` with eax 1) is never set; section 1 then draws the mesh's own slot material = `Mat_S_none` (U2, U4, ...). Needs the usx |
| E10 | update, slot assign, VA `0x10B833A4` | `0x2833A6` | 1 | `F3 0F 58 44 24 20` `addss xmm0,[esp+0x20]` (end = `[ebp+0x134]` 0.5 s + now) | `F3 0F 10 44 24 20` `movss xmm0,[esp+0x20]` (end = now) | a new line shows on the next update instead of 0.5 s later |
| E11 | update, layout, VA `0x10B833D2` | `0x2833D2` | 1 | `39 9D 00 01 00 00` `cmp [ebp+0x100],ebx` | `03 9D 00 01 00 00` `add ebx,[ebp+0x100]` | ebx = order-list count (the `jle 0x10B8346F` after it still leaves on 0) |
| E12 | layout, VA `0x10B833DE` | `0x2833DE` | 2 | `8B FF` `mov edi,edi` | `4B 90` `dec ebx` / `nop` | start at the newest (count - 1) |
| E13 | layout, VA `0x10B83448` | `0x283449` | 2 | `89 90 B0 00 00 00` `mov [eax+0xB0],edx` (stores Y back unchanged) | `89 88 CC 00 00 00` `mov [eax+0xCC],ecx` | the row's Z also goes to the closed pose (`[item+0xCC]`), so an expiring line swings out where it stands instead of sliding down across the newer lines (stock's bottom line did the same) |
| E14 | layout, VA `0x10B83460` | `0x283461` | 1 | `83 C3 01` `add ebx,1` | `83 EB 01` `sub ebx,1` | walk newest to oldest |
| E15 | layout, VA `0x10B83463` | `0x283465` | 1 | `3B 9D 00 01 00 00` `cmp ebx,[ebp+0x100]` | `3B 9D 18 01 00 00` `cmp ebx,[ebp+0x118]` (row table [0] = 0, written only by the ctor) | compare with 0 |
| E16 | layout, VA `0x10B83469` | `0x28346A` | 1 | `0F 8C 71 FF FF FF` `jl near 0x10B833E0` | `0F 8D 71 FF FF FF` `jge near 0x10B833E0` | loop while ebx >= 0: E11-E16 = newest at the bottom (Z 0), older lines pushed up |

18 bytes in 16 rows (E12, E13 two bytes each). Groups that only work together: E1-E6; E7+E8; E9 with U2/U4/.../U18; E11, E12, E14, E15, E16. E10 and E13 stand alone.

## Changes: `Packages\_Common\StaticMeshes\Interface_stm.usx`

Each message mesh's `Materials` array (property stream at the head of its export payload) holds three slots whose `Material` is a one-byte compact reference: slot 0 `0x99` = import 24 `Interface_txt.UH_Txt.Mat_UH_fond_mess` (the background), slot 1 `0x96` = import 21 `Mat_UH_Icones_Drone` (the icon placeholder; the exe sets the real icon as skin 1, E9 stops that), slot 2 `0x87` = import 6 `Mat_Texte_ZoneName` (text, set again by the exe as skin 2: unchanged). New: `0xB6` = import 53 `Interface_txt.UH_Txt.Mat_S_none` (`TranspBasicModernMaterial` on texture `S_none`, alpha 0; already used by `UH_Strategic_selection`). Same width: nothing moves.

| # | Mesh (export, payload offset) | File offset | Slot | Stock | New |
| --- | --- | --- | --- | --- | --- |
| U1 | `UH_mess_03_1L` (204, `0x4AC7EB`) | `0x4AC7F8` | 0 | `99` Mat_UH_fond_mess | `B6` Mat_S_none |
| U2 | same | `0x4AC803` | 1 | `96` Mat_UH_Icones_Drone | `B6` Mat_S_none |
| U3 | `UH_mess_01_3L` (205, `0x4ADF92`) | `0x4ADF9F` | 0 | `99` | `B6` |
| U4 | same | `0x4ADFAA` | 1 | `96` | `B6` |
| U5 | `UH_mess_01_2L` (206, `0x4AF6C5`) | `0x4AF6D2` | 0 | `99` | `B6` |
| U6 | same | `0x4AF6DD` | 1 | `96` | `B6` |
| U7 | `UH_mess_01_1L` (207, `0x4B0E6C`) | `0x4B0E79` | 0 | `99` | `B6` |
| U8 | same | `0x4B0E84` | 1 | `96` | `B6` |
| U9 | `UH_mess_02_3L` (208, `0x4B2613`) | `0x4B2620` | 0 | `99` | `B6` |
| U10 | same | `0x4B262B` | 1 | `96` | `B6` |
| U11 | `UH_mess_02_2L` (209, `0x4B3D46`) | `0x4B3D53` | 0 | `99` | `B6` |
| U12 | same | `0x4B3D5E` | 1 | `96` | `B6` |
| U13 | `UH_mess_02_1L` (210, `0x4B54ED`) | `0x4B54FA` | 0 | `99` | `B6` |
| U14 | same | `0x4B5505` | 1 | `96` | `B6` |
| U15 | `UH_mess_03_3L` (211, `0x4B6C94`) | `0x4B6CA1` | 0 | `99` | `B6` |
| U16 | same | `0x4B6CAC` | 1 | `96` | `B6` |
| U17 | `UH_mess_03_2L` (212, `0x4B83C7`) | `0x4B83D4` | 0 | `99` | `B6` |
| U18 | same | `0x4B83DF` | 1 | `96` | `B6` |

18 bytes in 18 rows. The exe looks the 9 meshes up only in widget 18's loader `0x10B81930` (its other references are the name-table registration run `0x1097E230`), and of main's packages only `Interface_stm.usx` names them; `Mat_UH_fond_mess` is used by these 9 meshes only (the 11 users of `Mat_UH_Icones_Drone` keep it). Odd rows (slot 0) remove the background on their own; even rows (slot 1) need E9.

## Option rows (v3 traits, not applied)

| Trait of v3 | Single stock constant? | Where |
| --- | --- | --- |
| 10 s per chat line | yes, per command, on the SENDER (every receiver shows the life the sender's exe sends) | SAY `0x10A1ACC3` `68 00 00 A0 40` `push 0x40A00000` (5.0), imm at file `0x11ACC4`; TEAMSAY `0x10A1AE06`, imm at file `0x11AE07`; 10.0 = `00 00 20 41`. For every message on the receiver it is 3 bytes in the add routine `0x109B81D0` (CL-3, `..\research\DATA-ROUTE.md` row 1), not one constant |
| then a 1 s fade | no | stock expiry is already a 1 s swing-out (`[widget+0x134]` 0.5 s = half the close time, MEASURED); an alpha fade needs 3 exe bytes plus curve data (DATA-ROUTE row 2) |
| 8 messages | no | 3 slots, 3 items, 3 x 3 meshes, the queue takes 3 (`0x10B83767`), the loops end at 3 (`0x10B828D7`, `0x10B831F8`) |
| lines 15 characters wider | no | the zone width 504 px (Engine.u) draws into a 512 px text bitmap; +15 characters need about 726 px (DATA-ROUTE row 8) |
| keep the envelope icon (operator's choice) | - | leave E9 and the even U rows stock |
| slide removed by data instead of E7 + E8 | - | `Packages\_Common\Curves\HUDAnimationCurve.crv` `Open_MessageY` / `Open_MessageZ` y values to 1.0 (DATA-ROUTE row 3, variant A, open half only); same look, one more file |

## Coexistence (transcript `build\overlap.txt`, ALL PASS)

| With | Result |
| --- | --- |
| main's 8 plugins, start logs (`System\*.log`, 2026-10-15 23:20) | no "ok" range or hook site within 16 B; nearest Modes `ok 0x10B7E280 +20`, 13,484 B away; Enhanced has no log, MatchRec logs no range |
| the 8 plugins' code | no image-range dword within 16 B (nearest Enhanced `0x10B8100C`, 1,843 B); no 8-byte run of main's bytes covering a changed byte (144 windows each); none names `Interface_stm` |
| `Deploy\dead-chat-gate` (`0x109B8B36`, `0x109B8B37`, `0x10B816A8`) | byte-disjoint (nearest 151 B: the mask byte to E1); our 18 bytes hold main's values in its exe; both laid on main = 21 bytes, md5 `497ced01884a63acdc5b00efd4f564f4` (the stack `files-with-dead-chat-gate\`, chat plus dead chat; `files\` stays chat only) |
| the channel plugins' 27 compared ranges (m9 list) | nearest QolHud `0x10B73C90 +25`, 55,959 B away |
| `Deploy\qol-hud` lean (in work) | its planned sites (other widgets' ctor masks, `0x10B73C90`, `0x10B70E98`, two overlay vtable slots, the `.text` slack, `.data` slack) are outside our ranges; nearest its `0x10B8392E` (widget 10 ctor), 1,220 B after E16 |

Byte ranges this feature edits, exe (VA): `0x10B81740`, `0x10B817A0`, `0x10B817AA`, `0x10B817B4`, `0x10B817BE`, `0x10B817C8`, `0x10B824C3`, `0x10B824CA`, `0x10B83047`, `0x10B833A6`, `0x10B833D2`, `0x10B833DE..DF`, `0x10B83449..4A`, `0x10B83461`, `0x10B83465`, `0x10B8346A`; usx: the 18 offsets above.

## Checks (lean)

| Check | Result |
| --- | --- |
| build twice from main (`build\build.py`, stock-checked writes, refuses on any other md5 or byte) | `build\b1` = `b2` (b2 deleted after the compare): exe `f1666348`, usx `91c890cd`; `files\` = `b1` |
| byte diff against main | exe 18 bytes in 16 runs = rows E1-E16; usx 18 bytes = rows U1-U18; same lengths |
| disassembly of every exe site before and after | `build\sites-dis.txt` (main and lean side by side; every other instruction of the windows unchanged) |
| usx re-parsed | 258 exports, 287 imports as main; the 9 meshes decode; slots read `Mat_S_none, Mat_S_none, Mat_Texte_ZoneName` |
| overlap | above |

## In-game test list

| # | Test | Expect |
| --- | --- | --- |
| 1 | spawn as spy (5 spawn-protection texts), type Say lines | each line appears at once at the bottom, nothing slides or swings in; older lines jump up by one text line |
| 2 | look at a line | text only: no dark box behind it, no envelope icon; stock letter size, stock colour, stock 3D tilt |
| 3 | 3 lines, one of them 2 lines long ("Spawn protection time for this map: 17.00 seconds.") | one left-aligned column, no gaps between lines, newest at the bottom |
| 4 | wait | each line lives as stock (about 5 s), then swings out where it stands in 1 s; nothing slides down; the remaining lines do not move |
| 5 | a 4th line while 3 are shown | as stock one line gives way (the widget takes 3 records), but at once (stock: it swung out for 0.5 s first); the new line appears at the bottom, the others pushed up |
| 6 | alive in modes 1 and 11 (briefing) | as above |
| 7 | with `Deploy\dead-chat-gate` (`files-with-dead-chat-gate\`): dead (0), kill cam (4), spectating (5) | the same look in each; a dead player's line reaches the list (host) |
| 8 | kill cam key hints, menus, end of match | the chat is hidden or shown exactly where stock shows it |
| 9 | drone, scope, other HUD widgets | unchanged |

## Known limits

- Run in game 2026-10-16 with dead-chat-gate (`files-with-dead-chat-gate\`, exe `497ced01`), Blackwing, host, one PC: the operator's verdict "chat works". The first run of that install fell back to the boot menu after the first chat line and crashed on the next map load (`SCDA_Online.exe+0x423CC7`); not seen again, cause unknown.
- The HUD's 3D tilt stays (the meshes are angled about 6.8 degrees in depth): the lines are parallel and left-aligned, but not flat like v3 / v4's canvas text.
- Row step 2 units = about 19 px at 720 lines (v3 about 17-18 px); a 3-unit step would leave the stock gaps, 1 unit overlaps.
- The exe without the usx shows the icon placeholder `Mat_UH_Icones_Drone` in section 1 (E9 without U2...U18); ship both files together.
- With all 3 slots busy, a new line takes the slot of the line that leaves (stock order: free slot first, else a closing one): that line's swing-out is cut at once (stock let it swing 0.5 s). With a free slot the leaving line swings out fully.
