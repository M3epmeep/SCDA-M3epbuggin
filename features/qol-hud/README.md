# qol-hud

The normal HUD (timer, zone name, score, gadgets, radar objects, messages, status displays) stays on screen while a merc looks through the drone or through the scope, drawn on top of that view's own overlay instead of vanishing or being covered until the view is left.

One file does it, and it patches nothing on disk:

| Piece | File | md5 | Installs to |
| --- | --- | --- | --- |
| plugin v3 | `QolHud.asi` (20,992 B), same file in `files\System\` and `build\QolHud.v3.asi` | `722365f7ef26110042b4d72615a2c4ae` | `System\QolHud.asi` (new, or replaces v2) |
| ini section (optional, not written by default) | written by `patch.ps1 -Settings "..."` only | - | appended to `System\Enhanced.ini` |

- Built and gated against the main branch exe `SCDA_Online.exe` md5 `0f1b2d1ce8167d267ee15d5a4ed4c3e6` and against the previous main build `d94c9137340f3996b5bc9ec361340d1e`; every byte the plugin checks or relies on is identical in both. The plugin never checks the exe's md5. It checks the bytes of what it takes over (25 at `0x10B73C90`, 75 at `0x10B70E98`, 112 at `0x10B70FE3`), installs nothing on a mismatch at the first, installs without the on-top part on a mismatch at the other two, and says so in `System\QolHud.log`.
- No `.u` package and no exe file changes. The Ultimate ASI Loader (`System\dinput8.dll`, shipped with CE) loads the plugin at start.
- **Which machine needs it:** the machine of the player who wants it. The HUD is drawn on the player's own machine; the plugin writes no game state and nothing that is replicated (only its own memory and, during a draw call, the same FOV swap the game makes itself). Players with and without it can share a match.
- "Sniper" is read as the merc's scope: the view of `BinocularMercRemoteCam`, whose HUD overlay is the game's `Hud_Snipe_Total` mesh.
- History: v1 (`build\QolHud.v1.asi`, `70c5e23e365504b985df2ca763b7ed15`) kept the gun reticle; v2 (`build\QolHud.v2.asi`, `2df8cf2022d0134e410363807b128e94`) left it out unless `Reticle=1` and passed two in-game runs, but the kept widgets were drawn under the overlay (the scope mask darkened the zone name, radar and top-right score; the drone frame covered them). v3 draws them on top (operator's order of 2026-09-29). **v3 has not run in the game.**

# Change log (rule 8)

| # | File | Site | Stock content | New content |
| --- | --- | --- | --- | --- |
| 1 | `System\QolHud.asi` | new file | - | the plugin, md5 `722365f7ef26110042b4d72615a2c4ae` |
| 2 | `SCDA_Online.exe`, **in memory at load** | VA `0x10B73C90` (file `0x273C90`), 6 bytes, the start of the widget mode test (vtable slot `+0x0C` of all 41 HUD widget classes) | `8B D1` mov edx,ecx / `8A 4C 24 04` mov cl,[esp+4] | `E9 <rel32>` jmp stub A, then 1 x `90`. Stub A (380 bytes, below) is the whole routine again plus the v3 record, and never returns into the stock one; the stock bytes `0x10B73C96`..`0x10B73CA8` stay in place and become unreachable |
| 3 | `SCDA_Online.exe`, **in memory at load**, only with `OnTop=1` and only after row 2 | VA `0x10B70E98` (file `0x270E98`), 7 bytes, the start of the two HUD list draws in `0x10B70E30` | `6A 00` push 0 / `68 EC 15 04 11` push 0x110415EC | `E9 <rel32>` jmp stub B, then 2 x `90`. Written only when the 75 bytes `0x10B70E98..0x10B70EE2` and the 112 bytes `0x10B70FE3..0x10B71052` (the per-frame HUD loop body) are the stock ones. Stub B (887 bytes) either runs the two stolen pushes and returns to `0x10B70E9F` (stock draw) or draws the split and returns to `0x10B70EDD` |
| 4 | `System\QolHud.log` | new, rewritten on every start | - | one line: `QolHud 3: installed at 0x10B73C90, Drone=1 Sniper=1 Binocular=0 StickyCam=0 Reticle=0 OnTop=1 DroneHide=0x0000000000000000 ... StickyCamUnder=0x0000000000000000; on top: installed at 0x10B70E98`, or `...; on top: off (OnTop=0), 0x10B70E98 untouched`, or `...; on top: REFUSED - ...`, or `... disabled ...`, `... no view is switched on ...`, `... REFUSED ...` with the reason |
| 5 (optional) | `System\Enhanced.ini` | end of file, only when asked for | - | `[QOLHUD]` and the keys of the table "Settings". Without the section the plugin runs on its defaults |

The stock routine at `0x10B73C90` (thiscall, `ecx` = widget, one stack argument = the mode, `ret 4`, answer in `eax`):

```
8B D1              mov  edx, ecx
8A 4C 24 04        mov  cl, [esp+4]
B8 01 00 00 00     mov  eax, 1
D3 E0              shl  eax, cl
23 42 34           and  eax, [edx+0x34]        ; the widget's mode mask
F7 D8 / 1B C0 / F7 D8   neg eax / sbb eax,eax / neg eax     ; 0 or 1
C2 04 00           ret  4
```

The stock render tail at `0x10B70E98` (inside `0x10B70E30`; `ebx` = viewport, `ebp` = HUD, `esi`/`edi` saved by the function):

```
6A 00 / 68 EC150411          push 0 / push 0x110415EC        ; EC list, player's FOV     <- the 7 stolen bytes
8B F3 / E8 ->0x109F7250      mov esi,ebx / call render(list, flag)
8B 7B 58                     mov edi,[ebx+0x58]              ; the viewport's actor
F3 0F 10 87 58040000         movss xmm0,[edi+0x458]          ; its FOV
8B 85 1C040000               mov eax,[ebp+0x41C]             ; the HUD FOV
6A 01 / 68 E0150411          push 1 / push 0x110415E0        ; E0 list, HUD FOV
F3 0F 11 44 24 18            movss [esp+0x18],xmm0           ; FOV saved
89 87 58040000               mov [edi+0x458],eax
E8 ->0x109F7250              call render(list, flag)
F3 0F 10 44 24 10 / F3 0F 11 87 58040000   FOV restored
5F 5E 5D C2 0400             pop edi / pop esi / pop ebp / ret 4      <- 0x10B70EDD, stub B's split exit
```

Stub A, as built (preferred base `0x6E700000`, RVA `0x10F5`). `[edx+..]` / `[esi+..]` are the plugin's own data (image base found by call/pop): `+0x2008` enabled views, `+0x2040` Reticle, `+0x2048` views with on-top live, `+0x2058` / `+0x205C` / `+0x2060` / `+0x2070` the record (HUD, mode, widgets recorded, lifted mask), `+0x2080 + 8*mode` hide lists, `+0x2520 + 8*mode` under lists, `+0x3000` / `+0x3100` per-widget list counts:

```
cmp  dword [esp], 0x10B7100C         ; called by the per-frame loop's test(7)?  (return address)
jne  test
call $+5 / pop edx / sub edx, 0x1103 ; edx = image base
cmp  dword [edx+0x2048], 0 / je test ; on top not live: no record
cmp  esi, 64 / jae test              ; esi = the caller's loop index
test esi, esi / jnz next
mov  [edx+0x2058], edi               ; widget 0: new record; edi = the loop's HUD
movzx eax, byte [edi+0x404] / mov [edx+0x205C], eax
xor  eax, eax / mov [edx+0x2070], eax / mov [edx+0x2074], eax / mov [edx+0x2060], eax
next:
cmp  [edx+0x2058], edi / jne test    ; same HUD
cmp  [edx+0x2060], esi / jne test    ; the next index in order
mov  eax, [0x110415E4] / mov [edx+esi*4+0x3000], eax   ; E0 count before this widget's update
mov  eax, [0x110415F0] / mov [edx+esi*4+0x3100], eax   ; EC count
lea  eax, [esi+1] / mov [edx+0x2060], eax
test:                                ; ---- the v2 mode test ----
mov  edx, ecx / movzx ecx, byte [esp+4] / mov eax, 1 / shl eax, cl
test [edx+0x34], eax / jne yes       ; stock "shown"
push esi / call $+5 / pop esi / sub esi, 0x1191     ; esi = image base
test [esi+0x2008], eax / je no       ; an enabled view?
test byte [edx+0x34], 2 / je no      ; a normal-play widget?
cmp  ecx, 15 / ja no
cmp  dword [edx], 0x10F933D8 / jne notReticle / cmp dword [esi+0x2040], 0 / je no
notReticle:
push edi / lea edi, [esi+ecx*8+0x2080] / mov eax,[edi] / or eax,[edi+4] / je lift   ; empty hide list
mov  eax, [0x1100FF00] / test eax,eax / je lift                                      ; the current HUD
mov  edi, [eax+0x3F8] / mov eax, [eax+0x3FC] / test eax,eax / je lift
xor  ecx, ecx
find: cmp ecx,edi / jge lift / cmp ecx,64 / jae lift / cmp [eax+ecx*4],edx / je found / inc ecx / jmp find
found: movzx edi, byte [esp+0xC] / lea edi,[esi+edi*8+0x2080] / bt [edi],ecx / jb noPop2   ; on the hide list
lift:                                ; the plugin's own "shown" ---- v3 ----
cmp  dword [esp+8], 0x10B7101F / jne yesPop2   ; only the per-frame loop's test(mode)
mov  ecx, [esp+4] / cmp ecx, 64 / jae yesPop2  ; the caller's esi = index
mov  eax, [esp] / cmp eax, [esi+0x2058] / jne yesPop2        ; the caller's edi = the recorded HUD
lea  eax, [ecx+1] / cmp eax, [esi+0x2060] / jne yesPop2      ; the widget just recorded
movzx eax, byte [esp+0xC]
bt   [esi+0x2048], eax / jae yesPop2                         ; on top live in this view
bt   [esi+eax*8+0x2520], ecx / jb yesPop2                    ; on the view's under list
bts  [esi+0x2070], ecx                                       ; lifted
yesPop2: pop edi / pop esi
yes:  mov eax, 1 / ret 4
noPop2: pop edi
no:   pop esi / xor eax, eax / ret 4
```

Stub B (RVA `0x1271`; `edi` = image base; the exact bytes of both stubs are printed in `build\gates\build_v3.txt`):

```
call $+5 / pop edi / sub edi, 0x1276
mov eax,[edi+0x2070] / or eax,[edi+0x2074] / je stock           ; nothing lifted in the last loop
cmp [edi+0x2058], ebp / jne fallback                              ; the loop ran for this HUD
movzx eax, byte [ebp+0x404] / cmp eax,[edi+0x205C] / jne fallback ; in this mode
mov ecx,[edi+0x2060] / test ecx,ecx / je fallback / cmp ecx,64 / ja fallback
cmp ecx,[ebp+0x3F8] / jne fallback                                ; every widget recorded
partition EC (count [0x110415F0], data [0x110415F4]) into the buffer at +0x3200:
    count <= 1024, first start 0, every run start <= end <= count, else fallback;
    runs of widgets not in the lifted mask first, then the lifted runs; headers {n,n,ptr} at +0x25A0 (base) / +0x25B8 (lifted)
