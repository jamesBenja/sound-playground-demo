# SOUND PLAYGROUND: project files (handoff for collaborators and other AI assistants)

This folder holds the working files behind the playable sketch at the root of this repository
(https://jamesbenja.github.io/sound-playground-demo/). The festival application itself is **not** stored here; it lives in the team's private Drive.

Status as of 2026-11-25. Evidence labels: VERIFIED = tested or measured; CONCEPT = design intent only.

## Layout

```
project/
  STATUS_REPORT.md                 what is verified, what is concept, owner decisions
  browser-demo/                    sketch 0.2: source docs and tests (the live file is ../index.html)
    README.md                      how it works, what changed from v0.1, limitations
    TEST_RESULTS.md                47/47 automated checks (VERIFIED), untested browsers
    tests/run_tests.cjs            Playwright + ffmpeg test (node tests/run_tests.cjs --long)
    examples/                      30 s recording + gesture log, stopped-early recording, screenshots
  console-3d/                      physical console, CAD study v2 (one parametric model)
    MODELING_NOTES.md              dimensions, ergonomics, open questions; read this first
    console_*.png, player_pad_rotary_detail.png     Cycles renders of the real geometry (no text on them)
    drawing_*_dimensioned.png      dimension sheets
    SOUND_PLAYGROUND_console_v2.step / .glb         CAD + exchange model
    sound_playground_console.blend                  Blender 5.3 scene (cameras, materials, scale figures)
    source/build_console_cad.py    CadQuery: ALL dimensions are parameters at the top -> STEP + parts
    source/render_console_blender.py   Blender (bpy) assembly + renders + .blend + GLB
    source/make_drawing_sheets.py  dimension sheets from the ortho renders
```

## Ground rules for anyone continuing this work

- The browser sketch is a Web Audio approximation. Do not present it as the Max/MSP instrument, Notch output or festival mapping.
- The 3D files are a design study. Do not claim weather (IP), structural, accessibility or electrical compliance.
- Keep the shared design: four stations (PULSE, BREATH, RESONANCE, MOVEMENT), each with one pad and one rotary control on the front band, one shared screen behind them, and two compact directional speakers.
- Change geometry in `build_console_cad.py` (parameters), then rebuild: `build_console_cad.py` → `render_console_blender.py` → `make_drawing_sheets.py`.
  Tested with CadQuery 2.8.0 and bpy 5.3.0 (`pip install cadquery bpy`).
- Any change to the live demo (`../index.html`) goes live on GitHub Pages as soon as it is pushed to `main`. Run the tests first and get the owner's approval.

## Owner decisions so far (2026-11-25)

Layout approved · speakers level (0°) · width kept at 2,400 mm · demo v0.2 published · v0.1 kept at ../v0.1.html.
