"""SOUND PLAYGROUND console, CAD study v2 (parametric, CadQuery).

Single source of geometry for every 3D deliverable:
  -> ../SOUND_PLAYGROUND_console_v2.step     (B-rep assembly, named + coloured parts)
  -> parts/*.stl + parts/parts.json           (tessellated parts read by render_console_blender.py)

Units: millimetres. Origin: floor level, centre of the console.
Axes: +X to the players' right, -Y towards the players (front edge), +Z up.
This is a design study. Nothing here is a structural, electrical, weather (IP),
or accessibility certification.
"""
import json, math
from pathlib import Path
import cadquery as cq

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
PARTS = HERE / "parts"
PARTS.mkdir(exist_ok=True)

# ---------------- key parameters (edit here) ----------------
P = dict(
    width=2400, depth=840, deck_top=850, deck_thk=60,
    station_x=[-900, -300, 300, 900],            # PULSE, BREATH, RESONANCE, MOVEMENT
    station_names=["PULSE", "BREATH", "RESONANCE", "MOVEMENT"],
    plate_w=520, plate_d=250, plate_cy=-255,     # control plate centre; plate front edge 40 mm behind deck edge
    pad_dx=-95, pad_d=166,                       # tactile pad diameter
    knob_dx=135, knob_d=64, knob_h=40,
    knob_values=[0.45, 0.50, 0.40, 0.75],        # pointer angles = demo default dial values
    leg_x=(1030, 1150), leg_y=(-260, 380),       # end legs, set back 160 mm from front edge
    spine_y=(120, 380),                          # rear service spine -> 540 mm clear knee depth
    plinth_h=40,
    mast_y=(290, 390), mast_w=140, mast_top=1365,
    screen_outer=(800, 92, 490), screen_glass=(740, 430), screen_cy=200, screen_cz=1265, screen_tilt=8,
    spk_size=(280, 120, 210), spk_x=620, spk_cy=200, spk_cz=1350, spk_pitch=0,
)

MAT = {}      # part name -> material key
SHAPES = {}   # part name -> cq.Workplane


def add(name, wp, mat):
    assert name not in SHAPES, name
    SHAPES[name] = wp
    MAT[name] = mat


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(x, y, z0, r, h):
    return cq.Workplane("XY").circle(r).extrude(h).translate((x, y, z0))


def fillet(wp, sel, r):
    try:
        return wp.edges(sel).fillet(r)
    except Exception:
        return wp


W, D, TOP, T = P["width"], P["depth"], P["deck_top"], P["deck_thk"]
FY = -D / 2  # front edge y

# ---------------- deck ----------------
deck = box(-W / 2, W / 2, -D / 2, D / 2, TOP - T, TOP)
deck = fillet(deck, "|Z", 40)
deck = fillet(deck, ">Z", 10)
deck = fillet(deck, "<Z", 4)
for sx in P["station_x"]:  # shallow pockets for flush control plates
    deck = deck.cut(box(sx - P["plate_w"] / 2 - 2, sx + P["plate_w"] / 2 + 2,
                        P["plate_cy"] - P["plate_d"] / 2 - 2, P["plate_cy"] + P["plate_d"] / 2 + 2, TOP - 3, TOP + 1))
for gx in (-600, 0, 600):  # engraved station dividers in the front band only
    deck = deck.cut(box(gx - 1, gx + 1, FY - 5, FY + 290, TOP - 1, TOP + 1))
# mast pass-through
deck = deck.cut(box(-P["mast_w"] / 2, P["mast_w"] / 2, P["mast_y"][0], P["mast_y"][1], TOP - T - 1, TOP + 1))
add("deck_top", deck, "powder_light")

