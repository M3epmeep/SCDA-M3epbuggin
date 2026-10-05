# two-player-load-crash (ResetHudDefer.asi)

Stops the crash of a player who joins a match while loading in, by holding the HUD build back until that player's character exists and then running it once. In the M3epbuggin channel this is the add-on `M3RHUD` (since 2026.10.05-m5).

`ResetHudDefer.asi` md5 `4e3396c444649d6ae8a6c3deb7ba53c2`, 7680 bytes. The exe on disk is never changed: the plugin patches it in memory at load, and does nothing when the character is already there. Static gate 52 PASS, 0 FAIL; not yet seen running in a two-player game.

# The crash (MEASURED 2026-10-05)

| Fact | Value |
| --- | --- |
| symptom | the joining player's game shows the engine's error box while loading in: `The instruction at 0x10B71EDA referenced memory at 0x00000024` (System event 26; no Windows crash dump, the engine catches it) |
| fault | `0x10B71EDA mov eax,[edx+0x24]`, main thread: `edi` = the HUD, `ecx` = `HUD+0x400` (PlayerOwner, a PlayerController), `edx` = `PC+0x408` (Pawn) = NULL |
| path | server: `AGameInfo::execSpawnPlayer` `0x109DF010` spawns the pawn, possesses it, then sends `eventclientResetHud` (`0x109DF740`, call at `0x109DF2B7`), a reliable client RPC. Client: `PlayerController.clientResetHud` (`if (myHUD != None) myHUD.ResetHud()`) -> `AHUD::execResetHud` `0x10B72F40` (native 2227) -> AHUD vtable `+0x438` = the HUD builder `0x10B71340` |
| cause | on the joining client the RPC runs before the new pawn has replicated; the builder reads `PlayerOwner.Pawn.Class` for its spy/merc split (`cmp eax,0x11044EC8`, PawnMerc, at `0x10B71EE6`) with no NULL check, at `0x10B71ECE..0x10B71EDA` and again at `0x10B726DB..0x10B726E7` |
| stock | the builder, `execResetHud`, `execSpawnPlayer` and the AHUD vtable are byte-identical in the stock exe `fc237f82`, Community Edition `0f1b2d1c` and `4a17634f`, the chat-list exe `0fd28e5f` and the Experimental exe `4dccc646`: original game code. No other community plugin touches these sites |
| builder | one function for every HUD (`0x10B71340`..`0x10B7298A`, `thiscall`, no stack argument, plain `ret`); it only appends widgets (AddWidget, slot `+0x448`) and never clears them, so it must run once per reset |

# The fix, as built (rule 8 change log)

Both sites are compared with their stock content first; nothing is written unless all of them are stock (and `GetModuleHandleA(NULL)` is `0x10900000`). Hook 2 is written before hook 1, so a held build always has its replay.

| # | Site (VA / file offset) | Stock | New |
| --- | --- | --- | --- |
| 2 | AHUD vtable slot `+0x440`, `0x10F82000` / `0x682000` (`.rdata`) | `0x10B72EC0`, the widget loop; the scene render calls it every frame at `0x10A5058F`, right after the HUD draw | address of `wrap` |
| 1 | HUD builder head `0x10B71340` / `0x271340` (`.text`) | `6A FF 68 93 1F E2 10` (`push -1` / `push 0x10E21F93`) | `E9 <rel32 to stub1> 90 90` |

Also checked as stock: `64 A1 00 00 00 00` at `0x10B71347` and the builder slot `0x10F81FF8` = `0x10B71340`.

| Code | Behaviour |
| --- | --- |
| `stub1` | `PlayerOwner` not NULL and `PlayerOwner.Pawn` NULL: remember the HUD (pointer, PlayerOwner, `XLevel` `+0x304`, object index `+0x4`, tick), log, `ret` (the build is held). Otherwise the two stolen pushes and on at `0x10B71347`. Registers and stack as found on both exits |
| `wrap` | the held HUD, same PlayerOwner, `XLevel` and index, and a pawn now: clear the entry, run the builder once, log the delay; pawn still NULL: keep waiting; another HUD or a changed identity: clear the entry without reading the old pointer, log. Then on into the stock `0x10B72EC0` with ecx and the argument untouched |

A HUD that is not yet built is the game's own state between its creation and its first reset; the per-frame HUD draw does not depend on the builder, and the widget getter (`+0x454`) is bounds-checked.

Log: `System\ResetHudDefer.log` (the load line, one line per site; one line per defer, replay and drop, capped at 64).

# Gates (MEASURED)

52 PASS, 0 FAIL: PE shape, kernel32-only imports, relocations (the image rebuilt at another base equals this one with its relocations applied), on each of the five exes the stock bytes, the whole instructions under hook 1, no branch or pointer into the stolen bytes, the exits the stubs rely on and the page protections; a path walk of the install code, `stub1` and `wrap` (stack balanced on every exit, every register as found).
