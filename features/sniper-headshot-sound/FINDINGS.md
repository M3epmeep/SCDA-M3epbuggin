# FINDINGS - sniper-headshot-sound

Facts read while building the feature, in the documentation folder's shape, ready to merge once the operator has validated the feature (rule 12). Sources: `SCDA_Online.exe` md5 0f1b2d1c (Community Edition main build of 2026-09-28) and md5 d94c9137 (the build before it), identical at every address below; `Engine.u` for the names; the main build's `MAPS.SM0` md5 d8e31526 and `SFO_Equipment.uax`. Static analysis and file decoding only. Nothing here was measured in a running game. `status: draft` applies to all of it.

## For `engine/pawns-controllers-and-damage.md`: the kill accounting and the sniper damage type

A player's damage goes through one virtual of the `PlayerController`. It calls the controller's damage routine and then, once per death, does the kill accounting. A scoped shot is its own damage type and has its own per-body-part table.

### Schema

| Routine | Address | Notes |
| --- | --- | --- |
| PlayerController damage virtual | `0x10BD8320`, vtable `0x10F7F740` slot `+0x3E4` | thiscall, 8 arguments, `ret 0x20`: Damage, InstigatorPawn, &HitLocation, &Momentum, DamageType, PillTag, weapon kind, owner pawn |
| `AController::TakeDamage` | `0x10BACF40` | called at `0x10BD83A3`, before the accounting; hands its argument 6 (PillTag) to the damage leaf as the table index |
| damage leaf | `0x10BAE4F0` | scales `Dmg_Snipe` by `DamageSnipeLookupTable[PillTag]`, every other type by `DamageLookupTable[PillTag]` |
| once-per-death gate | `0x10BD83BD` | `PC+0xA08` bit `0x8000000` (`bAffDiedText`) |
| team test | `0x10BD83F7` | victim and killer `PRI.TeamID` (`+0x410`) differ, before `Kills += 1` |
| sniper kill count | `0x10BD842B` `mov eax,[ebp+0x1614]`, `0x10BD8431` `add [eax+0x4B8],edi` | reached only for DamageType 15; `ebp` = killer pawn, `esi` = victim PlayerController, `edi` = 1; `PRI.iSnipeKills` is `PRI+0x4B8` |
| `SC4Weapon.execnewServerFireWeaponHitPawn` | `0x10DEAA50`, native 3491 | server call from the shooter's client, `_customTag` = PillTag; picks DamageType 15 when the binocular test is true; sends `ClientPlaySound(HeadShotSound)` to the shooter when PillTag is 0 |
| binocular test | `0x10DFEBF0`, vtable slot `+0x43C` | the shooter's controller is in state `SpyBinocular` (FName `0x228F`) or `MercBinocular` (`0x2293`) |

| Field | Offset | Notes |
| --- | --- | --- |
| `Pawn.Controller` | `Pawn+0x1474` | |
| `Pawn.PlayerReplicationInfo` | `Pawn+0x1614` | |
| pawn team byte | `Pawn+0x12A0` | 0 = merc |
| `Pawn.DamageLookupTable[17]` | `Pawn+0x1634` | indexed by PillTag |
| `Pawn.DamageSnipeLookupTable[17]` | `Pawn+0x1678` | indexed by PillTag |
| `Pawn.HeadShotSound` | `Pawn+0x1878` | |
| `Actor.bDeleteMe` / `bPendingDelete` / `bRemoveInLevelList` | `Actor+0x314` bits 0 / 1 / 2 | |

| Enum | Values |
| --- | --- |
| `SDamageType` | 1 `Dmg_Bullet`, 7 `Dmg_Explosion`, 15 `Dmg_Snipe` |
| `PillName` | 0 `ePN_Head` .. 16 `ePN_R_Foot` |
| `ESoundSlot` | 4 `SLOT_SFX` |

## For `formats/audio.md`: how a sound reaches the players

| Routine | Address | Notes |
| --- | --- | --- |
| `AActor::PlaySound` | `0x10A6C570` (native 264) | walks `Level.ControllerList` (`Level+0x7B8`, next `Controller+0x58C`, bIsPlayer `Controller+0x4C8` bit 4) and calls `HearSound` on each |
| `APlayerController::HearSound` | `0x10BD3120`, vtable slot `+0x430`, 7 arguments, `ret 0x1C` | slot 4 (`SLOT_SFX`): sends the event `ClientHearSound` through `0x10BDCE50` with the Actor, Id 4 and Parameters = (Volume x 1000, Radius, Pitch x 1000), the constant 1000 at `0x10FA4854`; other slots: local audio only. Neither path passes Volume or Radius to DARE |
| event thunk | `0x10BDCE50` | FindFunction(FName `0x15BA`) by `0x109948D0` (`this` in `edi`, `ret 8`, can return 0), then ProcessEvent (vtable `+0x10`) with flags `0x400000` |
| `PlayerController.ClientHearSound` | native 1190, `0x10BD3010` | (Actor, int Id, sound S, vector SoundLocation, vector Parameters, bool Attenuate, optional int BoneIdx), Net, unreliable. Entry `51 8B 44 24 08`. Returns at `0x10BD3073` when S is NULL. At `0x10BD307B` an Actor with `bDeleteMe` or `bRemoveInLevelList` is replaced by NULL. Never reads SoundLocation (`Parms+0x0C`) or Parameters (`Parms+0x18`). Plays through the audio object's vtable `+0x90` with (Actor, S, Id, the vector at `[0x110189A4]`, BoneIdx as float); `ret 0xC` |
| calc view | `0x109DFA80`, vtable slot `+0x6C` | camera location = `PC+0x71C` + `PC+0x734`, yaw = `PC+0x768` + `PC+0x750` |

