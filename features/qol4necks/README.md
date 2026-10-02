# qol4necks (QOL4Necks.asi)

The spy can neck a merc during the merc's jump and right after his landing, the height rule counts a jumping merc from his take-off floor, and at an interact press a possible neck always wins over light switches, panels and the gadget stock.

Built 2026-10-02 by B-1 / B-1b from the designs `research\J-1-clean-necks.md` (Q7 table C: J1, J2, J3) and `research\J-2-neck-priority.md` (D, D2), with the operator's eight decisions in `BRIEF-B1.md`. Nothing is installed and no game was started. Install by dragging `files\` onto an install (rule 12), or with `patch.ps1`.

# Change log (rule 8)

| # | Where | Change | Stock bytes | New content |
| --- | --- | --- | --- | --- |
| 1 | `System\QOL4Necks.asi` (new) | the plugin: no CRT, kernel32 only, preferred base `0x6ED00000`, relocatable (position-independent code, one empty reloc block) | - | md5 `1e432c2b204b1252cb6fbfc71d79ea89`, 12800 bytes |
| 2 | `System\QOL4Necks.ini` (new) | `[QOL4NECKS]` `Enabled=1` `Jump=1` `Landing=1` `NeckPriority=1` `NeckPriorityExclude=` `NeckPriorityStock=1` `Log=1` | - | md5 `64c5dee3c1c020b2d49f51e538a722ac`, 308 bytes |
| 3 | `SCDA_Online.exe` **in memory at load**, J1 (jump accept) | VA `0x10BCAE92`, file `0x2CAE92`, in `CheckGrabTarget`: the `CanBeGrabbed` event call | `8B CF FF 52 14` | `E9 EA 67 13 5E` |
| 4 | same, J2 (jump height) | VA `0x10BCB009`, file `0x2CB009`, in `CheckGrabTarget`: the height test | `D9 44 24 10 D9 E1` | `E9 8E 67 13 5E 90` |
| 5 | same, J3 (landing grace, host) | VA `0x10BC9F18`, file `0x2C9F18`, in `AskPermissionToGrab`: the 0.15 s grace test | `8B 93 00 03 00 00` | `E9 92 7A 13 5E 90` |
| 6 | same, D (neck priority) | VA `0x10BD8AD0`, file `0x2D8AD0`: `PlayerController.CanDoAction` | `83 B9 1C 09 00 00 00` | `E9 CE 8F 12 5E 90 90` |
| 7 | same, D2 (gadget stock) | VA `0x10DAA307`, file `0x4AA307`, in `sGagdetStock_Wait.Tick`: the stock's own key read | `38 98 DD 08 00 00` | `E9 00 78 F5 5D 90` |

The exe file is never written. The `E9` rel32 values above are those at the preferred base `0x6ED00000` with the exe at `0x10900000`; at load the plugin computes them from the actual bases (stubs at RVA `0x1681`, `0x179C`, `0x19AF`, `0x1AA3`, `0x1B0C`). Each site is byte-checked first (its stolen bytes plus context bytes; J2 also the jump constants 3000.0 at `0x10FA4AA0` and 1500.0 at `0x10FA495C`) and refused alone on a mismatch, with a `REFUSED` line in the log. No site shares a byte with SpyGrab (`0x10BCAE97`+11, `0x10BC9F2D`+6, `0x10C35FEB`+5, operand `0x10BCB011`+4), RootBerzerk, no-mic-guard, BombHud or HackHud.

