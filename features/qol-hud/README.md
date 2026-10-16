# qol-hud (lean)

> **In M3epbuggin 2026.10.16-m11** as part of `M3CHAT`, on the same exe as the chat (`features/chat-list/`, `features/dead-chat-gate/`): rows 1-21 below, with rows 18, 19 and 21 moved for Community Edition 2026.10.11-3 (section "On Community Edition 2026.10.11-3" at the end), plus row C, the chat's mode mask `0x10B816A8` `33` -> `3B` (open question 1 below), applied to m10's `M3CHAT` exe (md5 `039f3948`), giving md5 `0e863bf75751c01f24f31299758386e1`. It ran in game on the test version on 2026-10-16. The change log below was measured on Community Edition 2026.10.07-1 (exe `4a17634f`). It replaces plugin v3 (`QolHud.asi`, `M3QHUD` up to m9), whose measured facts stay in `FINDINGS.md`. Paths point into the builder's workspace, not into this repository.

The normal HUD (timer, zone name, score top right, gadget strip, radar, merc displays, prompts) stays on screen while a merc looks through the drone (HUD mode 3) or the scope (mode 9) and is drawn over that view's overlay, done by 249 bytes of `SCDA_Online.exe` and nothing else: no plugin, no ini, no log, no `patch.ps1`.

Measured against the main build `C:\Program Files (x86)\SCDA Community Edition` = Community Edition 2026.10.07-1. Working note: `NOTES.md` (facts 1-22). It replaces `QolHud.asi` v3 (`..\README.md`); do not install both (v3 checks the 25 bytes at `0x10B73C90`, finds them changed and installs nothing).

| Main file replaced | md5 | New file | md5 |
| --- | --- | --- | --- |
| `System\SCDA_Online.exe` (7,712,768 B) | `4a17634fbebc1cb2c6b550cc35337d9f` | `files\System\SCDA_Online.exe` (7,712,768 B) | `d7c3e994bca77869816b1e18727a3f24` |

Who needs it: the player who wants it, on their own machine. Only the local HUD's widget masks and draw order change; nothing replicated, no package, no save data. Players with and without it can share a match (INFERRED, as for v3).

# Changes

File offset = VA - `0x10900000` (`.text` and `.rdata`). Three row groups; each group can be dropped on its own:

| Group | Rows | Gives |
| --- | --- | --- |
| S1 | 1-15 | the drone view (mode 3) shows the widgets, by the stock mode test; drawn under the drone frame |
| S2 | 16 | the scope view (mode 9) shows the same widgets; drawn under the scope mask. Needs S1 (it keys on the bit S1 adds) |
| O | 17-21 | both views draw the widgets over the overlay. Without O the result is v2's look; O without S1/S2 changes nothing visible but the order of the few stock-shown widgets |

S1 and S2 are data and an in-place rewrite of one 25-byte routine; only O adds code (217 B in two `.text` caves plus 8 B of memory).

