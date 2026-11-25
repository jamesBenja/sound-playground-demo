"""Assemble the CadQuery parts in Blender, assign neutral materials, render with Cycles.

Run:  python3 render_console_blender.py [view ...] [--samples N] [--scale 0.5] [--no-save | --save-only]
Views: three_quarter top front side detail human   (default: all)
Reads parts/parts.json + parts/*.stl written by build_console_cad.py (the one geometry source).
Writes ../console_*.png, ../player_pad_rotary_detail.png, ../sound_playground_console.blend,
       ../SOUND_PLAYGROUND_console_v2.glb, ../renders_meta.json (camera data for drawing sheets).
"""
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
PARTS = HERE / "parts"
man = json.loads((PARTS / "parts.json").read_text())
P = man["parameters"]

args = sys.argv[1:]
SAMPLES = int(args[args.index("--samples") + 1]) if "--samples" in args else 160
SCALE = float(args[args.index("--scale") + 1]) if "--scale" in args else 1.0
SAVE = "--no-save" not in args
VIEWS = [a for a in args if a in ("three_quarter", "top", "front", "side", "detail", "human")] or \
        ["three_quarter", "top", "front", "side", "detail", "human"]

# ---------------- clean scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.system = "METRIC"
scn.unit_settings.length_unit = "MILLIMETERS"


def col(name):
    c = bpy.data.collections.new(name)
    scn.collection.children.link(c)
    return c


C_CONSOLE, C_ENV, C_PEOPLE = col("Console (from CadQuery)"), col("Studio"), col("Scale figures")
C_STAND = bpy.data.collections.new("Standing figures"); C_PEOPLE.children.link(C_STAND)
C_WHEEL = bpy.data.collections.new("Wheelchair user"); C_PEOPLE.children.link(C_WHEEL)
CURRENT = [C_STAND]


def hexrgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in srgb) + (1.0,)