partition E0 (count [0x110415E4], data [0x110415E8]) into +0x4200, headers at +0x25AC / +0x25C4, the same checks
push 0 / push base+0x25A0 / mov esi,ebx / mov eax,0x109F7250 / call eax                ; EC base, player's FOV
mov edx,[ebx+0x58] / push [edx+0x458] / mov eax,[ebp+0x41C] / mov [edx+0x458],eax   ; HUD FOV in
push 1 / push base+0x25AC / mov esi,ebx / mov eax,0x109F7250 / call eax                ; E0 base: overlay and stock-shown widgets
mov edx,[ebx+0x58] / pop [edx+0x458]                                                    ; FOV back
mov ecx,[ebx+0x128] / test ecx,ecx / je noClear
mov eax,[ecx] / push 0 / push 1 / push 0x3F800000 / push 1 / push 0 / push 0 / call [eax+0x10]   ; RI->Clear(0,0,1,1.0,1,0)
noClear:
push 0 / push base+0x25B8 / ... call 0x109F7250                                         ; EC lifted
(HUD FOV in) push 1 / push base+0x25C4 / ... call 0x109F7250 / (FOV back)               ; E0 lifted, on top
inc dword [edi+0x2050] / push 0x10B70EDD / ret                                           ; split exit
fallback: inc dword [edi+0x2054]
stock:    push 0 / push 0x110415EC / push 0x10B70E9F / ret                               ; the stolen bytes, back to stock
```

To apply this by hand without the plugin, both stubs have to be written into a free exe code cave with the plugin's data as absolute addresses, and both sites pointed at them. That route was not built.

# Mechanism in the stock game

Everything below is read from the exe (static). The HUD is one object per local player, vtable `0x10F81BC0`, reached as `PlayerController+0x95C`; the last HUD that added a widget also stands in the global `0x1100FF00`.

| Piece | Where | Fact |
| --- | --- | --- |
| widget array | `HUD+0x3F4` max, `+0x3F8` count, `+0x3FC` data | filled only through `AddWidget` `0x10B72C60` (HUD vtable `+0x448`) |
| HUD mode | `HUD+0x404` (byte); `+0x405` the mode before; `+0x406` the mode of the last frame | set through HUD vtable `+0x444` = `0x10B729F0` |
| widget mode mask | `widget+0x34` (dword) | bit n set = the widget is shown in mode n; written by the widget's ctor (`or [esi+0x34], imm`) |
| mask helpers | widget vtable `+0x04` `0x10B73C60` clear, `+0x08` `0x10B73C70` set bit n, `+0x0C` `0x10B73C90` test bit n | the same three routines in all 41 widget vtables (`0x10F92C08`..`0x10F935F4`) |
| the rule | per-frame loop `0x10B70EF0`, and the loops `0x10B70C20` and `0x10B72EC0` | `shown = HUD.mode == 7 or widget.test(7) or widget.test(HUD.mode)`; a widget that is not shown is hidden by `0x10B747E0` and its update is not called |
| callers of the test | none direct | `0x10B73C90` is referenced from the 41 vtable slots and from nowhere in `.text` |

## How the HUD is drawn, and why the overlay covered the kept widgets (v3)

| Piece | Where | Fact |
| --- | --- | --- |
| HUD meshes are actors in two lists | E0 `0x110415E0`, EC `0x110415EC`, each a TArray `{max, num, data}` | E0: camera-space items, drawn with the HUD FOV `HUD+0x41C`; EC: items whose element has `+0x68` set, drawn with the player's FOV |
| the lists are rebuilt every frame | per-frame loop `0x10B70EF0` | `0x10B70F0C` / `0x10B70F12` set both counts to 0; then, in widget-array order, every shown widget's update (+0x1C; all 44 update routines end in `0x10B73D00`) appends the actors of its visible sub-items (`+0x80` set) through `0x10BA1BB0` -> element vt+0x6C. So the list order is the widget-array order |
| the loop's registers | `0x10B70FE3`..`0x10B71052` | `esi` = widget index, `edi` = HUD, `ebp` = widget; test(7) is `call [edx+0Ch]` at `0x10B71009` (returns to `0x10B7100C`), test(mode) `call [eax+0Ch]` at `0x10B7101C` (returns to `0x10B7101F`), the update `call [eax+1Ch]` at `0x10B71045` |
| the lists are drawn in list order | `0x10B70E30` (called once, from `0x10A5057F`, `ebx` = viewport), `0x10B70E98`..`0x10B70EDC` | `render(EC, 0)` then `render(E0, 1)` with the HUD FOV swapped into `[[viewport+0x58]+0x458]`; `render` = `0x109F7250` builds a camera scene node and hands the list to `0x10A50B20`, which draws every actor not hidden (`actor+0x314` bit `0x400`) one after the other in list order |
| texts come last | `0x10B70C20` -> widget +0x2C `0x10B73F10` -> item vt+0x68 `0x10BA1CD0` | element type 6 (text) is drawn on the canvas after both lists, so HUD texts are never covered |
| depth before the HUD | `0x10A5024C` in `0x10A50050` | `RI->Clear(0, 0, 1, 1.0, 1, 0)` (depth and stencil) on `RI = [viewport+0x128]`, vtable `+0x10` (`0x10907E10` builds the D3D clear flags) |
| why the overlay won | widget array | the overlays (scope 21 `Hud_Snipe_Total`, drone 22 `HUD_DRONE`, sticky 27, spy binocular 21) sit after the normal widgets (3..20), so their actors are appended later and drawn over them. The scope mask darkens what is under it, the drone frame covers it |
| whether HUD materials write depth | - | not determined; v3 does not depend on it (it clears depth before the lifted part, as the engine does before the whole HUD) |

The modes, by who sets them:

| Mode | Set by | Site |
| --- | --- | --- |
| 0 | nothing shown; every remote camera of the binocular family sets 0 first | `0x10DE2410` (`BinocularRemoteCam` start) |
| 1 | normal play | `0x10BD0439` (where the HUD gets its owner), the kill cam's stop `0x109B78E2`, and others |
| 2 | `StickyCam` start virtual `+0x4E0` | `0x10D93E70`; stop `0x10D93B20` restores |
| 3 | `Drone` start virtual | `0x10DE8CF0`; stop `0x10DE8C70` restores the mode saved in `cam+0x4E8` |
| 4 | `KillCam` start | `0x109B7730` |
| 5 | spectating, by the texts its widget loads | `0x10BAED93` |
| 6 | end of game (`ClientDisplayEndOfGameHud`) | `0x10BD8BAD` |
| 7 | every widget shown | tested by the three loops |
| 8 | `BinocularSpyRemoteCam` start | `0x10DFB6B0`; stop `0x10DFB5B0` |
| 9 | `BinocularMercRemoteCam` start: the merc's scope | `0x10DFBB50`; stop `0x10DFBA80` |
| 10 | switched on and off inside the player input routine `0x10BDA840` | `0x10BDB680`, `0x10BDB674` |
| 11 | `MotherDroneCam` start (the briefing) | `0x10DA4760` |
| 12 | the mode of the quit session dialog widget | the call that sets it was not located; the setter handles it at `0x10B72A1F` and `0x10B72A8F` |
| 13 | the mode of the widget the HUD builds itself | `0x10B7EDD5` |
| 14 | set by `ResetHud` when `GameReplicationInfo.GameMode` is 3; the drone overlay carries it too | `0x10B72F60` |

The widgets of the versus HUD, in array order (live index as `test\hud-state.ps1` printed it in test runs 1 and 2). The names come from the meshes, materials and texts each widget's own code loads (`build\re\widget_names.txt`).

| Index | Size | Vtable | Stock modes | What | Drone / scope view with the plugin (defaults) |
| --- | --- | --- | --- | --- | --- |
| 0..2 | `0x6C`, `0x54`, ? | `0x10F92FA0`, `0x10F93360`, ? | 13; 7 (always); ? | built by the HUD itself; system message; one not found | unchanged |
| 3 | `0x54` | `0x10F93108` | 1, 10 | root | shown, on top |
| 4 | merc `0x68` / spy `0x58` | `0x10F92F14` / `0x10F934C8` | 1 | merc frame / spy goggle frame (`HUD_goggle_total`) | shown, on top |
| 5 | `0x98` | `0x10F93054` | 1, 2, 3, 8, 9 | interaction prompts and button icons | shown by the stock game already; stays in its stock place (under the overlay) |
| 6 | `0x50` | `0x10F93270` | 1 | not named (loads nothing of its own) | shown, on top |
| 7 | `0xA0` | `0x10F932AC` | 4 | kill cam | unchanged |
| 8 | `0x84` | `0x10F92F50` | 6 | end of game | unchanged |
| 9 | `0x9C` | `0x10F9348C` | 5 | spectating | unchanged |
| 10 | `0x74` | `0x10F930CC` | 1 | round timer (`Play_HUD_SpyUf_Time_30sec`, `UH_Merc_Helmet`) | shown, on top |
| 11 | `0x70` | `0x10F935F4` | 1 | zone name (`UH_ZoneName`) | shown, on top |
| 12 | `0x7C` | `0x10F93144` | 1 | score, top right (`UH_Score_Versus`) | shown, on top |
| 13 | `0x11C` | `0x10F92E50` | 1 | spy status and hacking panel (`UH_Spy_01`.., `Mat_UH_Hacking_Bords`) | shown, on top |
| 14 | `0x64` | `0x10F92FDC` | 1 | gadget strip (`UH_Gadget`) | shown, on top |
| 15 | `0xCC` | `0x10F9339C` | 1, 8 | radar objects (`NM_RA_Obj01`.., `NM_RA_ECC`, `NM_RA_DropZone`) | shown, on top |
| 16 | `0x25C` | `0x10F93324` | 1, 10 | not named | shown, on top |
| 17 | `0x68` | `0x10F92C80` | 12 | quit session dialog | unchanged |
| 18 | `0x14C` | `0x10F93090` | 1, 11 | messages (`UH_mess_*`) | shown, on top |
| 19 | `0x54` | `0x10F93450` | 1 | hook prompt | shown, on top |
| 20 | `0x54` | `0x10F93018` | 1 | reload gadget prompt | shown, on top |
| merc 21 | `0x108` | `0x10F93414` | 9 | **scope overlay** (`Hud_Snipe_Total`, `Hud_Snipe_Contour`) | unchanged, drawn first |
| merc 22 | `0x104` | `0x10F92ED8` | 3, 14 | **drone overlay** (`HUD_DRONE`) | unchanged, drawn first |
| merc 23 | `0x68` | `0x10F933D8` | 1 | **merc gun reticle** (`NH_Merc_ReticleDisp`) | hidden unless `Reticle=1` (then on top) |
| merc 24 | `0x58` | `0x10F9357C` | 1, 3 | system malfunction message | shown; in the drone view stock-shown, stays after the overlay |
| merc 25 | `0x70` | `0x10F935B8` | 1 | merc grenade display (`NH_Merc_GrenadeDisp`) | shown, on top |
| merc 26 | `0x74` | `0x10F92E9C` | 1 | merc detection display (`NH_Merc_Detection`) | shown, on top |
| merc 27 | `0xE4` | `0x10F93540` | 2 | sticky cam overlay (`Hud_Sticky_total`) | unchanged |
| spy 21 | `0xE8` | `0x10F92C44` | 8 | spy binocular overlay (`Hud_Binoculars_General`) | unchanged |
| spy 22 | `0xE0` | `0x10F93504` | 1 | hack display (`NM_RA_Hack`) | shown with `Binocular=1` / `StickyCam=1` |
| spy 23 | `0x90` | `0x10F932E8` | 1 | spy life bar (`UH_Life`) | shown with `Binocular=1` / `StickyCam=1` |

- Index 12 is the versus score; in a challenge the builder puts another score widget in the same place (`0x10B7219D`, jump table on the challenge type).
- "On top" means: drawn after the view's overlay and after a depth clear, in its own array order. A widget the stock game already shows in the view (the prompts 5, the malfunction message 24 in the drone view, the always-shown system message 1) keeps its stock place.

# Settings

`System\Enhanced.ini`, section `[QOLHUD]`, read once at game start. Every key is optional.

| Key | Default | Meaning |
| --- | --- | --- |
| `Enabled` | 1 | 0 installs nothing |
| `Drone` | 1 | the normal HUD stays on in the merc's drone view (HUD mode 3) |
| `Sniper` | 1 | the normal HUD stays on in the merc's scope view (HUD mode 9) |
| `Binocular` | 0 | the same for the spy's binoculars (HUD mode 8) |
| `StickyCam` | 0 | the same for the sticky camera view (HUD mode 2) |
| `Reticle` | 0 | 1 also keeps the merc's gun reticle; 0 leaves the view's own aiming mark alone |
| `OnTop` | 1 | 1 draws the kept widgets on top of the view's overlay (site `0x10B70E98` installed); 0 is the v2 behaviour exactly (the site is not touched, nothing is recorded) |
| `DroneHide`, `SniperHide`, `BinocularHide`, `StickyCamHide` | empty | widget indices (0..63) that stay hidden in that view, separated by commas, for example `SniperHide=13,16`. A widget the stock game shows in that view cannot be hidden this way |
| `DroneUnder`, `SniperUnder`, `BinocularUnder`, `StickyCamUnder` | empty | widget indices (0..63) that stay shown in that view but are drawn in their stock place, under the overlay (v2 behaviour for that widget), for example `SniperUnder=15` |

- With `Drone`, `Sniper`, `Binocular` and `StickyCam` all 0 nothing is installed.
- Any value other than 0 counts as 1.

# Build

- Sources: `build\builder\QolHud.cs` (the plugin, assembled with Iced from C#), `build\builder\Program.cs` (builder and static gate), `build\builder\QolHudBuild.csproj` (net9.0, Iced 1.21.0). The v1 and v2 sources are beside them as `.v1` and `.v2`.
- Build: in `build\builder`, `dotnet build -c Release -o bin`, then `bin\QolHudBuild.exe <out.asi> [<SCDA_Online.exe>]`. With an exe the static gate runs. The build is deterministic.
- Harness: `build\harness` (x86), `dotnet build -c Release -o bin`, then `bin\QolHarness.exe <mode> <SCDA_Online.exe> <QolHud.asi>`.
- All gates at once: `build\gates\run_v3.ps1 -MainExe <copy of main's exe> -PrevExe <copy of the d94c9137 exe> -Out <scratch>` (writes `build_v3.txt`, `harness_v3.txt`); the patch dry run: `build\gates\dryrun_v3.ps1 -Scratch <empty scratch dir>` (writes `dryrun_v3.txt`).