| # | File | Site | Stock content | New content |
| --- | --- | --- | --- | --- |
| 1 | `System\SCDA_Online.exe` | VA `0x10B85BE5`, file `0x285BE5`: mask of widget [2] (vt `0x10F93234`), ctor `0x10B85B70` (built from `0x109B1298`) | `02` (`83 4E 34 02` = `or dword [esi+0x34],2`: mode 1) | `0A` (`83 4E 34 0A` = `or dword [esi+0x34],0xA`: modes 1, 3) |
| 2 | same | VA `0x10B71EA7`, file `0x271EA7`: [3] root (vt `0x10F93108`), HUD builder `0x10B71340` | `02` (`81 4E 34 02 04 00 00` = `or ...,0x402`: modes 1, 10) | `0A` (`or ...,0x40A`: modes 1, 3, 10) |
| 3 | same | VA `0x10B71F6D`, file `0x271F6D`: [4] merc frame (vt `0x10F92F14`), builder | `02` (`83 4E 34 02`) | `0A` (`83 4E 34 0A`) |
| 4 | same | VA `0x10B72016`, file `0x272016`: [6] (vt `0x10F93270`), builder | `02` | `0A` |
| 5 | same | VA `0x10B83931`, file `0x283931`: [10] round timer (vt `0x10F930CC`), ctor `0x10B83920` | `02` | `0A` |
| 6 | same | VA `0x10B9D731`, file `0x29D731`: [11] zone name (vt `0x10F935F4`), ctor `0x10B9D720` | `02` | `0A` |
| 7 | same | VA `0x10B844E0`, file `0x2844E0`: [12] score top right `UH_Score_Versus` (vt `0x10F93144`), ctor `0x10B844D0` | `02` | `0A` |
| 8 | same | VA `0x10B724D0`, file `0x2724D0`: [13] spy status / hacking panel (vt `0x10F92E50`), builder's versus path (after base ctor `0x10B76920`) | `02` | `0A` |
| 9 | same | VA `0x10B7F420`, file `0x27F420`: [14] gadget strip (vt `0x10F92FDC`), ctor `0x10B7F410` | `02` | `0A` |
| 10 | same | VA `0x10B9430F`, file `0x29430F`: [15] radar objects (vt `0x10F9339C`), ctor `0x10B942F0` | `02` (`81 4E 34 02 01 00 00` = `or ...,0x102`: modes 1, 8) | `0A` (`or ...,0x10A`: modes 1, 3, 8) |
| 11 | same | VA `0x10B8BB26`, file `0x28BB26`: [16] (vt `0x10F93324`), ctor `0x10B8BAD0` | `02` (`or ...,0x402`) | `0A` (`or ...,0x40A`) |
| 12 | same | VA `0x10B7266F`, file `0x27266F`: [19] hook prompt (vt `0x10F93450`), builder | `02` | `0A` |
| 13 | same | VA `0x10B726BB`, file `0x2726BB`: [20] reload gadget prompt (vt `0x10F93018`), builder | `02` | `0A` |
| 14 | same | VA `0x10B9D09C`, file `0x29D09C`: [25] merc grenade display (vt `0x10F935B8`), ctor `0x10B9D090` | `02` | `0A` |
| 15 | same | VA `0x10B7B0A8`, file `0x27B0A8`: [26] merc detection display (vt `0x10F92E9C`), ctor `0x10B7B070` | `02` | `0A` |
| 16 | same | VA `0x10B73C90..0x10B73CAF`, file `0x273C90`, 32 B: the widget mode test (vt slot `+0x0C` of all 41 widget classes; no direct caller) and its 7 padding bytes | `8BD18A4C2404B801000000D3E0234234F7D81BC0F7D8C20400` + 7 x `CC` (below) | `8B51348BC2F7D0A80A750380CE028B4C24040FA3CA1BC0F7D8C20400` + 4 x `CC` (below): a widget whose mask holds modes 1 and 3 also answers for mode 9 |
| 17 | same | VA `0x10B70E98`, file `0x270E98`, 7 B: start of the two list draws in the HUD render `0x10B70E30` | `6A 00 68 EC 15 04 11` (`push 0` / `push 0x110415EC`) | `E9 E3 DC 2B 00 90 90` (`jmp 0x10E2EB80` / `nop` / `nop`) |
| 18 | same | VA `0x10F93430`, file `0x693430`: scope overlay [21] vtable `0x10F93414`, slot `+0x1C` (update) | `50 5E B9 10` (`0x10B95E50`) | `90 EE E2 10` (`0x10E2EE90`, cave W entry WS) |
| 19 | same | VA `0x10F92EF4`, file `0x692EF4`: drone overlay [22] vtable `0x10F92ED8`, slot `+0x1C` (update) | `20 B7 B7 10` (`0x10B7B720`) | `97 EE E2 10` (`0x10E2EE97`, cave W entry WD) |
| 20 | same | VA `0x10E2EB80..0x10E2EC2B`, file `0x52EB80`, 172 B: cave T + RR (the `.text` tail past VirtualSize `0x10E2EB41`, zero in main) | 172 zero bytes | `6A0068EC1504118A85040400003C0374043C09755EA1F0EF06118B0DF4EF06113BC1734F3B0DE41504117747E8470000008B8B280100008B1133C0506A01680000803F6A015050FF52108BF3E87F86BCFF33C08B0DF0EF0611E81A000000A1F4EF06118B0DE4150411E80A000000E9EA22D4FFE9A722D4FF2BC88B15E81504118D14825251518BD48B7B588B851C040000878758040000506A01528BF3E82E86BCFF8F875804000083C40CC3` (below) |
| 21 | same | VA `0x10E2EE90..0x10E2EEBC`, file `0x52EE90`, 45 B: cave W | 45 zero bytes | `BA505EB910EB05BA20B7B710A1E4150411A3F0EF0611FF742408FF742408FFD2A1E4150411A3F4EF0611C20800` (below) |