# ---------------- materials ----------------
def principled(name, color, rough=0.5, metal=0.0, coat=0.0, spec=0.5, bump=None, sss=0.0, aniso=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexrgb(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    if aniso:
        b.inputs["Anisotropic"].default_value = aniso
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.004, 0.004, 0.004)
    if bump:
        kind, scale, strength = bump
        tc = nt.nodes.new("ShaderNodeTexCoord")
        if kind == "peel":     # powder-coat orange peel
            tex = nt.nodes.new("ShaderNodeTexNoise"); tex.inputs["Scale"].default_value = scale; tex.inputs["Detail"].default_value = 4
            out = tex.outputs["Fac"]
        else:                  # perforated grille: regular dot grid
            tex = nt.nodes.new("ShaderNodeTexVoronoi"); tex.inputs["Scale"].default_value = scale; tex.inputs["Randomness"].default_value = 0.0
            ramp = nt.nodes.new("ShaderNodeMapRange"); ramp.inputs["From Min"].default_value = 0.22; ramp.inputs["From Max"].default_value = 0.3
            nt.links.new(tex.outputs["Distance"], ramp.inputs["Value"]); out = ramp.outputs["Result"]
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
            mix.inputs["A"].default_value = hexrgb("#0b0c0d"); mix.inputs["B"].default_value = hexrgb(color)
            nt.links.new(out, mix.inputs["Factor"]); nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = strength; bn.inputs["Distance"].default_value = 0.001
        nt.links.new(out, bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


MATS = {
    "powder_light":   principled("Powder coat RAL 7035-like light grey", "#c9cbc6", 0.52, bump=("peel", 900, 0.06)),
    "powder_mid":     principled("Powder coat mid grey", "#7f8484", 0.55, bump=("peel", 900, 0.06)),
    "powder_dark":    principled("Powder coat anthracite", "#3b3f42", 0.5, bump=("peel", 900, 0.05)),
    "powder_core":    principled("Powder coat dark grey (recessed core)", "#575c5e", 0.55, bump=("peel", 900, 0.05)),
    "plinth":         principled("Plinth dark grey", "#2c2f31", 0.7),
    "stainless":      principled("Brushed stainless", "#b9bcbb", 0.3, metal=1.0, aniso=0.4),
    "stainless_dark": principled("Bead-blasted stainless", "#8d908f", 0.45, metal=1.0),
    "diffuser":       principled("Frosted polymer pad (unlit)", "#ecebe4", 0.42, coat=0.15, sss=0.25),
    "anodised_dark":  principled("Anodised aluminium knob", "#3c3f42", 0.38, metal=0.85),
    "screen_glass":   principled("Display cover glass (off)", "#060708", 0.12, coat=0.25, spec=0.25),
    "grille":         principled("Perforated speaker grille", "#34383a", 0.6, metal=0.6, bump=("grille", 280, 0.25)),
    "accent_pulse":     principled("Station ring PULSE", "#6f98a3", 0.5),
    "accent_breath":    principled("Station ring BREATH", "#8c829f", 0.5),
    "accent_resonance": principled("Station ring RESONANCE", "#b49f78", 0.5),
    "accent_movement":  principled("Station ring MOVEMENT", "#a08589", 0.5),
}
CLAY = principled("Scale figure clay", "#d8d5ce", 0.75)
FLOOR = principled("Studio floor", "#dcdcd8", 0.85)

# ---------------- import console parts (mm -> m) ----------------
console_objs = []
for part in man["parts"]:
    bpy.ops.wm.stl_import(filepath=str(PARTS / part["stl"]), global_scale=0.001)
    ob = bpy.context.selected_objects[0]
    ob.name = part["name"]
    for c in ob.users_collection:
        c.objects.unlink(ob)
    C_CONSOLE.objects.link(ob)
    ob.data.materials.append(MATS[part["material"]])
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    ob.select_set(False)
    console_objs.append(ob)

# ---------------- studio: floor cyclorama + daylight ----------------
bpy.ops.mesh.primitive_plane_add(size=1)
floor = bpy.context.object; floor.name = "floor_cyclorama"
for c in floor.users_collection: c.objects.unlink(floor)
C_ENV.objects.link(floor)
me = floor.data
import bmesh
bm = bmesh.new()
R, Wd, Yb = 4.0, 140.0, 7.0   # curved back wall behind the console (no visible horizon line)
prof = [(-30.0, 0.0)] + [(Yb + R * math.sin(a), R - R * math.cos(a)) for a in [i * (math.pi / 2) / 16 for i in range(17)]] + [(Yb + R, 14.0)]
verts = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-Wd / 2, Wd / 2)]
for i in range(len(prof) - 1):
    bm.faces.new((verts[0][i], verts[1][i], verts[1][i + 1], verts[0][i + 1]))
bm.to_mesh(me); bm.free()
me.materials.append(FLOOR)
for p in me.polygons: p.use_smooth = True

world = bpy.data.worlds.new("Studio daylight"); scn.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = hexrgb("#eef0f1"); bg.inputs["Strength"].default_value = 0.75

sun = bpy.data.lights.new("Sun (soft daylight)", "SUN")
sun.energy = 2.6; sun.angle = math.radians(9); sun.color = (1.0, 0.985, 0.96)
so = bpy.data.objects.new("Sun", sun); C_ENV.objects.link(so)
so.rotation_euler = (math.radians(42), 0, math.radians(-32))   # from front-left, high

area = bpy.data.lights.new("Softbox", "AREA")
area.energy = 900; area.size = 3.0; area.color = (0.97, 0.98, 1.0)
ao = bpy.data.objects.new("Softbox", area); C_ENV.objects.link(ao)
ao.location = (2.6, -3.2, 3.0)
ao.rotation_euler = (Vector((0, 0, 0.9)) - ao.location).to_track_quat("-Z", "Y").to_euler()


# ---------------- scale figures (neutral clay mannequins) ----------------
def link_people(ob):
    for c in ob.users_collection: c.objects.unlink(ob)
    CURRENT[0].objects.link(ob)
    ob.data.materials.append(CLAY)
    for p in ob.data.polygons: p.use_smooth = True
    return ob