## For `formats/audio.md`: the shared bank `FIX`

Measured on the main build's `MAPS.SM0` (182,933,888 B, md5 d8e31526a7a931df4c1108f05ace94c0), which carries the 12 stock directory entries.

| Fact | Detail |
| --- | --- |
| size | `FIX` at 636, 160,172 B: 325 events (A), 913 resources (B), 11,204 B of section C, one sub-map (id -1) with 689 data entries and two sub-blocks: 0 (PCM) at 160,808, 17,813,236 B; 1 (Ogg Vorbis) at 17,974,044, 2,907,203 B |
| data entries of `FIX` | the resource index carries bit 31: `0x80000000 + index`. The per-map blocks use the plain index |
| resource types | 1 (one sound) 692, 4: 167, 3: 23, 2: 19, 7: 7, 8: 5. Types other than 1 are containers and have no data entry |
| a container's children | a type 4 container: records of 16 bytes in section C, at the offset in the container's word 3: `u32 0x80000000 + resource index`, `u32` weight, `u32 1`, `u32 0` (B[0xAC], the grenade throw of events 6 and 24: children `0xAD`, `0xAE`, `0xB0`, `0xB1`, `0xB2`). Types 2 and 3 name their children in section C in another layout, not decoded; every child is named as `0x80000000 + index` |
| an event's distances | parameters 4 / 6 / 7 of the A record (at `+12 + 4 x n`, 16.16 fixed point). Stock values: flash grenade explosion 3 / 4 / 18, gun 10.5 / 20.5 / 30.5, gun burst 10.5 / 32.5 / 50.5, armed mine 1.5 / 2.5 / 6.5, turret 2 / 6 / 15. `Play_Snipe_inOut` and `Play_Snipe_zoom` (heard by the player himself) carry 65536 in all three. Read as metres with parameter 7 the largest distance: not measured |
| a resource's loudness | word 5 of the B record, dB in signed 16.16 fixed point: 0 on most, -2.3 on the flash explosion (`0xFFFDB334`), -30.4 and -44.5 on two nano drone sounds |
| sample format of the merc equipment group (group 5) | 37 PCM samples, all 24,000 Hz, 16 bit, mono; the Ogg Vorbis samples of `Play_Gun_SFO_Burst` and `Play_Maglight_Chim_loop` are 48,000 Hz mono |
| loudness of the group's PCM samples | loudest 50 ms, with the loudness word: the seven loudest -1.5 to -7.5 dBFS, among them the drone explosion (-1.7), the nano drone explosion (-3.5) and the children of the containers of events 7, 1 and 6 / 24; flash grenade explosion -9.0; median about -20, quietest -42; four samples are silence |
| one event, two names | `Play_Turret_loop` and `Play_Torch_RayLight` (`SFO_Equipment.uax`) both carry event 33 group 5; `Stop_Turret_loop` and `Stop_Torch_RayLight` both event 34 |
| events without a record | `Play_SFOModule_InOut`, `_MarkFeedB`, `_zoom`, `_zoomShow` (events 20 to 23, group 5) are in `SFO_Equipment.uax` and in no `FIX` record |

### An unused cue

| Cue | Event | A record | Resource | Sample | Named by |
| --- | --- | --- | --- | --- | --- |
| `Play_Turret_On` (`SFO_Equipment.uax` export 40, outer `Group_Dare`) | 36, group 5 | A[78] at 8,792; parameters 2 / 6 / 15 | B[0xD2] at 59,680, id `0x0005002D`, type 1, PCM, 39,670 B, 19,835 frames, not looped, 0 dB | file offset 4,974,252, md5 521f75480bff410416b1bbad244bd2c5, peak -8.1 dBFS | no `.u`, no map, no exe, no plugin of the install; no other event and no container of any block plays the resource |
| `Play_Turret_Off` (export 41) | 35, group 5 | A[77] | B[0xD1], same shape | file offset 4,934,580, md5 5d0ceec9 (first 8) | the same |

A sample of at most 39,670 bytes written over such a sample, with the record's length and frame count kept, changes no offset of the bank: every block still round-trips through `dare_block` and `dare_census` gives the same tallies.

