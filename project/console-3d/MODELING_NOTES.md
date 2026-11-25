# SOUND PLAYGROUND console: CAD study v2, modelling notes

Design study only. Nothing here claims structural, wind-load, electrical, weather-rating (IP),
vandal-resistance or accessibility compliance. Evidence labels: **VERIFIED** = measured from the model
or checked by script; **CONCEPT** = modelled as a plausible intent, not engineered; **OPEN** = an
unresolved question for the team.

## One model, every output

```
source/build_console_cad.py   (CadQuery, all dimensions are parameters at the top)
   ├─► SOUND_PLAYGROUND_console_v2.step      B-rep assembly, 74 named, coloured parts (editable in FreeCAD, Fusion, Rhino, etc.)
   └─► source/parts/*.stl + parts.json        tessellated parts + bounding boxes
          └─► source/render_console_blender.py  (Blender 5.3 Python, Cycles)
                 ├─► sound_playground_console.blend   editable scene: console, studio, cameras, scale figures
                 ├─► SOUND_PLAYGROUND_console_v2.glb   console only, PBR materials
                 └─► console_*.png, player_pad_rotary_detail.png   (no text on any render)
                        └─► source/make_drawing_sheets.py ─► drawing_*_dimensioned.png  (dimensions computed from parameters + ortho cameras)
```

To change something, edit the parameter block in `build_console_cad.py`, then run the three scripts in
order. Renders are real path-traced geometry (Cycles, CPU, 128 samples, denoised). No image generation was used.
The scale figures and wheelchair are simple clay mannequins built in the Blender script, for scale only.

Rebuild:
```
pip install cadquery bpy        # tested: CadQuery 2.8.0, bpy 5.3.0, Python 3.13
cd source
python3 build_console_cad.py
python3 render_console_blender.py            # all views; e.g. "three_quarter --samples 32 --scale 0.5" for a quick look
python3 make_drawing_sheets.py
```

## Deliverables

| File | What it is |
|---|---|
| `console_three_quarter.png` | main complete-console render, front-left three-quarter, eye height ≈1.6 m |
| `console_top_orthographic.png` | plan (top orthographic) |
| `console_front_elevation.png` | player-side elevation (orthographic) |
| `console_side_section.png` | side view with the right end leg hidden = section through the knee space, with a wheelchair user (extra view) |
| `player_pad_rotary_detail.png` | close-up of the RESONANCE station: pad, bezel, colour ring, encoder knob, tactile dots |
| `console_human_scale.png` | console with three figures: an adult at PULSE, a wheelchair user at RESONANCE, a shorter adult at MOVEMENT |
| `drawing_plan_dimensioned.png`, `drawing_front_dimensioned.png`, `drawing_side_section_dimensioned.png` | dimension sheets (text kept off the renders) |
| `sound_playground_console.blend` | editable Blender scene |
| `SOUND_PLAYGROUND_console_v2.step` / `.glb` | updated CAD and exchange model |

## Geometry (VERIFIED from the model unless marked)

| Element | Value |
|---|---|
| Deck | 2,400 × 840 mm, 60 mm thick, top at **850 mm**, R40 plan corners, R10 top edge |
| Stations | 4 × at x = −900 / −300 / +300 / +900 (600 mm pitch), order PULSE, BREATH, RESONANCE, MOVEMENT left to right as seen by the players |
| Control plate | 520 × 250 × 3 mm brushed stainless, flush in a 3 mm pocket; front edge 40 mm behind the deck edge |
| Pad | **Ø166 mm** frosted polymer diffuser (CONCEPT: LED-backlit, unlit in renders), muted colour ring, Ø200 stainless bezel 6 mm proud; centre 165 mm from the front edge |
| Rotary encoder knob | Ø64 × 40 mm fluted anodised aluminium knob on a Ø96 collar; pointer set to the demo's default dial values; centre 230 mm right of the pad |
| Tactile markers | 1–4 raised Ø8 mm dots at the deck's front edge in front of each pad (station number by touch, no text) |
| Display | 32-inch class in an 800 × 490 × 92 mm enclosure, 740 × 430 mm cover glass, **tilted back 8°**, glass bottom edge at 1,058 mm (208 mm above the deck), enclosure top at 1,514 mm, sun hood to 1,532 mm |
| Display mount | one 140 × 100 mm central mast at the rear (y = 290–390), rising through the deck from the service spine; VESA bracket |
| Speakers | 2 × compact directional housings 280 × 120 × 210 mm, centres at x = ±620, **1,350 mm** high, on pitch-adjustable yokes from a crossbar behind the display; aimed straight and level at their station pair (owner decision 2026-11-25; was 5° down) |
| Clearance, controls → high parts | no screen, mast, crossbar or speaker part overlaps any pad/knob/plate in plan (script check); nearest high part (sun hood front edge) is **224 mm behind** the control plates' rear edge |
| Structure | two 120 mm end legs (set back 160 mm from the front edge), rear service spine 2,060 × 260 mm full height on a recessed 40 mm plinth |
| Knee/toe space | open **2,060 mm wide × 540 mm deep × 790 mm high** under the whole front of the deck |
| Overall | 2,400 W × 840 D × ≈1,532 mm H. Width kept at 2,400 mm (owner decision 2026-11-25) |