def capsule(a, b, r, r2=None, name="limb"):
    a, b = Vector(a), Vector(b); r2 = r if r2 is None else r2
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r, radius2=r2, depth=d.length, location=(a + b) / 2)
    ob = bpy.context.object; ob.name = name
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    link_people(ob)
    for p, rr in ((a, r), (b, r2)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=rr, location=p)
        link_people(bpy.context.object)
    return ob


def ellipsoid(c, sx, sy, sz, name="mass"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=c)
    ob = bpy.context.object; ob.name = name; ob.scale = (sx, sy, sz)
    return link_people(ob)


def ik(shoulder, hand, upper, fore, pole):
    s, h = Vector(shoulder), Vector(hand)
    d = h - s; L = min(d.length, upper + fore - 1e-4)
    a = (upper ** 2 - fore ** 2 + L ** 2) / (2 * L)
    hgt = math.sqrt(max(upper ** 2 - a ** 2, 0))
    dn = d.normalized(); pv = Vector(pole) - dn * Vector(pole).dot(dn); pv.normalize()
    return s + dn * a + pv * hgt


def person_standing(x, y_feet, height, hands, lean=0.0):
    k = height / 1.75
    hip_z, sh_z = 0.93 * k, 1.43 * k
    hip = Vector((x, y_feet + 0.02, hip_z))
    chest = Vector((x, y_feet + 0.02 + lean, sh_z - 0.10 * k))
    for sx in (-1, 1):
        ankle = Vector((x + sx * 0.10 * k, y_feet, 0.08 * k)); knee = Vector((x + sx * 0.10 * k, y_feet + 0.03, 0.49 * k))
        capsule(hip + Vector((sx * 0.09 * k, 0, 0)), knee, 0.075 * k, 0.055 * k, "thigh")
        capsule(knee, ankle, 0.052 * k, 0.04 * k, "shin")
        capsule(ankle, ankle + Vector((0, 0.17 * k, -0.04 * k)), 0.04 * k, 0.035 * k, "foot")
    ellipsoid(hip + Vector((0, 0, 0.04 * k)), 0.165 * k, 0.11 * k, 0.12 * k, "pelvis")
    capsule(hip + Vector((0, 0, 0.1 * k)), chest, 0.13 * k, 0.15 * k, "torso")
    ellipsoid(chest + Vector((0, 0, 0.02 * k)), 0.19 * k, 0.11 * k, 0.12 * k, "chest")
    neck = chest + Vector((0, 0.02, 0.16 * k))
    capsule(chest + Vector((0, 0, 0.08 * k)), neck, 0.05 * k, 0.045 * k, "neck")
    ellipsoid(neck + Vector((0, 0.03 * k, 0.12 * k)), 0.085 * k, 0.1 * k, 0.115 * k, "head")
    for sx, hand in zip((-1, 1), hands):
        sh = chest + Vector((sx * 0.19 * k, 0, 0.08 * k))
        el = ik(sh, hand, 0.30 * k, 0.27 * k, (sx * 0.6, -0.3, -1))
        capsule(sh, el, 0.048 * k, 0.04 * k, "upper_arm")
        capsule(el, hand, 0.038 * k, 0.03 * k, "forearm")
        ellipsoid(Vector(hand) + Vector((0, 0.02, 0.01)), 0.04 * k, 0.07 * k, 0.022 * k, "hand")