## For `formats/package-container.md` and `formats/audio.md`: a `.uax` read with the corrected record layouts

`SFO_Equipment.uax` (4,487 B, version 272): 60 names, 4 imports (`Core`, `Engine` packages; the classes `Sound` and `Package`), 53 exports: export 1 `Group_Dare` (class `Package`, flags `0x70004`, 2 bytes), then 52 `Sound` exports (flags `0xF0004`, 36 to 41 bytes) whose group is export 1. A sound's object path is `<package>.Group_Dare.<name>`.

The script packages that name `SFO_Equipment`: `System\PC\SC4Ingredients.u`, `SC4Inventory.u`, `SC4Specific.u`; also `Packages\_Common\Animations\gadgets_animation.ukx` and `gadgets_animation.evtsound`.

## For `engine/native-code-and-exe.md`: ProcessEvent, net functions, loading an object by name

| Routine | Address | Notes |
| --- | --- | --- |
| `AActor::ProcessEvent` | `0x109EE440`, PlayerController vtable slot `+0x10` | tests `Level+0x64C` bit 2, then jumps to `UObject::ProcessEvent` |
| `UObject::ProcessEvent` | `0x1096E1C0` | returns when `[0x1100CC6C]` is 0 or when vtable `+0x30` answers non-zero; calls vtable `+0x20`(function, parms) and returns when it answers non-zero (the call was sent to the remote side); a function with the native flag (`function+0x6D` bit 4, flag `0x400`) is then called directly through `[function+0x70]` |
| native ABI | - | `execFoo(Parms, Result, Flags)`, thiscall, `ret 0xC`; the flags word of ProcessEvent carries the mask of the optional parameters shifted left by 16 |
| `UObject::StaticLoadObject` | `0x109992F0` | cdecl, six arguments (Class, InOuter, Name UTF-16, Filename UTF-16, LoadFlags, Sandbox), its own exception frame (`push 0x10E219A0`); 20 call sites. `LoadMap` at `0x10A126C8`: (Class class `0x11019148`, 0, `L"PawnSpyMercDependency"`, `L"SC4Specific"`, `0x8001`, 0) with the load-context flag `0x1100FD6C` set to 0 around it. `execGetLevelBrief` at `0x10A6B31A`: (Texture class `0x1103F0D0`, 0, a name built at run time, 0, `0x2002`, 0) |
| `UObject.DynamicLoadObject_Fname` | native 411, `0x1096DE80` | the script loader takes three FNames (package, group, object) and a class; calls `0x109994D0` with eight arguments and the flags 2, or `0x2002` when MayFail is set |
| `Sound` class global | `0x11031250` | sizeof `0x50`, registered at `0x109C91E5` (`mov ecx,0x50` / `mov edx,0x11031250` / call `0x10963600`); FName of `Sound` = `0x022D`. The engine finds its own cue `L"Play_Menu_Music"` with this class at `0x10C5C093` |

## For `tools/plugins-and-instruments.md`: Microsoft Defender and a plugin

| Fact | Detail |
| --- | --- |
| detection | a no-import, one-RWX-section `.asi` of 37,376 B (md5 f90c4828, version 1 of this feature) was detected by Microsoft Defender as `Trojan:Win32/SmokeLoader!pz` (ThreatID 2147888371) and removed from the build folder seconds after it was written, twice (2026-09-28 21:59:37 and 21:59:45) |
| what that plugin did | started a thread, resolved `CreateThread`, `CreateEventA`, `VirtualAlloc`, `CreateFileA`, `ReadFile`, `GetFileSize`, `LoadLibraryA` and winmm `PlaySoundA` by name at run time, carried a 16 KB data block (a tone) |
| not detected | version 2 of the same feature, the same scheme (no import directory, one RWX section, position independent, 8,704 B, md5 9e9dcfc0), built 2026-09-28 23:49, loaded 16 times by its harness: it starts no thread, reads no file and resolves `VirtualProtect`, `GetPrivateProfileIntA`, `CreateFileA`, `WriteFile`, `SetFilePointer`, `CloseHandle`. The other plugins of the scheme on the same PC (`QolHud.asi`, `RollFix.asi`, `BombHud.asi`, `HackHud.asi`, `FileScore.asi`) were not detected either |
| not known | which of the differences the detection answered to |

## Citations

1. `SCDA_Online.exe`, md5 0f1b2d1ce8167d267ee15d5a4ed4c3e6 (7,712,768 B).
2. `SCDA_Online.exe`, md5 d94c9137340f3996b5bc9ec361340d1e (7,712,768 B).
3. `Engine.u` of the same builds (enum and function names).
4. `Packages\_Common\SoundsDARE\MAPS.SM0`, md5 d8e31526a7a931df4c1108f05ace94c0 (182,933,888 B), main build of 2026-09-28.
5. `Packages\_Common\Sounds\SFO_Equipment.uax` (4,487 B) and the 17 other `.uax` packages of the same build.
6. Microsoft Defender detection history of 2026-09-28 on this PC.
