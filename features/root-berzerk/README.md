# root-berzerk (RootBerzerk.asi)

The merc can start the **berserk spin during the wall-run stagger**. When a sprinting merc runs head-on into a wall he
is staggered for ~0.7 s: the controller goes to state `MercWaitForSprintBump`, whose move code is the class default
`Controller.PawnMove` (it zeroes acceleration and reads no input), so the one place the exe reads the berserk button
(`MercWalking.PawnMove`, `0x10BC4392`) is never reached and the stagger swallows the key. This plugin runs the **stock**
berserk start at the tail of that state's `PlayerTick`, so a berserk pressed during the stagger fires at once instead of
being dropped. Nothing else about the spin changes: same button, same 1.5 s cooldown, same reload and crouch tests, the
same `ChangeAction(180)` + `GotoState('MercRotativeAttack')` the game runs from `MercWalking`.

This expands the "merc runs into a wall" feature: the merc can berserk throughout the stagger and is not blocked by the
root motion (R-1's measured finding: no root-motion lock, action test or network check refuses a spin that starts inside
the stagger).

- **One in-memory hook of 7 bytes at VA `0x10BC7A29`** (file `0x2C7A29`), the tail of
  `APlayerController::execMercWaitForSprintBump_PlayerTick` (`0x10BC7950`), just before its own epilogue. The exe on
  disk is never patched; the plugin patches it in memory at load and byte-checks first.
- **Only the merc's own machine needs it.** The hook is in the *player* controller's tick; the host's copy of a remote
  merc runs `ServerTick` (not `PlayerTick`), and the host and other clients accept the spin with stock action and state
  RPC. **Bots are not reached** (`AIController.MercWaitForSprintBump` has no `PlayerTick`), so AI mercs stay stock.
- **Role test (version 2):** the stub goes on only where `RemoteRole` (`+0x2D1`) **!= 3**, the test the stock end of the
  same stagger uses (`MercWaitForSprintBump.CtrlSeqAnimEnd`, `0x10BC78E5`: `cmp byte [edi+0x2D1],3 / je return`).
  Measured in the exe: `+0x2D1` is `RemoteRole`, `+0x2D2` is `Role`; a joined client's own controller has Role 3 /
  RemoteRole 4, the listen host's own controller Role 4 / RemoteRole 2, the host's copy of a remote player Role 4 /
  RemoteRole 3 (and never runs `PlayerTick`). Version 1 had the test inverted (it went on only when `RemoteRole` == 3)
  and therefore never started a spin for any merc; it is replaced.
- No byte of SpyGrab's four sites (`0x10BCAE97`, `0x10BC9F2D`, `0x10C35FEB`, `0x10BCB011`) is touched; the two plugins
  combine (see R-1 Q7). A scan of the 13 plugins of the 2026-10-05 test install finds no exe address and no byte pattern
  inside any range this plugin writes, byte-checks or calls, and none inside the hooked function. The protocol is
  unchanged.
- Gated against **five** exes, byte-identical over every range this plugin reads and over every role site above:
  `0f1b2d1ce8167d267ee15d5a4ed4c3e6` (Community Edition 2026.09.28-1), `4dccc646989b2214f8c15b095114314e`
  (Experimental), `fc237f825cbd74368901dcf8008946d7` (stock), `4a17634fbebc1cb2c6b550cc35337d9f` (Community Edition
  2026.10.02-5) and `0fd28e5f875c37db072735e005174407` (the test version's exe; it adds two sections `.chat` / `.chatd`
  after `.reloc`, `.text` unchanged in layout). The plugin never checks the exe's md5: it compares the bytes of the
  site, the two event helpers and the three stock-berserk constants with the stock bytes and leaves the site alone
  (logged `REFUSED` with the bytes read) if any differ.
- No CRT, no thread; all setup in `DllMain`. Its own `kernel32` import table (the loader binds it); no dependency on the
  exe's IAT. Position-independent (preferred base `0x6EB00000`, relocatable): a relocated load works. Every exe address
  is used as **VA + delta**, delta = the exe's actual base (`GetModuleHandleA(0)`) − `0x10900000`, so a relocated exe is
  read, written and called at the right place (the game loads at a fixed base, so delta is 0 there).