# Proof without the game

| Gate | Result | Log |
| --- | --- | --- |
| static gate, main exe `0f1b2d1c` | ALL PASS, 65 checks | `build\gates\build_v3.txt` |
| static gate, previous main `d94c9137` | ALL PASS, 65 checks | same file |
| determinism | 5 builds, one md5 `722365f7...` | same file |
| harness, 16 modes on main's exe bytes and 16 on the previous build | 32 runs ALL PASS, 440 checks, 0 fail | `build\gates\harness_v3.txt` |
| `patch.ps1` dry run on a scratch copy of main's `System` (67 files) | ALL PASS, 18 checks: apply adds one file equal to the stack; revert leaves 0 differences (md5, size, date); apply with settings and revert returns `Enhanced.ini` to its md5; a v2 build is recognised, refused for apply, removed by revert; the main path is refused in 5 spellings and main is not written | `build\gates\dryrun_v3.txt` |

What the static gate shows, beyond v2's site A checks: the per-frame loop resets both lists and calls test(7) / test(mode) with the return addresses and registers the record relies on; every widget update ends in the list append `0x10B73D00`; the two lists are referenced in `.text` only by the render tail, the per-frame reset, the teardown, the registration, the append and the exit cleanup; `0x10B70E30` has one caller, which passes the viewport in `ebx`; `0x109F7250` is called only by the render tail, reads only the list's count itself and returns with `ret 8`; the engine's pre-HUD clear is `RI->Clear(0,colour,1,1.0,1,0)` on `[viewport+0x128]`; nothing branches into the 7 stolen bytes; an install changes 13 bytes, all inside the two sites; stub A leaves only by `ret 4` with the stack and `ebx`/`esi`/`edi`/`ebp` as on entry and writes only its own records; stub B leaves only to `0x10B70EDD` (entry stack) or `0x10B70E9F` (with the two stolen pushes), never writes `ebx`/`ebp`, calls only `0x109F7250` (4x) and the RI clear (1x), writes only its own data and the FOV slot, and swaps and restores the FOV around both E0 calls.