def wheelchair_user(x, y_hip, hands):
    seat_z = 0.49
    hip = Vector((x, y_hip, seat_z + 0.07))
    for sx in (-1, 1):  # chair: rear wheels, push rims, casters, frame, seat, back
        wx = x + sx * 0.30
        bpy.ops.mesh.primitive_torus_add(major_radius=0.29, minor_radius=0.014, location=(wx, y_hip - 0.02, 0.30), rotation=(0, math.radians(90), 0))
        link_people(bpy.context.object)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.26, minor_radius=0.007, location=(wx + sx * 0.03, y_hip - 0.02, 0.30), rotation=(0, math.radians(90), 0))
        link_people(bpy.context.object)
        capsule((wx, y_hip - 0.02, 0.30), (x + sx * 0.21, y_hip - 0.02, 0.30), 0.02, name="axle")
        bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.018, location=(x + sx * 0.2, y_hip + 0.40, 0.075), rotation=(0, math.radians(90), 0))
        link_people(bpy.context.object)
        capsule((x + sx * 0.21, y_hip + 0.40, 0.14), (x + sx * 0.21, y_hip + 0.40, seat_z - 0.02), 0.012, name="caster_fork")
        capsule((x + sx * 0.21, y_hip - 0.12, seat_z - 0.02), (x + sx * 0.21, y_hip + 0.40, seat_z - 0.02), 0.013, name="seat_rail")
        capsule((x + sx * 0.21, y_hip - 0.12, seat_z - 0.02), (x + sx * 0.21, y_hip - 0.16, 0.92), 0.013, name="back_post")
        capsule((x + sx * 0.21, y_hip + 0.40, seat_z - 0.02), (x + sx * 0.15, y_hip + 0.50, 0.12), 0.012, name="footrest_hanger")
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y_hip + 0.12, seat_z)); s = bpy.context.object; s.scale = (0.42, 0.44, 0.04); link_people(s)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y_hip - 0.15, 0.72)); s = bpy.context.object; s.scale = (0.40, 0.03, 0.34); link_people(s)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y_hip + 0.52, 0.11)); s = bpy.context.object; s.scale = (0.34, 0.14, 0.02); link_people(s)
    # occupant: thighs forward under the deck, shins down to the footplate
    for sx in (-1, 1):
        knee = Vector((x + sx * 0.10, y_hip + 0.42, seat_z + 0.10))
        ankle = Vector((x + sx * 0.10, y_hip + 0.48, 0.17))
        capsule(hip + Vector((sx * 0.10, 0, 0)), knee, 0.08, 0.058, "thigh")
        capsule(knee, ankle, 0.052, 0.04, "shin")
        capsule(ankle, ankle + Vector((0, 0.16, -0.035)), 0.04, 0.034, "foot")
    ellipsoid(hip + Vector((0, 0, 0.02)), 0.17, 0.12, 0.1, "pelvis")
    chest = hip + Vector((0, 0.07, 0.44))
    capsule(hip + Vector((0, 0, 0.08)), chest, 0.13, 0.15, "torso")
    ellipsoid(chest + Vector((0, 0, 0.02)), 0.19, 0.11, 0.12, "chest")
    neck = chest + Vector((0, 0.02, 0.16))
    capsule(chest + Vector((0, 0, 0.08)), neck, 0.05, 0.045, "neck")
    ellipsoid(neck + Vector((0, 0.03, 0.12)), 0.085, 0.1, 0.115, "head")
    for sx, hand in zip((-1, 1), hands):
        sh = chest + Vector((sx * 0.19, 0, 0.08))
        el = ik(sh, hand, 0.30, 0.27, (sx * 0.7, -0.2, -1))
        capsule(sh, el, 0.048, 0.04, "upper_arm"); capsule(el, hand, 0.038, 0.03, "forearm")
        ellipsoid(Vector(hand) + Vector((0, 0.02, 0.01)), 0.04, 0.07, 0.022, "hand")


# figures face +Y (towards the console). Station geometry from the CAD parameters (m).
SX = [v / 1000 for v in P["station_x"]]; CY = P["plate_cy"] / 1000; TOPZ = P["deck_top"] / 1000
pad = lambda i: (SX[i] + P["pad_dx"] / 1000, CY - 0.01, TOPZ + 0.03)
knob = lambda i: (SX[i] + P["knob_dx"] / 1000, CY - 0.03, TOPZ + 0.055)
person_standing(SX[0], -0.80, 1.78, (pad(0), knob(0)), lean=0.12)          # adult at PULSE
CURRENT[0] = C_WHEEL
wheelchair_user(SX[2], -0.70, (pad(2), knob(2)))
CURRENT[0] = C_STAND                          # wheelchair user at RESONANCE
person_standing(SX[3] + 0.02, -0.74, 1.60, ((SX[3] - 0.02, CY - 0.12, TOPZ + 0.02), knob(3)), lean=0.10)  # shorter adult at MOVEMENT