Memory used by group O, not in the file: `0x1106EFF0` (A) and `0x1106EFF4` (B), two dwords in the `.data` page past its VirtualSize (`.data` ends at `0x1106EA24`, `.rsrc` starts at `0x1106F000`; mapped read-write and zero at load; nothing in the exe or the 8 CE plugins references the range).

By hand: write rows 1-21 at their file offsets into a copy of main's exe (each row's stock bytes must be there first).

## Row 16, the widget mode test

```
stock (25 B + 7 x CC)                          new (28 B + 4 x CC)
8B D1        mov  edx,ecx                      8B 51 34     mov  edx,[ecx+0x34]   ; the widget's mode mask
8A 4C 24 04  mov  cl,[esp+4]                   8B C2        mov  eax,edx
B8 01000000  mov  eax,1                        F7 D0        not  eax
D3 E0        shl  eax,cl                       A8 0A        test al,0x0A          ; modes 1 and 3 both set?
23 42 34     and  eax,[edx+0x34]               75 03        jne  0x10B73C9E       ; no: the mask as it is
F7 D8        neg  eax                          80 CE 02     or   dh,2             ; yes: mode 9 (bit 9) too
1B C0        sbb  eax,eax                      8B 4C 24 04  mov  ecx,[esp+4]      ; the mode asked for
F7 D8        neg  eax                          0F A3 CA     bt   edx,ecx          ; bit (mode mod 32), as shl
C2 04 00     ret  4                            1B C0        sbb  eax,eax
                                               F7 D8        neg  eax              ; 1 or 0, as stock
                                               C2 04 00     ret  4
```

The answer is the stock one for every mask, except that a mask holding modes 1 and 3 also answers yes for mode 9. In the merc versus HUD those are rows 1-15's widgets and stock widget [24] (system malfunction message, modes 1, 3); widget [5] (prompts) already has mode 9. The three widget loops (`0x10B70EF0` per frame, `0x10B70C20` texts, `0x10B72EC0`) all ask this routine, so meshes and texts follow it alike.

## Rows 20-21, the caves