## What changed from the v1 schematic

- The v1 had two 570 mm pedestals under the outer stations, so PULSE and MOVEMENT had no knee space. Now the support is two slim
  end legs plus a rear spine, which leaves all four stations open underneath.
- v1 had two screen posts on the deck between the stations. Now there is one central mast at the deck's rear edge, behind the gap
  between BREATH and RESONANCE, and nothing stands near the RESONANCE controls.
- v1 had cube speakers on the rear deck corners at table height. Now the speakers sit at ear height on adjustable yokes either side of the display.
- Added: a sun hood, flush control plates, a pad bezel and colour ring, fluted knobs, tactile station dots, service doors with
  vent slots and locks on the rear spine, plinths, and engraved station dividers.

## Ergonomic and design concerns (OPEN, for the team)

1. **Deck height 850 mm** suits standing adults and wheelchair users (many guidelines give 710–865 mm for reach-over surfaces), but it is high
   for children under about 8. A lower child step or one lowered station is undecided. The local standard (e.g. DIN 18040) still needs checking.
2. **Knee space**: 790 mm clear height and 540 mm depth are drawn to common guidance (≥ 685–700 mm high, ≥ 480 mm deep), not
   verified against any standard. The rear spine bounds the toe space; wheelchair footplates fit in the side section, but this should be
   checked with real chairs, including power chairs.
3. **Station pitch 600 mm** is tight for four adults side by side, and very tight when a wheelchair (≈ 650–700 mm wide) is at a station.
   2,400 mm works for 3 adults + 1 wheelchair user but is snug. Consider 2,600–2,800 mm or angled end stations.
4. **Screen viewing angle**: from the outer stations (x = ±900 mm) the centre of the display is about 48° off-axis at ~0.8 m. That
   is acceptable for IPS-type panels but noticeably skewed. A wider or curved display, or angling the two outer stations inward, would help.
5. **Sightlines** (VERIFIED geometrically): from a seated eye height of 1,200 mm, the line to the bottom of the glass passes about 230 mm above the knob tops,
   so players' hands and knobs do not hide the screen. Standing users (eye ≈1,600 mm) look down about 22° to the screen centre.
6. **Speaker coverage**: the speakers are now level (owner decision). At the players' position (≈0.8 m) the axis is at 1,350 mm, and a ±15°
   cone covers about 1,140–1,560 mm: seated ears (≈1,150–1,250) and most standing adults (≈1,450–1,650), though the tallest are at the edge.
   `spk_pitch` stays a parameter to re-check after listening tests. Driver type (beam-steered array, ultrasonic
   parametric or small horn), real directivity and spill into the square are **not engineered**.
7. **Glare and sun**: the 8° tilt and the hood are a concept response. Outdoor daylight readability requires a high-brightness
   (≥ 1,500–2,500 nit) panel, optical bonding and a thermal plan; none of that is specified.
8. **Reach to the dial**: the knob is 230 mm to the right of the pad, which favours right-handed reaching. A left-handed player can use it, but it is worth testing.

## Weather, service and cabling (CONCEPT only)

- Sloped (filleted) deck edges and a flush plate pocket shed water. The pocket would need drainage or a sealed gasket, which is not modelled.
- Electronics are intended in the rear spine (computer, audio interface, amplifiers, power), behind two lockable rear doors
  with low vent slots. The thermal design is open.
- Cable route (not modelled internally): each station plate is screwed down over a sealed cut-out; cables run inside the 60 mm deck
  to the spine; the display and speaker cables rise inside the hollow mast and crossbar.
- Plinths are recessed 15 mm for toe clearance. Anchoring or ballast to the square's paving is **not designed**.
- Materials are drawn as powder-coated steel/aluminium (light grey deck, darker core), brushed stainless control plates and an anodised knob.
  No vandal or fire rating is claimed.

## Known model simplifications

- Pads are solid bodies (no LED, diffuser stack or sensor internals). Knobs are not separate encoder parts.
- Speaker grilles use a procedural perforation texture, not modelled holes.
- The display is shown switched off (dark glass). No screen content is rendered, to avoid implying any Palace output.
- The scale figures are simple mannequins; the wheelchair is generic and not a specific product.
