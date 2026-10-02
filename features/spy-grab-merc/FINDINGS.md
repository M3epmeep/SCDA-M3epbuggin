# FINDINGS - spy-grab-merc

Facts read while researching, building and testing the feature (packages G-1, G-2, builds B-1, B-1b, B-2, the stairs rig T-1 and in-game run 1), in the documentation folder's shape, ready to merge once the operator has validated the feature (rule 12). Source: `SCDA_Online.exe` md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6` (Community Edition main build), main's script packages (`Engine.u`, `Core.u`, `SC4Specific.u`), `Packages\_Common\Animations\SC4_PERSO.ukx` (the `merc` MeshAnimation) and the stair meshes. Static analysis, except where citation 5 (run 1 in a running game, 2026-10-01) is named. `status: draft` applies to all of it.

Filed by the orchestrator on the operator's order "it works, wrap up everything in the deploy folder" (2026-10-01); the text of the grab sections is agent B-1b's, whose own write of this file was refused by the session tool, with the stairs switch, the bot fill and the pawn-object facts added.

## For `engine/pawns-controllers-and-damage.md`: grabbing a merc

A spy's grab of a merc runs through one C++ gate function, shared by the prompt (run on the spy's own machine) and the grant (run on the host), plus one script state machine on each side. Nothing in the path is script-overridable except the pawn's `CanBeGrabbed` event, which every root-motion or knocked-out state overrides with a shared `return false` stub (`0x10A6CA50`).

### Field offsets

| Offset | Field | Notes |
| --- | --- | --- |
| `Controller +0x3F8` | `GoToPosCase` | 1 = `GOTOPOS_SPYGRAB`; written before `GotoState('SpyWalkTo')` |
| `Controller +0x408` | `Pawn` | the controlled pawn; names the real pawn of a twin pair (citation 5) |
| `Controller +0x420` | `WalkToBase` | the grabbed pawn, written by `SpyWalkTo.OkToGrabMercAtPos` |
| `Controller +0x46C` | `TimeForWeaponTrans` | the grab request is re-armed 1.0 s after a weapon transition |
| `Controller +0x474` / `+0x480` | `TimeOfLastRotativeAttack` / `TimeBetween2RotativeAttacks` (default 1.5 s) | gates a new berserk spin |
| `Controller +0x490` / `+0x494` | `SprintBeginTime` / `SprintStaminaCoef` | |
| `Controller +0x498` | `TimeOfInvulnerabilityForGrab` | set to `Level.TimeSeconds + 0.15` by every entry into `MercWalking`; while in force the host refuses a grab of that controller's pawn |
| `Controller +0x4C8` bit 4 / bit 5 | `bServerIsOKToGrab` / `bPreGrab` | set by `SpyWalkTo.OkToGrabMercAtPos` |
| `Controller +0x4F4` / `+0x4F8` / `+0x4FC` / `+0x500` | `fGrabMaxDistance` 200 / `iGrabYawOffset` 1800 / `iGrabMaxYawDif` 11800 / `iGrabMaxYawRot` 9100 (class defaults, no ini override in main) | the host runs the same test at x1.5 (distance 300, yaw limits 17700 / 13650) |
| `Controller +0x58B` bit 0 / bit 4 | the interact (grab) input / the special (spin) input | |
| `Controller +0x5DC` | the walk-to destination vector | set to the target's `Location` at the grab request |
| `Pawn +0x4E0` | `PawnState` (`EPawnState`): 1 `PawnWalking`, 4 `PawnInRootMotion`, 12 `s_PawnGrabbed`, 13 `s_GrabbingPawn` | |
| `Pawn +0x4E4` / `+0x4EC` / `+0x4F0` / `+0x4F4` / `+0x4F8` | `PawnGrabbed` / `PossiblePawnToGrab` / `GrabbingPawn` / `CopyPawnGrabbed` / `CopyGrabbingPawn` | |
| `Pawn +0x89C` / `+0x8AC` / `+0x8B0` | `ARotativeAttack` / `ASprintBump` / `ASprintWall` (animation name fields) | |
| `Pawn +0x11C8` / `+0x11CC` | `LastInvulnerabilityTimeToDTAndGrab` / `InvulnerabilityTimeToDTAndGrab` (default 5 s) | the only writer of `+0x11C8` is `WakeUpAfterKOOnTheFloor.BeginState`; not involved in the spin or the wall stagger |
| `Pawn +0x11D4` bit 25 | `bPossibleGrab` | the grab prompt |
| `Pawn +0x128C` | the pawn's view yaw, copied from `PlayerController+0x5D4` | used by the grab's "target looks away" test; nothing in the engine writes it for an AI merc (T-1) |
| `Pawn +0x1404` / `+0x1474` / `+0x1478` | `PawnCoop` / `Controller` / `WeaponLoaded` | |
| `Pawn +0x1580` | `Health` | 100 at spawn, 0 dead (citation 5) |
| `Pawn +0x15B8` / `+0x15BC` | `iLastAction` / `CurrentAction` | `CurrentAction` stays at the last action run until the next one; no writer other than the action dispatcher was found |
| `Pawn +0x1810` | `a_fAnimRate[26]`; index 4 is the play rate passed with the spin and the wall-stagger animations (measured 1.0) | |
| `LevelInfo +0xA2C` / `+0xA4C` / `+0xAEC` / `+0xB0C` | `SpyStandPill` / `SpyCrouchPill` / `MercStandPill` / `MercCrouchPill` (32-byte pill records, no ini override in main) | half height 90 (standing) / 60 (crouched), radius 35 |
| `Pawn +0x514` | the pawn's current pill half height | used to correct a crouched pawn's location to its standing centre |