```
; T: entered by row 17; ebx = viewport, ebp = HUD, stack as at 0x10B70E98
10E2EB80  6A00 / 68EC150411   push 0 / push 0x110415EC   ; the stolen pushes = render(EC,0)'s arguments
10E2EB87  8A8504040000        mov  al,[ebp+0x404]        ; HUD mode
10E2EB8D  3C03 / 7404         cmp al,3 / je 0x10E2EB95   ; drone view
10E2EB91  3C09 / 755E         cmp al,9 / jne BACK        ; merc scope
10E2EB95  A1F0EF0611          mov  eax,[A]               ; the overlay's run [a,b) in list E0 (recorded by W)
10E2EB9A  8B0DF4EF0611        mov  ecx,[B]
10E2EBA0  3BC1 / 734F         cmp eax,ecx / jae BACK     ; need a < b
10E2EBA4  3B0DE4150411 / 7747 cmp ecx,[E0.num] / ja BACK ; need b <= num
10E2EBAC  E847000000          call RR                    ; E0[a,b): the overlay, HUD FOV
10E2EBB1  8B8B28010000        mov  ecx,[ebx+0x128]       ; RI
10E2EBB7  8B11 / 33C0         mov edx,[ecx] / xor eax,eax
10E2EBBB  50 6A01 680000803F 6A01 50 50 / FF5210   RI->Clear(0,0,1,1.0,1,0)   ; the engine's own pre-HUD clear (0x10A5024C)
10E2EBCA  8BF3 / E87F86BCFF   mov esi,ebx / call 0x109F7250   ; EC with the player's FOV, as stock
10E2EBD1  33C0 / 8B0DF0EF0611 / E81A000000      xor eax,eax / mov ecx,[A] / call RR       ; E0[0,a)
10E2EBDE  A1F4EF0611 / 8B0DE4150411 / E80A000000 mov eax,[B] / mov ecx,[E0.num] / call RR ; E0[b,num)
10E2EBEE  E9EA22D4FF          jmp  0x10B70EDD            ; pop edi / esi / ebp, ret 4
10E2EBF3  E9A722D4FF  BACK:   jmp  0x10B70E9F            ; the stock tail, pushes already done
; RR: render E0[eax,ecx) with the HUD FOV exactly as the stock tail renders E0
10E2EBF8  2BC8                sub  ecx,eax               ; count (render skips 0)
10E2EBFA  8B15E8150411        mov  edx,[E0.data]
10E2EC00  8D1482              lea  edx,[edx+eax*4]
10E2EC03  52 51 51 / 8BD4     push data / push num / push max / mov edx,esp   ; a TArray header on the stack
10E2EC08  8B7B58              mov  edi,[ebx+0x58]        ; the viewport's actor
10E2EC0B  8B851C040000        mov  eax,[ebp+0x41C]       ; HUD FOV
10E2EC11  878758040000 / 50   xchg eax,[edi+0x458] / push eax   ; in; the actor's FOV saved
10E2EC18  6A01 52 / 8BF3      push 1 / push header / mov esi,ebx
10E2EC1D  E82E86BCFF          call 0x109F7250
10E2EC22  8F8758040000        pop  dword [edi+0x458]     ; FOV back
10E2EC28  83C40C / C3         add esp,12 / ret

; W: the two overlay classes' update slot (rows 18-19); thiscall update(p1,p2), ret 8
10E2EE90  BA505EB910 / EB05   WS: mov edx,0x10B95E50 / jmp W   ; scope overlay update
10E2EE97  BA20B7B710          WD: mov edx,0x10B7B720           ; drone overlay update
10E2EE9C  A1E4150411 / A3F0EF0611   W: mov eax,[E0.num] / mov [A],eax
10E2EEA6  FF742408 FF742408   push p2 / push p1
10E2EEAE  FFD2                call edx                   ; the stock update, ecx = the widget
10E2EEB0  A1E4150411 / A3F4EF0611   mov eax,[E0.num] / mov [B],eax
10E2EEBA  C20800              ret  8
```

E0 = `0x110415E0` {max, num `0x110415E4`, data `0x110415E8`}, EC = `0x110415EC`, render(list, flag) = `0x109F7250`. In modes 3 and 9 with a valid record the HUD meshes are drawn in this order: the overlay's actors, the engine's depth / stencil clear, list EC, the rest of E0 in its stock order. In every other case (normal play, spy views, kill cam, a record that does not fit the list) T runs the stock bytes. The lists themselves, the widget update order and every widget's own code stay stock; W only reads `E0.num`.

# Checks (lean, no harness)

