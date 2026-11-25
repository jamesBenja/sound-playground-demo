# SOUND PLAYGROUND: status report (2026-11-25)

Evidence labels: **VERIFIED** (tested or measured), **NOT TESTED**, **CONCEPT** (design intent only).
The original folders `01_PLAYABLE_DIGITAL_DEMO/` and `02_PHYSICAL_CONSOLE_3D/` are unchanged (checksums verified).

## A. Playable browser demo → `03_OUTPUT_BROWSER_DEMO/`
- **VERIFIED**: 47/47 automated checks in headless Chromium: audio start by gesture, mouse, keys 1–4, focused pad + Space,
  4 simultaneous touches, rotary dials, no clipping at maximum (−2.3 dBFS peak), no stuck notes after 300 random events,
  and 30 s / 3 min / stopped-early recordings that contain VP9 video and stereo Opus audio, plus an ordered, timestamped gesture log.
- **PUBLISHED** with the owner's approval: https://jamesbenja.github.io/sound-playground-demo/ (v0.1 kept at `/v0.1.html`),
  commit 14e0b09 on jamesbenja/sound-playground-demo `main`. The Pages build succeeded. The live URL could not be opened from the build
  environment (network policy), so please check it once in a browser.
- **NOT TESTED**: Firefox, Safari/iOS, real touch hardware, and listening quality by people. Gesture replay is not implemented.
- Not done: the Karlsruhe application was not edited, and no link was added to it.

## B. Physical console model → `04_OUTPUT_3D/`
- **VERIFIED**: one parametric CadQuery source → STEP (74 solids, 2,400 × 840 × 1,532 mm) → Blender 5.3 scene → Cycles renders + GLB.
  STEP and GLB were re-imported and checked. No image generation was used.
- **VERIFIED by script**: all four pad/knob pairs are on the front band; no display, mast, crossbar or speaker part overlaps any control
  in plan (nearest is 224 mm behind). Knee/toe space is 2,060 W × 540 D × 790 H mm.
- Deliverables: three-quarter, plan, front elevation, side section, pad + rotary detail, and human-scale renders; three dimensioned drawing sheets;
  `.blend`, STEP, GLB; MODELING_NOTES.md (including 8 open ergonomic questions).
- **CONCEPT only**: weather resistance, service access, cable routing, speaker directivity, display brightness, structure and anchoring.
  No compliance (IP, accessibility, structural) is claimed.

## Owner decisions (2026-11-25)
1. Overall layout: approved.
2. Speakers: changed to level (0°); the affected views were re-rendered.
3. Width: kept at 2,400 mm.
4. Demo link: added by the owner to the new application iteration. Claude audited that application's text
   (Google Doc "Application audit + revised text"); the original PDF is unchanged.
