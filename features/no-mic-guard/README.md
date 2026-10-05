# no-mic-guard (NoMicGuard.asi)

Lets the game start and run on a PC with no working microphone, instead of crashing during start-up. Without it the game crashes at `SCDA_Online.exe+37A133`. In the M3epbuggin channel this is the add-on `M3NMIC` (since 2026.10.05-m4).

Built 2026-10-01 (B-1). `NoMicGuard.asi` md5 `cc449c0dd59f646cd018fc2243e1b025`, 12800 bytes. The exe on disk is never changed: the plugin patches it in memory at load, and does nothing at all when a capture device works.

# The crash (MEASURED 2026-10-01)

| Fact | Value |
| --- | --- |
| symptom | crash about 5 s after start, before `entry_vs` is shown; `System\CrashCatch.log`: `code 0xC0000005 at SCDA_Online.exe+37A133, tried to read 0x00000000`; Windows Application log: APPCRASH, fault offset `0x0037a133` |
| seen | main (launched by the launcher) 13:19, working copy 13:22 |
| call chain | sound-engine start-up `0x10C75770` -> at `0x10C758B5` the voice init `0x10C79DF0` (only when `[esi+0x2C]` is 0; no test of the voice-mute setting) |
| cause | at `0x10C7A0E5` `call 0x10C8F7B2` (`jmp [0x10E2F04C]`, the import of `DirectSoundCaptureCreate`) with `lpcGUID` = `0x10E2F87C` = `DSDEVID_DefaultVoiceCapture` `{DEF00003-9C6D-47ED-AAF1-4DDA8F2B5C03}`, out pointer `[esi+0x280]`. Its HRESULT is never tested. `0x10C7A116 mov eax,[esi+0x280]`, then `0x10C7A133 mov ecx,[eax]` reads address 0 |
| why it fails on this PC | `DirectSoundCaptureCreate` returns `0x88780078` `DSERR_NODRIVER` for both `DSDEVID_DefaultVoiceCapture` and the NULL (default) device. The PC's only microphone was unplugged; the one active recording endpoint, a Stereo Mix, is not usable by DirectSound |
| stock | the 85 bytes from `0x10C7A0E5` are identical in the stock exe `fc237f82`, Community Edition main `0f1b2d1c` and the Experimental exe `4dccc646`: original game code, not a patch of ours. The whole voice module `0x10C75000`..`0x10C7C000` is byte-identical in `0f1b2d1c` and `4dccc646` (MEASURED, `cmp` 0 bytes differ), so one plugin fits both |
| workaround | connect a microphone before starting the game (INFERRED: not tried) |

# The capture readers (MEASURED)

The voice object is a singleton at `[0x1100FFDC]` (getter `0x10C7B200`, constructor `0x10C79DA0` which zeroes `+0x280` / `+0x28C` / `+0x290`). The engine also keeps it at `[engine+0x2C]`. Its capture-path fields are the capture object `+0x280`, the pre-QI buffer `+0x28C`, the capture-buffer interface `+0x290` and the lock scratch `+0x2B0` / `+0x2B4`. Every reader of them, and whether it can run with no capture object:

| Reader | Reads | Reached | Guarded |
| --- | --- | --- | --- |
| voice init `0x10C79DF0` (`0x10C7A116`..`0x10C7A1D7`) | `+0x280`, `+0x28C`, `+0x290`, `+0x2B0/4` | once at start-up (crashes here) | **site 1** |
| start-capture-once `0x10C7A230` (`0x10C7A23C`, `0x10C7A261`) | `+0x290` | the voice tick `0x10C7A283`, every tick until latch `[0x11049710]` is set | **site 2** |
| capture-read `0x10C7A4D0` (`+0x290`, `+0x29C`, `+0x2A0`, writes `+0x2AC`) | `+0x290` | tick `0x10C7A2AD`, only while the local talker records (`[+0x2C0]` and `[+0x2C4]` set) | **site 3** |
| encode-and-send `0x10C7A8F0` (`0x10C7A8F3`, `0x10C7A98F`) | `+0x290` | only when `0x10C7A4D0` returns non-zero | covered by site 3 (caller skips it) |
| stop `0x10C7B100` / start `0x10C7B1A0` | `+0x290` | voice on/off, join/leave | already stock-guarded (`cmp [+0x290],0 / je`) |
| playback mix `0x10C7AB70` / `0x10C7ACB0`, add/remove talker `0x10C7A520` / `0x10C7A850` | no capture field (per-talker buffers `+0x2B8` / `+0x2BC` only) | every tick | not touched: hearing the others keeps working |

Nothing releases `+0x280` / `+0x28C` / `+0x290` on shutdown (`0x10C7B0C0` releases per-talker buffers only), so there is no release path to guard.

# The fix, as built (rule 8 change log; MEASURED unless noted)

Three in-memory hooks, each byte-checked at load; a site whose bytes are not the stock ones is left alone and logged. Position-independent `.asi`, no import table, no CRT, one RWX section, preferred base `0x6EC00000` (`0x6E500000`..`0x6EA00000` are other plugins'; `0x6EB00000` is reserved for root-berzerk). Each guard reads the capture field the stock instruction was about to read; when it is non-zero the stub runs the stolen instruction(s) and continues at the stock address, so **the plugin does nothing at all when a capture device works**. The sites lie outside every ProxVoice checked range (MEASURED against `ProxVoice.asi`'s own table).