| Check | Result | Log |
| --- | --- | --- |
| byte diff of `files\System\SCDA_Online.exe` against main | 249 bytes differ; every one inside a row above, every row holds differing bytes: 21 rows = 21 groups (15 x 1, 27, 7, 3, 3, 150, 44 B). As contiguous runs they are 31, because inside rows 16 and 18-21 some new bytes equal the stock ones (zero bytes in the cave code, the `0x10` high byte of the pointers, `CC` padding) | `scratch\check_b1.txt` |
| disassembly of every site before and after | rows 1-15 `or dword [esi+0x34],2 / 0x402 / 0x102` -> `0xA / 0x40A / 0x10A`; row 16 and the caves as above; every branch lands on an instruction start; nothing in `.text` branches into `0x10B73C91..0x10B73CAF` or `0x10B70E99..0x10B70E9E`, and the only file dwords pointing into row 16 are the 41 vtable slots = `0x10B73C90` | `scratch\sites_before_after.txt`, `scratch\py\xrefs.py` |
| two builds from main | one md5 `d7c3e994bca77869816b1e18727a3f24`. Variants by the same script: rows 1-16 only (`--groups S1,S2`) `5c169f4d267e3f904a01ded4c6a1f475`, rows 1-15 only (`--groups S1`) `b3c0fc10c1154399969205873eced418` | `scratch\py\build_lean.py` |
| the 8 CE plugins (`Enhanced`, `MatchRec`, `Modes`, `ObjHack`, `ProxVoice`, `RollFix`, `SpawnProt`, `VentChain`): every `ok` range and hook VA of their start logs, every image-range dword in their files, against rows 1-21 and the two data dwords | none inside or within 16 B; nearest: `Enhanced.asi`'s `0x10B70F08` 105 B after row 17, `Modes.asi`'s hook `0x10B73FF0` 832 B after row 16; no plugin references either cave or the `.data` slack | `scratch\check_b1.txt` |
| `dead-chat-gate` (file `0x0B8B36`, `0x0B8B37`, `0x2816A8`) | disjoint, none within 16 B | `scratch\check_b1.txt` |
| LEAN-C chat-list (exe file bytes `0x281740`, `0x2817A0`, `0x2817AA`, `0x2817B4`, `0x2817BE`, `0x2817C8`, `0x2824C3`, `0x2824CA`, `0x283047`, `0x2833A6`, `0x2833D2`, `0x2833DE..DF`, `0x283449..4A`, `0x283461`, `0x283465`, `0x28346A`), checked against `Deploy\chat-list\lean\files\System\SCDA_Online.exe` (`f1666348`) | disjoint, none within 16 B; widget 18 untouched. Its 18 bytes in `Interface_stm.usx`: this stack writes no package | `scratch\combined_check.txt` |
| LEAN-G spy-grab-merc / qol4necks / root-berzerk (cave `0x10E2EC40..0x10E2EE0F`; site bytes file `0x2C7A29` (7), `0x2C9F18` (6), `0x2C9F2F` (4), `0x2CAE97` (5), `0x2CAE9E` (4), `0x2CB011` (4), `0x2D8AD0` (7), `0x4AA307` (6)), checked against their `lean\files\System\SCDA_Online.exe` (`bafe978b`, `c1da8b29`, `b6f20e1a`) | disjoint, none within 16 B; cave T ends 20 B before `0x10E2EC40`; all six stacks on one exe = 630 B, no byte written twice | `scratch\combined_check.txt` |
| main's own cave code (door carry `0x10E2EB50..0x10E2EB7F` and `0x10E2EEE0..0x10E2EFB4`, flashbang `0x10E2EE40..0x10E2EE79`, JammerLauncher spawn `0x10E2EFC0..0x10E2EFEA`) | untouched: T starts right after the door carry tail (`0x10E2EB80`); W sits in the zero run `0x10E2EE7A..0x10E2EEDF` between flashbang and door carry, 22 B and 35 B clear | `scratch\py\caves.py` |

# v3's parts

