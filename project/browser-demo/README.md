# SOUND PLAYGROUND: interactive digital sketch 0.2

A single-file browser instrument for four players: **PULSE, BREATH, RESONANCE, MOVEMENT**.
Each station has one pad and one rotary dial, as on the planned physical console, and the
four voices drive one shared schematic Palace preview.

> **This is a prototype, not the installation.** Sound is synthesised in the browser with
> the Web Audio API; it is not the Max/MSP instrument. The Palace image is a simplified
> schematic elevation. It is not festival projection-mapping geometry and not a Notch render.

## Open it

1. Double-click `index.html` (current Chrome, Edge or Firefox). No install, build or server is needed.
2. Press **Enable sound**, or simply press any pad (that also counts as the sound-start gesture).
3. Hold pads with the mouse, with fingers (multitouch, up to four at once), or with keys **1 2 3 4**.
   A focused pad also responds to Space/Enter.
4. Turn a dial by dragging around it, scrolling over it, or with the arrow / PageUp / PageDown / Home / End keys.
5. **Record 30 s** or **Record 3 min**, play, and stop early if you like. Two links appear:
   a video file with sound (`.webm`; `.mp4` on browsers that only record MP4) and a gesture log (`.json`).
   Nothing is uploaded.

## What each station does

| Station | Pad | Dial | Shared screen |
|---|---|---|---|
| **PULSE** (rhythm) | tap = one beat; hold = groove on the chord root | **Density**: 5 rhythm patterns, from half notes to syncopated 16ths with ghost notes | windows flash in time |
| **BREATH** (atmosphere) | hold = swelling, breathing chord pad that follows the harmony; release = 1 s fade | **Tone**: filter brightness | violet wash over the roof and sky |
| **RESONANCE** (harmony) | strike = strummed bell chord; hold = repeats on beats 1 and 3+ | **Colour**: adds the 9th / 7th tones, brightens, tightens the strum | amber pilasters on the central block |
| **MOVEMENT** (space) | hold = arpeggio that travels across the stereo field | **Direction**: right half sweeps left→right, left half right→left; further from centre = faster; centre = gentle swing | a light band follows the sound's position |

All voices share one clock (84 bpm) and one D-minor progression that changes every two bars:
**D minor → B♭ major 7 → G minor 9 → A sus4**. That is why any combination stays in key and in time.
The current chord is shown on the shared screen.

## Changes from v0.1

- **Audio start**: one AudioContext only, created on the first gesture; pressing Enable again does nothing
  harmful; the button and status follow the real context state (including a browser suspending it). The first touch on
  a phone also starts sound (pointerup fallback, because touch `pointerdown` is not a user activation in Chrome).
- **Stuck notes**: each pad tracks the set of pointers/keys holding it. `pointerup`, `pointercancel` and
  `lostpointercapture` may all fire; release happens once, when the last holder lets go. Window blur and a hidden
  tab release everything. Key auto-repeat is ignored.
- **Multitouch**: four fingers on four pads work independently, and lifting one finger releases only its pad.
- **Clipping**: master → compressor (-10 dB threshold, 16:1) → soft-clip ceiling at 0.94 (-0.5 dBFS). Measured worst case
  with everything at maximum: peak about -2.5 dBFS (see TEST_RESULTS.md).
- **Musicality**: a shared harmonic clock, voices pitched from the current chord, a generated room reverb, and a sustained
  BREATH pad that glides between chords (v0.1 used filtered noise over a fixed 110 Hz tone).
- **Rotary dials** replace the linear sliders, matching the physical encoders.
- **Recording**: the files carry the true duration and a stop reason (`timer` / `user`). The log has an audio-clock time for
  every gesture, plus the musical step and chord, the initial dial values, tempo and progression. The 3-minute
  recording was tested end to end. An MP4 fallback is coded for browsers without WebM recording (Safari), but it is untested.
- **Palace**: a cleaner schematic of the central block, tower, wings and mansard roofs, labelled on-canvas as schematic
  (the label is part of every recorded video).
- **Layout**: on phones the four stations sit in a compact 2×2 grid, so all of them fit on one screen for multitouch.

## Files

- `index.html`: the whole demo (HTML, CSS, JS; no dependencies, no network requests).
- `TEST_RESULTS.md`: what was tested, how, results, and what is untested.
- `tests/run_tests.cjs`: automated Playwright + ffmpeg test (`node tests/run_tests.cjs`, add `--long` for the 3-minute recording).
- `examples/`: a 30-second recording with its gesture log, a stopped-early recording, the 3-minute gesture log, and screenshots.

## Known limitations (be explicit with the jury)

- Gesture logs are not replayed. The log has enough to reconstruct a performance (clock, step, chord, dial values),
  but deterministic replay is **not implemented**.
- Recording relies on `canvas.captureStream` + `MediaRecorder`. If the tab is hidden, the browser stops drawing the canvas and
  the video freezes. Keep the tab visible while recording.
- Only Chromium was tested automatically. Firefox, Safari (desktop and iOS) and real touch hardware still need a manual pass.
- `window.SoundPlaygroundTest` is a read-only status hook used by the automated test. It changes no behaviour.
- Hosting: if it is ever published, label it "Interactive digital sketch" and only after the artists approve it. **It has not been published.**