# ---------------- player stations ----------------
for i, (sx, nm) in enumerate(zip(P["station_x"], P["station_names"])):
    key = nm.lower()
    cy = P["plate_cy"]
    plate = box(sx - P["plate_w"] / 2, sx + P["plate_w"] / 2, cy - P["plate_d"] / 2, cy + P["plate_d"] / 2, TOP - 3, TOP)
    plate = fillet(plate, "|Z", 12)
    px, kx = sx + P["pad_dx"], sx + P["knob_dx"]
    plate = plate.cut(cyl(px, cy, TOP - 4, 90, 6))
    add(f"{key}_control_plate", plate, "stainless")
    for dx in (-P["plate_w"] / 2 + 18, P["plate_w"] / 2 - 18):
        for dy in (-P["plate_d"] / 2 + 18, P["plate_d"] / 2 - 18):
            add(f"{key}_screw_{'L' if dx < 0 else 'R'}{'F' if dy < 0 else 'B'}", cyl(sx + dx, cy + dy, TOP, 4.5, 0.6), "stainless_dark")
    # pad: stainless bezel, muted colour ring, frosted illuminated diffuser (166 mm)
    r = P["pad_d"] / 2
    bezel = cyl(px, cy, TOP - 3, r + 17, 9).cut(cyl(px, cy, TOP - 4, r + 6, 12))
    bezel = fillet(bezel, ">Z", 2.5)
    add(f"{key}_pad_bezel", bezel, "stainless")
    ring = cyl(px, cy, TOP - 3, r + 6, 8.0).cut(cyl(px, cy, TOP - 4, r + 3, 12))
    add(f"{key}_pad_colour_ring", ring, f"accent_{key}")
    pad = cyl(px, cy, TOP - 3, r, 10.5)
    pad = fillet(pad, ">Z", 6)
    add(f"{key}_pad_diffuser", pad, "diffuser")
    # rotary encoder knob: collar + fluted body + pointer groove
    collar = fillet(cyl(kx, cy, TOP, 48, 4), ">Z", 1.5)
    add(f"{key}_knob_collar", collar, "stainless")
    kr, kh = P["knob_d"] / 2, P["knob_h"]
    knob = cyl(0, 0, 0, kr, kh)
    knob = fillet(knob, ">Z", 3)
    for j in range(18):
        a = 2 * math.pi * j / 18
        knob = knob.cut(cyl((kr + 1.2) * math.cos(a), (kr + 1.2) * math.sin(a), 4, 3.0, kh))
    knob = knob.cut(box(-1.75, 1.75, 4, kr - 6, kh - 1.6, kh + 1))  # pointer groove towards local +Y
    ang = -135 + 270 * P["knob_values"][i]                        # clockwise from 12 o'clock
    knob = knob.rotate((0, 0, 0), (0, 0, 1), -ang).translate((kx, cy, TOP + 4))
    add(f"{key}_knob", knob, "anodised_dark")
    # tactile station markers (1-4 raised dots) at the front edge, no text
    for j in range(i + 1):
        dot = cq.Workplane("XY").sphere(4).translate((px - (i * 7) + j * 14, FY + 22, TOP - 1.5))
        add(f"{key}_tactile_dot_{j + 1}", dot, "powder_light")

# ---------------- structure ----------------
lx0, lx1 = P["leg_x"]
ly0, ly1 = P["leg_y"]
PH = P["plinth_h"]
for side, s in (("left", -1), ("right", 1)):
    leg = box(min(s * lx0, s * lx1), max(s * lx0, s * lx1), ly0, ly1, PH, TOP - T)
    leg = fillet(leg, "|Z", 16)
    add(f"{side}_end_leg", leg, "powder_mid")
    add(f"{side}_leg_plinth", box(min(s * (lx0 + 15), s * (lx1 - 15)), max(s * (lx0 + 15), s * (lx1 - 15)), ly0 + 15, ly1 - 15, 0, PH), "plinth")

sy0, sy1 = P["spine_y"]
spine = box(-lx0, lx0, sy0, sy1, PH, TOP - T)
# two lockable rear service doors (3 mm seams), vent slots, lock barrels
for x0, x1 in ((-1000, -15), (15, 1000)):
    seam = box(x0, x1, sy1 - 3, sy1 + 1, PH + 40, TOP - T - 40).cut(box(x0 + 3, x1 - 3, sy1 - 4, sy1 + 2, PH + 43, TOP - T - 43))
    spine = spine.cut(seam)
    for k in range(10):
        vx = x0 + 90 + k * ((x1 - x0) - 180) / 9
        spine = spine.cut(box(vx - 35, vx + 35, sy1 - 6, sy1 + 1, PH + 70, PH + 76))
        spine = spine.cut(box(vx - 35, vx + 35, sy1 - 6, sy1 + 1, PH + 90, PH + 96))
add("rear_service_spine", spine, "powder_core")
for x in (-60, 60):
    add(f"service_door_lock_{'L' if x < 0 else 'R'}",
        cq.Workplane("XZ").circle(11).extrude(-6).translate((x, sy1, 560)), "stainless_dark")
add("spine_plinth", box(-lx0 + 15, lx0 - 15, sy0 + 15, sy1 - 15, 0, PH), "plinth")

# ---------------- screen mast, crossbar, display ----------------
my0, my1 = P["mast_y"]
mw = P["mast_w"]
mast = box(-mw / 2, mw / 2, my0, my1, TOP - T, P["mast_top"])
mast = fillet(mast, "|Z", 8)
add("screen_mast", mast, "powder_dark")
add("mast_base_flange", fillet(box(-110, 110, my0 - 25, min(my1 + 25, D / 2 - 5), TOP, TOP + 8), "|Z", 6), "powder_dark")
cb_z = P["spk_cz"] - 15
add("speaker_crossbar", fillet(box(-640, 640, my0 + 15, my0 + 75, cb_z - 30, cb_z + 30), "|X", 6), "powder_dark")

sw, sd, sh = P["screen_outer"]
gw, gh = P["screen_glass"]
housing = box(-sw / 2, sw / 2, -sd / 2, sd / 2, -sh / 2, sh / 2)
housing = fillet(housing, "|Y", 14)
housing = housing.cut(box(-gw / 2 - 4, gw / 2 + 4, -sd / 2 - 1, -sd / 2 + 5, -gh / 2 - 4, gh / 2 + 4))
glass = box(-gw / 2, gw / 2, -sd / 2 + 1.5, -sd / 2 + 5, -gh / 2, gh / 2)
hood = box(-sw / 2 - 10, sw / 2 + 10, -sd / 2 - 95, sd / 2, sh / 2, sh / 2 + 5)
for s in (-1, 1):
    cheek = (cq.Workplane("YZ").polyline([(-sd / 2, sh / 2), (-sd / 2 - 95, sh / 2), (-sd / 2, sh / 2 - 120)]).close()
             .extrude(5).translate((s * (sw / 2 + 10) - (5 if s > 0 else 0), 0, 0)))
    hood = hood.union(cheek)
