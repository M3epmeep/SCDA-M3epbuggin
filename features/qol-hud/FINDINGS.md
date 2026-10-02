# FINDINGS - qol-hud

Facts read while building the feature, in the documentation folder's shape, ready to merge once the operator has validated the feature (rule 12). Source: `SCDA_Online.exe` md5 0f1b2d1c (Community Edition main build of 2026-09-28) and md5 d94c9137 (the build before it), static analysis, and for the draw order also the game's own loop and render run on fakes in a harness. Only the live widget indices were measured in a running game (citation 3). `status: draft` applies to all of it.

## For a new file `engine/hud.md` (no file holds the HUD yet)

The versus HUD is one native object per local player, vtable `0x10F81BC0`, ctor `0x10B6F690`, held in `PlayerController+0x95C`. It owns an array of widgets. Each widget is a plain C++ object of its own class, not a `UObject`; all 41 widget classes share a 15-slot vtable shape. Which widgets are drawn is decided by one byte on the HUD, the mode, against one mask on each widget.

### Schema

| Field | Offset | Notes |
| --- | --- | --- |
| HUD widget array | `HUD+0x3F4` max, `+0x3F8` count, `+0x3FC` data | appended only by `AddWidget` `0x10B72C60` |
| HUD owner | `HUD+0x400` | the local `PlayerController` |
| HUD mode | `HUD+0x404` | byte; the page the HUD shows |
| HUD mode before | `HUD+0x405` | byte; written by the mode setter |
| HUD mode of the last frame | `HUD+0x406` | byte; written at the end of the per-frame loop |
| current HUD | `0x1100FF00` | global; the HUD that last added a widget |
| last mode that was not 0 | `0x1100FEFC` | global byte; written by the mode setter |
| widget mode mask | `widget+0x34` | dword; bit n set = shown in mode n |
| widget sub-items | `widget+0x20` count, `+0x24` data | shown and hidden as a group |

| HUD vtable slot | Address | Does |
| --- | --- | --- |
| `+0x430` / `+0x434` | `0x10B71090` / `0x10B710C0` | called by the camera start / stop virtuals: writes -1.0 / 0.0 to `[[HUD+0x400]+0x804]+0x78` and calls that object's vtable `+0x8C` |
| `+0x438` | `0x10B71340` | the builder: adds the widgets of the local player's team and game mode |
| `+0x440` | `0x10B72EC0` | one of the three loops over the widgets |
| `+0x444` | `0x10B729F0` | set mode(n), `ret 4` |
| `+0x448` | `0x10B72C60` | `AddWidget(w)` |
| `+0x454` / `+0x458` | `0x10B72DF0` / `0x10B72E20` | `GetWidget(i)` (NULL when `i >= count`) / count |

| Widget vtable slot | Address (base) | Does |
| --- | --- | --- |
| `+0x04` | `0x10B73C60` | clear the mode mask |
| `+0x08` | `0x10B73C70` | set bit n of the mode mask |
| `+0x0C` | `0x10B73C90` | test bit n of the mode mask, returns 0 or 1; the same routine in all 41 vtables, no direct caller |
| `+0x1C` | per class | per-frame update(arg, `[HUD+0x304]`), `ret 8` |
| `+0x24` | per class | init |

The rule, in the per-frame loop `0x10B70EF0` and in the loops `0x10B70C20` and `0x10B72EC0`:

```
shown = HUD.mode == 7  or  widget.test(7)  or  widget.test(HUD.mode)
shown      -> 0x10B74770 (show the sub-items), then the widget's update
not shown  -> 0x10B747E0 (hide the sub-items), no update
```

### HUD modes

