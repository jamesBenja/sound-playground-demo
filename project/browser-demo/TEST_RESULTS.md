# SOUND PLAYGROUND sketch 0.2: test results

**Environment:** headless Chromium (Playwright, Linux), real trusted mouse and keyboard input, multitouch via the
Chrome DevTools `Input.dispatchTouchEvent`, recordings inspected with ffprobe / ffmpeg.
**Command:** `node tests/run_tests.cjs --long`. Raw output: `tests/out/results.json`.
**Result:** **47 / 47 checks passed** (final run on 2026-11-25 against the exact `index.html` now published on GitHub Pages; log: `tests/out/final_run.log`).

Labels: **VERIFIED** = an automated check passed; **NOT TESTED** = needs a person, a device or another browser.

## Automated checks (VERIFIED)

| Area | Check | Measured |
|---|---|---|
| Load | no console errors or warnings on load, during play, or across a 3-minute session | 0 errors |
| Load | no horizontal scroll at 390 px (phone) and 820 px (tablet) | 0 px overflow |
| Audio start | no AudioContext exists before a user gesture | `none` |
| Audio start | Enable sound → context `running`; pressing Enable twice more keeps one running context and correct status | pass |
| Audio start | pressing a pad first (no Enable click) starts audio and plays the note | running, 10 sources |
| Mouse | hold PULSE pad → groove scheduled; release → stops | pass |
| Keyboard | hold 2 → BREATH sustains, key auto-repeat ignored; release → voice released | pass |
| Keyboard | keys 1, 3, 4 held together all play | pass |
| Keyboard | focused pad plays with Space (accessibility) | pass |
| Multitouch | 4 simultaneous touches on 4 pads → all active, counter "4 of 4 playing" | pass |
| Multitouch | lifting 2 fingers releases exactly those 2 stations | pass |
| Dials | dragging RESONANCE dial 90° clockwise raises it by one third | 0.40 → 0.73 |
| Dials | End / ArrowDown keys, aria-valuenow updated; mouse wheel | pass |
| Clipping | volume 100 %, every dial at its loudest/densest, all four voices held 12 s: post-limiter peak | 0.767 = **−2.3 dBFS** (pre-limiter 0.544); 0 clipped frames |
| Load | live audio sources stay bounded under full load | 29 live sources |
| Stuck notes | 300 random pointerdown / pointerup / lostpointercapture / pointercancel events (6 pointer ids) mixed with key presses → no station left active | pass |
| Stuck notes | 4 s after release, every oscillator/noise source has ended | 0 live sources |
| Stuck notes | window blur while holding a key releases the note | pass |
| Recording, stopped early (~6 s) | WebM with VP9 1280×720 video + Opus stereo 48 kHz audio; decodes to the right length; audible, not clipped; JSON log ordered, 4 pad downs / 4 ups, `stopReason: user` | 6.33 s, 191 frames, mean −22.3 dB, peak −4.9 dB |
| Recording, 30 s | same checks; stops itself (`stopReason: timer`) | 29.96 s, 900 frames, mean −23.1 dB, peak −4.3 dB |
| Recording, 3 min | same checks; stops itself | 179.96 s, 5,395 frames, mean −23 dB, peak −3.8 dB, 74 logged events |

Example outputs are in `examples/`. The 3-minute video (53 MB) is not kept, only its gesture log. It can be regenerated with `--long`.

## Browser / device differences

| Browser | Status |
|---|---|
| Chromium / Chrome (desktop, Linux, headless) | VERIFIED above |
| Chrome Android, real multitouch screen | NOT TESTED (touch was emulated via DevTools) |
| Firefox desktop | NOT TESTED. Uses only standard APIs (Web Audio, Pointer Events, `captureStream`, `MediaRecorder` WebM/Opus), which Firefox supports |
| Safari macOS / iOS | NOT TESTED. Audio should work; recording uses the coded MP4 fallback, which is untested. iOS silent switch and audio-session behaviour are unknown |
| Hidden tab while recording | KNOWN LIMIT: browsers stop drawing a hidden canvas, so the video freezes while the audio continues |

## Not verified by machine (needs people)

- **Musical quality.** The harmony, timing and mix were designed deliberately (shared 84 bpm clock, D-minor progression, voices
  pitched from the current chord), but no human has listened yet. Please judge by ear, ideally with four people.
- Latency feel on real touch screens and Bluetooth speakers.
- Whether the schematic Palace reads clearly and honestly to a jury.

## Bugs found and fixed during testing

- (test harness) pads below the fold were missed by raw mouse coordinates → the test scrolls each pad into view.
- (test harness) misread CDP `touchEnd` semantics; the demo behaved correctly.
- The single-column phone layout showed only one station per screen, which made multitouch impossible → compact 2×2 grid at ≤ 540 px.
