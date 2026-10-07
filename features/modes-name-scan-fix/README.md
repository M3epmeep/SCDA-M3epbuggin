# modes-name-scan-fix - Modes.asi without its background name scan

The patched `Modes.asi` no longer walks the engine's name table from its own thread, so a map load can no longer crash the game at `Modes.asi+0x9F75`.

**State: built and statically gated (8 PASS, 0 FAIL); never loaded or run. Not validated.**

## Cause

`Modes.asi` (Community Edition 2026.10.02-5, "Modes v11") starts an install thread at RVA `0xAC40`. After its hooks it loops every 3 s, for up to 200 passes (about 600 s), looking up `HUD_MSGSPY_IN_GAME_BLACKOUT` and `HUD_MSGMERC_IN_GAME_BLACKOUT` with `FindName` (RVA `0x9E40`). `FindName` copies the name table's data pointer once (`[0x110198D8]` in the exe), checks the array once at the start and then reads every slot unchecked (RVA `0x9F75` `mov esi,[esi+ebx*4]`); the module is built with NO_SEH. When the game thread adds names past the table's capacity (a map load), `FName` grows the array through `GMalloc->Realloc`, which frees the old block (`VirtualFree(MEM_RELEASE)` for blocks over 32 KB) before storing the new pointer, and the plugin's walk reads freed memory. A fault on a plugin's own thread is not caught by the engine, so the process ends.

Measured 2026-10-07 on a joining client loading `BLKG1_VS`: `0xC0000005` at `Modes.asi+0x9F75`, read of `0x03DCDEB8` = data `0x03DC0000` + slot `0x37AE` * 4, on the install thread, 311.7 s after start (`Deploy\two-player-load-crash\resume.md`, run 6; analysis `Deploy\two-player-load-crash\build\N2-notes.md`).

## Files

| File | Change | md5 replaced | md5 new |
| --- | --- | --- | --- |
| `System\Modes.asi` | replaced (107520 bytes, same size) | `e5d6f25e1cdb2af2afda2568342015c2` (CE 2026.10.02-5) | `f04f5a9d7b963d14139150ad431bb1a7` |

The main build `C:\Program Files (x86)\SCDA Community Edition` (CE 2026.09.28-1) carries no `Modes.asi`; this feature applies to an install that has the CE 2026.10.02-5 one.

## Changes

File offset = RVA - `0xC00` (`.text` is RVA `0x1000` at raw `0x400`). VA at the preferred base `0x10000000`. No relocation entry covers a changed byte.

| # | Site | File offset | Stock | New |
| --- | --- | --- | --- | --- |
| 1 | RVA `0xBF30`, first instruction of the name-retry loop | `0xB330` | `33 FF` (`xor edi,edi`) | `EB 10` (`jmp short 0x1000BF42`) |
| 2 | RVA `0xBF42` | `0xB342` | `0F 85 DB 02 00 00` (`jne 0x1000C223`) | `E9 FE 06 00 00 90` (`jmp 0x1000C645`, the install thread's own `xor eax,eax` / `pop` / `add esp,0x27C` / `ret 4`) |

The install thread ends right after its hooks, its two workers and its shared memory are set up. Skipped with the loop: the 200 retries, the diagnostic lookups every 10th pass, the two `HUD_MSG*_IN_GAME_CHAOS` lookups after the loop and the closing log line. The game-thread paths that use the four indices look up any that is still 0 themselves (RVA `0x10700` for the BLACKOUT pair at `[0x10022928]` / `[0x1002292C]`, RVA `0x12128` for the CHAOS pair at `[0x10022938]` / `[0x1002293C]`), on the thread that grows the table, so they cannot race it.

Not covered: worker 1 (RVA `0x1F30`) still calls `FindName("ECC")` from its own thread every 3 s until its class globals resolve (up to 400 passes). Route R2 in `N2-notes.md` (re-read the live pointer per pass) would narrow that one too.

## Build

`.\build.ps1 [-Stock <CE 2026.10.02-5 System\Modes.asi>]` writes `files\System\Modes.asi` and prints the gates (`build\gates.txt`): stock md5, stock bytes at both sites, no relocation over a patched byte, 7 bytes differ (8 written), patched sites disassembled.

## Install

- Drag the contents of `files\` onto the install root and replace `System\Modes.asi`; keep the stock copy to put back.
- A launcher's game-file check reports the replaced `Modes.asi` as modified, and its repair puts the stock one back: start `System\SCDA_Online.exe` directly, or ship it as a channel add-on.
- Check: `System\Modes.log` keeps its install lines and no longer shows the retry-loop lines.