| Mode | Meaning | Set at |
| --- | --- | --- |
| 0 | nothing; set first by every camera of the binocular family | `0x10DE2410` |
| 1 | normal play | `0x10BD0439` (where the HUD gets its owner), `0x109B78E2` (the kill cam's stop), `0x10BAEDEE`, `0x10BD82CD` (unless the mode is 6) |
| 2 | sticky camera view | `0x10D93E70` |
| 3 | drone view | `0x10DE8CF0` |
| 4 | kill cam | `0x109B7730` |
| 5 | spectating, by the texts its widget loads | `0x10BAED93` (local player only: `[Level+0x7BC]` is the controller) |
| 6 | end of game | `0x10BD8BAD` (`ClientDisplayEndOfGameHud`) |
| 7 | every widget shown | tested by the loops; bit 7 on a widget means "always shown" |
| 8 | spy binocular view | `0x10DFB6B0` |
| 9 | merc scope view | `0x10DFBB50` |
| 10 | switched on and off inside the player input routine `0x10BDA840` | `0x10BDB680` sets it; `0x10BDB674` sets the mode stored in `HUD+0x405` |
| 11 | briefing drone camera | `0x10DA4760` |
| 13 | the widget the HUD ctor builds itself | `0x10B7EDD5` |
| 14 | game mode 3 (`GameReplicationInfo.GameMode == 3`) | `0x10B72F60`, in `AHUD::execResetHud` |

The mode setter `0x10B729F0` does not take every request: when the current mode is 5 to 14 it follows the jump table at `0x10B72AC0`, which lets only some requests through, and when `[0x110097C8 + 4 * requested mode]` is not 0 it stores the current mode in `HUD+0x405` and sets mode 0.

### The remote cameras and their HUD mode

Every remote camera class stores the HUD's mode in `cam+0x4E8` in its start virtual (vtable `+0x4E0`), sets its own mode, and restores the stored one in its stop virtual (`+0x4E4`).

| Class | Vtable | Start `+0x4E0` | Stop `+0x4E4` | Per-frame input `+0x4AC` | HUD mode |
| --- | --- | --- | --- | --- | --- |
| `StickyCam` | `0x10F9F0B0` | `0x10D93E70` | `0x10D93B20` | `0x10D94000` | 2 |
| `Drone` | `0x10F62A08` | `0x10DE8CF0` | `0x10DE8C70` | `0x10DE9180` | 3 |
| `KillCam` | `0x10F8E360` | `0x109B7730` | `0x109B7830` (sets mode 1, not the stored one) | `0x109B6D50` | 4 |
| `BinocularRemoteCam` | `0x10F656B0` | `0x10DE2410` | `0x10DE1FA0` | `0x10DE2010` | 0 |
| `BinocularSpyRemoteCam` | `0x10F64040` | `0x10DFB6B0` | `0x10DFB5B0` | `0x10DFB610` | 0, then 8 |
| `BinocularMercRemoteCam` | `0x10F6AF78` | `0x10DFBB50` | `0x10DFBA80` | `0x10DFBAE0` (calls `0x10DE2010` first) | 0, then 9 |
| `MotherDroneCam` | `0x10F746A8` | `0x10DA4760` | `0x109BA280` | `0x10CC2840` | 11 |

- The vtable of a class is the one its registration stores next to the class global, for `Drone` at `0x10E06F19`, for `BinocularRemoteCam` at `0x10E076CE`.
- `0x10DE2010` stands in the vtable of `BinocularRemoteCam`, and `BinocularMercRemoteCam`'s own input routine calls it first. The `Drone` vtable holds `0x10DE9180` in that slot. [Pawns, controllers and damage](../../SCDA-Documentation-main/engine/pawns-controllers-and-damage.md) and [executable addresses](../../SCDA-Documentation-main/engine/exe-addresses-and-patches.md) name `0x10DE2010` "the drone's implementation"; by the vtables it is the binocular's. To be checked before either file is changed.
- The merc scope's start writes the camera's `Owner` (`cam+0x2FC`) into `GetWidget(0x15)+0xF4` (`0x10DFBB7D`..`0x10DFBB8D`), and its per-frame routine writes `(1 - ([cam+0x534] - [cam+0x528]) / ([cam+0x52C] - [cam+0x528])) * 0.9` into `GetWidget(0x15)+0xF8` (`0x10DFBAF8`..`0x10DFBB3A`). The drone's start writes the drone into `GetWidget(0x16)+0x4C` (`0x10DE8D09`..`0x10DE8D13`). The spy binocular writes `GetWidget(0x15)+0xD8`..`+0xE4` (`0x10DFB628`..`0x10DFB69D`, `0x10DFB6EE`).

### The widgets of the versus HUD

In the order the builder adds them. The index is the order plus three: see the last row.

| Order | Size | Vtable | Ctor | Modes | Loads |
| --- | --- | --- | --- | --- | --- |
| 0 | `0x54` | `0x10F93108` | inline | 1, 10 | nothing of its own |
| 1 merc / spy | `0x68` / `0x58` | `0x10F92F14` / `0x10F934C8` | inline | 1 | - / `HUD_goggle_total` |
| 2 | `0x98` | `0x10F93054` | `0x10B7FFC0` | 1, 2, 3, 8, 9 | `HUD_inter_bouton`, the button icons `B_A`.. |
| 3 | `0x50` | `0x10F93270` | inline | 1 | nothing of its own |
| 4 | `0xA0` | `0x10F932AC` | `0x10B89140` | 4 | `killc_bord`, `KillC_video` |
| 5 | `0x84` | `0x10F92F50` | `0x10B7DA70` | 6 | `Win_MultiMovie` |
| 6 | `0x9C` | `0x10F9348C` | `0x10B98310` | 5 | `HUD_INTERACTION_SPEC_MOD_*` |
| 7 | `0x74` | `0x10F930CC` | `0x10B83920` | 1 | `Play_HUD_SpyUf_Time_30sec`, `UH_Merc_Helmet` |
| 8 | `0x70` | `0x10F935F4` | `0x10B9D720` | 1 | `UH_ZoneName` |
| 9 | `0x7C` | `0x10F93144` | `0x10B844D0` | 1 | `UH_Score_Versus` (versus; a challenge builds another class here) |
| 10 | `0x11C` | `0x10F92E50` | `0x10B76920` | 1 | `UH_Spy_01`.., `Mat_UH_Hacking_Bords` |
| 11 | `0x64` | `0x10F92FDC` | `0x10B7F410` | 1 | `UH_Gadget` |
| 12 | `0xCC` | `0x10F9339C` | `0x10B942F0` | 1, 8 | `NM_RA_Obj01`.., `NM_RA_ECC`, `NM_RA_DropZone` |
| 13 | `0x25C` | `0x10F93324` | `0x10B8BAD0` | 1, 10 | nothing found |
| 14 | `0x68` | `0x10F92C80` | inline | 12 | `HUD_INTERACTION_QUIT_SESSION`, `UH_4Zones_Left` |
| 15 | `0x14C` | `0x10F93090` | `0x10B81650` | 1, 11 | `UH_mess_*` |
| 16 | `0x54` | `0x10F93450` | inline | 1 | `HUD_INTERACTION_HOOK` |
| 17 | `0x54` | `0x10F93018` | inline | 1 | `HUD_INTERACTION_RELOADGADGET` |
| merc 18 | `0x108` | `0x10F93414` | `0x10B95CC0` | 9 | `Hud_Snipe_Total`, `Hud_Snipe_Contour`, `HUD_MSGMERC_SNIPE_SHOOT` |
| merc 19 | `0x104` | `0x10F92ED8` | `0x10B7B5A0` | 3, 14 | `HUD_DRONE`, `HUD_GADGET_DRONE_STATUS_1`.. |
| merc 20 | `0x68` | `0x10F933D8` | `0x10B954E0` | 1 | `NH_Merc_ReticleDisp` |
| merc 21 | `0x58` | `0x10F9357C` | inline | 1, 3 | `HUD_GAMEMESSAGE_SYSTEM_MALFUNCTION` |
| merc 22 | `0x70` | `0x10F935B8` | `0x10B9D090` | 1 | `NH_Merc_GrenadeDisp` |
| merc 23 | `0x74` | `0x10F92E9C` | `0x10B7B070` | 1 | `NH_Merc_Detection` |
| merc 24 | `0xE4` | `0x10F93540` | `0x10B9B920` | 2 | `Hud_Sticky_total` |
| spy 18 | `0xE8` | `0x10F92C44` | `0x10B74D90` | 8 | `Hud_Binoculars_General` |
| spy 19 | `0xE0` | `0x10F93504` | `0x10B9A1F0` | 1 | `NM_RA_Hack` |
| spy 20 | `0x90` | `0x10F932E8` | `0x10B8ABE0` | 1 | `UH_Life`, `LifeBar_Red` |
| before the builder | `0x6C`, `0x54` | `0x10F92FA0`, `0x10F93360` | HUD ctor, `0x10B6FA1E` and `0x10B6FA52` | 13; 7 | - ; `HUD_GAMEMESSAGE_MU_DATAS_LOST` |

- Index: the HUD ctor adds two widgets, which gives order + 2. The fixed-index writers only fit order + 3: `GetWidget(0x15)` is then the scope overlay on a merc (order 18, `0x108` bytes, written up to `+0xFB`) and the binocular overlay on a spy (order 18, `0xE8` bytes, written up to `+0xE7`; the spy's order 19 has `0xE0` bytes and would be overrun), `GetWidget(0x16)` is the drone overlay (order 19), and `GetWidget(8)`, where `ClientDisplayEndOfGameHud` writes `+0x6C`, is the end-of-game widget (order 5). A third widget added before the builder was not found in the exe. INFERRED until read from a running game.
- The team split of the builder tests the class chain of `[[HUD+0x400]+0x408]` (the owner's pawn) for `PawnMerc` `0x11044EC8`, at `0x10B71EE6` and `0x10B726F0`.
- Index: test runs 1 and 2 (v2 plugin, main build) read the live array: merc HUD 28 widgets, scope overlay 21, drone overlay 22, gun reticle 23; spy HUD 24 widgets, binocular overlay 21. The index is order + 3, as the fixed-index writers require.

### Draw order

A widget does not draw its meshes itself. Each sub-item (a `HudItemToDisplay` UObject, `widget+0x20` count, `+0x24` data) owns elements, and each element owns one or more actors. Every frame the per-frame loop empties two global actor lists and lets every shown widget append the actors of its visible sub-items; the HUD render then draws both lists, actor after actor, in list order. Texts are drawn afterwards on the canvas. The HUD's meshes are therefore painted in widget-array order, so a widget later in the array covers the widgets before it: the view overlays (scope 21, drone 22, sticky cam 27, spy binocular 21) cover the normal widgets (3..20).

| Field | Offset | Notes |
| --- | --- | --- |
| list E0 | `0x110415E0` max, `0x110415E4` num, `0x110415E8` data | TArray of actor pointers; camera-space items; drawn with the HUD FOV |
| list EC | `0x110415EC` max, `0x110415F0` num, `0x110415F4` data | items whose element has `+0x68` set; drawn with the player's FOV, before E0 |
| HUD FOV | `HUD+0x41C` | float, computed from the screen aspect in `0x10B70CB0`; swapped into `[[viewport+0x58]+0x458]` for the E0 draw |
| HUD camera node | `HUD+0x428` | created every frame by `0x10B70D40` (from the per-frame loop), deleted by `0x10A15024`; the render runs only while it is set |
| sub-item visible | `item+0x80` | only visible sub-items are appended |
| element list choice | `element+0x68` | set: EC, clear: E0 (`0x10BA1BF6`) |
| actor hidden | `actor+0x314` bit `0x400` | skipped by the list draw (`0x10A50BB6`) |
| viewport render interface | `viewport+0x128` | `FRenderInterface`; vtable `+0x10` = `Clear(UseColor, Color, UseDepth, Depth, UseStencil, Stencil)`, `ret 0x18` (`0x10907E10` in the D3D device) |
| viewport HUD | `viewport+0x68` | the HUD the render uses |

| Routine | Address | Does |
| --- | --- | --- |
| per-frame loop | `0x10B70EF0` (edi = HUD) | `0x10B70F0C` / `0x10B70F12` set both list counts to 0; then for each widget in array order (esi = index, ebp = widget): test(7) `call [edx+0Ch]` at `0x10B71009`, test(mode) `call [eax+0Ch]` at `0x10B7101C`; shown: `0x10B74770` then update `call [eax+1Ch]` at `0x10B71045` |
| list append | `0x10B73D00` | called at the end of every widget update (44 callers); hands each visible sub-item with E0 and EC to `0x10BA1BB0`, which calls each element's vt+0x6C with the list it belongs to |
| registration | `0x10B73CB0` (widget vt+0x10) | appends once at init through `0x10BA1900`; the next per-frame loop empties the lists again |
| HUD render | `0x10B70E30` | called once, from `0x10A5057F` in `0x10A50050` (ebx = viewport, argument = the HUD); canvas texts of `HUD+0x43C` (22) and `HUD+0x44C` (3), then `render(EC, 0)`, then `render(E0, 1)` with the HUD FOV, at `0x10B70E98`..`0x10B70EDC` |
| list render | `0x109F7250` (esi = viewport, args list and flag, `ret 8`) | builds a camera scene node from the viewport actor's location, rotation and FOV (flag 0: the remote camera as view actor; flag 1: the player controller), stores the list in `node+0x1EC`, calls `0x10A50B20` |
| actor list draw | `0x10A50B20` | for each actor in list order: skip if hidden, gather lights, draw (`0x10A4E010`); no sorting |
| canvas texts | `0x10B70C20` -> widget vt+0x2C `0x10B73F10` -> item vt+0x68 (`0x10BA1CD0` for `HudItemToDisplay_InCamera`) | element type 6 drawn with the canvas, after both lists |
| pre-HUD clear | `0x10A5024C` in `0x10A50050` | `RI->Clear(0, 0, 1, 1.0, 1, 0)`: depth and stencil, after the world and before the fade overlay and the HUD |

- Whether the HUD materials (the ModernMaterial family) write or test depth was not determined.
- A plugin that wants widgets on top of an overlay can draw the lists in two parts: the widgets the stock rule shows (the overlay among them), the engine's pre-HUD clear again, then the rest. `QolHud.asi` v3 does this by recording, in the widget mode test, where each widget's run starts in both lists (the per-frame loop's return addresses `0x10B7100C` / `0x10B7101F` identify the calls), and by drawing from its own copies at `0x10B70E98`.

### Citations

[1] `SCDA_Online.exe` (PC Community Edition main build, md5 0f1b2d1c), disassembly of the HUD routines `0x10B6F690`..`0x10B9F460`, the remote camera routines `0x10DE1F60`..`0x10DE9180` and `0x10DFB5B0`..`0x10DFBBD0`, the widget vtables `0x10F92C08`..`0x10F935F4`, and the class registration runs at `0x10E05C40`.

[2] `SCDA_Online.exe` (md5 0f1b2d1c and d94c9137, byte-identical in every range below), disassembly of the scene render `0x10A50050`..`0x10A50719`, the list render `0x109F7250`, the actor list draw `0x10A50B20`, the HUD item routines `0x10BA1900`..`0x10BA2140`, the `HudItemToDisplay_InCamera` vtable `0x10F7C428` and the D3D render interface vtable `0x10F5B4B8`; the real per-frame loop and HUD render run on fake widgets in an x86 harness (`build\harness`).

[3] `SCDA_Online.exe` in game (v2 plugin, main build), test runs 1 and 2 of 2026-09-29: the live widget array read with `test\hud-state.ps1`.

## For `engine/exe-addresses-and-patches.md`

| Address | Size | What | Notes |
| --- | --- | --- | --- |
| `0x10B73C90` | 25 | the widget mode test | `mov edx,ecx / mov cl,[esp+4] / mov eax,1 / shl eax,cl / and eax,[edx+0x34] / neg / sbb / neg / ret 4`; referenced from 41 vtable slots, from nowhere in `.text` |
| `0x10B729F0` | - | the HUD mode setter | HUD vtable `+0x444` |
| `0x10B70EF0` | - | the HUD per-frame loop | called with `edi` = the HUD |
| `0x1100FEFC` | 1 | last HUD mode that was not 0 | written by the mode setter |
| `0x110097C8` | 4 x n | table of dwords indexed by the requested HUD mode | a non-zero entry turns a request for that mode into mode 0 |
| `0x110415E0` | 12 | HUD actor list E0, TArray {max, num, data} | camera-space HUD items; emptied and refilled every frame by `0x10B70EF0` |
| `0x110415EC` | 12 | HUD actor list EC, TArray {max, num, data} | HUD items drawn with the player's FOV |
| `0x10B70E30` | - | the HUD render | draws EC then E0 at `0x10B70E98`..`0x10B70EDC`; one caller `0x10A5057F` (ebx = viewport) |
| `0x109F7250` | - | render(list, flag), esi = viewport, `ret 8` | the two calls of the HUD render are its only callers |
| `0x10B73D00` | - | append a widget's visible sub-items to E0 / EC | ends every widget update |
| `0x10A5024C` | - | the pre-HUD `RI->Clear(0,0,1,1.0,1,0)` | depth and stencil |

Byte patches (in memory, by `QolHud.asi` v3): `0x10B73C90`, 6 bytes `8B D1 8A 4C 24 04` -> `E9 <rel32> 90`, stub of 380 bytes that answers the mode test itself and records the per-frame loop's list positions; `0x10B70E98`, 7 bytes `6A 00 68 EC 15 04 11` -> `E9 <rel32> 90 90`, stub of 887 bytes that draws the lists stock or split.

## For `tools/plugins-and-instruments.md`

| Plugin | Base | Sites | Does |
| --- | --- | --- | --- |
| `QolHud.asi` v3 | `0x6E700000` | `0x10B73C90` (6 B), `0x10B70E98` (7 B) | keeps the normal-play HUD widgets shown in the drone view and the merc scope view, drawn on top of the view's overlay; log `System\QolHud.log` |

- A hook on a routine that is reached only through vtables can replace the whole routine and never return into it; the stolen bytes then need no replay and no resume address.
- A stub can tell its callers apart by the return address on its stack when the routine is reached only through vtables and each call site is known (the widget mode test: `0x10B7100C` / `0x10B7101F` are the per-frame loop's two calls).
- A plugin that is loaded at a relocatable base and carries no fixups reaches game addresses by `mov eax,imm / call eax` and `push imm / ret`, never by rel32.