| # | Site (VA / file off) | Stock bytes | New content | Guard behaviour |
| --- | --- | --- | --- | --- |
| 1 | `0x10C7A116` / `0x37A116` | `8B 86 80 02 00 00` (`mov eax,[esi+0x280]`, 6 B) | `E9 <rel32>` + `90` (jmp to stub 1; `E9 BA 70 F8 5D 90` at the preferred base) | `[esi+0x280]` (capture object) == 0: drop the `ebx` pushed at `0x10C7A111` (`add esp,4`) and continue at `0x10C7A1DA`, past the whole CreateCaptureBuffer / QI / Lock / Unlock block; else run the load and continue at `0x10C7A11C` |
| 2 | `0x10C7A23C` / `0x37A23C` | `8B 86 90 02 00 00 8B 08` (`mov eax,[esi+0x290]` / `mov ecx,[eax]`, 8 B) | `E9 <rel32>` + `90 90 90` (jmp to stub 2; `E9 3E 90 F8 5D 90 90 90` at the preferred base) | `[esi+0x290]` (capture buffer) == 0: leave exactly as the stock `jne 0x10C7A270` does (`xor eax,eax / pop esi / ret`), the latch deliberately not set; else run both loads and continue at `0x10C7A244` |
| 3 | `0x10C7A4D0` / `0x37A4D0` | `8B 87 90 02 00 00` (`mov eax,[edi+0x290]`, 6 B) | `E9 <rel32>` + `90` (jmp to stub 3; `E9 53 6E F8 5D 90` at the preferred base) | `[edi+0x290]` (capture buffer) == 0: return 0 (`ret`, nothing pushed yet), so the caller's `test eax,eax / je` skips the encode-and-send `0x10C7A8F0`; else run the load and continue at `0x10C7A4D6` |

The `<rel32>` of each jmp is `stub - (site + 5)` and is computed by the installer from the plugin's actual load base; the preferred-base bytes above are the values when the plugin loads at `0x6EC00000`. Site 1's skip is stack-balanced: over the stock block `[0x10C7A116, 0x10C7A1DA)` there are 20 pushes and a net esp delta of +4 (MEASURED push/pop structure; the five COM `stdcall` pop counts -- CreateCaptureBuffer 4 args, QueryInterface 3, Release 1, Lock 7, Unlock 4 -- are INFERRED from the DirectSoundCapture / DirectSoundCaptureBuffer signatures), so the stub's single `add esp,4` reaches the stock esp at `0x10C7A1DA`.

`System\NoMicGuard.log`: one line per site at load (installed / left alone), and one timestamped line the first time each guard fires. Nothing per frame.

# What is lost without a microphone (INFERRED from the code)

Only local voice capture and transmission. Voice playback (hearing the other players) reads no capture field and keeps working: the talker mix `0x10C7AB70` / `0x10C7ACB0` runs every tick regardless, and the stop/start of the talker buffers (`0x10C7B100` / `0x10C7B1A0`) is already stock-guarded. ProxVoice's forced voice-on sets `+0x7FE4 = 0` and calls the stock-guarded start `0x10C7B1A0`; it never calls the capture readers directly, so it tolerates the missing device.

# Gate

`build\gates\build.txt`: 110 PASS, 0 FAIL, four builds one md5 (determinism). `build\gates\harness.txt`: the real `.asi`, loaded at its base, patches each site in a mapped copy of each exe and routes correctly for both the mic-present and no-mic cases (stack balance, eax, the fired-log firing once); 42 checks, 0 FAIL, on both `0f1b2d1c` and `4dccc646`. Re-run with `build\gates\run.ps1`.

# Checked for M3epbuggin m4 (2026-10-05)

| Check | Result |
| --- | --- |
| static gate on Community Edition 2026.10.02-5's SMOKE exe `4a17634fbebc1cb2c6b550cc35337d9f` and M3CHAT's exe `0fd28e5f875c37db072735e005174407`, with every plugin of a CE -5 + M3epbuggin m3 install scanned (Enhanced, Modes, ObjHack, ProxVoice, QOL4Necks, QolHud, RollFix, SniperHeadshotSound, SpawnProt, SpyGrab, VentChain) | 105 PASS, 0 FAIL; the rebuild is byte-identical (`cc449c0d`); no installed plugin references a site byte |
| harness (the real `.asi` patching a mapped copy of each exe, mic-present and no-mic paths) | 21 of 21 PASS on each exe |
| start on a CE -5 + m3 install with `NoMicGuard.asi` added, no microphone, `SCDA_Online.exe` started directly | window at 3.5 s; all three sites `installed`; the init and start-capture guards fired; main menu reached; alive and responding at 90 s; no crash report |

The voice sites are original game code, identical in the stock exe, Community Edition 2026.09.28-1 (`0f1b2d1c`), the Experimental exe (`4dccc646`) and both exes above.

# Install

The M3epbuggin channel installs `System\NoMicGuard.asi` (add-on `M3NMIC`). By hand: copy `NoMicGuard.asi` into the game's `System` folder. Start the game once with no microphone: `System\NoMicGuard.log` shows the load line and `installed` for all three sites, then one line the first time each guard fires.
