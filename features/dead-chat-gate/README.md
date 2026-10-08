# dead-chat-gate

Removes the original game's two dead-player chat gates in `SCDA_Online.exe` (3 bytes, no new code), so a dead player's line reaches everyone and a dead, kill-cam or spectating player sees the stock chat.

Measured against the main build `<Community Edition 2026.10.07-1 install>` = Community Edition 2026.10.07-1. Research notes are in the builder's workspace (`G1-notes.md`, facts 1-25).

## Changes

| # | File | Site | Stock content | New content | Who needs it |
| --- | --- | --- | --- | --- | --- |
| 1 | `System\SCDA_Online.exe` (main md5 `4a17634fbebc1cb2c6b550cc35337d9f`) | VA `0x109B8B36`, file offset `0x0B8B36`: the host's fan-out `execSimpleStringToTeam` (n3916) tests `Owner.Pawn [+0x408]` = 0 or `Pawn.Health [+0x1580]` <= 0 and drops the line (`0x109B8B36..0x109B8B4F`) | `8B 80` (`mov eax,[eax+0x408]`, start of `8B 80 08 04 00 00 3B C3 0F 84 A6 00 00 00 39 98 80 15 00 00 0F 8E 9A 00 00 00`) | `EB 18` (`jmp short 0x109B8B50`; the other 24 bytes stay, unreached) | the host (listen host or dedicated server) |
| 2 | same file | VA `0x10B816A8`, file offset `0x2816A8`: the stock chat widget 18's ctor `0x10B81650` sets its mode mask, `or dword [esi+0x34],0x802` at `0x10B816A5` (modes 1, 11); low byte of the imm32 | `02` (`81 4E 34 02 08 00 00`) | `33` (mask `0x833` = modes 0 dead, 1, 4 kill cam, 5 spectating, 11) | each player who wants to see the chat while dead |

File offset = VA - `0x10900000` (`.text`). No relocation covers either site; the PE header and checksum are unchanged; no Community Edition 2026.10.07-1 plugin byte pattern or logged check range covers either site (MEASURED, `G1-notes.md` fact 22).

## File stack

`files\System\SCDA_Online.exe`: 7,712,768 B, md5 `f61d28a45b375a6d3f4e3a49884475c8` = main `4a17634f` with rows 1 and 2 (exactly 3 bytes differ: `0xB8B36` `8B`->`EB`, `0xB8B37` `80`->`18`, `0x2816A8` `02`->`33`; built 2026-10-08 by stock-checked byte writes). Drag the contents of `files\` onto the install root and choose replace. It replaces the whole exe: it carries only this feature, not chat list or any other exe change.

In the M3epbuggin channel the same two edits ride inside `M3CHAT`'s exe (chat list v4d, `Deploy\chat-list\BRIEF-v4d.md`): one launcher add-on owns one file.

## What is known

| Point | State |
| --- | --- |
| Row 1 is the whole dead-sender test on the route and the minimal edit (the skipped code writes only eax and flags) | VERIFIED; worked in game as chat list v3's site 9 (host, 2026-09-30 run 5) |
| Sending while dead: Say bar, `Console.Talk` / `TeamTalk`, exec SAY / TEAMSAY test no pawn, health or mode; TEAMSAY needs `PRI.Team`, kept while dead | VERIFIED; MEASURED in modes 0 and 4, mode 5 INFERRED |
| Receiving while dead: the receivers' loop and `execSimpleStringToClient` test no pawn or health; the mask alone hides the chat | VERIFIED |
| Row 2: the HUD loop `0x10B70EF0` and the text post draw read the mask live (`0x10B73C9D`); widget 18's own update gates pass while dead | VERIFIED; the look on screen in modes 0, 4, 5 INFERRED (not run) |
| Mixed installs play together: neither edit changes anything replicated | INFERRED (no two-player run) |

## Open

1. In game: modes 0, 4, 5 on screen (place, overlap with the kill cam's key hints and the spectating texts); mode 5 typing.
2. A two-player run: a dead client's line through an edited host to a stock client.
3. Community Edition's `Modes.asi` hooks `0x109B8C20` (client receive) on every machine; its filter was not read.
