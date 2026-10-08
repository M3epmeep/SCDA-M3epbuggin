# chat-list

> **In this channel since 2026.10.07-m8: v4d on Community Edition 2026.10.07-1's exe.** `M3CHAT` ships md5 `2f0cb988f58fe3989cef45f27996b414` (7,725,056 bytes) = the list's look (v3's drawing, unchanged) drawn only in the frames the game's own chat widget runs (v4, `--stock-vis 1`), plus the game's own two dead-chat gates removed (`--dead-chat 1 --dead-show 1`: the host's fan-out `0x109B8B36` `8B 80` -> `EB 18`, the chat widget's mode mask `0x10B816A8` `02` -> `33`), so the list shows while dead, in the kill cam and spectating, and a dead player's line reaches everyone when the host runs it. Gates: static 83 of 83, harness 204 of 204, coexistence 60 of 0 failures. Seen working in game on 2026-10-08 (one PC, host: lines typed while dead, sent and listed). m3-m7 shipped v3 `0fd28e5f` (always on), m1 and m2 `3fba79cf`. Sections "v4 look only" and "v4d" below; the rest is v3's change log as its builder wrote it.

The chat is drawn by the game's own canvas text routine as an overlay at the bottom left - up to 8 messages as a list, the newest at the bottom and older lines pushed up without any slide, each message for 10 seconds and then fading over 1 second, lines 15 characters longer at the stock letter size, no frame - always: alive, dead, in the kill cam, spectating, in the drone and scope views, with a menu open, and kept over a respawn, a team switch and a new level, while the stock chat widget is switched off; on the host a dead or spectating player's line goes out to every player.

Version 3, built by CL-7 on 2026-09-30 as a patch of `System\SCDA_Online.exe` (main build md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6`). No plugin, no import, no Win32 call, no API lookup, no thread, no input reading, no file access. State: **built, gates pass (0 FAIL), run 5 in game on 2026-09-30: works alive, dead, in the kill cam and after a team switch and a respawn; operator's verdict "ok, chat succeeded"** (test log row 5; a second player, spectating and the menus with live lines were not seen). Version 2 (CL-5, md5 `b28c9113`, papers `*.v2`) worked alive (run 3) and failed the dead state (run 4); version 1 (CL-4, md5 `c4f50a7f`, papers `*.v1`) drew nothing.

2026-10-03 (C-1): v3 rebuilt on main 2026.10.02-4's exe `4a17634f` (`0f1b2d1c` + door carry) is in `files-m4\` (md5 `0fd28e5f`); see the section "v3 on main 2026.10.02-4".

2026-10-08 (V-1b): v4 "look only" on Community Edition 2026.10.07-1 (exe `4a17634f`) is in `files-v4\` (md5 `2724a697`): the list look of v3, drawn exactly where and when the stock chat would be drawn, no dead chat; see the section "v4 look only on Community Edition 2026.10.07-1". The default builds are still v3 byte for byte.

Orders, in the operator's words: 16:1x "New feature: the bottom left chat. It should be the same size, but messages do not scroll in anymore but are displayed as a list. The most current always at the bottom, then shoved upwards when a new msg arrives. And after 10 seconds, the message fades. Message limit is 8 messages / notifications. Testrun it, spawning as spy will show spawn protection messages that should be good as proof of concept"; 19:3x "ok, Merc hud worked well, expansion on the ´chat functions extend the line lenght per line by 15 chars remove the frame arund it and put them closer together, when a character is dead, the chat should remain and still be shown, including incoming messages, players who are dead, are still able to chat"; 20:1x "Full plugin", "start working on the scda_online.exe but, what do you need to patch it?"; 20:2x "Wider chat, same text size"; 21:4x "instead of fixing the rendering, can you detect incoming messages and just put them on a new custom overlay?"; 22:5x "set also next goal in resume for the chat: that it shows when dead, and that it also works to chat when dead"; 23:27 "continue on the chat always working feature"; 2026-09-30 00:03 "resume".

## Where it must be installed

| Part | Runs on | Needed for |
| --- | --- | --- |
| overlay (sites 7, 8, `.chat`, `.chatd`) | every machine that wants the list | the list itself, on that player's screen; mixed installs play together (the overlay only reads the local MessageManager) |
| dead-sender site 9 (`0x109B8B36`) | the **HOST** (listen server) | a dead or spectating player's line reaching anyone. Only the host runs `MessageManager.SimpleStringToTeam`; with a stock host a dead player's line is dropped there, whatever the players have installed. The sender and the receivers need nothing for it |
| nothing | - | receiving a dead player's line: the receivers' path has no alive test |

## Why v2 failed in run 4 (causes, VERIFIED on main 0f1b2d1c unless marked)

| # | Fact of run 4 | Cause | Site | v3 |
| --- | --- | --- | --- | --- |
| a / H3 | the dead player's typed line never reached the list | the HOST's fan-out drops every line whose sender has no pawn or a pawn with Health <= 0: `mov eax,[MM+0x2FC]` (Owner) `/ mov eax,[eax+0x408]` (Controller.Pawn) `/ je exit / cmp [eax+0x1580],0` (Pawn.Health) `/ jle exit`. The operator was the host and dead (mode 0); the line was dropped before any MessageManager got it (that Enter was pressed is not seen: INFERRED) | `0x109B8B36..0x109B8B4F` in `execSimpleStringToTeam` `0x109B8680` (native 3916) | 2 bytes `EB 18`: the test is jumped over to the receivers' loop `0x109B8B50`; harness X: the real fan-out gives 0 receivers with main's bytes and 3 (the sender included) with v3's |
| a | (the rest of the route) | no other condition reads the pawn, its health, the player state, the HUD mode or spectating - see "The route of a typed line" | - | - |
| fact 5 | nothing captured for the merc after the team switch | a merc gets no spawn protection texts at all: the only exports carrying "Spawn protection" are `PawnSpy.Tick` and `PawnSpy.Timer` (SC4Specific.u exports 1022, 1024; sent by `PawnSpy.MessagePlayer` straight to the owner's `SimpleStringToClient`) | SC4Specific.u | nothing to fix |
| b / H2 | the list emptied at 8.80 s (1 -> 0, `exp` 0, `drop` 0) | v2's `resetList` emptied the list whenever the HUD `[viewport+0x68]` or the MessageManager `[[HUD+0x400]+0xA10]` differed from the last frame's. After the reset the record still in the stack (3.6 s of its 5 s) was not taken again, so from 8.80 s v2 read no MessageManager or another one (which owner changed is not recorded: INFERRED the team switch through the menu) | v2 Overlay (`ChatExe.cs.v2`) | an owner change never touches the list; the capture follows the local PlayerController's MessageManager (next rows) |
| H1 | "the capture stalls after a new MessageManager" | REFUTED for run 4: after the 8.80 s reset the last sequence taken was -1 and stayed -1 (nothing was captured afterwards), so a stale sequence number did not cause the silence. The mechanism exists in v2 when a new MessageManager takes the freed one's address (its counter `[MM+0x420]` restarts at 0 and v2 sees no owner change) | v2 capture | the counter `[MM+0x420]` going back, or the record with the last number taken being another record (its text pointer), starts the capture over; records already listed are skipped (source, sequence, text) |
| b | (a new level) | v2 dropped every entry when the level clock went back (a new level restarts `[XLevel+0x614]`) | v2 expire | an own clock: the sum of the level-time steps of 0..1 s; a new level or a load does not age or drop the entries |
| c / H4 | "v2 draws nothing while dead" | REFUTED: run 3 drew in mode 0; modes 0, 4 (run 4) and 5 (run 3) passed every gate ("nothing to draw" is the last gate). The one mode-5 menu gate of run 4 was the quit dialog (shot `r4-025s`) | probe logs | harness R: messages present in modes 0, 4, 5, 13 and all others reach the RI's DrawPrimitive |
| d | the menu gate | the menus are drawn after the site (`[0x1100FF7C]` vt+0x28), so a menu covers the chat where they overlap; v2 did not draw at all while a menu answered vt+0x38 != 0 | v2 Overlay | the menu gate is OFF by default (builder `--menu-gate 1` turns it on); no page of the dead state holds the gate (above) |

## The route of a typed line (every condition, VERIFIED on main unless marked)

| # | Step | Site | Conditions | Reads pawn / health / state / HUD mode / spectating? |
| --- | --- | --- | --- | --- |
| 1 | key T / Y | `PlayerProfilePC.ini` `Console Talk` / `Console TeamTalk` | - | no |
| 2 | `Console.Talk` / `TeamTalk` | Engine.u exports 9784 / 9785 | `TypedStr = "Say "` / `"TeamSay "`, `GotoState('Typing')`, no condition | no (bytecode) |
| 3 | `Console.Typing.BeginState`, `KeyType`, `KeyEvent` | Engine.u 9808, 9796, 9800 | `bIgnoreKeys`, the character ranges; on Enter (key 0x0D) with a non-empty line: `ConsoleCommand(TypedStr)`; Escape clears | no (bytecode, all 735 bytes of `KeyEvent` walked) |
| 4 | `Interaction.ConsoleCommand` | native `0x10A1BDC0` (n1218) | the interaction's master and its client's viewport exist; whitelist `0x10A1CBC0`: SHOT, SAY, TEAMSAY, QUIT, EXIT | no |
| 5 | exec `SAY` / `TEAMSAY` | `0x10A1ABD6` / `0x10A1ACF4` in `0x10A1A040` | text not empty; the viewport's PlayerController `[+0x2C]`; TEAMSAY also its PRI `[PC+0x618]` and PRI.Team `[PRI+0x414]` (team = `[Team+0x408]`); formats `"%s : %s"` / `"%s (team): %s"`, channel 7, life 5.0; `ProcessEvent(PC.MessageManager [PC+0xA10], SimpleStringToTeam 0x1EAD)` via `0x10A179A0` | no |
| 6 | client -> host | `MessageManager.SimpleStringToTeam`: native 3916, flags `0x00020CC0` (net, reliable), replication code 3 (Engine.u export 7969) | INFERRED: the engine's replication (role, owning connection); no state test | no (INFERRED) |
| 7 | the host's fan-out | `0x109B8680`; game state `[0x1100AA2C]+0x4B8`: `0x60000` = lobby (37-character chunks to the menu manager), `0x80000` = in game | in game: `[MM+0x2FC]` Owner not 0; **Owner.Pawn `[+0x408]` not 0 and Pawn.Health `[+0x1580]` > 0, else the line is dropped (`0x109B8B36..4F`)**; then for every controller of `[MM+0x304]`'s list `XLevel+0x1F4`: PRI `[+0x618]`, PRI.Team `[+0x414]` not 0, team filter `[Team+0x408]` (TEAMSAY), MessageManager `[+0xA10]` not 0 -> `0x109B7A20` | **YES: the only one** (v3 site 9) |
| 8 | host -> each receiver | `0x109B7A20`: `ProcessEvent(receiver MM, SimpleStringToClient 0x1EAF)`, replication code 4 (Engine.u 7974) | none | no |
| 9 | the receiver | `execSimpleStringToClient` `0x109B8C20` -> add `0x109B81D0` | channel above 20 -> 0, life 0 -> 5; record at index 0: text, `+0xC` channel, `+0x10` life, `+0x14` `[Level+0x5C8]`, `+0x1C` sequence = `[MM+0x420]`, then the counter +1 | no |
| 10 | the record lives | MessageManager tick `0x109B8520` | removed after its life (5 s for chat) | no |
| 11 | v3's capture | `.chat` capture | every frame: the viewport's PlayerController's MessageManager (else the HUD owner's); no HUD, canvas or closed menu needed | no |
| 12 | v3's draw | `.chat` Overlay | a HUD (`[viewport+0x68]`, else `[PC+0x95C]`), the site's canvas, a live message; HUD_TOGGLE `[0x1100FF04]` and the HUD's `bIsMessageZoneActive` (`HUD+0x410` bit 0x10, never written by script, on in modes 0, 4, 5 in game) as switchable gates | no |

## How the game draws a frame (VERIFIED on main 0f1b2d1c, from v2)

| Part | Fact |
| --- | --- |
| player scene render | `0x10A50050`, thiscall (scene node; RI, flag), `ret 8`; `[node+4]` = viewport. Called by the three viewport draws `0x10A148EA`, `0x10A16171`, `0x10A16784`. Order: RI begin, canvas update `0x109FCB20`, flush, console pre-render, the scene, then the HUD block, then flush `0x10A5C5C0` at **`0x10A50607`**, the menus (`[0x1100FF7C]` vt+0x28), the console post-render `0x10A1D470`, flush, RI end |
| HUD block | `0x10A5055E`..`0x10A50606`: HUD = `[viewport+0x68]`; if `[HUD+0x428]` != 0: HUD render `0x10B70E30(HUD)`, HUD vt+0x440(canvas), per-widget post draw `0x10B70C20`; then the HUD PostRender event (name `0x1242`). The function reads no HUD-mode byte; every path passes `0x10A50607` |
| viewport and owners (v3) | `[viewport+0x2C]` = UPlayer.Actor, the local PlayerController (`0x10A155D8`: `[Actor+0x95C]` myHUD -> the HUD loop `0x10B70EF0`; `0x10B80BE3`); `[PC+0xA10]` MessageManager; `[HUD+0x400]` PlayerOwner, `+0x404` CurrentDrawMode (the mode byte), `+0x410` bools (bit 0x10 `bIsMessageZoneActive`, INFERRED from the declaration order in Engine.u), `+0x428` the HUD scene node (INFERRED from the declaration order) |
| HUD render gates | `0x10B70E30` and `0x10B70C20` return at once when the menu object `[0x1100FF7C]` answers vt+0x38 != 0 or `[0x1100FF04]` != 0 (`HUD_TOGGLE`, `0x10A11650`; not bound in main's `PlayerProfilePC.ini`, not in the typed-console whitelist) |
| canvas | `+0x28` util, `+0x2C` font, `+0x5C/+0x60` SizeX/Y, `+0x64` scaleCarriageReturn 0.75, `+0x78` MediumFont (font 0) |
| canvas text block | `0x109FBEF0`: ecx = text, edx = canvas; stack out, x, y, hj, vj, direction x/y/z, width, font, scale, colour; `ret 0x30`; draws each glyph through the util's DrawTile `0x10A5CAF0` (RGB halved, alpha kept) |
| clock | `[XLevel+0x614]` (double), XLevel = `[HUD+0x304]` or `[PC+0x304]` |
| MessageManager | stack `+0x404` max, `+0x408` count, `+0x40C` records (0x24: `+4` chars incl. NUL, `+8` text, `+0xC` channel, `+0x1C` sequence; newest at index 0; records are moved with their text pointer), sequence counter `+0x420`, history `+0x3F4..`, history length `+0x400` |
| stock chat widget | widget 18, vtable `0x10F93090`, update slot `+0x1C` `0x10B82930`, mode mask `0x802` (modes 1, 11) |

## What the patch changes

Two new sections carry the code and its data; three places of the stock image point at them or step over a test; four header fields and two section headers describe them. Every other byte of main's exe is unchanged (static gate). File offset = VA - `0x10900000` inside `.text` and `.rdata`.

| # | File | Site | Stock | New | Purpose |
| --- | --- | --- | --- | --- | --- |
| 1 | `System\SCDA_Online.exe` | file `0x146`, FileHeader.NumberOfSections | `05 00` | `07 00` | two sections added |
| 2 | same | file `0x15C`, OptionalHeader.SizeOfCode | `00 E0 52 00` | `00 F0 52 00` | + `.chat`'s 0x1000 |
| 3 | same | file `0x160`, OptionalHeader.SizeOfInitializedData | `00 30 2B 00` | `00 50 2B 00` | + `.chatd`'s 0x2000 |
| 4 | same | file `0x190`, OptionalHeader.SizeOfImage | `00 20 7E 00` | `00 50 7E 00` | image ends after `.chatd` |
| 5 | same | file `0x300`, section header 6 (was 40 zero bytes) | zeros | `.chat`: VirtualSize `0xBBB`, RVA `0x7E2000`, raw size `0x1000`, raw `0x75B000`, flags `0x60000020` (code, execute, read) | the code |
| 6 | same | file `0x328`, section header 7 (was 40 zero bytes) | zeros | `.chatd`: VirtualSize `0x1300`, RVA `0x7E3000`, raw size `0x2000`, raw `0x75C000`, flags `0xC0000040` (initialized data, read, write) | the data |
| 7 | same | VA `0x10A50607` (file `0x150607`), scene render, the call to the canvas-util flush after the HUD block | `E8 B4 BF 00 00` (`call 0x10A5C5C0`) | `E8 F4 19 69 00` (`call 0x110E2000` Overlay) | Overlay runs once per rendered frame after everything the HUD draws and ends with `jmp 0x10A5C5C0` |
| 8 | same | VA `0x10F930AC` (file `0x6930AC`), widget 18 vtable slot `+0x1C` | `30 29 B8 10` (`0x10B82930`, stock update) | `85 22 0E 11` (`0x110E2285` Suppress) | the stock chat widget hides its 3 items and never appends them |
| 9 | same | VA `0x109B8B36` (file `0x0B8B36`), host `MessageManager.SimpleStringToTeam` `0x109B8680`, in-game branch | `8B 80` (first 2 bytes of `mov eax,[eax+0x408]`; the test ends `jle 0x109B8BEA` at `0x109B8B4A`) | `EB 18` (`jmp short 0x109B8B50`; the other 24 bytes stay, unreached) | the host sends a line whose sender has no pawn or Health <= 0 to every player like any other (the owner test before it stays) |
| 10 | same | file `0x75B000..0x75BFFF` appended: `.chat` | - | 3,003 bytes of code (md5 `743975a4cbfa85d71cd34fef2d40a5ad`), zero padded to 0x1000 (page md5 `915310241bba081e3d03659528d0fd93`) | Overlay and its subroutines, Suppress; listing `build\gates\listing.txt` |
| 11 | same | file `0x75C000..0x75DFFF` appended: `.chatd` | - | 0x2000 bytes (md5 `dde7bf827fbe42f9b63be5911c893812`); `0x000..0x0F3` v2's constants, FN table and W offsets, `0x1100..0x1117` v3's switches, `R_LASTSEQ`, `R_GATE`, `R_FRAMEMODE`, `R_STKSEQ`, `R_NEWSEQ` -1, the rest zero (runtime state) | constants and state |

- v1's two other sites are main's again (static gate). CheckSum (file `0x198`) is left as found, `0x00768CB7`, as in main (main's own stored checksum is already stale; the loader does not check an exe's). No relocation entries for the new sections (no `DYNAMIC_BASE`, loads at `0x10900000`); the only relocation entry touching a changed byte is the vtable slot's own; sites 7 and 9 need none.
- Result: 7,725,056 bytes (main + `0x3000`), md5 **`3fba79cf53149f7aaa7c4afccaa867f7`**.

### The new code

| Routine | VA | Does |
| --- | --- | --- |
| Overlay | `0x110E2000` | `pushad`; the util of the site; viewport `[node+4]`; owners (PlayerController `[viewport+0x2C]`, HUD `[viewport+0x68]` else `[PC+0x95C]`, the HUD's owner `[HUD+0x400]`, MessageManager of the viewport's PC else of the HUD's owner), each change counted, nothing reset; clock; capture (a new source: from its oldest record; its counter `[MM+0x420]` back: the same); fixLines, expire, trimRows, alphas; then the draw when a HUD and the site's canvas exist and the switched-on gates pass; the gate's frame counter; `popad`; `jmp 0x10A5C5C0` |
| Suppress | `0x110E2285` | widget 18's update (thiscall, `ret 8`): `0x10BA1780(item, 0)` for its 3 items |
| clock | `0x110E22C5` | level = `[HUD+0x304]` else `[PC+0x304]`; step = (float)(time - last time) (SSE2 double); 0 <= step <= MaxStep advances the own clock `R_NOW`, else the step is counted and ignored |
| removeFront / recText | `0x110E2365` / `0x110E238D` | drop the oldest entry / a record's characters and the length the list keeps (to the first NUL, at most 127) |
| capture | `0x110E23BA` | the stack's count, newest sequence and text for the probe; start over when the newest sequence is below the last taken or the record with the last number taken has another text pointer; then every record above the last number, oldest first: skipped when listed (isDup), else addEntry |
| isDup / addEntry | `0x110E2518` / `0x110E257C` | an entry with this source, sequence and text? / a new newest entry (sequence, channel, source, the own clock, text, line count at the wrap 726 font px; the line count marked known when the game's `0x10BA6CE0` answered) |
| lineCount / fixLines | `0x110E2628` / `0x110E269B` | v2's line count / later line counts for entries taken without a HUD |
| expire / trimRows / alphas | `0x110E26E6` / `0x110E2745` / `0x110E277D` | v2's: Life + Fade, 8 messages, 12 rows; alpha 1 until Life, then linear to 0 over Fade |
| drawList / textAt | `0x110E2824` / `0x110E2B74` | v2's (VERIFIED visible in game run 3): the canvas text block `0x109FBEF0` on the screen canvas, shadow pass and text pass per entry, newest at the bottom row |

Game routines are reached only through the FN table in `.chatd` (show `0x10BA1780`, lines `0x10BA6CE0`, text `0x109FBEF0`, glyph `0x109FEF70`) and one virtual call (the menu's vt+0x38, only with the menu gate switched on). Absolute data: `0x1100FF04`, `0x1100FF7C` (read) and `.chatd`.

### Constants and switches (builder parameters, stored in `.chatd`)

| Constant | Value | From |
| --- | --- | --- |
| ExtraChars / wrap | 15 / 726 font px | the order; 504 + 15 x 14.8 |
| MaxMessages / MaxRows | 8 / 12 | the order / 12 rows of 18 px at 720 lines |
| LifeSeconds / FadeSeconds | 10 / 1 | the order |
| ScaleK, XK, YK, Colour, Shadow | 0.755 / 720, 112 / 720, 642 / 720 - 9 x ScaleK, `0x87B2E8`, 1 px at 720 lines | the stock chat's measured size and place (v2, seen right in run 3) |
| MenuGate (`--menu-gate`) | 0 | the brief: draw also while a menu covers the HUD (the menu draws over the chat where they overlap) |
| NodeGate (`--node-gate`) | 0 | the overlay does not need the HUD's scene node |
| ToggleGate (`--toggle-gate`) | 1 | `HUD_TOGGLE` is the player's own "hide the HUD"; not bound and not typeable in main, so it never stops the chat there |
| ZoneGate (`--zone-gate`) | 1 | the HUD's own message-zone switch; never written by script, on in every mode seen in game |
| MaxStep (`--max-step`) | 1 s | a larger level-time step (a load) or a negative one (a new level) does not age the list |
| DeadChat (`--dead-chat`) | 1 | site 9 |

Other builds: `ChatExeBuild build <main exe> <out> [--extra N] [--max N] [--rows N] [--life S] [--fade S] [--shadow 0|1] [--shadow-alpha A] [--colour RRGGBB] [--zone-colour] [--scale720 S] [--x720 PX] [--y720 PX] [--shadow720 PX] [--menu-gate 0|1] [--node-gate 0|1] [--toggle-gate 0|1] [--zone-gate 0|1] [--max-step S] [--dead-chat 0|1]`.

## Requirements

| # | Order | How | Status |
| --- | --- | --- | --- |
| 1 | list, newest at the bottom, pushed up, no scroll-in | own list, one grid from the bottom up | harness VERIFIED; in game VERIFIED (run 3) |
| 2 | 10 s, then a fade | per message alpha on the own clock | harness VERIFIED (B, K); fade on screen INFERRED |
| 3 | at most 8 | MaxMessages 8, MaxRows 12 | harness VERIFIED (C, D, E) |
| 4 | +15 characters, same letter size | wrap 726 font px at the stock chat's measured scale | harness VERIFIED; in game run 3 (size looked right) |
| 5 | no frame, rows closer | text only, the text block's own line step | by construction; run 3 |
| 6 | shown while dead, incoming included; in every view; kept over a menu, a respawn, a team switch, a new level | the draw site runs every rendered frame whatever the HUD mode; capture and list independent of the HUD, the menu, the owners and the level clock | static VERIFIED (control flow of `0x10A50050`); harness VERIFIED (R modes 1, 11, 0, 4, 5, 13, 3, 9, 2, 8; G; K; O; T) |
| 7 | dead players can chat | the host no longer drops a dead sender's line (site 9); nothing else on the route tests death | static VERIFIED (route table); harness VERIFIED on the real fan-out (X); two players in game open |
| 8 | "just put them on a new custom overlay" | stock widget suppressed, own overlay | harness VERIFIED (S) |

## Gates (transcripts in `build\gates\`, runner `run-gates.ps1 -Work <scratch>`; v2's in `build\gates\v2\`)

| Gate | Result (2026-09-30 00:51-00:53) |
| --- | --- |
| `build.txt` | 3 PASS, 0 FAIL: 3 builds from main, one md5 (exe `3fba79cf`, `patch.ps1` `35a5eb1b`); `files\System\SCDA_Online.exe` and `patch.ps1` equal the build |
| `gate.txt` (static) | 74 PASS, 0 FAIL: header and sections; every byte of main's length (only the listed 9 fields differ; v1's sites main's); the draw site, the slot, the stock update unreferenced, the HUD render's one caller, every path of the scene render passes the site; **site 9**: main's 26 bytes are the dead-sender test, the 5 skipped instructions only branch to the exit and write nothing but eax, the target `0x109B8B50` is `mov eax,[ecx+0x304]`, the owner test before it unchanged, no branch lands in the skipped bytes; relocations; 23 relied-on ranges equal to main (incl. the fan-out, send-to-client, SimpleStringToClient, add); `.chatd` constants and switches; the wrap snap at every height 16..4320; a rebuild from the constants read back gives the file byte for byte; `.chat` disassembled (720 instructions; absolute data only in `.chatd` and the two HUD globals; calls only through the FN table and the menu's vt+0x38; one jmp out, to the flush; no `int`/`syscall`/`in`/`out`/`rdtsc`/`cpuid`); coexistence (QolHud v3, main's `Enhanced.asi`, DedServer windows, main's flashbang cave) |
| `harness.txt` | 157 PASS, 0 FAIL. The whole patched image mapped at `0x10900000`, the real scene tail, text block, DrawTile and flush: **R** modes 1, 11, 0, 4, 5, 13, 3, 9, 2, 8 and three screen sizes; **G** the menu, scene-node, HUD_TOGGLE and zone gates with the defaults and each switch flipped (entries kept, drawn again), no HUD (captured, line count fixed later), PC.myHUD instead of the viewport's HUD, the per-gate counters; **L** v2's A..E and 3,000 random frames against the model; **K** a new level (clock back), a 30 s load, no level; **O** a new HUD, a HUD without owner, no viewport actor, a new PlayerController with a new MessageManager, a new one at the same address (counter back; counter not back but the record with the last number another one), back to an earlier one (nothing twice), no MessageManager for a while, death and respawn; **T** run 4's timeline (menu, owner loss at 8.8 s, load, new level, merc, modes 0, 4, 5 with the quit dialog): 6 of 6 messages taken, the list never emptied; **X** the host's REAL fan-out `0x109B8680`: main's bytes drop a dead sender's line (no pawn, Health 0) and pass a living one's, v3's pass all (no pawn, Health 0, Health -25, alive; TEAMSAY to the team only), then each receiver's REAL `0x109B8C20` and add `0x109B81D0` put it into all 3 MessageStacks and the dead sender's own overlay draws it in mode 5; **S** the real HUD loop with widget 18 suppressed; **Q** QolHud.asi v3 loaded. Mutation checks (not in the transcript, 2026-09-30 00:4x): a build with `--dead-chat 0` fails 9 checks (all X v3 cases), a build with `--menu-gate 1` fails 7 |
| `dryrun.txt` | 34 PASS, 0 FAIL, on a scratch copy of main's `System`: refusals (main path, `Running.ini`, both switches, a foreign exe), apply (= the stack), status, apply again, revert (byte-identical, date restored, backup removed), a dragged stack; v1 installed and dragged; **v2 installed with its backup: status names it, -Apply refused, -Revert restores main byte-identical; a dragged v2 reverted, then v3 applied and reverted** |
| `probe.txt` | 1 PASS, 0 FAIL: `test\chat-state.ps1` v3 read the harness's live `.chatd` (`--hold` with a HUD change, a PlayerController and MessageManager change, a menu, mode 5): header with the switches, the owners and the stack on every line, mode 5 with messages, owner changes and frames per gate in the heartbeats |
| Defender | no detection of any CL-7 file (history read 00:53; the newest entry is CL-2's `ChatList.asi` of 2026-09-29 19:25) |

## Coexistence

| With | Result |
| --- | --- |
| `qol-hud` v3 (`QolHud.asi` `722365f7`) | compatible (static and harness Q, S) |
| main's `Enhanced.asi` (`f5a6da95`) | none of its 70 byte patterns covers a changed byte (static gate) |
| `DedServer.asi` | no changed byte inside its 15 compared windows; the dedicated server's host would also carry site 9 if it ran this exe |
| other exe stacks | excluded: `widescreen-zoom` and `widescreen-menu` replace the same exe and put their `.wsz` section at the same `0x110E2000` |
| launcher | its game-file check refuses PLAY for a changed exe; tests start the exe directly; for players the patched exe ships as a launcher game change (the operator's step) |

## Apply

Game closed; from PowerShell in this folder:

```
.\patch.ps1 -GameDir "<game folder>"            # status
.\patch.ps1 -GameDir "<game folder>" -Apply
.\patch.ps1 -GameDir "<game folder>" -Revert
```

`-Apply` refuses unless the exe is main's `0f1b2d1c` (and names v2 or v1 when one of them is installed: run `-Revert` first), builds the patched exe from the change list it carries, checks the stack's md5 `3fba79cf`, keeps `System\SCDA_Online.exe.0f1b2d1ce8167d267ee15d5a4ed4c3e6.chat-list.bak`, then writes. `-Revert` rebuilds main's exe from v3, v2 (`b28c9113`) or v1 (`c4f50a7f`), checks main's md5, restores the date from the backup and removes it. Both refuse the main branch path, a running `SCDA_Online.exe` of this install (`-AllowRunningGame` lifts that for dry runs on scratch copies) and `System\Running.ini`. `patch.ps1` md5 `35a5eb1bcb4f7caf16e859cd57bfb781`.

## In-game tests (orchestrator): run 5

The loop is `HANDOVER.md` "Test loop". v3 specifics; the probe is `test\chat-state.ps1 -OutFile <path> -Seconds 900` (v3 only; v2's is `chat-state.ps1.v2`):

| Step | The operator does | The probe must show | If not |
| --- | --- | --- | --- |
| 1 | installed alone (`-Apply`, md5 `3fba79cf`), launch as the HOST, spawn as spy | `calls` grows about as fast as the frame rate; `src 1/1`; mode 11 then 1 | `calls` 0: the site is not reached (check the md5) |
| 2 | wait for the spawn protection texts; type a line | `stack` newest # grows with each text, `last taken #` follows it, `capt` grows, msgs listed, `gate drawn`; on screen bottom left as in run 3 | `stack` grows but `capt` does not: capture stalls (send the line); msgs listed and `gate drawn` but nothing seen: drawn but invisible (shot) |
| 3 | open the in-game menu, close it | msgs stay (no drop to 0 without `exp`/`drop`), `gate drawn` while the menu is open (the chat under the menu), `chg` counters as they are | msgs 0 without `exp`/`drop`: emptied (must not happen) |
| 4 | switch team (as in run 4: menu, load, merc) | `chg hud / pc / mm` grow by 1 each (a new PlayerController and MessageManager), `clkskip` +1 (the new level), young messages still listed; a line typed as merc: `stack` newest and `capt` grow | `mmnow` changes but `mm` stays 0 or `stack` stays: the MessageManager is read from elsewhere (send the line) |
| 5 | die (a frag at the feet as merc, or be killed), stay dead, type a line and press Enter | mode 0, then 4 (kill cam), 5 (spectating); the typed line: `stack` newest # grows, `capt` grows, it is listed and drawn (`gate drawn`); a second player's line arrives too | the line not in `stack` while the exe is the host's: the host's site 9 (md5); as a client of another host: that host needs v3 |
| 6 | open the quit dialog while dead | still `gate drawn`, the chat visible bottom left over the dark screen | - |
| 7 | respawn | nothing reset (`chg` unchanged), messages keep fading on their clock | - |
| after | close the game, `-Revert`, the working copy check | - | - |

Counters: `dup` = records seen again and skipped (an earlier MessageManager read again); `seqrst` = the capture started over (a new MessageManager at the same address); `linefix` = line counts filled in once a HUD was there; `frames per gate` in each heartbeat.

## Known limits

- Run in game once (run 5, one player, host): the list alive, dead (mode 0), in the kill cam (mode 4), after a team switch and after a respawn, and the host's dead-sender site are VERIFIED in game. Not seen in game: a second player, spectating (mode 5), a menu or the quit dialog with live lines, drone and scope.
- In the kill cam the list's upper rows lie over the kill cam's two key hints at the left edge (run 5, shot `r5-051s`).
- Dead chat needs v3 on the **host**. As a client of a stock host a dead player's line is still dropped by that host.
- A menu that covers the HUD is drawn over the chat where they overlap; on dark or transparent pages the chat shows (the brief's default). `--menu-gate 1` hides the chat under menus as v2 did.
- A level-time step above 1 s does not age the list (a load, a hitch of more than a second, the game paused): messages stay that much longer.
- A message is cut to 127 characters; 12 rows at most. No icon, no channel colours (stock has none either).
- A record already listed is recognised by source, sequence and text; the same text with the same sequence number from a new MessageManager at the same address within 11 s would be taken for the old one (INFERRED never: the counter and text-pointer checks run first).
- Reverting a dragged stack means putting main's exe back (from main, a copy, or `patch.ps1 -Revert`).

## Drag-and-drop stack (files/)

| Install path | md5 | Replaces (main-build md5) |
| --- | --- | --- |
| `System\SCDA_Online.exe` (7,725,056 B) | `3fba79cf53149f7aaa7c4afccaa867f7` | `0f1b2d1ce8167d267ee15d5a4ed4c3e6` (7,712,768 B) |

- Built by `build\builder` from a read-only copy of main's exe; three builds give one md5; `patch.ps1 -Apply` on a copy of main gives the same file (dry run).
- Dragging the contents of `files\` (its `System` folder) onto the install root and choosing replace applies the feature (on the host: including dead chat). The drop makes no backup and checks no md5; `patch.ps1` does both.
- The stack replaces the whole exe: it cannot be combined with another exe stack, and it must be rebuilt when main's exe changes.

## v3 on main 2026.10.02-4

Built by C-1 on 2026-10-03 (brief `BRIEF-C1.md`, notes `C1-notes.md`). Main 2026.10.02-4 (release `v2026.10.02-4`, 2026-10-02 21:05Z, "Club House lifts carry you up and down again") ships a new SMOKE exe `4a17634f` = `0f1b2d1c` + SYNCADE's door carry (`toolbox\patch_door_carry_exe.py`). `files-m4\` carries v3 rebuilt on it, for the M3epbuggin channel's `M3CHAT` add-on (`"over": "SMOKE"`). `files\` (v3 on `0f1b2d1c`) and `patch.ps1` are unchanged.

| Item | Value |
| --- | --- |
| base | `4a17634fbebc1cb2c6b550cc35337d9f`, 7,712,768 B (sha256 `bcbb05de...b944`). Obtained by two routes that agree byte for byte: (1) C-1 downloaded release `v2026.10.02-4` (`REALSYNCADE/SCDA-Launcher`, `scda-ce-2026.10.02-4.scdaupd`) and applied the SMOKE add-on's delta (`payloads/System__SCDA_Online.exe`, SCPD1) with `scpatch.py` to stock `fc237f82` (sha256 `ee80d235...`, from the `sources` store of `REALSYNCADE/SCDA-Experimental`); (2) the copy the launcher itself built in `%LOCALAPPDATA%\M3eptemp\...\under\System` (read only, md5 and compare). The catalogue's `sources.lock.json` does not name it: `slots.json` points to `../release-sources/SCDA_Online.exe.smokemine.flashbang.doorcarry` |
| door carry | `4a17634f` = `0f1b2d1c` + SYNCADE's `toolbox\patch_door_carry_exe.py`: 239 bytes differ from `0f1b2d1c`, in three spans (266 B) all in `.text`: the hook at `0x10DAFB06` (file `0x4AFB06`, 5 B) `8D 43 28 89 08` -> `E9 D5 F3 07 00` (jmp `0x10E2EEE0`); the main cave `0x10E2EEE0..0x10E2EFB4` (file `0x52EEE0`, 213 B, was zero; one call to FarMoveActor `0x10A1EBD0`); the tail `0x10E2EB50..0x10E2EB7F` (file `0x52EB50`, 48 B, was zero; jumps back to `0x10DAFB0B`). The PE header is byte-identical (5 sections, SizeOfImage `0x7E2000`, CheckSum `0x00768CB7`, same length), so no section was appended. `patch_door_carry_exe.build()` on `0f1b2d1c` gives `4a17634f` byte for byte |
| overlap | none. The chat list's 9 fields (header `0x146..0x34F`, `0x109B8B36` 2 B, `0x10A50607` 5 B, `0x10F930AC` 4 B) and `.chat` / `.chatd` (appended after `.reloc`) are at least 1,458,424 B from door carry (the nearest is `0x10F930AC`, to the main cave). The chat list leaves the `.text` slack `0x10E2EB41..0x10E2EFFF` untouched. Nothing moved: `.chat` is still at raw `0x75B000` / VA `0x110E2000` and `.chatd` at raw `0x75C000` / VA `0x110E3000` |
| result | `files-m4\System\SCDA_Online.exe`, 7,725,056 B, md5 **`0fd28e5f875c37db072735e005174407`**. It equals `3fba79cf` with door carry's 239 bytes laid on, byte for byte. Against `4a17634f` it differs in exactly v3's 41 changed bytes plus the 12,288 appended bytes |
| builder | `build\builder\Program.cs` (md5 `25a48b28`; the prior copy is `Program.cs.pre-c1`, `c8d40eb9`) accepts `4a17634f` beside `0f1b2d1c`. The build info, the gate header and patch.ps1 name the base. patch.ps1 recognises v2 and v1 only on `0f1b2d1c`. On `4a17634f` the gate adds two door-carry checks. `0f1b2d1c` still gives `3fba79cf` / patch.ps1 `35a5eb1b` (3 builds) and the same 74-check gate |
| gates (`build\gates\m4\`) | `build.txt`: 3 builds, one md5 (exe `0fd28e5f`, patch.ps1 `91747510`). `gate.txt`: ALL PASS, 76 checks: v3's 74 (the dead-site gate included), plus door carry kept byte for byte with its flow (hook -> cave -> tail -> `0x10DAFB0B`), plus no changed byte within 16 B of it. `harness.txt`: ALL PASS, 157 checks; the transcript equals v3's except for the exe path. `sites.txt` (`sites.py`): ALL PASS. `patch-m4.ps1` is not delivered; its dry run on a scratch `System` applied `4a17634f` -> `0fd28e5f`, reverted to `4a17634f` and refused `3fba79cf` as another build |
| plugin sites | every site holds its stock bytes, and the 256 B on each side equal `0f1b2d1c`'s and `4a17634f`'s. The sites: QolHud A `0x10B73C90` and B `0x10B70E98` (with its 3 compared blocks); SniperHeadshotSound `0x10BD842B` `8B 85 14 16 00 00`; SpyGrab `0x10BCAE97`, `0x10BC9F2D`, `0x10C35FEB` and `0x10BCB00F` (with 30.0 at `0x10FA4A68`); QOL4Necks J1 `0x10BCAE92`, J2 `0x10BCB009` (with 3000.0 / 1500.0), J3 `0x10BC9F18`, D `0x10BD8AD0` and D2 `0x10DAA307`. D2 is the nearest to door carry, 22,522 B away |
| papers | `build\gates\m4\`: `build.txt`, `gate.txt`, `harness.txt`, `sites.txt` with `sites.py` (run as `sites.py <new exe> <4a17634f> <0f1b2d1c>`), `patch-m4.ps1` (`91747510`, generated, not delivered); brief `BRIEF-C1.md`, notes `C1-notes.md`. Working copies in `scratch\c1\`: the bases `base-4a17634f.exe` and `base-0f1b2d1c.exe` (the latter rebuilt from `files\` by reverting v3's changes; md5 verified), the compiled builder `bld\bin`, the harness `har\bin` and its runtime `rt\`, the 0f1b2d1c gate transcript `gate-0f1b.txt` (74/74). The build outputs the transcripts name (`m4out1\SCDA_Online.exe`, `old1\SCDA_Online.exe`) were byte copies of `files-m4\` and `files\` (same md5) and were deleted by C-1b; the downloads (`scratch\c1\dl\`: bundle and stock exe) are gone |
| not done | no game was started and nothing was installed. The chat list and door carry have not been seen together in game |

## v4 look only on Community Edition 2026.10.07-1

v4 draws v3's chat list (requirements 1-5 and 8 unchanged) exactly where and when the stock chat would be drawn, and leaves the host's dead-sender test as the base has it. Built by V-1b on 2026-10-08 (brief `BRIEF-v4.md`, notes `V4-notes.md`; V-1 began it and was paused) for the M3epbuggin channel. Orders, in the operator's words (2026-10-07): "new build, use https://raw.githubusercontent.com/REALSYNCADE/SCDA-Launcher/main/latest.json as main reference, in case you need to reverse it, remove the no mic guard, and the new chat features, but maintain the new UI look, all gameplay changes that are in the new build should be included"; "i ment chat list look, keep drone and scope hud as well. keep voice".

| Item | Value |
| --- | --- |
| base | Community Edition 2026.10.07-1's SMOKE exe `4a17634fbebc1cb2c6b550cc35337d9f`, 7,712,768 B (unchanged since 2026.10.02-4; `scratch\c1\base-4a17634f.exe` = `scratch\v4\ce-2026.10.07-1\SCDA_Online.exe`) |
| build | `ChatExeBuild build <4a17634f> <out> --dead-chat 0 --stock-vis 1` (new switch `--stock-vis 0|1`, default 0) |
| result | `files-v4\System\SCDA_Online.exe`, 7,725,056 B, md5 **`2724a6976315aee7992e1562aca61d64`**; replaces `4a17634f` |
| default builds | unchanged: `3fba79cf` from `0f1b2d1c` and `0fd28e5f` from `4a17634f` (patch.ps1 `35a5eb1b` / `91747510`); with `--stock-vis 0` the builder emits no new byte |
| not done | no game was started and nothing was installed; v4 has not run in game |

### The gate's route

| # | Fact | Status |
| --- | --- | --- |
| 1 | widget 18's mode mask is live, not a constant: `[widget+0x34]`; its ctor `0x10B81650` (one call, `0x10B7262B` in the HUD builder `0x10B721F0`) has the base ctor write 0 (`0x10B739F1`), then `or [esi+0x34],0x802` (`0x10B816A5`); the mode test vt+0xC `0x10B73C90` is `(1 << mode) & [widget+0x34]` | VERIFIED (disassembly) |
| 2 | the HUD loop `0x10B70EF0` has one caller, `0x10A155FD` in `0x10A15550` (the engine tick `0x10A14E80`): once per tick, for viewport 0's PlayerController `[viewport+0x2C]` and its HUD `[PC+0x95C]`; it returns at once on HUD_TOGGLE `[0x1100FF04]`; per widget it calls the update slot +0x1C when the mode is 7 or vt+0xC(7) or vt+0xC(mode) answers 1, else the hide path `0x10B747E0`; it does not test the menu | VERIFIED (disassembly) |
| 3 | the loop is not inside the scene render: the scene render `0x10A50050` (site 7) runs from Engine::Draw `0x10A14220`: the normal path `0x10A148EA`, or a one-shot request path `0x10A15D40` (`[[viewport+0x64]+0x40]`, cleared at once) that can render twice (`0x10A16171`, `0x10A16784`) | VERIFIED; that `0x10A15D40` is the screenshot path INFERRED |
| 4 | the stock chat's items are drawn only when the HUD `[viewport+0x68]` exists, `[HUD+0x428]` != 0 (`0x10A50573`), the menu's vt+0x38 answers 0 and HUD_TOGGLE is 0 (`0x10B70E30`), with the visibility the last HUD loop gave them | VERIFIED (disassembly) |
| 5 | one HUD loop per site-7 call in game: run 5's probe (v3) counted `supp` and `calls` rising by the same number in mode 11 (907 / 907) and in mode 1 as merc (403 / 403) | VERIFIED (run 5 probe) |
| 6 | which comes first within one tick, the draw or the loop (the client tick vt+0x7C at `0x10A15593` runs before the loop) | not settled; the route does not depend on it (harness V3) |

Route built: the brief's stamp route, as a one-shot flag. Suppress (which the loop calls only when the stock chat would be shown) sets `R_STAMP`; Overlay copies it into `R_VIS` and clears it at its entry on every call; the draw needs `R_VIS` (gate 12 "the stock chat is not shown"). With one loop per draw this is exact in either order within a tick: the draw follows the visibility the last loop gave the stock items. `--stock-vis 1` also forces the scene render's own HUD-block conditions on (the node gate `[HUD+0x428]`, the menu gate vt+0x38, the toggle gate HUD_TOGGLE). The brief's fallback (a test of the mode against the mask at draw time) was not needed and would not follow the loop's other conditions (no PlayerController, HUD_TOGGLE) nor QolHud's answer. Capture, owners, the own clock, expiry, limits and alphas still run every frame: a hidden list keeps its entries, which age on and show again with the life they have left.

### Changes against Community Edition 2026.10.07-1 (rows 5, 8, 9, 10, 11 differ from v3)

| # | File | Site | Stock | New | Purpose |
| --- | --- | --- | --- | --- | --- |
| 1-4 | `System\SCDA_Online.exe` | file `0x146`, `0x15C`, `0x160`, `0x190` | as v3 rows 1-4 | as v3 rows 1-4 | two sections, their sizes |
| 5 | same | file `0x300`, section header 6 | zeros | `2E63686174000000FF0B000000207E000010000000B0750000000000000000000000000020000060`: `.chat`, VirtualSize **`0xBFF`** (v3 `0xBBB`), RVA `0x7E2000`, raw size `0x1000`, raw `0x75B000`, flags `0x60000020` | the code |
| 6 | same | file `0x328`, section header 7 | zeros | as v3 row 6: `.chatd`, VirtualSize `0x1300`, RVA `0x7E3000`, raw size `0x2000`, raw `0x75C000`, flags `0xC0000040` | the data |
| 7 | same | VA `0x10A50607` (file `0x150607`) | `E8 B4 BF 00 00` | `E8 F4 19 69 00` (`call 0x110E2000` Overlay), as v3 | Overlay after the HUD block, ends with `jmp 0x10A5C5C0` |
| 8 | same | VA `0x10F930AC` (file `0x6930AC`), widget 18 vtable slot +0x1C | `30 29 B8 10` | **`BF 22 0E 11`** (`0x110E22BF` Suppress; v3 `85 22 0E 11`) | the stock widget hidden; v4: the stamp |
| 9 | same | VA `0x109B8B36` | `8B 80` | **not changed** (v3: `EB 18`) | no dead chat: the host drops a dead sender's line as the base does |
| 10 | same | file `0x75B000..0x75BFFF` appended: `.chat` | - | 3,071 bytes of code (md5 `1c639b4275cb39f7ee967b74005e5e01`), zero padded to 0x1000 (page md5 `40b47515d4384196fbf53dfcb1ef7fd2`) | Overlay with the stamp gate, Suppress with the stamp; listing `build\gates\v4\listing.txt` |
| 11 | same | file `0x75C000..0x75DFFF` appended: `.chatd` | - | 0x2000 bytes (md5 `badc1ca2291dfc95328ec6cca550c5c9`) = v3's `.chatd` with 5 dwords changed: `0x008` version 3 -> **4**, `0x1100` K_GMENU 0 -> **1**, `0x1104` K_GNODE 0 -> **1**, `0x1114` K_DEADCHAT 1 -> **0**, `0x11AC` K_STOCKVIS 0 -> **1** | constants and state |

- Against `4a17634f`: 39 bytes differ inside its length (32 header bytes, 3 at the draw site, 4 at the slot), plus the 12,288 appended bytes. CheckSum left as found (`0x00768CB7`); no relocation added; the only relocation entry touching a changed byte is the slot's own.
- New code (only with `--stock-vis 1`): Overlay's first instructions after its call counter `mov eax,[R_STAMP]` / `mov [R_VIS],eax` / `mov dword [R_STAMP],0`; after the zone gate `cmp dword [K_STOCKVIS],0` / `je draw` / `cmp dword [R_VIS],0` / `je gate12` (`mov dword [R_GATE],12`); per-gate counters 13 (`0x11C0..0x11F3`); Suppress `mov dword [R_STAMP],1` after its counter. New `.chatd` fields `K_STOCKVIS 0x11AC`, `R_STAMP 0x11B0`, `R_VIS 0x11B4` (zero in a default build). Labels: overlay `0x110E2000`, suppress `0x110E22BF`, clock `0x110E2309`, capture `0x110E23FE`, addEntry `0x110E25C0`, expire `0x110E272A`, drawList `0x110E2868`, textAt `0x110E2BB8`, end `0x110E2BFE`.

### Requirements in v4

| # | v4 | Evidence |
| --- | --- | --- |
| 1-5, 8 | kept: the list code and constants are v3's (wrap 726 font px, 8 messages, 12 rows, 10 s + 1 s, no frame, stock widget suppressed) | harness L (A..E, M 3,000 frames against the model), R4 at three screen sizes, S4 |
| 6, visibility | removed: drawn only where widget 18 runs (modes 1, 11, 7; with QolHud also 3, 9); not in 0, 4, 5, 13, 2, 8 (nor 3, 9 without QolHud); not under a covering menu, with HUD_TOGGLE, without the HUD scene node | harness R4, G4, S4, Q4, V |
| 6, robustness | kept: capture, owners, clock and expiry every frame; entries kept while hidden and drawn again with the life left | harness V4, O, T, K |
| 7 | removed: site 9 holds the base's 26 bytes | static gate (dead site), harness X4 |

### Gates (`build\gates\v4\`, runner `run-gates-v4.ps1 -Work scratch\v4\work`, 2026-10-08 19:44 PC)

| Gate | Result |
| --- | --- |
| `build.txt` | PASS: three v4 builds, one md5 (exe `2724a697`, its patch.ps1 `5b46326a`, not delivered); default builds `0fd28e5f` / `3fba79cf` and patch.ps1 `91747510` / `35a5eb1b` equal `files-m4\` / `files\`; `files-v4\` = the build |
| `gate.txt` (static) | ALL PASS, 79 checks: v3's 76 on `4a17634f` (header, every byte, the sites, the dead site "holds main's bytes (built with --dead-chat 0)", relocations, the 23 compared ranges, `.chatd`, the rebuild, `.chat` disassembled with v3's rules: 755 instructions, absolute data only in `.chatd` and the two HUD globals, calls only through the FN table and the menu's vt+0x38, no `int`/`syscall`/`in`/`out`/`rdtsc`/`cpuid`; QolHud, Enhanced, DedServer, door carry kept byte for byte and 1,458,424 B away) plus 3 v4 checks (the switches; the stamp in Suppress and Overlay's entry; the stamp gate as the last test before the only call of drawList, reached by no other branch) |
| `gate-defaults.txt` | PASS: the static gates of both default builds equal C-1's transcripts line for line (76 and 74 checks) |
| `harness.txt` | ALL PASS, 187 checks: R4 (modes 1, 11, 0, 4, 5, 13, 3, 9, 2, 8, 7: the real HUD loop, then the real scene tail), G4, V (the one-shot stamp: loop/draw/draw, loop/loop/draw, the draw-first order, mode 0 for 4 s with a message arriving hidden, no PlayerController), L, K, O, T, X4 (the real fan-out with the base's bytes: no pawn, Health 0, Health -25 and a dead TEAMSAY dropped, a living SAY to 3, a living TEAMSAY to 2, delivered through the real SimpleStringToClient and add, drawn in mode 1, kept but hidden in mode 5), S4, Q4 (QolHud v3 loaded: drawn in modes 3, 9, 1, 11, hidden in 0, 4, 5) |
| `harness-defaults.txt` | PASS: the harness on `0fd28e5f` and `3fba79cf` gives v3's transcripts (157 checks each), and C-1's compiled harness the same lines |
| `coexist.txt` | ALL PASS, 43 checks (next section) |
| `probe.txt` | PASS: `build\probe-v4\chat-state.ps1` (a copy of `test\chat-state.ps1` that also reads data version 4; the v3 probe refuses it) read the harness's live v4 `.chatd`: header v4 with stock visibility 1, `vis 1` with "drawn", "a menu covers the HUD", mode 5 `vis 0` with "stock chat not shown" |

### Coexistence

| With | Result |
| --- | --- |
| CE 2026.10.07-1's plugins, from their start logs (`scratch\v4\ce-2026.10.07-1\`) | v4 holds the base's bytes over every "ok 0x... +N" range and hook site; nearest v4 change: Modes 2,589 B, ObjHack 199 B, VentChain 117,684 B, ProxVoice, RollFix, SpawnProt above 1.6 MB; MatchRec is disabled (no reads, no ranges in its log); Enhanced's 70 byte patterns cover no changed byte |
| ObjHack.asi | compares 42 B at `0x10A506D1` and 16-B heads at `0x109FCE80`, `0x109FCF60`, `0x109FD2B0`, `0x109992F0` (read from its code, `0x100045F0..0x10004682`), hooks 5 B at `0x10A506E7` (`call 0x10A57BB0`, after the menus and the console in the scene render): 199 B after site 7's last changed byte; its countdown box draws after the list, as with v3 |
| Modes.asi, hook at `0x109B8C20` | its handler `0x1000E9C0` either replays the 8 stock bytes `8B 44 24 04 83 78 04 00` (held by v4) and continues at `0x109B8C28`, or returns (`ret 0xC`) before the add: every MessageStack record the capture reads is written by the stock add `0x109B81D0` (unchanged), so v4 lists what the stock chat would list |
| the channel's plugins (QolHud v3, SniperHeadshotSound, SpyGrab, QOL4Necks, RootBerzerk `0x10BC7A29` 10 B) | every compared site held, +-256 B equal to `4a17634f` and `0f1b2d1c`, the nearest v4 change over 70 KB away |
| image addresses inside the plugins | none of the 13 plugins carries an address inside `.chat` / `.chatd` (`0x110E2000..0x110E4FFF`); the nearest to a changed byte is 199 B (ObjHack) |
| other exe stacks | excluded, as v3 (they replace the same exe) |

### Drone and scope (brief point 4)

Widget 18's mask `0x802` does not hold modes 3 (drone) and 9 (scope): the stock chat is hidden there and so is v4's list. With `QolHud.asi` v3 (defaults Drone=1, Sniper=1) its stub at `0x10B73C90` answers 1 for widget 18 in modes 3 and 9, the HUD loop calls Suppress, and v4 draws the list in the drone and scope views on top of QolHud's split (harness Q4 modes 3 and 9, S4 "QolHud in"). v4 carries no mode list of its own.

### Install, known limits, open

- The channel's `M3CHAT` add-on (`"over": "SMOKE"`): its payload becomes `files-v4\System\SCDA_Online.exe` (`2724a697`, replaces `4a17634f`). By hand: drag the contents of `files-v4\` onto a Community Edition 2026.10.07-1 install root and choose replace. No patch script is delivered for v4.
- In-game test to do: the list as in run 5 in modes 1 and 11; hidden when dead, in the kill cam and spectating, under the in-game menu and the quit dialog; never a second (stock) chat; drone and scope only with QolHud; the probe `build\probe-v4\chat-state.ps1` (`vis`, gate "stock chat not shown", `supp` rising one per frame while `vis` is 1).
- A tick that renders the scene twice (the one-shot request path `0x10A15D40`, INFERRED screenshots) draws the list in its first render only (harness V1).
- The draw follows the stock items' state of the last HUD loop: when the draw comes first in a tick, one tick late, as the stock items (harness V3).
- Run 5's first 18.6 s in "mode 1" with `supp` flat (v3): cause not found (INFERRED the team-switch menu); under v4 the list is hidden whenever the loop does not update widget 18, as the stock chat.
- Papers: `build\builder\ChatExe.cs` `383cac46` (v3: `ChatExe.cs.v3` `88f85393`), `build\builder\Program.cs` `b17accc2` (v3 + C-1: `Program.cs.v3` `25a48b28`), `build\builder\PeFile.cs` `ff1c0538` unchanged, `build\harness\Program.cs` `2a633fec` (v3: `Program.cs.v3` `2a12c285`), `build\gates\v4\run-gates-v4.ps1` `89f4ed57`, `build\gates\v4\coexist.py` `4e386d62`, `build\probe-v4\chat-state.ps1` `645ebf3d`, `README.md.prior-v4` `c6bed60e` (this file before the section). Work folder `scratch\v4\work` (tools and builds, 57 MB).

## v4d: look + dead chat (M3epbuggin m8)

v4d draws v4's list where the stock chat would be drawn and removes the game's own two dead-chat gates: the host sends a dead or spectating player's line to every player (delivery), and the chat widget runs, so the list is drawn, while dead, in the kill cam and while spectating (display). Built by V-2 on 2026-10-08 (brief `BRIEF-v4d.md`, notes `V4d-notes.md`; the gates were found by `Deploy\dead-chat-gate\G1-notes.md`, facts 1-25). Orders, in the operator's words: "can you simply remove the gate that stops the messages from being delivered when dead in the original code?" (2026-10-07); "relaunch a subagent to look into finding the gate that blocks dead players from sending and recieving messages"; "implement the dead chat fix, deploy both and launch map for test" (2026-10-08).

| Item | Value |
| --- | --- |
| base | Community Edition 2026.10.07-1's SMOKE exe `4a17634fbebc1cb2c6b550cc35337d9f`, 7,712,768 B (`scratch\c1\base-4a17634f.exe`) |
| build | `ChatExeBuild build <4a17634f> <out> --dead-chat 1 --stock-vis 1 --dead-show 1` (new switch `--dead-show 0|1`, default 0, refused without `--stock-vis 1`) |
| result | `files-v4d\System\SCDA_Online.exe`, 7,725,056 B, md5 **`2f0cb988f58fe3989cef45f27996b414`**; replaces `4a17634f` |
| v4 and default builds | unchanged: v4 `2724a697` (also with an explicit `--dead-show 0`), defaults `0fd28e5f` from `4a17634f` and `3fba79cf` from `0f1b2d1c` (patch.ps1 `5b46326a`, `91747510`, `35a5eb1b`) |
| where it acts | delivery: on the HOST (listen host or dedicated server) only; display: on each player who runs it. Neither edit changes a replicated function, property or package (G1 fact 25: mixed installs play together, INFERRED) |
| not done | no game was started and nothing was installed; v4d has not run in game |

### Changes against Community Edition 2026.10.07-1 (rows that differ from v4)

| # | File | Site | Stock | New | Purpose |
| --- | --- | --- | --- | --- | --- |
| 1-8, 10 | `System\SCDA_Online.exe` | as v4 | as v4 | as v4 (the `.chat` code is v4's byte for byte, md5 `1c639b42`) | the list, the stamp route |
| 9 | same | VA `0x109B8B36` (file `0x0B8B36`), host `MessageManager.SimpleStringToTeam` `0x109B8680`, in-game branch | `8B 80` (`mov eax,[eax+0x408]` / `cmp eax,ebx` / `je 0x109B8BEA` / `cmp [eax+0x1580],ebx` / `jle 0x109B8BEA`: no pawn or Health <= 0 -> the line is dropped) | **`EB 18`** (`jmp short 0x109B8B50`, the receivers' loop; the other 24 bytes kept, unreached) = v3's row 9 | delivery gate removed (host) |
| 11 | same | file `0x75C000..0x75DFFF`, `.chatd` | - | 0x2000 bytes (md5 `ce9edd8b934f4a5ca23cd0bba6d2c87c`) = v4's `.chatd` with one dword changed: `0x1114` K_DEADCHAT 0 -> **1**; data version stays 4 | constants and state |
| 12 (new) | same | VA `0x10B816A8` (file `0x2816A8`): the imm32's low byte of `or dword [esi+0x34],0x802` at `0x10B816A5` in widget 18's ctor `0x10B81650` | `02` (`81 4E 34 02 08 00 00`, mask `0x802` = modes 1, 11) | **`33`** (`81 4E 34 33 08 00 00`, mask `0x833` = modes 0, 1, 4, 5, 11) | display gate removed: the HUD loop updates the chat widget (Suppress, the stamp) while dead (0), in the kill cam (4) and spectating (5) |

- Byte diff v4 -> v4d: exactly 4 bytes, same length: file `0x0B8B36` `8B` -> `EB`, `0x0B8B37` `80` -> `18`, `0x2816A8` `02` -> `33`, `0x75D114` (`.chatd` +0x1114) `00` -> `01` (coexist F).
- Against `4a17634f`: 42 bytes differ inside its length (v4's 39 + site 9's 2 + the mask byte), plus the 12,288 appended bytes. No base relocation covers either new site; CheckSum left as found.
- The builder checks the base's `81 4E 34 02 08 00 00` at `0x10B816A5` before it writes the byte. `--dead-show` adds no code and no `.chatd` field: the static gate and the harness read the mask from the exe itself.

### Gates (`build\gates\v4d\`, runner `run-gates-v4d.ps1 -Work scratch\v4d\work`, 2026-10-08 20:13 PC)

| Gate | Result |
| --- | --- |
| `build.txt` | PASS: three v4d builds, one md5 (exe `2f0cb988`, its patch.ps1 `2fdd5fe7`, not delivered); v4 `2724a697` / `5b46326a` with and without `--dead-show 0` = `files-v4\`; defaults `0fd28e5f` / `3fba79cf` = `files-m4\` / `files\`; `--dead-show 1` without `--stock-vis 1` refused; `files-v4d\` = the build |
| `gate.txt` (static) | ALL PASS, 83 checks: v4's 79 (site 9 now "patched: EB 18 = jmp short 0x109B8B50, the other 24 bytes main's"; the ctor range compared except the mask byte) plus 4 v4d checks: the mask instruction `or dword [esi+0x34],0x802` -> `0x833`, one byte, the ctor's other 62 instructions main's; the ctor's only access to `[esi+0x34]` is that `or` (after the base ctor `0x10B739A0` and the vtable store); the ctor has one caller (`0x10B7262B`, HUD builder) and no pointer, vtable `0x10F93090` stored only by it; no branch into the instruction, the mode test `0x10B73C90` reads `[+0x34]` live |
| `gate-v4.txt`, `gate-defaults.txt` | PASS: v4's static gate with this builder = `build\gates\v4\gate.txt` (79 checks, 259 lines); the default builds' = C-1's (76 and 74) |
| `harness.txt` | ALL PASS, 204 checks. R4 modes 1, 11, 0, 4, 5, 13, 3, 9, 2, 8, 7, 6, 12 (real HUD loop, real tail): drawn in 0, 1, 4, 5, 11 and 7, gate 12 in 13, 3, 9, 2, 8, 6, 12; G4 dead chat 1, modes 0, 4, 5 drawn, mode 6 hidden, mode 5 under a covering menu: gate 7, menu / node / toggle / zone gates and the list kept while hidden as v4; V with mode 6 as the hidden mode; L, K, O, T (T9 mode 0 and T10 mode 4 now drawn); X4d the REAL fan-out: the base's bytes (control) drop a dead sender (no pawn, Health 0), v4d's pass it (no pawn, Health 0, Health -25: 3 receivers; dead TEAMSAY: the team only), through the real SimpleStringToClient and add into all 3 MessageStacks, then the dead sender's own list draws it in modes 0, 4, 5 and keeps it hidden in 6; S4 the loop stamps in 0, 1, 4, 5, 11, 7; Q4 QolHud v3: drawn in 3, 9, 1, 11, 0, 4, 5 |
| `harness-v4.txt`, `harness-defaults.txt` | PASS: v4 gives `build\gates\v4\harness.txt` (187 checks, 207 lines); the defaults give v3's transcripts (157 each) |
| `coexist.txt` | ALL PASS, 60 checks (next section) |
| `probe.txt` | PASS: `build\probe-v4\chat-state.ps1` on the harness's live `.chatd`: v4d header "dead chat (host) 1", "widget 18 mask 0x833 (modes 0 1 4 5 11) = v4d dead show", "dead-sender site 0x109B8B36 EB18 (stepped over)", mode 1 and mode 5 "vis 1" with "drawn", the menu gate; v4 still reads as before (mask `0x802`, site `8B80`, mode 5 "vis 0" with "stock chat not shown") |

### Coexistence

| With | Result |
| --- | --- |
| CE 2026.10.07-1's plugins (start logs) | v4d holds the base's bytes over every logged "ok" range and hook site; nearest v4d change: ObjHack 199 B (as v4), Modes 233 B (site 9 to its `0x109B8C20` hook), VentChain 12,465 B; the others over 300 KB |
| Modes.asi | its handler still replays the base's 8 bytes at `0x109B8C20` (233 B after site 9); the receiver `0x109B8C20..0x109B8C4B`, the add and send-to-client are the base's; the fan-out `0x109B8680..0x109B8C19` differs only at site 9's 2 bytes. Its `.rdata` carries `00 00 8B 80 08 04 00 00` (8 of site 9's area's bytes) only inside a 40-B compare blob that matches the base at `0x10B7E11F` (its end-panel site), not at site 9 |
| every plugin of CE 2026.10.07-1 and the channel (13) | no image-range dword inside `.chat` / `.chatd` or within 16 B of a change; around the two new sites no plugin carries a run of the base's bytes of 8 B or more except Modes' blob above; nearest compared range to the mask byte: Modes `0x10B7E280`, 13,333 B; to site 9: Modes `0x109B8C20`, 233 B |
| QolHud v3 | its stub reads the live mask (bit 1 for normal-play widgets): with `0x833` it still answers in 3 and 9 (harness Q4); its three compared blocks equal the base |

### Point 3 of the brief: what else could hide the list (report only)

| Mode | v4d | Why | Status |
| --- | --- | --- | --- |
| 0 dead, 4 kill cam, 5 spectating | drawn | the stamp follows the live mask (the loop reads `[widget+0x34]` at `0x10B73C9D`); gate 12 passes. The forced-on node gate `[HUD+0x428]` and the zone flag `HUD+0x410` bit 0x10 were non-zero in these modes in game (v2, which always tested both, passed every gate in modes 0 and 4 in run 4 and 5 in run 3; v3 drew in 0 and 4 in run 5). The menu gate hides it only while a menu covers the HUD (run 4's quit dialog in mode 5), the toggle gate only with HUD_TOGGLE: both as the stock HUD render | harness VERIFIED; node / zone in these modes MEASURED (runs 3-5); in game with v4d not seen |
| 6 end of game, 12 quit dialog | hidden (gate 12) | mask `0x833` has neither bit 6 nor bit 12: the loop takes widget 18's hide path, no stamp, as the stock chat; in 12 a covering dialog also trips the menu gate (7) | harness VERIFIED (R4 6 and 12, G4 6, X4d 6); the mode meanings are the brief's / G1's |
| 7 | drawn | the loop updates every widget in mode 7 (as v4) | harness VERIFIED |
| 3 drone, 9 scope | hidden; drawn with QolHud v3 | as v4 | harness VERIFIED |

### Install, known limits, open

- The channel's `M3CHAT` add-on (`"over": "SMOKE"`): its payload becomes `files-v4d\System\SCDA_Online.exe` (`2f0cb988`, replaces `4a17634f`). By hand: drag the contents of `files-v4d\` onto a Community Edition 2026.10.07-1 install root and choose replace. Dead chat needs it on the HOST; the list while dead needs it on that player.
- In-game test to do: a dead player's typed line on the host's list (and, with a second player, on another machine); the list in modes 0, 4, 5 (probe `vis 1`, gate "drawn", `supp` rising one per frame); hidden at the end of the game and under the in-game menu / quit dialog; probe header shows mask `0x833` and site `EB18`.
- The kill cam: run 5 (v3, which drew there too) saw the list's upper rows over the kill cam's two key hints (shot `r5-051s`); v4d draws there again.
- v4's limits stand (a two-render tick draws in its first render only; one tick late when the draw comes first).
- Papers: `build\builder\ChatExe.cs` `99e24306`, `PeFile.cs` `bd8470c6`, `Program.cs` `0786fe8c`, `build\harness\Program.cs` `60377b6b`, `build\probe-v4\chat-state.ps1` `46391cfa` (v4's each as `*.v4`: `383cac46`, `ff1c0538`, `b17accc2`, `2a633fec`, `645ebf3d`); `build\gates\v4d\run-gates-v4d.ps1` `344cafe1`, `coexist-v4d.py` `720429f3`; `README.md.prior-v4d` `5ecf8bb3` (this file before the section). Work folder `scratch\v4d\work` (56 MB).

## Build and papers

| File | md5 (first 8) | What |
| --- | --- | --- |
| `build\builder\ChatExe.cs` | `99e24306` | v3 + v4's `--stock-vis` (V-1b) + v4d's `--dead-show` (V-2; each emits nothing new without it): configuration, data layout, code (Iced assembler); v4 `ChatExe.cs.v4` (`383cac46`), v3 `ChatExe.cs.v3` (`88f85393`), v2 `ChatExe.cs.v2`, v1 `.v1` |
| `build\builder\PeFile.cs` | `bd8470c6` | PE layout, the patch (3 sites, v4d a fourth: the mask byte), relocation reader; v4 `.v4` (`ff1c0538`), v2 `.v2` |
| `build\builder\Program.cs` | `0786fe8c` | `build`, `gate` (incl. the dead-site gate; v4 adds the switch and stamp-route checks, v4d the mask-site checks), `dis`; generates `patch.ps1` (with v2's and v1's change lists); since C-1 it also accepts main 2026.10.02-4's `4a17634f` (section above); v4 `Program.cs.v4` (`b17accc2`), v3 + C-1 `Program.cs.v3` (`25a48b28`), v3 as built `Program.cs.pre-c1` (`c8d40eb9`), v2 `.v2` |
| `build\builder\ChatExeBuild.csproj` | `7e9f2714` | net9.0, Iced 1.21.0 (unchanged) |
| `build\harness\Program.cs`, `ChatHarness.csproj` | `60377b6b`, `91d5b127` | x86 harness v3, v4 and v4d (a v4 exe runs the v4 set with the exe's own widget mask, a v3 exe exactly v3's; `--hold N` keeps a live `.chatd` for the probe test); v4 `Program.cs.v4` (`2a633fec`), v3 `Program.cs.v3` (`2a12c285`), v2 `Program.cs.v2` |
| `build\gates\run-gates.ps1` | `f4881c7f` | all gates, offline builds; v2 `.v2`, v1 `.v1` |
| `test\chat-state.ps1` | `fd950dd4` | read-only probe v3; v2 `chat-state.ps1.v2`, v1 `.v1` |
| `build\gates\v4\run-gates-v4.ps1`, `coexist.py`; `build\probe-v4\chat-state.ps1` | `89f4ed57`, `4e386d62`; `46391cfa` | v4's gates and transcripts; the probe for v3, v4 and v4d (section "v4 look only on Community Edition 2026.10.07-1"; v4d adds the mask and dead-site readout to its header, v4's probe `chat-state.ps1.v4` `645ebf3d`) |
| `build\gates\v4d\run-gates-v4d.ps1`, `coexist-v4d.py` | `344cafe1`, `720429f3` | v4d's gates and transcripts (section "v4d: look + dead chat (M3epbuggin m8)") |
| `build\SCDA_Online.v2-b28c9113.exe`, `build\SCDA_Online.v1-c4f50a7f.exe` | `b28c9113`, `c4f50a7f` | the exes of v2 and v1, kept (rule 4) |
| `README.md.v2`, `DEPLOY-NOTICE.txt.v2`, `patch.ps1.v2`, `build\gates\v2\` | - | v2's papers and gate transcripts |

## History

| Agent | Route | Result |
| --- | --- | --- |
| CL-1 | plugin, stock baseline | cut off by a cleared cache; source only |
| CL-2 | plugin `ChatList.asi` | removed by Defender 2026-09-29 19:25:37 (`Trojan:Win32/SmokeLoader!pz`); given up, no exclusion, no variant |
| CL-3 | data study | `research\DATA-ROUTE.md`; the operator chose the exe route |
| CL-4 | exe v1 `c4f50a7f`: own list, drawn into the stock widget's text bitmap and 3D boxes | in game (runs 1 and 2): the list logic worked, **nothing on screen** |
| CL-5 | exe v2 `b28c9113`: v1's list logic, own canvas overlay after the HUD, stock widget suppressed | run 3: WORKS alive; run 4: dead chat never arrived, the list emptied at a menu |
| CL-6 | v3 | cut off by the session limit at its first step, wrote nothing |
| CL-7 | exe v3 `3fba79cf`: the host's dead-sender test stepped over; owners, clock and capture that survive a menu, a respawn, a team switch and a new level; the menu gate off; probe instruments | built, gates pass (0 FAIL), not run in game |
| C-1 | v3 rebuilt on main 2026.10.02-4's `4a17634f` (`0fd28e5f`) | built, gates pass |
| V-1 / V-1b | exe v4 `2724a697` on CE 2026.10.07-1: v3's look, drawn only where the stock chat is (stamp of the HUD loop), no dead chat | V-1 paused at its first step; V-1b built it, gates pass (0 FAIL), not run in game |
| V-2 | exe v4d `2f0cb988` on CE 2026.10.07-1: v4 + the host's dead-sender test stepped over + widget 18's mask `0x833` (the list while dead, in the kill cam, spectating) | built, gates pass (0 FAIL), not run in game |

## Test log

| Run | Date | Build | Result |
| --- | --- | --- | --- |
| 1 (hand) | 2026-09-29 21:27 | v1 `c4f50a7f` | logic works, nothing drawn: the operator saw no message during the whole match; `test\results\run1-hand\` (probe bug: box fields empty) |
| 2 (diag) | 2026-09-29 21:32 | v1 `c4f50a7f` | logic works, nothing drawn: spawn protection and typed chat captured, newest in box 0, older pushed up, fades 255 -> 0 after 10 s, frame opacity 0 written; shots `d05`..`d11` show the whole HUD but no chat; `test\results\run2-diag\` |
| 3 (hand) | 2026-09-29 22:48 | v2 `b28c9113` | WORKS, operator's verdict: "it worked". Installed alone, spy, probe 90 s + 14 shots, game handed to the operator. Overlay drawn and visible: probe gate "drawn" in modes 11, 1, 0 (frames and texts grow), 11 messages captured, 0 dropped; shot `v03` (mode 11): 4 typed messages as a list bottom left, newest at the bottom, no frame; shot `v09` (mode 1): spawn protection text bottom left in the stock colour. Not seen: a message while dead (mode 5 seen once, list empty), chatting while dead, drone and scope views. Reverted 22:51, working copy = main. `test\results\run3-v2\` |
| 4 (hand, dead state) | 2026-09-29 23:21 to 23:23 | v2 `b28c9113` | FAILS the next goal, operator's verdict: "it still did not work". Installed alone, launched with `trace_blackwing_launch_merc.jsonl` (ended as spy), probe from 23:22:50 (`chat-state.txt`), shots every 4 s from 23:23:09 (`shots\r4-*`, 7 kept; the ones after the game closed deleted). Timeline (probe seconds): 5.2 spawn protection message captured in mode 1 but gate "a menu covers the HUD"; 6.2-8.3 mode 13, drawn; 8.8 mode 1, the list EMPTIED (1 -> 0 msgs at age 3.1, `exp` 0) as a menu opened; 18.6-19.7 a load (calls 0), then mode 11 (briefing) and mode 1: the operator came back as MERC (shot `r4-017s`); 35.3 mode 0 = dead after an explosion (shots `r4-017s`, `r4-021s`: the `Say` bar open, "ewqeqeasdd" typed while dead); 40.3 mode 4 (kill cam), 42.3 mode 5 with the menu gate (shot `r4-025s`: the quit dialog); game closed 23:23:38. `capt` stayed 1 to the end: no message after the first reached the list, so the dead player's typed message was never received (whether Enter was pressed is not seen). The overlay itself was not gated in modes 0 and 4 ("nothing to draw"). Reverted 23:24, working copy = main (0 content differences). `test\results\run4-dead\` |
| 5 (hand, dead state) | 2026-09-30 01:04 to 01:08 | v3 `3fba79cf` | WORKS, operator's verdict: "ok, chat succeeded". Installed alone, launched 01:04:59 with `trace_blackwing_launch.jsonl`, in match after 75 s as host and spy (`PawnSpy_Two`); probe from 01:07:01 (`chat-state.txt` `b9193a99`, 72 s), shots every 5 s (`shots\r5-*`, 14 kept; the 6 after the game closed deleted). Before the probe started: `capt` 7, `exp` 7, 1,655 frames drawn, owner changes hud / pc / mm 5 each on the way into the match. Timeline (probe seconds): 0-20 mode 1, list empty; 20.2 mode 11 with `chg` 6 / 6 / 6 and `clkskip` 12 -> 13: the team switch and its load; 32.0 mode 1 as merc; 37.6 mode 0 = dead ("You killed yourself with your own grenade."); **38.7 mode 0: the dead player's typed line "M3epmeep : ewtrete" in the stack (#0), taken, listed, gate "drawn"** (shot `r5-041s`: the body, the line bottom left, the Say bar open); 42.5 mode 4 (kill cam): Say and TeamSay lines #2 to #24 arrive, each taken at once (`last taken` = the newest on every line), 8 listed from 49.4, older ones leave by the limit and by their time (shot `r5-051s`: 8 lines); 62.6 mode 1 (respawn): the 8 lines stay, 7 more lines taken (shot `r5-066s`); game closed by the operator 01:08:13. Totals: `capt` 39, `drop` 21, `exp` 10, `dup` 0, `seqrst` 0, 4,346 frames drawn, no frame under any gate but "nothing to draw". SEEN: in the kill cam the list's upper rows lie over the kill cam's two key hints (shot `r5-051s`). NOT SEEN: mode 5 (spectating), the in-game menu and the quit dialog with live lines, drone and scope, a second player (a dead player's line on another machine). Reverted 01:08:40, working copy = main (0 content differences, no `Running.ini`). `test\results\run5-v3\` |