What the harness shows: it maps the exe's own 64 KB around the HUD code at its own address, loads the real `QolHud.asi`, then (A-E, as v2) compares 3.7 million answers of the mode test with a model of the rule, and (F, new) runs the game's **real** per-frame loop `0x10B70EF0` and **real** render `0x10B70E30` on a fake HUD with the 28 merc widgets, whose updates append fake actors to the real list globals, with the render call `0x109F7250` and the RI clear replaced by recorders. For 13 HUD modes it compares every draw call, the actors it receives, the FOV during it, the clear's arguments, the engine lists afterwards (untouched) and the registers with a model: the stock order everywhere, the split exactly in the views with on-top live. Nine further cases: mode changed between loop and render, another HUD, a widget added, 1,100 actors in one list, mode 7 after a scope frame, a repeated render, normal play after a view: the render falls back to stock whenever the record does not match the lists. Modes: stock, default, nosection, reloc, disabled, noviews, droneonly, sniperonly, allviews, hide, reticle, ontopoff, under, foreign (site A altered: refused), foreignb (render tail altered: on-top part refused, the rest installed), foreignloop (loop body altered: the same).

| Merc HUD of 28 widgets, defaults, harness F | Normal play | Drone view | Scope view |
| --- | --- | --- | --- |
| stock: widgets drawn | 18 | 3 | 2 |
| v3: widgets drawn / of them on top of the overlay | 18 / 0 | 18 / 15 | 18 / 16 |