vesa = box(-100, 100, sd / 2, sd / 2 + (my0 - (P["screen_cy"] + sd / 2)) + 6, -100, 100)


def place_screen(wp):
    return wp.rotate((0, 0, 0), (1, 0, 0), -P["screen_tilt"]).translate((0, P["screen_cy"], P["screen_cz"]))


add("display_enclosure_32in", place_screen(housing), "powder_dark")
add("display_glass", place_screen(glass), "screen_glass")
add("display_sun_hood", place_screen(hood), "powder_dark")
add("display_vesa_bracket", place_screen(vesa), "stainless_dark")

# ---------------- two compact directional loudspeakers on adjustable yokes ----------------
kw, kd, kh = P["spk_size"]
for side, s in (("left", -1), ("right", 1)):
    body = fillet(box(-kw / 2, kw / 2, -kd / 2, kd / 2, -kh / 2, kh / 2), "|Y", 12)
    body = fillet(body, "<Y", 3)
    body = body.cut(box(-kw / 2 + 12, kw / 2 - 12, -kd / 2 - 1, -kd / 2 + 4, -kh / 2 + 12, kh / 2 - 12))
    grille = box(-kw / 2 + 13, kw / 2 - 13, -kd / 2 + 1.5, -kd / 2 + 4, -kh / 2 + 13, kh / 2 - 13)
    # yoke: two side cheeks with pivot axle (pitch adjustable), rear bar, short arm to the crossbar
    yoke = box(-kw / 2 - 14, -kw / 2 - 4, -30, kd / 2 + 25, -32, 32).union(box(kw / 2 + 4, kw / 2 + 14, -30, kd / 2 + 25, -32, 32))
    yoke = yoke.union(box(-kw / 2 - 14, kw / 2 + 14, kd / 2 + 10, kd / 2 + 25, -32, 32))
    pivots = cq.Workplane("YZ").circle(13).extrude(kw + 36).translate((-kw / 2 - 18, 0, 0))
    arm = box(-25, 25, kd / 2 + 25, (my0 + 15) - P["spk_cy"] + 2, -25, 25)
    def place(wp, pitch=True):
        if pitch:
            wp = wp.rotate((0, 0, 0), (1, 0, 0), P["spk_pitch"])
        return wp.translate((s * P["spk_x"], P["spk_cy"], P["spk_cz"]))

    add(f"{side}_directional_speaker", place(body), "powder_dark")
    add(f"{side}_speaker_grille", place(grille), "grille")
    add(f"{side}_speaker_yoke", place(yoke, False).union(place(pivots, False)), "stainless_dark")
    add(f"{side}_speaker_arm", place(arm.translate((0, 0, -15)), False), "powder_dark")

# ---------------- export ----------------
COL = {  # approximate RGB for STEP colours (render materials are defined in Blender)
    "powder_light": (0.79, 0.80, 0.78), "powder_mid": (0.62, 0.64, 0.64), "powder_dark": (0.23, 0.25, 0.26),
    "plinth": (0.18, 0.19, 0.20), "powder_core": (0.33, 0.35, 0.36), "stainless": (0.72, 0.73, 0.72), "stainless_dark": (0.45, 0.46, 0.46),
    "diffuser": (0.93, 0.93, 0.90), "anodised_dark": (0.22, 0.23, 0.24), "screen_glass": (0.03, 0.03, 0.04),
    "grille": (0.17, 0.18, 0.19), "accent_pulse": (0.42, 0.62, 0.67), "accent_breath": (0.56, 0.51, 0.65),
    "accent_resonance": (0.72, 0.62, 0.44), "accent_movement": (0.66, 0.52, 0.55),
}
asm = cq.Assembly(name="SOUND_PLAYGROUND_console_v2")
manifest = []
for name, wp in SHAPES.items():
    shape = wp.val() if len(wp.vals()) == 1 else cq.Compound.makeCompound(wp.vals())
    asm.add(shape, name=name, color=cq.Color(*COL[MAT[name]]))
    stl = PARTS / f"{name}.stl"
    cq.exporters.export(shape, str(stl), tolerance=0.15, angularTolerance=0.08)
    bb = shape.BoundingBox()
    manifest.append(dict(name=name, material=MAT[name], stl=stl.name,
                         bbox_mm=[round(v, 1) for v in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)]))
asm.save(str(OUT / "SOUND_PLAYGROUND_console_v2.step"))
(PARTS / "parts.json").write_text(json.dumps(dict(parameters=P, parts=manifest), indent=1))
print(f"{len(manifest)} parts exported")