# ---------------- render settings ----------------
scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 8
scn.view_settings.view_transform = "AgX"
scn.view_settings.look = "AgX - Base Contrast"
scn.view_settings.exposure = -0.55
scn.render.image_settings.file_format = "PNG"
scn.render.film_transparent = False
scn.render.use_persistent_data = True


def camera(name, loc, target, lens=40, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"; cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd); C_ENV.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


VIEW_DEF = {
    "three_quarter": dict(file="console_three_quarter.png", res=(2400, 1600), people=False,
                          cam=dict(loc=(-3.45, -3.35, 1.70), target=(0.10, 0.02, 0.86), lens=42)),
    "top": dict(file="console_top_orthographic.png", res=(2400, 1200), people=False,
                cam=dict(loc=(0, 0, 6.0), target=(0, 0.0001, 0), ortho=2.80)),
    "front": dict(file="console_front_elevation.png", res=(2400, 1500), people=False,
                  cam=dict(loc=(0, -8.0, 0.82), target=(0, 0, 0.82), ortho=2.80)),
    "side": dict(file="console_side_section.png", res=(1600, 1600), people=True, standing=False, hide=["right_end_leg", "right_leg_plinth"],
                 cam=dict(loc=(8.0, -0.25, 0.92), target=(0, -0.25, 0.92), ortho=2.15)),
    "detail": dict(file="player_pad_rotary_detail.png", res=(2400, 1600), people=False,
                   cam=dict(loc=(SX[2] - 0.42, CY - 0.78, TOPZ + 0.52), target=(SX[2] + 0.03, CY + 0.02, TOPZ + 0.01), lens=58)),
    "human": dict(file="console_human_scale.png", res=(2400, 1600), people=True,
                  cam=dict(loc=(-2.1, -4.9, 2.05), target=(0.12, -0.05, 0.92), lens=38)),
}
CAMS = {v: camera("CAM_" + v, **VIEW_DEF[v]["cam"]) for v in VIEW_DEF}   # every view camera is saved in the .blend
if "--save-only" in args:
    VIEWS = []
meta = {}
for v in VIEWS:
    d = VIEW_DEF[v]
    cam = CAMS[v]
    scn.camera = cam
    C_PEOPLE.hide_render = not d["people"]
    C_STAND.hide_render = not d.get("standing", True)
    for ob in console_objs: ob.hide_render = ob.name in d.get("hide", [])
    scn.render.resolution_x, scn.render.resolution_y = int(d["res"][0] * SCALE), int(d["res"][1] * SCALE)
    scn.render.resolution_percentage = 100
    scn.render.filepath = str(OUT / d["file"])
    bpy.ops.render.render(write_still=True)
    meta[v] = dict(file=d["file"], hidden=d.get("hide", []), res=[scn.render.resolution_x, scn.render.resolution_y], **{k: list(x) if isinstance(x, tuple) else x for k, x in d["cam"].items()})
    print("rendered", v, flush=True)

prev = json.loads((OUT / "renders_meta.json").read_text()) if (OUT / "renders_meta.json").exists() else {}
prev.update(meta)
(OUT / "renders_meta.json").write_text(json.dumps(prev, indent=1))

if SAVE:
    C_PEOPLE.hide_render = False; C_STAND.hide_render = False
    for ob in console_objs: ob.hide_render = False
    scn.camera = bpy.data.objects.get("CAM_three_quarter") or scn.camera
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "sound_playground_console.blend"), compress=True)
    # GLB of the console only (no studio, no figures)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in console_objs: ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "SOUND_PLAYGROUND_console_v2.glb"), use_selection=True, export_format="GLB", export_apply=True)
    print("saved blend + glb", flush=True)