Exes checked (all five sites, context bytes and constants identical): `0f1b2d1ce8167d267ee15d5a4ed4c3e6` (Community Edition main, the test version's base), `4dccc646989b2214f8c15b095114314e` (Experimental; also the working copy's exe today), `3fba79cf53149f7aaa7c4afccaa867f7` (chat-list's exe, run by the test version `<game folder or workspace path>`).

# What each site does

| Site | Runs on | Does |
| --- | --- | --- |
| J1 | the spy's machine (prompt) and the host (grant) | a merc with `PawnType 0`, `PawnState 2` (in the air), `CurrentAction 18` (jump), `Physics 2`, not grabbed, answers `CanBeGrabbed` like a walking merc (true). Running jumps included (decision 2) |
| J2 | same | for that jumping merc only: admitted when `abs(dZ) <= L` (stock) or `abs(dZ - h) <= L`, `h = sqrt(3000 * JumpHeight) * t - 750 * t^2`, `t = Level.TimeSeconds - fAirTime`; `L` = the float the operand at `0x10BCB011` points to (30 stock, 80 with SpyGrab; 30 if it points outside the exe or is not in 0..1000). Every other target: the stock / SpyGrab test unchanged |
| J3 | the host | no 0.15 s landing grace for a merc (`PawnType 0`, `PawnState` 1 or 2) whose `CurrentAction` is 18, 19 or 141, after every landing (decision 3). 297, 180, 124 and everything else keep the grace |
| D | the spy's own machine (client or listen host) | while `Pawn.PossiblePawnToGrab` is set, and for the rest of a press during which it was, `CanDoAction` refuses every object action (switches, panels, terminals), so the IM never offers the object and a press spent on a refused neck does nothing (decisions 5, 7, 8). Only for a local spy: no remote camera, `RemoteRole != 3`, `PC+0x414 == 1`, a pawn. Actions in `NeckPriorityExclude` stay stock |
| D2 | the spy's own machine | the gadget stock's key read sees "not pressed" under the same rule (decision 6) |

The press latch (D, D2): key held -> the latch is set while a neck is possible; key up -> the key-up time is noted, and the latch clears once `Level.TimeSeconds` has moved past it (the one-tick grace for the IM's release tick). B-1b addition: the latch sees the key only while `CanDoAction` is asked (the spy touches an object or a gadget stock), so calls more than 0.5 s apart, or the clock going back (a new map), start a fresh press. Without it, a press released out of reach of every object would leave the latch up and swallow the next press on a switch (the harness's mutation run shows exactly that).

# Settings (`System\QOL4Necks.ini`, section `[QOL4NECKS]`; a missing key means its default)

| Key | Default | Does |
| --- | --- | --- |
| `Enabled` | 1 | 0 = nothing is installed (log: `disabled ...`) |
| `Jump` | 1 | J1 + J2. 0 = both sites left stock (not installed) |
| `Landing` | 1 | J3. 0 = site left stock |
| `NeckPriority` | 1 | D. 0 = site left stock |
| `NeckPriorityExclude` | empty | action numbers 0-255 that a possible neck does not hold back, separated by commas or spaces; `;` ends the list; e.g. `30,32` (hacking panel actions). Larger numbers are ignored |
| `NeckPriorityStock` | 1 | D2. 0 = site left stock |
| `Log` | 1 | 1 = event lines in `System\QOL4Necks.log` (64 at most per run, 16 per kind). 0 = no event lines |

# Log (`System\QOL4Necks.log`, rewritten at every start)

Always: one config line and one line per site (`installed`, `not installed (Key=0)`, or `REFUSED - ...` with the 8 bytes read at the site). With `Log=1` also event lines `t=<GetTickCount> ms  <text>`: J1 once per (merc, jump), J2 once per jump admitted only through the take-off floor (dZ, h, dZ - h, limit), J3 per skipped grace that was running, D once per press that a neck held back, D2 once per press. After a start the log must read `config: Enabled=1 Jump=1 Landing=1 NeckPriority=1 NeckPriorityExclude=none NeckPriorityStock=1 Log=1` and `installed` five times.

# Deviations from the design

1. `Log=0` drops only the event lines; the config and site lines are always written, so a refusal is always visible (B-1; accepted).
2. A switch at 0 leaves its site uninstalled instead of a runtime switch test (B-1; accepted).
3. The D/D2 latch's stale guard (above; B-1b). Constant 0.5 s; INFERRED safe because the IM and the detection ask `CanDoAction` every tick while the spy touches an object (J-2 Q1).

# Mixed installs

J1/J2 decide on the spy's machine (prompt) and on the host (grant); J3 on the host only; D/D2 on the spy's machine only. Spy and host both with the plugin: everything as above. Spy only: prompt through the jump, but a stock host refuses a jumping merc (`CantGrab`) and keeps the landing grace; neck priority works fully. Host only: no prompt in the air (stock), landing grace skipped. The merc's machine plays no part. Tables in J-1 Q7 C and J-2 D.

# Build and gates (`build\`)

`build\src\QOL4Necks.cs` (Iced generator), `build\builder\` (build + static gate), `build\harness\` (runs the real `.asi` in an x86 process against the exe's own code mapped at its addresses: scenes per site against a model written from the designs; catchers at every exit check registers, esp, xmm0-7, x87 and the stack), `build\gates\run.ps1` (PowerShell; writes `build\gates\build.txt` and `build\gates\harness.txt`).

Last run 2026-10-02 17:42: static gate 138 PASS / 0 FAIL (PE, position independence, writes / calls / branches, stack walk of every stub and routine, per exe: bytes, whole instructions, no reloc / branch / pointer into the stolen bytes, constants, operand, overlaps, simulated install; four builds one md5; no installed plugin in main, the working copy or the test version names an address inside the stolen bytes). Harness 36 of 36 runs (12 modes x 3 exes), 7785 checks, 0 FAIL: modes default, shipped ini, disabled, Log=0, switches off, exclude list, a byte mismatch at J3 and D2 (only those two parked), changed jump constant (only J2 parked), SpyGrab's operand (80), plugin relocated, exe relocated, plain loader on the wrong exe (all refused). Scenes: J1 predicate true / each part false; J2 take-off, apex, rising, landing, ledge 60 and 100 above, spy above, JumpHeight 0 / 2000, t < 0, Level None, NaN, after the flight, operand outside the image, operand to 80; J3 actions 18 / 19 / 141 (skipped) and 297 / 180 / 124 (kept), PawnType / PawnState refusals, grace over; D latch across press, refusal, release, the one-tick grace, a new press, stale press, clock back, remote camera, RemoteRole 3, a merc, no pawn, actions 30 / 5 with the exclude list; D2 both branches and its refusals; event-line text, numbers and caps; counters. A mutation run (J3 141 -> 142, stale guard off) fails 5 checks, as it should.

# In-game checks (not run here)

From J-1: T1-T10 (jump in place with and without SpyGrab, press at the landing, running jump drift, ledge / crate 40-120 above, jump off a ledge, ramps / stairs, walk-off / drop-tech / hook fall, SpyGrab spin / stagger / stairs and RootBerzerk unchanged, bots, interrupted grant). From J-2: checks 1-10 (switch beside a neckable merc, not neckable, forced host refusal, key held through a refusal, hacking panel / HackTerminal, bomb zone, gadget stock, ledge / ladder / pipe / vent / crouch / weapon / camera, a merc player, load log alongside every plugin). Added for the stale guard: neck a merc that stands by a switch, release the key away from every object, walk to a switch, one tap flips it.

# Install / revert (`patch.ps1`)

`.\patch.ps1` (status of the working copy), `.\patch.ps1 -Game "<install>" -Status | -Install | -Revert`. `-Install` checks the exe's bytes (all five sites, context, constants), the files' md5s and leftovers first; it never writes main and refuses while `System\Running.ini` exists or a game runs. `-Revert` removes `QOL4Necks.asi` (ours only), `QOL4Necks.ini` and `QOL4Necks.log`.