### The grab gate (`CheckGrabTarget`, `0x10BCAE50`)

One function, `EAX` = target pawn, `EBX` = the grabbing controller, three stack arguments `(MaxDist, MaxYawDif, MaxYawRot)`, `ret 0xC`, `AL` = 1 allowed. Two callers only: `FindGrabTarget` (`0x10BBDC40`, spy's own machine, unscaled) and `AController::execAskPermissionToGrab` (`0x10BC9F00`, host, all three arguments x1.5 from `.rdata 0x10FA46B0`). Gates run in this order; the height and walk tests are never scaled:

| # | Test | Site | Pass condition |
| --- | --- | --- | --- |
| 1 | both alive | `0x10BCAE58`, `0x10BCAE6B` | `Health > 0` |
| 2 | target answers `CanBeGrabbed` | `0x10BCAE78`-`0x10BCAE9C` | true (every root-motion or knocked-out state's override is the shared `return false` stub `0x10A6CA50`) |
| 3 | post-KO grace | `0x10BCAEA2`-`0x10BCAEC3` | `Level.TimeSeconds - LastInvulnerabilityTimeToDTAndGrab > InvulnerabilityTimeToDTAndGrab` (5 s) |
| 4 | horizontal distance | `0x10BCAECF`-`0x10BCAF20` | `sqrt(dX^2+dY^2) <= MaxDist`; Z excluded |
| 5 | target looks away from the spy | `0x10BCAF26`-`0x10BCAF5C` | `abs(norm(target.viewYaw + 1800 - yaw(spy->target))) <= MaxYawDif` |
| 6 | spy faces the target | `0x10BCAF62`-`0x10BCAF81` | `abs(norm(spy.Yaw - yaw(spy->target))) <= MaxYawRot` |
| 7 | crouch correction | `0x10BCAF87`-`0x10BCB003` | sweeps a crouched pawn up to its standing pill before the height test |
| 8 | vertical offset of the pill centres | `0x10BCB009`-`0x10BCB01B` | `abs(dZ) <= 30.0` (float at `.rdata 0x10FA4A68`), symmetric (spy above or below the target fail alike); NOT scaled on the host |
| 9 | walk reachability | `0x10BCB039`-`0x10BCB1A5`, callee `0x109F08F0` (name given here: `WalkReach`) | a pill swept along the floor from the spy to 36 uu short of the target (`.rdata 0x10FA4CFC`) reaches within 0.01 uu; both pawns' own collision is switched off for the sweep |

`FindGrabTarget` walks the level's pawn list (`[PC+0x304]`, count `+0x54`, data `+0x58`) and skips a pawn whose `PawnType != 0`; an AI merc (`NPCPawnMerc_Zero`) has `PawnType` 0 (measured, citation 5), so the rule makes it a grab target like a player merc.

`WalkReach` (`0x109F08F0`, 9 stack args, `ret 0x24`) is a floor walk, not a line trace: floor probe 36 uu straight down (no floor = fail), a floor is walkable at normal Z >= 0.7 (0.777 for later floors), a blocking hit is stepped over up to 32 uu above the pill's feet (`.rdata 0x10FA49B4`) and is a wall above that, success at remaining distance <= 0.01 uu, give-up at remaining < 50 uu with no progress or after 10 stuck iterations. On the measured stair meshes (`IND08_STM` 24.4 uu rise / 36.5 uu run = 33.8 deg; `NSA01_STM` 20 uu rise; `CLUBE_STM` 16 uu rise; `BLW_Anne_STM.BLK_Det_Escalier01` 25.6 uu rise / 35.3 uu run, about 36 deg; ramps 20 to 39 deg) every rise is below the 32-uu step and every ramp is walkable, so the walk test is not what blocks a grab on stairs; the height gate (test 8, dZ <= 30) is: a 70-uu-apart pair on a 33.8-degree stair already differs by 47 uu.

There is no script hook and no ini key for the height limit: it is one `fld dword [0x10FA4A68]` at `0x10BCB00F` (operand at `0x10BCB011`, file offset `0x2CB011`), while the float itself is read at 56 other sites in the exe (among them the merc's own terminate-move test, `0x10BBA52C`, same 30.0 constant and the same walk test with a 1.0 uu minimum step). Retargeting that one operand to the exe's existing 80.0 (`.rdata 0x10FA4C30`) lets a spy grab a merc on stairs and leaves every other reader of 30.0 unchanged; the walk test still refuses a ledge, a floor, a railing or a wall (read statically; the stairs grab itself was validated in game by the operator, citation 5, the refusal cases were not run).

### The berserk spin and the wall stagger

Both moves put the merc in pawn state `PawnInRootMotion` (4) for the whole animation via the action dispatcher (`GotoState('PawnInRootMotion')` at `0x10BEE16D` for the spin, `0x10BEC1CB` for the wall stagger and the sprint-into-pawn bump), which is why `CanBeGrabbed` (gate 2 above) refuses all three the same way. `Pawn.CurrentAction` (`+0x15BC`) tells them apart: 180 spin, 124 wall stagger, 139 sprint-into-pawn bump. The controller state (`MercRotativeAttack` / `MercWaitForSprintBump`) has no `EndState`, so nothing of it runs when a later `GotoState` (a host grab grant, or the animation's own end) replaces it.

| Move | Animation | Frames @ fps | Root motion | Ends into |
| --- | --- | --- | --- | --- |
| berserk spin (action 180) | `ARotativeAttack` = `AtakStAlTu` | 41 @ 30 | rotation only, position fixed: turns in place | `MercRotativeAttack.CtrlSeqAnimEnd` -> `MercWalking` |
| wall stagger (action 124) | `ASprintWall` = `AtakStChEd2` | 21 @ 30 | 80 uu straight back over the animation | `MercWaitForSprintBump.CtrlSeqAnimEnd` -> `MercWalking` |
| sprint-into-pawn bump (action 139) | `ASprintBump` = `AtakStAlFd2` | 35 @ 30 | none | `MercWaitForSprintBump.CtrlSeqAnimEnd` -> `MercWalking` |

A channel-0 animation node (vtable `0x10F90B30`) reports its own normalised play position at `+0x60` (0 at the start) and its end position at `+0x68` as `1 - 1/frames` (not 1.0): for a 41-frame sequence, end = 0.9756. The node's `+0x70` holds the play rate already converted to "normalised position per second" (`frames-per-second x play-rate / frames`); the real playable length of the animation is therefore `end / rate`, not `frames / fps`. For the stock spin (`a_fAnimRate[4]` = 1.0, 41 frames at 30 fps): end 0.9756, rate 0.7317/s, length 0.9756 / 0.7317 = **1.333 s** (`(frames-1)/fps`), not `frames/fps` = 1.367 s. The spin's own damage window (`MercRotativeAttack.NotifyBump`, host only, damage type 9) lasts while the position is <= 0.8 (`.rdata 0x10FA4958`), i.e. until 0.8 x 1.333 = 1.067 s, about 0.266 s before the spin's true end.

A type-2 cross-fade node (vtable `0x10F90A90`, `+0x50` == 2) reports the name and position of its child 1 (the animation fading in), which is why an animation reader written for a plain channel node must also resolve a cross-fade first.

### A grab granted while the target is still in `PawnInRootMotion`

Stock code never starts a grab on a target in this state (gate 2 always refuses it), so the following is new ground, read statically:

- The grant (host) runs `GotoState('Grabbed')` on the target's controller. Neither `MercRotativeAttack` nor `MercWaitForSprintBump` declares `EndState`, so nothing of the interrupted state runs.
- On the target's own client the animation's stock end can still arrive after the grant and reach `MercRotativeAttack.CtrlSeqAnimEnd` / `MercWaitForSprintBump.CtrlSeqAnimEnd` locally, which would send it to `MercWalking` and call `ServerChangeState('MercWalking')`; the host ignores that RPC while `Controller+0x534` bit 0 (`bControlledByServer`, set at the grab's action 151) is set (`PlayerController::execServerChangeState`, `0x10BD098B`). The host's own `ClientChangeState('Grabbed')` is unconditional.
- The grab's own action (261 on the grabbed pawn) plays the grab animation on channel 0, the same channel the spin and the wall stagger used, with a 0.1 s tween. `APawn::SeqAnimEnd` is dispatched by one routine (`0x10C2BBF0`, the only caller of the pawn's `SeqAnimEnd` and `Controller.CtrlSeqAnimEnd` thunks) that reads the animation name from the node **now occupying the channel slot**, not from the node that actually ended (`0x10C2BC2F`-`0x10C2BC44`). After action 261 that slot holds the grab animation (via the cross-fade), so a late end of the replaced spin or stagger is reported with the grab animation's name, and the shared `SeqAnimEnd` exit at `0x10C3775F` (`GotoState('PawnWalking')`, `SetPhysics(1)`) is only reachable there for `ARotativeAttack` / `ASprintBump` / `ASprintWall`, which a grabbed pawn's node no longer names. Not run in a game.
- The wall stagger's 80-uu root-motion push continues for as long as the animation still plays after the grant, since nothing in the grant tears down `bUseRootMotionAdditionnalPhysics` / `iLockRootMotionType` / `RootMotionAdditionnalPhysics` (cleared only by other action handlers, never by the grant or by `SeqAnimEnd`).
- No grab spot is computed: the host sends the target's own `Location` at the grant, and the spy walks to within 80 uu of it on XY only (Z of the delta forced to 0). Once grabbed, the target's physics becomes `PHYS_FollowParent` (`EPhysics` 5) and its position is pulled to `spy.Location + (70.85, 0, 0)` turned by the spy's rotation (`.rdata 0x10FA517C`), Z included: the grabbed pawn's centre snaps to the spy's centre height at the instant of the grab, so a height difference at the grant (a stair: 47 to 53 uu on the measured `IND08_STM` flight at the grab's 70-80 uu range) is pulled out immediately rather than eased.

### Pawn objects in memory (citation 5)

| Fact | Detail |
| --- | --- |
| every pawn has a twin | each live pawn (player spy, AI merc) appears twice in the object table: the same class, the same object name, a location a few uu apart, both holding the same controller at `Pawn+0x1474` |
| the real one | the pawn the controller names (`Controller+0x408`), and the only one in the level's pawn list (`[PC+0x304]`, count `+0x54`, data `+0x58`) |
| not a flag word | `Pawn+0x328` reads 0 on every live pawn; `bDeleteMe` / `bIsAPawn` are not there |

## For `engine/game-modes-and-match-flow.md`: the lobby's bot fill

Measured in run 1 (citation 5) on a one-PC LAN versus match, the operator hosting as spy with no other player:

| Fact | Detail |
| --- | --- |
| session object | `[0x1100AA2C]`; lobby state word `+0x4B8`: bit `0x40000` while the lobby is up, `0x80000` in the match (read `0x40002`, then `0x80002`); mercs listed `+0x4424` |
| bot fill | `+0x54` = fill value (1 easy, 2 medium, 3 hard, 0 none, the stock default) and byte `+0x58` = 1, the two stores the lobby's Bots button's setter `0x10DC0A90` makes (`Page_LOOBY` zone 39 item 5, menu variable `0x72`) |
| at match start | the host code `0x10D953D0` sets `NumBots = 3 - mercs listed` and `BotsDifficulty` = the fill (read statically); with the fill 1 and 0 mercs listed, three AI mercs spawned |
| the bots | class `NPCPawnMerc_Zero`, controller `AIController`, `PawnType` 0 (`Pawn+0x12A0` low byte; the host spy reads 1), health 100; a killed bot respawns and gets a new pawn object |

## For `engine/exe-addresses-and-patches.md`

### Grabbing a merc

| Address | Size | What | Notes |
| --- | --- | --- | --- |
| `0x10BCAE50` | - | `CheckGrabTarget` (name given here) | `EAX` = target pawn, `EBX` = grabbing controller, stack `(MaxDist, MaxYawDif, MaxYawRot)`, `ret 0xC`, `AL` = allowed; the one function both the prompt and the grant call |
| `0x10BCAE97` | 11 | `cmp dword [esp+0x14],0` / `je 0x10BCB1E8` (`83 7C 24 14 00 0F 84 46 03 00 00`) | the `CanBeGrabbed` result test in `CheckGrabTarget`; `spy-grab-merc` hooks it |
| `0x10BCB00F` | 6 | `fld dword [0x10FA4A68]` (`D9 05 68 4A FA 10`) | the height test's limit; operand at `0x10BCB011` (one `.reloc` entry); retargeted to `0x10FA4C30` (80.0) by `spy-grab-merc` |
| `0x10BC9F2D` | 6 | `ja 0x10BCA0D7` (`0F 87 A4 01 00 00`) | the host's `TimeOfInvulnerabilityForGrab` refusal in `execAskPermissionToGrab` |
| `0x10BBDC40` | - | `FindGrabTarget` | called first in `AController::execSpyWalking_PawnMove` (native 1047, `0x10BBDDC0`); walks `XLevel+0x50`, skips `PawnType != 0`, unscaled `CheckGrabTarget` |
| `0x10BC9F00` | - | `AController::execAskPermissionToGrab` (native 1388) | host only; `CheckGrabTarget` call at `0x10BC9F7C` with all three arguments x1.5 (`.rdata 0x10FA46B0`) |
| `0x10A0B805` | 4 | native 1485 (`PawnInRootMotion.CanBeGrabbed`) table entry | holds `0x10A6CA50`, the shared `return false` stub |
| `0x109F08F0` | - | `WalkReach` (name given here) | 9 stack args, `ret 0x24`; sweeps a pill along the floor, not a line trace |
| `0x10BE2330` | - | mesh instance of an actor | `Actor+0x80`, via `Actor.Mesh (+0x70)` |
| `0x10BB0A80` | - | channel animation name | `ECX` = mesh instance, `EAX` = channel, `ESI` = FName out |
| `0x10ABBB40` | - | channel animation position | `ECX` = mesh instance `+0x120`, `EAX` = channel, returns in `ST0` |
| `0x10F90B30` | - | plain channel node vtable | `+0x60` position, `+0x68` end (`1 - 1/frames`), `+0x6C` sequence, `+0x70` rate (normalised position/s), `+0x84` bit 0 loop / bit 1 reverse |
| `0x10F90A90` | - | cross-fade node vtable | `+0x50` == 2 identifies it, `+0x64` child count, `+0x68` child array; child 1 is the animation fading in |
| `0x10C2BBF0` | - | pawn anim-end dispatcher | vtable `+0x40C`, the only caller of `Controller.CtrlSeqAnimEnd` (via `0x10C3C320`) and `Pawn.SeqAnimEnd` (via `0x10C3C2E0`); reads the animation name from the node presently in the channel slot, not the node that ended |
| `0x10C35980` | - | `APawn::execSeqAnimEnd` (native 1311) | shared exit `0x10C3775F` for `ARotativeAttack` / `ASprintBump` / `ASprintWall`: `GotoState('PawnWalking')`, `SetPhysics(1)`; the trio's own `jmp 0x10C3775F` sits at `0x10C35FEB` |
| `0x10BCC490` | - | `MercRotativeAttack.NotifyBump` | host only (`Role == 4`); damage type 9 (`Dmg_ProximityAttack`) while the spin's channel-0 position <= 0.8 (`.rdata 0x10FA4958`) |
| `0x10BC7590` | - | `MercSprint.NotifyHitWall` | action 124 (`ASprintWall`) when the hit is within 30 deg of head-on or horizontal speed^2 < 10 |
| `0x10BC77A0` | - | `MercSprint.NotifyBump` | action 139 (`ASprintBump`), damage type 12 (`Dmg_SprintAttack`) on the victim via RPC `0x10BC7D40` -> `0x10BC9A20` |
| `0x10BD4C44` | - | `TimeOfInvulnerabilityForGrab` store | `movss [edi+0x498]` on entry into `MercWalking` |
| `0x10C2EE60` | - | pawn physics dispatcher | `cmp ebx,5` at `0x10C2EED1` selects `PHYS_FollowParent` |
| `0x10C3B790` | - | `PHYS_FollowParent` tick | pulls the grabbed pawn to `grabber.Location + offset` every tick, offset turned by the grabber's rotation, Z included (`subss` at `0x10C3B87F`) |
| `0x1100AA2C` | 4 | the lobby session object pointer | bot fill `+0x54` / `+0x58`, state `+0x4B8`, mercs listed `+0x4424` |

The exe's `DllCharacteristics` is 0 (no `DYNAMIC_BASE`), so it always loads at its preferred base `0x10900000`; file offset = VA - `0x10900000` for `.text`, `.rdata` and `.data`.

### Constants

| Constant | Value | Home | Notes |
| --- | --- | --- | --- |
| grab height limit | 30.0 | `.rdata 0x10FA4A68` | read at 56 sites, among them the merc's terminate-move test (`0x10BBA52C`); no ini key, no class default |
| 80.0 | 80.0 | `.rdata 0x10FA4C30` | existing read-only float; the stairs change points the height test's operand here |
| 60.0 | 60.0 | `.rdata 0x10FA46F4` | existing read-only float (the alternative F1-60) |
| host distance/yaw leniency | 1.5 | `.rdata 0x10FA46B0` | scales `MaxDist`, `MaxYawDif`, `MaxYawRot` on the host only; not the height or the walk |
| walk end offset (short of the target) | 36.0 | `.rdata 0x10FA4CFC` | also the walk's own floor probe depth |
| walk step-up | 32.0 | `.rdata 0x10FA49B4` | a blocking hit at or below this height above the pill's feet is stepped over, not a wall |
| walk minimum distance | 0.1 | `.rdata 0x10FA4724` | below this the walk test is skipped |
| spin damage cutoff (channel-0 position) | 0.8 | `.rdata 0x10FA4958` | `MercRotativeAttack.NotifyBump`, host only |
| grabbed-pawn offset from the grabber | 70.85 | `.rdata 0x10FA517C` | one reader, `0x10C3B7C4`; horizontal component only measured (a walking pawn's `Rotation.Pitch` was not confirmed to be 0) |
| post-`MercWalking` grab grace | 0.15 s | `.rdata 0x10FA47D0` | `TimeOfInvulnerabilityForGrab = Level.TimeSeconds + 0.15`, written by every entry into `MercWalking` (20+ sites); shared, not specific to the spin or the wall stagger |
| post-KO grab grace | 5 s | class default (`Pawn.InvulnerabilityTimeToDTAndGrab`) | only writer of the matching timestamp is `WakeUpAfterKOOnTheFloor.BeginState` |

## For a Blackwing map file (none exists yet)

| Fact | Detail |
| --- | --- |
| detention-block staircase | `BLW_Anne_STM.BLK_Det_Escalier01`, `StaticMeshActor` export 2342 of `BLKG1_VS` at (2012, -464, -336), yaw 32768; 19 treads 256 uu wide, rise 25.6, run 35.3 (about 36 deg), 674 uu long; ground floor Z -648 to mezzanine Z -139; first tread top Z -614.4 at Y -154..-192, head lip at Y -828, Z -124; up the stairs is -Y |
| second flight | export 2432, the same mesh, mezzanine to the top floor at Z 377 |

## Citations

[1] `SCDA_Online.exe` (Community Edition main build, md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6`), disassembly of the grab path `0x10BBDC40`-`0x10BCB1E8`, `0x10BC9F00`-`0x10BCA110`, the animation-end path `0x10C2BBF0`-`0x10C37798`, the action handlers `0x10BC7590`-`0x10BC78E0` and `0x10BEB5C3`-`0x10BEE1BC`, the `PHYS_FollowParent` path `0x10C2EE60`-`0x10C3B87F`, the node and cross-fade vtables `0x10F90A90`, `0x10F90B30`, and the lobby bot-fill path `0x10DC0A90`, `0x10D953D0`.

[2] `Packages\_Common\Animations\SC4_PERSO.ukx` (`merc` MeshAnimation, md5 `7965b08c257794d9595ad1ff885cbd70`): `AtakStAlTu` (41 frames), `AtakStChEd2` (21 frames, root track), `AtakStAlFd2` (35 frames).

[3] `System\PC\Engine.u` (md5 `b41331d86a61be18784ae1a64ffde15e`), `System\PC\SC4Specific.u` (md5 `69eb6d421787706eb1f56c3efadd805c`): class defaults and field layout of `Controller`, `Pawn` and `LevelInfo` (`EPawnState`, the pill records, the grab distance/yaw defaults).

[4] `Packages\_Common\StaticMeshes\IND08_STM.usx`, `NSA01_STM.usx`, `CLUBE_STM.usx`, `KIN01_STM.usx`, `FRQ01_usx.usx`, `FRQ02_STM.usx`, `BLW_Anne_STM.usx`: collision and visible faces of the measured stair and ramp meshes; the map package `BLKG1_VS` for the staircase placements.

[5] Run 1 in the game, 2026-10-01 01:01-01:05: `SCDA_Online.exe` md5 `0f1b2d1c` with `SpyGrab.asi` v2 `ca67503e`, `BLKG1_VS` LAN versus match hosted as spy with the lobby's bot fill 1; memory read by `Deploy\spy-grab-merc\test\rig\` scripts; logs in `Deploy\spy-grab-merc\test\results\run1-20261001-0101\`; the operator's verdict "it works".