# In-game test list (v3)

Install with `.\patch.ps1 -GameDir "<game folder>" -Apply` (game closed), reset with `-Revert`. Run `test\hud-state.ps1 -Watch 120` in a second window during steps 3 to 6: it prints the mode, the on-top counters and one row per widget, the lifted ones as `SHOWN, ON TOP`.

1. Start the game. `System\QolHud.log` reads `QolHud 3: installed at 0x10B73C90, Drone=1 Sniper=1 Binocular=0 StickyCam=0 Reticle=0 OnTop=1 ...; on top: installed at 0x10B70E98`.
2. Play a merc in a versus match. Normal play looks as before (the probe: `frames drawn split` does not grow).
3. Raise the scope. The scope overlay is there, and the zone name, the radar, the round timer, the score top right, the gadget strip and the merc displays are drawn **over** the scope's mask, at full brightness, not darkened. The probe: `frames drawn split` grows every frame, `frames with a lifted widget drawn stock` stays 0, the lifted rows read `SHOWN, ON TOP`. Screenshot to compare with `test\results\upsilon-2\SCOPE-full_140816_728.jpg`.
4. Leave the scope. The HUD is as in step 2, nothing doubled or left over.
5. Launch the drone outside the merc base and fly it. The drone frame's brackets are there, and the zone name, radar and top-right score are drawn over them (compare `DRONE-resp_141804_047.jpg`). Leave the drone by the key and by letting it explode: the HUD is as in step 2.
6. Look for anything wrong about depth inside the lifted part: the radar's 3D objects and the gadget cubes look as in normal play.
7. Die while in the scope and while flying the drone; the kill cam and the end of the match appear as in the stock game.
8. `OnTop=0` (by `-Settings "OnTop=0"`): the log ends `; on top: off (OnTop=0), 0x10B70E98 untouched`, and the views look as with v2.
9. Optional: `SniperUnder=12` puts the score back under the scope mask; `Binocular=1`, `StickyCam=1` as a spy; `Reticle=1` as a merc.
10. Optional, together with the bomb or hack objective only on the operator's order (rule 11: one deployment at a time): their timers stay visible in both views.