`RootBerzerk.asi` version 2, md5 `fa93639acb4059b5a3b844f93d52b1d2` (8704 bytes).

| Version | md5 | State |
| --- | --- | --- |
| 1 (2026-10-02, B-1) | `fdac01a04b0e18c749dd050f2ebc368b` | replaced: role test inverted (`cmp byte [edi+0x2D1],3 / jne out`), never spins; kept as `scratch\b2\RootBerzerk.v1.asi` |
| 2 (2026-10-05, B-2) | `fa93639acb4059b5a3b844f93d52b1d2` | shipped: `cmp byte [edi+0x2D1],3 / je out`; log lines start `RootBerzerk 2`; nothing else changed |

# Settings

`System\RootBerzerk.ini`, section `[ROOTBERZERK]`. A missing file or key means the default.

| Key | Default | Does |
| --- | --- | --- |
| `Enabled` | 1 | 0 = the plugin installs nothing (log: `disabled ...`) |
| `Bump` | 0 | 0 = only the **wall** stagger (action 124 / `ASprintWall`) can be broken by a berserk. 1 = also the stagger after sprinting **into a player** (action 139 / `ASprintBump`, ~1.167 s) |
| `Log` | 1 | 1 = write `System\RootBerzerk.log` (config line, site line, one line per spin started from a stagger). 0 = no log file |

# Log

`System\RootBerzerk.log`, rewritten at each start when `Log=1` (the config and site lines begin
`RootBerzerk 2 (Deploy\root-berzerk): `; a log beginning `RootBerzerk 1` comes from the replaced version 1):
- a config line: `config: Enabled=1 Bump=0 Log=1`
- one site line: `berserk 0x10BC7A29: installed`, or `REFUSED - the bytes are not the expected ones ...; read <10 bytes>`, or `REFUSED - GetModuleHandleA(0) is not the SCDA exe image ...`, or `REFUSED - VirtualProtect failed`
- one line per spin started from a stagger (up to 64): `t=<ms> ms  berserk started from the wall stagger: action <124|139>, <s> s into the stagger`

# Change log (rule 8)