| v3 part | Lean | Why |
| --- | --- | --- |
| widgets kept in the drone view (mode 3) | kept with a difference: rows 1-15, the 15 merc versus widget classes v3 lifted, by their own mask byte. Messages / chat [18] is not included (it is chat-list's widget, and its low mask byte `0x2816A8` is dead-chat-gate's). The other score / status classes a challenge HUD builds at [12] / [13] are not included (v3's rule caught any normal-play widget) | the stock mode test shows a widget whose mask holds the mode; one byte per class |
| widgets kept in the scope view (mode 9) | kept with a difference: the same set (plus stock [24], as v3), through row 16 | bit 9 is out of reach of the ctors' `or dword [esi+0x34],imm8` (an imm8 sets bits 0..6 only), so the test routine answers mode 9 for "modes 1 and 3" |
| gun reticle hidden in both views (`Reticle=0`) | kept exactly | [23] keeps mask `0x02`, so neither mode 3 nor the routine's rule reaches it |
| spy views stock (`Binocular=0`, `StickyCam=0`) | kept exactly | modes 2 and 8 unchanged; mode 3 / 9 bits on shared classes only matter for a merc |
| on top: split draw at `0x10B70E98` with the engine's clear between | kept with a difference: the split point is the overlay's own run (recorded by its update, rows 18-19), not a per-widget record in the mode test; the stock-shown widgets (system message [1], prompts [5], malfunction [24] in the drone view) are now on top too (v3 kept them under); all of EC is drawn after the clear (v3 drew the stock-shown widgets' EC items before the overlay); no copies of the lists, no 1,024-actor cap, update order untouched | order alone is not enough: the overlays' `BasicModernMaterial` parts (`Mat_Hud_Snipe_contour`, `Mat_hud_drone_noir`) sit at X 200 / 140 in front of the widgets (X 550..2200) and the engine clears depth before the HUD (INFERRED: they would still hide a widget drawn after them); the record route needs no hook in the per-frame loop |
| `[QOLHUD]` settings (`Enabled`, `Drone`, `Sniper`, `Binocular`, `StickyCam`, `Reticle`, `OnTop`, `*Hide`, `*Under`) | dropped | no ini (brief). By bytes: `OnTop=0` = drop rows 17-21; one widget less = leave its row out; drone only = rows 1-15; scope without drone is not available by bytes |
| `System\QolHud.log`, counters, `test\hud-state.ps1` plugin rows | dropped | no log, no plugin state; the probe was written for the plugin and was not checked against this stack |
| `patch.ps1` (apply, revert, settings, v1 / v2 recognition) | dropped | drag-and-drop stack; revert = main's exe |
| byte checks at load and refusal on a foreign build | dropped | the stack is built by stock-checked writes on main's exe; rows 1-21 give the stock bytes for a hand check |

# In-game test (on a working copy equal to main, rule 11)

Install: drag the contents of `files\` onto the install root and replace (game closed); no `System\QolHud.asi` beside it. Reset: main's `System\SCDA_Online.exe`.

1. Normal play as a merc: the HUD is as in stock (nothing moved, missing or doubled); as a spy too.
2. Scope (right mouse button): the zone name, radar, round timer, score top right, gadget strip, merc grenade and detection displays and the hook / reload prompts are drawn **over** the scope mask at full brightness, not darkened (compare `..\test\results\upsilon-2\SCOPE-full_140816_728.jpg`); the gun reticle is not drawn; the scope's own frame, cross, distance, zoom and ammo look as in stock.
3. Leave the scope (zoom key again): the HUD is as in step 1, nothing left over.
4. Drone (gadget key, outside the merc base): the same widgets over the frame brackets (compare `DRONE-resp_141804_047.jpg`, where the left bracket covered the zone name and radar); the drone's own status, count and bindings panel look as in stock. Leave by the key and by self-destruct: HUD as in step 1.
5. Depth inside the lifted part: the radar's 3D objects and the gadget cubes look as in normal play; the world markers (coloured octagons) show over the overlay.
6. Entering and leaving either view: no frame with the overlay missing or drawn twice.
7. Die while in the scope and while flying the drone: the kill cam (mode 4), the respawn and the end of the match (mode 6) are as in stock.
8. A spy's binocular view (mode 8): unchanged (radar and prompts under the binocular overlay, as in stock).
9. Messages / chat while in a view: not shown by this stack (open question 1).

# Open questions for the operator

1. Messages / chat [18] in the views: v3 showed it. To add it, its mask needs mode 3: file `0x2816A8` low byte `02` -> `0A` on main, or `33` -> `3B` together with dead-chat-gate; that byte is dead-chat-gate's and the widget is chat-list's (LEAN-C), so it is left to them.
2. Challenge HUDs: the other score / status classes at [12] / [13] (`0x10B84C70` vt `0x10F93180`, `0x10B84CB0` vt `0x10F931BC`, `0x10B85640` vt `0x10F931F8`, and the `0x10B76920` family) are not edited; one mask byte each if mercs use the drone or scope there.
3. Cave and memory register: rows 20-21 claim `0x10E2EB80..0x10E2EC2B` and `0x10E2EE90..0x10E2EEBC`; group O uses `0x1106EFF0..0x1106EFF7` of the `.data` slack, a range `engine\exe-addresses-and-patches.md` does not list yet (`NOTES.md` facts 11, 12; `FINDINGS.md` was refused by the subagent harness, the findings went back to the orchestrator as text).
4. If the in-game test shows something of an overlay's own drawn over its frame (an overlay item kept in list EC would now come after the clear), the remedy is a record of the overlay's EC run as well (about 40 B more).

# On Community Edition 2026.10.11-3

## Files

| Build | Input (replaced) | Output | Bytes |
| --- | --- | --- | --- |
| `hud-only\System\SCDA_Online.exe` (the feature alone) | CE 2026.10.11-3 SMOKE exe md5 `ceb13a00f2e48b52c6d7aeff93f3a29d` (sha256 `8cd78553`) | `5b3cda981d4ebd83e89f71b541e72fb3` | 249 (groups S1, S2, O) |
| `m10-hud\System\SCDA_Online.exe` (the test build) | M3epbuggin m10 `M3CHAT` exe `039f3948a11b0ab0093bbf8787f9c941` (= `ceb13a00` + chat-list lean 18 B + dead-chat-gate 3 B) | `0e863bf75751c01f24f31299758386e1` | 250 (S1, S2, O + C) |

Both builds twice, one md5 each. With the m10 exe goes m10's `Packages\_Common\StaticMeshes\Interface_stm.usx` `91c890cd` (unchanged here).

## Rows that differ from `..\README.md`

| # | Site | Stock | 10.07-1 lean | 10.11-3 lean |
| --- | --- | --- | --- | --- |
| 18 | VA `0x10F93430`, file `0x693430`: scope overlay [21] vtable slot `+0x1C` | `50 5E B9 10` (`0x10B95E50`) | `90 EE E2 10` (`0x10E2EE90`) | `40 EC E2 10` (`0x10E2EC40`, WS) |
| 19 | VA `0x10F92EF4`, file `0x692EF4`: drone overlay [22] vtable slot `+0x1C` | `20 B7 B7 10` (`0x10B7B720`) | `97 EE E2 10` (`0x10E2EE97`) | `47 EC E2 10` (`0x10E2EC47`, WD) |
| 21 | cave W, 45 B | zero | VA `0x10E2EE90..0x10E2EEBC`, file `0x52EE90` | VA `0x10E2EC40..0x10E2EC6C`, file `0x52EC40`; the same 45 bytes (`BA505EB910EB05BA20B7B710A1E4150411A3F0EF0611FF742408FF742408FFD2A1E4150411A3F4EF0611C20800`) |
| C (m10 build only) | VA `0x10B816A8`, file `0x2816A8`: widget 18 (chat) mode mask, ctor `0x10B81650` | `02` (modes 1, 11) | not in lean (open question 1) | `3B` (dead-chat-gate's `33` + mode 3): the chat also shows in the drone and, by row 16, the scope, as v3 showed it |

Rows 1-17 and 20 (cave T + RR at `0x10E2EB80..0x10E2EC2B`, file `0x52EB80`) and the `.data` slack A/B `0x1106EFF0..0x1106EFF7`: byte for byte as `..\README.md`.

## Checks (`check-1011.txt`, ALL PASS)

| Check | Result |
| --- | --- |
| stock bytes | every HUD site holds the same stock bytes in 10.07-1 and 10.11-3; the builder refuses any other |
| byte diff | hud-only vs 10.11-3: 249 B = the 10.07-1 lean bytes with W moved; m10-hud vs m10: 250 B; m10-hud vs 10.11-3: chat 21 + HUD 249, C on the shared byte |
| caves | `0x10E2EB80..0x10E2EC9F` zero in 10.11-3; T + W end 52 zero bytes before 10.11-3's code at `0x10E2ECA0`; no absolute dword or rel32 branch in the 10.11-3 exe or its 8 plugins points into `0x10E2EB70..0x10E2EC9F`; the one exe dword in the `.data` slack (`0x1106EE3E` at file `0x558FB7`) is float table data, there in 10.07-1 too |
| 10.11-3 changes | nearest to a HUD code site 51,759 B |
| chat bytes | disjoint, nearest 1,223 B |
| 10.11-3 plugins (`Enhanced`, `MatchRec`, `Modes`, `ObjHack`, `ProxVoice`, `RollFix`, `SpawnProt`, `VentChain` as in `C:\Dash\SCDA M3epbuggin\System`) | no image dword within 16 B of a HUD byte or A/B; nearest `Enhanced.asi` `0x10B70F08`, 106 B |