# Verified and inferred

| Claim | State |
| --- | --- |
| the widget rule, the mode byte, the mode setter, the three loops | VERIFIED (disassembly) |
| drone = mode 3, merc scope = mode 9, spy binocular = mode 8, sticky cam = mode 2 | VERIFIED (each class's start virtual), and measured in game (runs 1 and 2) |
| the scope overlay, drone overlay and gun reticle are the widgets named; live indices 21 / 22 / 23 | VERIFIED (the meshes each one loads); indices measured in game (run 1) |
| the HUD meshes are drawn from the two actor lists, rebuilt every frame in widget-array order, drawn in list order; texts after them | VERIFIED (disassembly; the harness runs the real loop and render) |
| the overlay covers the kept widgets because it is appended later | VERIFIED by the draw order; measured effect in game (v2 screenshots) |
| the engine clears depth and stencil before the HUD with `RI->Clear(0,0,1,1.0,1,0)` | VERIFIED (disassembly) |
| `[viewport+0x68]` (the HUD the render uses) is the same object as `PlayerController+0x95C` (the HUD the loop runs) | INFERRED (both carry the HUD camera node at `+0x428`); if not, stub B always takes the stock path (counted in `frames with a lifted widget drawn stock`) |
| the split draws the lifted widgets on top in the game | INFERRED; the first thing the test shows |
| a depth clear in the middle of the HUD has no other visible effect (stencil, render target) | INFERRED (the same call the engine makes before the HUD) |
| the lists hold fewer than 1,024 actors each in a real match | INFERRED; above that the frame is drawn stock and counted |
| the timers of `spy-bomb-objective` and `spy-hack-terminal` cannot be covered by any view | VERIFIED from their sources: `IDirect3DDevice9::ColorFill` on the backbuffer inside `UD3DRenderDevice::Present` (`0x109089AF`, `0x10908A10` / `0x10908A27`), after the frame is complete; values from the local level's objects and the local PRI, no HUD-mode or view-target gate. Not measured in game |
| players with and without the plugin can share a match | INFERRED from the stubs writing no game state |

# Open points

- The gun reticle stays hidden in both views by default; `Reticle=1` brings it back (then on top).
- The spy views (`Binocular`, `StickyCam`) were not ordered; they are in the plugin switched off.
- The interaction prompts (index 5) are shown in the views by the stock game and keep their stock place; if their icons sit under the overlay badly, that is stock behaviour (say so and they can be lifted too).
- A change of the shipped `HudParams.ini` was not needed and not made.

# Test log

| # | Date | Build | Result |
| --- | --- | --- | --- |
| 1 | 2026-09-29 09:49 to 10:04, automated run (test loop, unattended), working copy equal to main (exe `0f1b2d1c`), defaults, no `[QOLHUD]` section, host alone on Blackwing | v2 `2df8cf20` | PASS for the two ordered views; evidence in `test\results\` (`hud-state` dumps, mode watch, screenshots) |
| 2 | 2026-09-29 14:04 to 14:19, operator's order (host as Upsilon, screenshots of scope and drone), same install and defaults, host alone on Blackwing | v2 `2df8cf20` | PASS: scope mode 9 draws 20 widgets (3 by the stock rule); drone mode 3 with radar, round timer, markers and gadget icon kept. Evidence `test\results\upsilon-2\` (`SCOPE-full_140816_728.jpg`, `DRONE-resp_141804_047.jpg`, lobby frames, mode watch, `QolHud.log`). Operator's verdict after the screenshots: the score top right and the kept HUD must be drawn above the scope and drone overlays -> v3 |
| 3 | 2026-09-29 from 19:34, operator's hand test (order "load the following features ... the HUD overlay for drone and snipe for testing"), working copy equal to main (exe `0f1b2d1c`) plus `QolHud.asi` only, defaults (no `[QOLHUD]` section), host alone on Blackwing as merc (launch replay `trace_blackwing_launch.jsonl`, speed 0.6, in match after 63 s) | v3 `722365f7` | `QolHud.log`: "QolHud 3: installed at 0x10B73C90 ... OnTop=1 ...; on top: installed at 0x10B70E98". Operator's verdict, word for word: "ok, Merc hud worked well". Launch output `test\results\run3-hand\` |

| Test list # (v2) | Result | Measured |
| --- | --- | --- |
| 1 log | PASS | `QolHud 2: installed at 0x10B73C90, Drone=1 Sniper=1 Binocular=0 StickyCam=0 Reticle=0`, all hide lists 0; site `E9 52 D4 B8 5D 90`, plugin at its preferred base `0x6E700000` |
| 2 merc, normal play | PASS | mode 1: 28 widgets, 20 shown by the stock rule, 20 with the plugin |
| 3 scope | PASS | right mouse button: mode 1 -> 9, remote cam `BinocularMercRemoteCam`; 3 widgets by the stock rule, 20 with the plugin; on screen: zone name, radar, round timer, gadget strip, the scope overlay; the gun reticle is not drawn. The widgets outside the scope circle are darkened by the scope's own mask; the radar reaches into the left edge of the circle (`results\merc-scope\`): placement is the operator's call |
| 4 leave the scope | PASS | mode 9 -> 1, 20 of 20 as before |
| 5 drone | PASS, short | gadget key: mode 1 -> 3, remote cam `Drone`; 4 widgets by the stock rule, 20 with the plugin; radar, round timer and gadget strip on screen with the drone overlay (`results\merc-c-3\`). The drone was launched in the merc base ("Restricted area! Drone jammed!") and ended after 2.2 s: mode 3 -> 1, 20 of 20. A free flight and the exit by key were NOT run. At the spawn point itself the gadget key launched nothing (4 presses) |
| 6 widget index | SETTLED | the live index is the array order as printed by `hud-state.ps1`: merc HUD 28 widgets (scope overlay 21, drone overlay 22, gun reticle 23, grenade display 25, detection display 26), spy HUD 24 widgets (binocular overlay 21); the dumps are `results\merc-normal\hud-state.txt` and `results\spy-normal\hud-state.txt` |
| 7 hide lists | not run | - |
| 8 death, kill cam | PASS in normal play | death by the own frag: mode 1 -> 0 (1 widget) -> 4 kill cam (2 widgets), the same counts by the stock rule and with the plugin; after the kill cam mode 1, 20 of 20. Death INSIDE a view and the end of the match were NOT run |
| 9 spy | PASS | mode 1: 24 widgets, 18 by the stock rule, 18 with the plugin; the spy's views were not entered |
| 10 options | not run | - |

Test tools added by the run: `test\view-test.ps1` (mode watch and screenshots while keys are sent), `_tools\game-probe\launch-match.ps1` with `_tools\input-trace\traces\trace_blackwing_launch_merc.jsonl` (host as merc), `_tools\game-probe\shot-loop.ps1`.

Run 2 (operator's screenshots):

| Step | Result | Measured |
| --- | --- | --- |
| lobby, one Right | focus on the first Upsilon slot; Enter there: "There is no action available" | the side is changed by the lobby item Switch Team (Right, Right, Down, Enter), then Up, Enter launches; the player shows in the Upsilon column before the launch (`lobby-switched_*.png`) |
| scope | PASS | first zoom press (right mouse button): mode 1 -> 9, `BinocularMercRemoteCam`, x2.0; 3 widgets by the stock rule, 20 with the plugin (`SCOPE-full_140816_728.jpg`) |
| two more zoom presses | the zoom key toggles | press 2: 9 -> 1, press 3: 1 -> 9, press 4: 9 -> 1 |
| drone | PASS, short | gadget key C (the operator's profile binds `UseGadgetMerc` to C, `CrouchMerc` to Ctrl): no drone in the first life (12 presses over 4 min, no `Drone` actor); after a death by the own frag and a respawn the first press gave mode 1 -> 3, remote cam `Drone`, back to 1 within 3 s (jammed in Upsilon H.Q.) (`DRONE-resp_141804_047.jpg`) |
| drone placement | for the operator | the drone frame's left bracket covers the zone name and part of the radar |
| reset | done | `-Revert`, boot step 6: 0 content differences |