| # | Where | Change | Stock bytes | New content |
| --- | --- | --- | --- | --- |
| 1 | `System\RootBerzerk.asi` (new) | the plugin, version 2 | - | md5 `fa93639acb4059b5a3b844f93d52b1d2`, 8704 bytes |
| 2 | `System\RootBerzerk.ini` (new) | `[ROOTBERZERK]` `Enabled=1` `Bump=0` `Log=1` | - | md5 `218858ae07ea424c3a37d5c5023ef62d` |
| 3 | `SCDA_Online.exe`, **in memory at load** | the berserk hook: VA `0x10BC7A29` (file `0x2C7A29`), 7 bytes at the tail of `APlayerController::execMercWaitForSprintBump_PlayerTick` `0x10BC7950` (the epilogue `pop edi / pop esi / pop ebp / pop ebx / add esp,0x48`, followed by `ret 0xC` at `0x10BC7A30`); `edi` = this controller | `5F 5E 5D 5B 83 C4 48` | `E9 <rel32 to the stub> 90 90` (at the preferred base `E9 37 97 F3 5D 90 90`, stub at `0x6EB01165`). The stub: with the merc in the wall stagger (`RemoteRole` `+0x2D1` != 3, i.e. not the host's copy of a remote player; berserk button `+0x58B` bit 4; `Pawn` `+0x408` != None and its `Controller` `+0x1474` == this; `bControlledByServer` `+0x534` bit 0 clear; `Pawn.Health` `+0x1580` > 0; `PawnState` `+0x4E0` == 4 `PawnInRootMotion`; `CurrentAction` `+0x15BC` == 124, or 139 with `Bump=1`; `GrabbingPawn` `+0x4F0` == None; `Level.TimeSeconds − TimeOfLastRotativeAttack (+0x474) > TimeBetween2RotativeAttacks (+0x480)`; `bReloading` `+0x11D7` bit 2 clear; `bIsCrouched` `+0x16F8` bit 5 clear) it runs `ChangeAction(180, force)` (helper `0x109442E0`) and `GotoState('MercRotativeAttack')` (FName `0x20E8`, helper `0x109447B0`), exactly as the stock block `0x10BC43FF`-`0x10BC4425`. Then, in every case, it replays `5F 5E 5D 5B 83 C4 48` and jumps to `0x10BC7A30` (the stock `ret 0xC`). Registers and xmm0..7 are saved/restored (`pushad`/`popad` + an 0x80-byte xmm frame); the only exe write is the 7 site bytes. By hand on disk: nothing (the plugin patches memory only) |

The plugin checks, before it writes, that the image at `GetModuleHandleA(0)` is a PE with `SizeOfImage` >= `0x2C8000`,
then that the site reads `5F 5E 5D 5B 83 C4 48 C2 0C 00` at `0x10BC7A29 + delta`, the helper entries
`83 EC 08 89 0C 24 8B 4C 24 04` at `0x109442E0` and `83 EC 0C 8B 54 24 14 57` at `0x109447B0`, and the stock-berserk
constants `B0 01 B9 B4 00 00 00` at `0x10BC43FF` (action 180), `C7 01 E8 20 00 00` at `0x10BC4417` (FName
`MercRotativeAttack`) and `F6 85 8B 05 00 00 10` at `0x10BC4392` (the berserk button). Any mismatch parks the site
(logged `REFUSED`). The 7 bytes are written under `VirtualProtect` with the old protection restored.

# Mixed installs

Only the merc's own machine runs the plugin; it changes local decisions only, so the host and the other clients may run
it or not.

| Merc's machine | Host | Other clients | Result |
| --- | --- | --- | --- |
| plugin | plugin or stock | plugin or stock | the merc can spin at any moment of the wall stagger; the host accepts action and state with stock code, deals the spin damage, and every client plays the spin |
| stock | plugin | any | stock for that merc: the host's plugin never runs for a remote merc |
| stock | stock | any | stock |
| host plays a merc | - | - | the host is the merc's machine: its own plugin decides |
| bot merc | any | any | stock (bots are not reached) |

# In-game checks for the orchestrator (T1-T7, from R-1; not run here)

| # | Check |
| --- | --- |
| T1 | sprint a merc head-on into a wall, press berserk at 0.1 s, 0.35 s and 0.6 s into the stagger: the spin starts at once each time; `RootBerzerk.log` shows one line each |
| T2 | the merc stays where the stagger had pushed him and turns in place (no snap back toward the wall, no extra slide) |
| T3 | the spin lasts its full length, a spy that walks into it during the first 0.8 s is hit (host), and the merc returns to walking at its end |
| T4 | as a client merc against a stock host, and as the host's merc: the spin starts (one log line on that machine; this checks the version 2 role test on both) and the other clients see the same spin |
| T5 | press berserk within 1.5 s after a previous spin: refused (cooldown stock); during a reload: refused |
| T6 | with SpyGrab: grab a staggering merc (granted), then press berserk: the merc stays grabbed; spin first, then a spy tries: refused until the spin's last 0.5 s |
| T7 | sprint into a player (`ASprintBump`) with `Bump=0`: stock (no spin until the stagger ends); with `Bump=1`: the spin can start in that stagger too |

# Install

`patch.ps1` installs/reverts `System\RootBerzerk.asi` + `System\RootBerzerk.ini` into a game folder and never writes the
main branch (`C:\Program Files (x86)\SCDA Community Edition`) or a running game.

```
.\patch.ps1 -GameDir "<install>"                         status only
.\patch.ps1 -GameDir "<install>" -Apply                  apply the shipped files
.\patch.ps1 -GameDir "<install>" -Apply -Settings "Bump=1"   apply with a custom ini (keys: Enabled, Bump, Log; 0 or 1)
.\patch.ps1 -GameDir "<install>" -Revert                 remove the plugin, its ini and its log
```

After an apply, start the game once: `System\RootBerzerk.log` must read `RootBerzerk 2 ... config: Enabled=1 Bump=0
Log=1` and `berserk 0x10BC7A29: installed`. `-Apply` and `-Revert` refuse the main branch before reading anything in it.
An install that still carries version 1 (md5 `fdac01a0...`) shows `an older RootBerzerk.asi`; `-Apply` then refuses
until `-Revert` has removed it.

# Offline gates (this folder)

`build\gates\run.ps1 -Exes <exe copy>, <exe copy>, ... [-AsiDir <plugin folder>] [-Unnamed <file name>, ...]`
rebuilds the builder and the harness and writes `build\gates\build.txt` and `build\gates\harness.txt` (version 2:
the five exes of `scratch\exe`, the 13 plugins of `scratch\asi`; `-Unnamed` keeps a local-only plugin out of the
transcript while it is still scanned).

- **Static gate** (`build\builder`): **121 PASS / 0 FAIL** - 32 plugin checks: the PE shape, one RWX section, preferred
  base, one empty reloc block, the kernel32 import table; the plugin makes no absolute memory reference (position
  independent), writes only its data / the log cursor / the stack / the 7 site bytes, calls only its routines, its IAT
  slots and the two engine helpers, and leaves by `push (SiteRet + delta) / ret`; its first test is
  `cmp byte [edi+0x2D1],3 / je exit` (the same exit as the button test, no `jne`: version 2). 17 checks per exe x 5
  exes: the site's stock bytes decode as whole instructions, `edi` is the controller and is not rewritten to the site,
  the helper entries and constants match, no branch / `.reloc` / pointer lands in the stolen bytes, no overlap with
  SpyGrab's sites, and a simulated install changes only the 7 site bytes. 3 overlap checks (section H) over the 13
  plugins: no dword holding an exe address (as VA or RVA) inside or up to 15 bytes before any range this plugin writes,
  byte-checks or calls; no byte-pattern string (70, all in `Enhanced.asi`) whose match in any of the five exes covers
  such a range; nothing inside the hooked function `0x10BC7950`-`0x10BC7A33`. Four builds give one md5 (deterministic).
- **Harness** (`build\harness`): runs the real stub against each exe's own code with mock controller / pawn / level and
  recording stand-ins for the two helpers; the expected result of each scene comes from the rule, not from the plugin.
  **8 modes x 5 exes = 40 runs, 945 checks, 0 FAIL** (21 scenes per mode): a joined client's own merc (Role 3 /
  RemoteRole 4) and the listen host's own merc (Role 4 / RemoteRole 2) spin, the host's copy of a remote player (Role 4 /
  RemoteRole 3) does not, any other RemoteRole spins; each refusal condition alone (each leaves the mocks untouched,
  replays the stolen bytes and balances esp); action 139 with `Bump=0` (refused) and `Bump=1` (accepted); the cooldown
  edge (exactly 1.5 s refused, just over accepted); `Enabled=0` (nothing installed), `Log=0` (no file); the plugin
  relocated off its preferred base; the exe mapped at a delta of `0x20000000` (the rebasing applied and verified); and a
  real `LoadLibrary` against the wrong exe image (refused, nothing patched). Version 1 under this model fails 7 checks:
  it spins only for RemoteRole 3 (`scratch\b2\v1_under_v2_model.txt`).

# Open questions for the operator (from R-1; they do not change the build)

1. Also allow the spin in the stagger after sprinting into a **player** (`Bump=1`)? Shipped default: no (the order named the wall).
2. Bots stay stock (decided for B-1), or later give AI mercs the same (R-1 option C, a shared hot site)?
3. A staggering merc can now escape SpyGrab's stagger grab by spinning first: is that wanted?
4. Ship through the launcher to everyone, as SpyGrab is, although only the merc's own machine needs it?
