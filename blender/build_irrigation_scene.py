"""
Rooftop tyre-garden irrigation: step-by-step 3D build guide for Blender (4.2+).

Builds the rooftop walkway (parapet wall, tiled roof, 9 tyre planters, water butt)
and an animated, step-by-step install of a per-plant irrigation system:

    water butt -> 12 V brushless pump -> screen filter -> 9-valve manifold
    -> 9 separate 4/7 mm micro-tubes (one per tyre) -> 2 adjustable drippers per tyre
    ESP32 + DS3231 clock opens one valve at a time on each tyre's own schedule.

Usage
  * In Blender: open the Scripting workspace, open this file, press "Run Script".
  * Headless:   blender -b -P build_irrigation_scene.py -- --save irrigation_guide.blend
                python3 build_irrigation_scene.py --save out.blend --stills renders/
                (python3 needs `pip install bpy==4.2.0`)

Scrub the timeline: each install step is a named timeline marker ("Step 1 ...").
Step text is shown on screen; part labels float next to the parts.
"""

import math
import sys
import os
import argparse

import bpy
from mathutils import Vector, Matrix

# --------------------------------------------------------------------------
# Plant schedule. Keep in sync with firmware/rooftop_irrigation/rooftop_irrigation.ino
# T1 is the tyre nearest the water butt.
# --------------------------------------------------------------------------
TYRES = [
    # name,               plant kind,   every N days, litres per watering
    ("T1 Wildflowers",    "wildflower", 3, 0.8),
    ("T2 Thrift & grass", "grass",      3, 0.8),
    ("T3 Pansies",        "pansy",      1, 0.8),
    ("T4 Empty / new",    "empty",      0, 0.0),   # 0 = valve off until planted
    ("T5 Lavender",       "lavender",   4, 0.6),
    ("T6 Geranium+nast.", "geranium2",  2, 1.0),
    ("T7 Geranium",       "geranium",   2, 1.0),
    ("T8 Strawberries",   "strawberry", 1, 1.5),
    ("T9 Gravel/succ.",   "gravel",     7, 0.4),
]
DRIP_LPH = 20.0  # 2 drippers x ~10 L/h each, measured in step 8


def run_minutes(litres):
    return litres / DRIP_LPH * 60.0


# --------------------------------------------------------------------------
# Layout (metres). X runs along the walkway, wall face at y=0, floor z=0.
# --------------------------------------------------------------------------
WALL_H = 1.02
TYRE_Y = 0.40
TYRE_X = [7.0 - i * 0.80 for i in range(9)]       # T1..T9
BUTT_X, BUTT_Y, BUTT_R, BUTT_H = 8.70, 0.30, 0.24, 1.0
BOX_X, BOX_Z = 7.85, 0.86                          # enclosure centre on wall
MAN_Z = 0.17                                       # manifold pipe height
VALVE_X = [7.52 + i * 0.075 for i in range(9)]     # valve i feeds tyre i
TUBE_Z0, TUBE_DZ = 0.60, 0.010                     # tube bundle on wall
BENCH = Vector((13.0, 1.4, 0.80))                  # wiring bench (step 7)

# Steps: (title, body lines, duration in frames)
STEPS = [
    ("STEP 0  -  What you have now",
     ["9 tyre planters, 100 L water butt at the far end, one shared drip line.",
      "Problem: one shared line = every plant gets the same water at the same time,",
      "and gravity alone (<0.1 bar) is too weak to open timer valves.",
      "Remove the old line and droppers.  KEEP the white wall clips - we reuse them."],
     120),
    ("STEP 1  -  Pump + float switch in the water butt",
     ["Sit the 12 V brushless submersible pump (5 m head) flat on the butt floor.",
      "Fix the float switch ~15 cm above the pump intake (cable tie to a weighted rod).",
      "Float DOWN = butt nearly empty -> controller refuses to run the pump (no dry run).",
      "Run 13 mm hose + both cables out through a hole in the lid with a grommet."],
     150),
    ("STEP 2  -  Solar power",
     ["Bolt the 10 W 12 V panel to the coping on an angle bracket, facing south-ish.",
      "Panel -> PWM charge controller -> 12 V 7 Ah sealed battery (5 A fuse on +).",
      "Everything electrical is powered from the controller LOAD terminals so the",
      "controller cuts power before the battery is flattened."],
     140),
    ("STEP 3  -  Controller enclosure",
     ["Fix an IP65 box (~300x250x120 mm) to the wall with 4 masonry screws + plugs,",
      "above the manifold and below the coping. Cable glands on the BOTTOM only.",
      "Inside: battery, charge controller, ESP32, DS3231 clock, 10 MOSFET modules,",
      "12->5 V buck converter. Waterproof test button on the box front."],
     140),
    ("STEP 4  -  Valve manifold (one valve per tyre)",
     ["Chain 9 x 1/2\" BSP tees with hex nipples (PTFE tape on every thread), end cap last.",
      "Screw a 12 V NC solenoid valve into each tee - ARROW pointing away from manifold.",
      "Pump hose -> screen filter -> manifold inlet.  Each valve outlet: 1/2\" F -> 4/7 mm barb.",
      "Valve nearest the tyres feeds T1 ... valve nearest the butt feeds T9."],
     150),
    ("STEP 5  -  Run 9 separate micro-tubes",
     ["One 4/7 mm black micro-tube from each valve to its own tyre, along the wall",
      "in the existing white clips. Label both ends (T1...T9) with tape before cutting.",
      "Each tube drops down the wall at its tyre. No joins along the run = no leaks,",
      "and each tyre can get its own schedule."],
     150),
    ("STEP 6  -  Drippers in each tyre",
     ["At the tyre: 4 mm tee -> two short tails -> two ADJUSTABLE drippers (0-70 L/h)",
      "on stakes, either side of the plant, pushed into the soil.",
      "Bend the tube end into the tyre so it can't kink on the rim. Empty tyre (T4):",
      "fit the drippers now, leave the valve OFF in the schedule until it's planted."],
     150),
    ("STEP 7  -  Wiring (inside the enclosure)",
     ["RED = +12 V from controller LOAD.  BLACK = ground.  YELLOW = ESP32 signal.",
      "Each valve + pump: +12 V -> device -> MOSFET module OUT-.  Diode across every coil",
      "(stripe to +12 V).  ESP32 from the buck (5 V -> VIN).  DS3231 on SDA 21 / SCL 22.",
      "Float switch GPIO32->GND, test button GPIO33->GND, battery divider -> GPIO34."],
     180),
    ("STEP 8  -  Programme, calibrate, test",
     ["Upload firmware/rooftop_irrigation.ino. Set each tyre: every N days + litres.",
      "Press the test button: each tyre runs 60 s in turn. Catch one dripper pair in a",
      "jug, multiply ml by 60 = L/h. Turn dripper caps until each tyre gives ~20 L/h,",
      "or put your measured flow in DRIP_LPH. Then it waters one tyre at a time at 06:30."],
     280),
    ("DONE  -  Weekly 2-minute check",
     ["Glance at the butt level and the LED on the box.  Monthly: rinse the screen filter",
      "and flick each dripper cap open/closed to clear grit.  Winter: lift the pump,",
      "drain the manifold, store the battery indoors and charged.",
      "Average use ~4 L/day -> a full 100 L butt lasts ~3 weeks with no rain."],
     160),
]

STEP_START = []
_f = 1
for _t, _b, _d in STEPS:
    STEP_START.append(_f)
    _f += _d
FRAME_END = _f - 1


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for item in list(coll):
            coll.remove(item)


def collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    lc = bpy.context.view_layer.layer_collection.children[name]
    bpy.context.view_layer.active_layer_collection = lc
    return c


_MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=0.0, alpha=1.0):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1.0)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1.0)
        p.inputs["Emission Strength"].default_value = emit
    p.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, alpha)
    _MATS[name] = m
    return m


def emit_mat(name, color, strength=1.0, alpha=1.0):
    """Flat unlit material for on-screen text and panels."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    if alpha < 1.0:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = alpha
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*color, alpha)
    _MATS[name] = m
    return m


def brick_mat(name, c1, c2, mortar, scale, brick_w=0.5, row_h=0.25, vertical=False):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 2.0
    br.inputs["Mortar Size"].default_value = 0.006
    br.inputs["Brick Width"].default_value = brick_w
    br.inputs["Row Height"].default_value = row_h
    if vertical:
        # Wall faces lie in the XZ plane; the brick texture is laid out in XY
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (math.radians(-90), 0, 0)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    m.diffuse_color = (*c1, 1)
    _MATS[name] = m
    return m


def setmat(ob, m):
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return ob


def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    # Bake the size in so procedural textures (bricks, tiles) are in real metres
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return setmat(ob, m)


def cyl(name, loc, r, h, m, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.shade_smooth()
    return setmat(ob, m)


def sphere(name, loc, r, m, scale=(1, 1, 1), sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=r, location=loc, subdivisions=sub)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    return setmat(ob, m)


def cone(name, loc, r, h, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0, depth=h, location=loc, rotation=rot, vertices=8)
    ob = bpy.context.object
    ob.name = name
    return setmat(ob, m)


def tube(name, pts, r, m, rounded=0.03):
    """Poly-line pipe through pts with small rounded corners."""
    pts = [Vector(p) for p in pts]
    if rounded and len(pts) > 2:
        smooth = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            d1 = (b - a)
            d2 = (c - b)
            k1 = min(rounded, d1.length / 2)
            k2 = min(rounded, d2.length / 2)
            p0 = b - d1.normalized() * k1
            p2 = b + d2.normalized() * k2
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                smooth.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t ** 2 * p2)
        smooth.append(pts[-1])
        pts = smooth
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(ob)
    cu.materials.append(m)
    return ob


def text(name, body, loc, size, m, rot=(0, 0, 0), align="LEFT", parent=None, extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "TOP"
    cu.space_line = 1.05
    cu.extrude = extrude
    ob = bpy.data.objects.new(name, cu)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    cu.materials.append(m)
    if parent:
        ob.parent = parent
    ob.visible_shadow = False
    return ob


def group(name, objs, pivot):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.1
    bpy.context.view_layer.active_layer_collection.collection.objects.link(e)
    e.location = pivot
    bpy.context.view_layer.update()
    inv = e.matrix_world.inverted()
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = e
        o.matrix_parent_inverse = inv
        o.matrix_world = mw
    return e


def hide_key(ob, hidden, frame):
    ob.hide_render = hidden
    ob.hide_viewport = hidden
    ob.keyframe_insert("hide_render", frame=frame)
    ob.keyframe_insert("hide_viewport", frame=frame)


def show_between(ob, f0, f1=None):
    if f0 > 1:
        hide_key(ob, True, 1)
        hide_key(ob, True, f0 - 1)
    hide_key(ob, False, f0)
    if f1 is not None:
        hide_key(ob, True, f1)


def pop_in(ob, frame, drop=0.35, dur=18):
    """Group appears at `frame`: grows from nothing while dropping into place."""
    final_loc = ob.location.copy()
    final_scale = ob.scale.copy()
    ob.scale = (0.0001,) * 3
    ob.location = final_loc + Vector((0, 0, drop))
    ob.keyframe_insert("scale", frame=1)
    ob.keyframe_insert("scale", frame=frame)
    ob.keyframe_insert("location", frame=frame)
    ob.scale = final_scale
    ob.location = final_loc
    ob.keyframe_insert("scale", frame=frame + dur)
    ob.keyframe_insert("location", frame=frame + dur)


def key_value(socket, values):
    for f, v in values:
        socket.default_value = v
        socket.keyframe_insert("default_value", frame=f)


def track_to(ob, target, axis="TRACK_Z"):
    c = ob.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = axis
    c.up_axis = "UP_Y"
    return c


# --------------------------------------------------------------------------
# Scene pieces
# --------------------------------------------------------------------------
def build_world():
    sc = bpy.context.scene
    world = bpy.data.worlds.new("Sky")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(50)
    sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.2

    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 2.6
    sun.angle = math.radians(3)
    so = bpy.data.objects.new("Sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), math.radians(-20), math.radians(200))


def build_roof():
    collection("00 Rooftop (existing)")
    floor_m = mat("Roof membrane", (0.62, 0.62, 0.58), 0.9)
    brick = brick_mat("Brick", (0.42, 0.12, 0.07), (0.30, 0.09, 0.06), (0.40, 0.37, 0.32), 4.0, 0.215, 0.075, vertical=True)
    coping = mat("Coping stone", (0.22, 0.22, 0.21), 0.9)
    tile = brick_mat("Roof tile", (0.40, 0.17, 0.10), (0.26, 0.12, 0.09), (0.18, 0.10, 0.08), 4.0, 0.165, 0.10)
    ridge = mat("Ridge tile", (0.45, 0.20, 0.12), 0.7)
    grey = mat("AC unit", (0.85, 0.86, 0.86), 0.4)

    L0, L1 = -0.6, 10.6
    box("Street level", (6.0, 1.0, -6.0), (80.0, 60.0, 0.1), mat("Street level", (0.12, 0.13, 0.11), 0.95))
    box("Walkway", ((L0 + L1) / 2, 0.65, -0.03), (L1 - L0, 1.3, 0.06), floor_m)
    wall = box("Parapet wall", ((L0 + L1) / 2, -0.17, WALL_H / 2), (L1 - L0, 0.34, WALL_H), brick)
    box("Coping", ((L0 + L1) / 2, -0.17, WALL_H + 0.04), (L1 - L0, 0.42, 0.08), coping)
    # Upstand / flashing at wall base
    box("Upstand", ((L0 + L1) / 2, 0.01, 0.09), (L1 - L0, 0.02, 0.18), floor_m)
    # Pitched tiled roof rising from the walkway edge
    pitch = math.radians(42)
    slope_len = 3.2
    cy = 1.30 + math.cos(pitch) * slope_len / 2
    cz = 0.05 + math.sin(pitch) * slope_len / 2
    box("Tiled roof", ((L0 + L1) / 2, cy, cz), (L1 - L0, slope_len, 0.06), tile, rot=(pitch, 0, 0))
    box("Gutter edge", ((L0 + L1) / 2, 1.30, 0.05), (L1 - L0, 0.08, 0.06), floor_m)
    # Hip/ridge roll near the tyre end (like photo 3)
    tube("Hip ridge", [(L0 + 0.2, 1.35, 0.12), (L0 + 1.4, 3.6, 2.2)], 0.09, ridge, rounded=0)
    # Velux windows
    glass = mat("Glass", (0.25, 0.35, 0.45), 0.05, 0.5)
    for x in (2.0, 3.0, 6.0, 7.0):
        box(f"Roof window {x}", (x, 2.1, 0.88), (0.6, 1.0, 0.07), glass, rot=(pitch, 0, 0))
    # AC units at the far end (as in photo 1)
    box("AC unit A", (9.8, 0.35, 0.45), (0.9, 0.35, 0.9), grey)
    box("AC unit B", (9.8, 0.35, 1.25), (0.9, 0.35, 0.7), grey)
    return wall


PLANT_GREEN = (0.12, 0.35, 0.08)


def make_plant(kind, cx, cy, top, idx):
    objs = []
    g = mat("Leaf", PLANT_GREEN, 0.7)
    g2 = mat("Leaf light", (0.25, 0.45, 0.12), 0.7)
    rnd = lambda k: math.sin(idx * 12.9898 + k * 78.233) * 0.5  # deterministic jitter

    def ring(n, rad, fn):
        for k in range(n):
            a = 2 * math.pi * k / n + idx
            fn(k, cx + math.cos(a) * rad * (0.7 + 0.3 * rnd(k)), cy + math.sin(a) * rad * (0.7 + 0.3 * rnd(k + 3)))

    if kind == "strawberry":
        ring(9, 0.12, lambda k, x, y: objs.append(sphere(f"Straw leaf {idx}.{k}", (x, y, top + 0.05), 0.06, g, (1, 1, 0.35))))
        red = mat("Strawberry", (0.7, 0.03, 0.03), 0.4)
        ring(3, 0.16, lambda k, x, y: objs.append(sphere(f"Berry {idx}.{k}", (x, y, top + 0.02), 0.018, red)))
    elif kind in ("geranium", "geranium2"):
        objs.append(sphere(f"Geranium mound {idx}", (cx, cy, top + 0.06), 0.11, g, (1, 1, 0.6)))
        pink = mat("Geranium pink", (0.85, 0.15, 0.35), 0.5)
        ring(5, 0.06, lambda k, x, y: objs.append(sphere(f"Bloom {idx}.{k}", (x, y, top + 0.15), 0.032, pink)))
        if kind == "geranium2":
            orange = mat("Nasturtium", (0.95, 0.35, 0.02), 0.5)
            ring(4, 0.15, lambda k, x, y: objs.append(sphere(f"Nast {idx}.{k}", (x, y, top + 0.09), 0.03, orange, (1, 1, 0.4))))
    elif kind == "lavender":
        purple = mat("Lavender", (0.42, 0.30, 0.75), 0.6)
        for k in range(14):
            a = k * 2.4
            r = 0.03 + 0.07 * ((k * 37) % 10) / 10
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            objs.append(cyl(f"Lav stem {idx}.{k}", (x, y, top + 0.09), 0.004, 0.18, g2, verts=6))
            objs.append(sphere(f"Lav head {idx}.{k}", (x, y, top + 0.19), 0.012, purple, (1, 1, 2.2), sub=1))
    elif kind == "pansy":
        objs.append(sphere(f"Pansy mound {idx}", (cx, cy, top + 0.03), 0.12, g, (1, 1, 0.35)))
        cols = [mat("Pansy purple", (0.35, 0.15, 0.6)), mat("Pansy yellow", (0.95, 0.75, 0.1))]
        ring(8, 0.09, lambda k, x, y: objs.append(sphere(f"Pansy {idx}.{k}", (x, y, top + 0.07), 0.025, cols[k % 2], (1, 1, 0.4))))
    elif kind in ("grass", "wildflower"):
        for k in range(16):
            a = k * 2.4
            r = 0.02 + 0.12 * ((k * 53) % 10) / 10
            objs.append(cone(f"Blade {idx}.{k}", (cx + math.cos(a) * r, cy + math.sin(a) * r, top + 0.08),
                             0.012, 0.18, g2, rot=(rnd(k) * 0.4, rnd(k + 1) * 0.4, 0)))
        if kind == "wildflower":
            white = mat("Daisy", (0.95, 0.95, 0.9))
            ring(5, 0.1, lambda k, x, y: objs.append(sphere(f"Daisy {idx}.{k}", (x, y, top + 0.17), 0.02, white, (1, 1, 0.4))))
        else:
            pink = mat("Thrift pink", (0.9, 0.55, 0.7))
            ring(4, 0.08, lambda k, x, y: objs.append(sphere(f"Thrift {idx}.{k}", (x, y, top + 0.19), 0.022, pink)))
    elif kind == "gravel":
        stone = mat("Gravel", (0.6, 0.57, 0.52), 0.9)
        for k in range(22):
            a = k * 2.4
            r = 0.2 * ((k * 31) % 10) / 10
            objs.append(sphere(f"Pebble {idx}.{k}", (cx + math.cos(a) * r, cy + math.sin(a) * r, top + 0.005), 0.02, stone, (1.3, 1, 0.6), sub=1))
        objs.append(sphere(f"Succulent {idx}", (cx + 0.05, cy, top + 0.03), 0.05, g2, (1, 1, 0.6)))
    elif kind == "empty":
        red = mat("Red saucer", (0.8, 0.05, 0.05), 0.3)
        objs.append(cyl(f"Saucer {idx}", (cx + 0.1, cy + 0.05, top + 0.01), 0.09, 0.02, red))
    return objs


def build_tyres():
    collection("00 Rooftop (existing)")
    rubber = mat("Tyre rubber", (0.025, 0.025, 0.028), 0.75)
    soil = mat("Soil", (0.10, 0.06, 0.035), 0.95)
    soils = []
    for i, (name, kind, _, _) in enumerate(TYRES):
        x = TYRE_X[i]
        bpy.ops.mesh.primitive_torus_add(major_radius=0.26, minor_radius=0.06, location=(x, TYRE_Y, 0.10),
                                         major_segments=48, minor_segments=16)
        t = bpy.context.object
        t.name = f"Tyre {name}"
        t.scale = (1, 1, 1.65)
        bpy.ops.object.shade_smooth()
        setmat(t, rubber)
        s = cyl(f"Soil {name}", (x, TYRE_Y, 0.08), 0.235, 0.16, soil)
        soils.append(s)
        make_plant(kind, x, TYRE_Y, 0.16, i)
    return soils


def build_butt():
    collection("00 Rooftop (existing)")
    butt_m = mat("Water butt", (0.03, 0.04, 0.035), 0.5)
    butt = cyl("Water butt", (BUTT_X, BUTT_Y, BUTT_H / 2), BUTT_R, BUTT_H, butt_m, verts=48)
    lid = cyl("Water butt lid", (BUTT_X, BUTT_Y, BUTT_H + 0.02), BUTT_R + 0.01, 0.04, butt_m, verts=48)
    water = cyl("Water in butt", (BUTT_X, BUTT_Y, 0.36), BUTT_R - 0.01, 0.68,
                mat("Water", (0.15, 0.35, 0.55), 0.05, 0, 0, 1.0), verts=48)
    wp = water.active_material.node_tree.nodes["Principled BSDF"]
    s0, s1 = STEP_START[1], STEP_START[2]
    key_value(wp.inputs["Alpha"], [(1, 1.0), (s0, 1.0), (s0 + 20, 0.15), (s1 - 15, 0.15), (s1, 1.0)])
    # Downpipe/diverter from the roof (existing)
    tube("Rain diverter pipe", [(BUTT_X, BUTT_Y + 0.15, BUTT_H + 0.02), (BUTT_X, BUTT_Y + 0.15, 1.4),
                                (BUTT_X, 1.4, 1.4)], 0.03, butt_m)
    return butt, lid, water


def build_old_system():
    """The existing single shared drip line, removed in step 0. Clips are kept."""
    collection("00 Rooftop (existing)")
    blk = mat("Old drip line", (0.02, 0.02, 0.02), 0.5)
    clip_m = mat("Wall clip", (0.95, 0.95, 0.95), 0.4)
    old = []
    old.append(tube("Old drip mainline", [(BUTT_X - 0.2, 0.25, 0.5), (BUTT_X - 0.4, 0.03, 0.62), (0.2, 0.03, 0.62)], 0.006, blk))
    for i, x in enumerate(TYRE_X):
        old.append(tube(f"Old dropper {i}", [(x, 0.03, 0.62), (x, 0.03, 0.35), (x, TYRE_Y - 0.1, 0.2)], 0.003, blk))
    for k in range(13):
        x = 0.2 + k * 0.62
        box(f"Wall clip {k}", (x, 0.012, 0.645), (0.025, 0.02, 0.07), clip_m)
    return old


def build_pump(f):
    collection("01 Pump + float switch")
    pump_m = mat("Pump body", (0.08, 0.08, 0.09), 0.4)
    blue = mat("Pump intake", (0.1, 0.2, 0.6), 0.5)
    hose_m = mat("13mm hose", (0.05, 0.12, 0.05), 0.4)
    cable_m = mat("Cable black", (0.01, 0.01, 0.01), 0.5)
    float_m = mat("Float", (0.9, 0.9, 0.85), 0.4)
    objs = []
    px, py = BUTT_X, BUTT_Y
    objs.append(cyl("Pump", (px, py, 0.05), 0.045, 0.08, pump_m))
    objs.append(cyl("Pump intake strainer", (px, py, 0.008), 0.05, 0.015, blue))
    objs.append(cyl("Pump outlet", (px + 0.04, py, 0.07), 0.009, 0.05, pump_m, rot=(0, math.pi / 2, 0)))
    hose = tube("Pump hose 13mm", [(px + 0.06, py, 0.07), (px + 0.12, py, 0.07), (px + 0.12, py, 0.95),
                                   (px + 0.12, py, BUTT_H + 0.12), (px - 0.35, 0.10, BUTT_H + 0.12),
                                   (px - 0.35, 0.10, 0.45), (8.28, 0.10, 0.30), (8.30, 0.09, MAN_Z)], 0.009, hose_m, 0.06)
    objs.append(hose)
    # Float switch on a rod, 15 cm above intake
    objs.append(cyl("Float rod", (px - 0.12, py + 0.05, 0.3), 0.005, 0.6, mat("Rod", (0.6, 0.6, 0.6), 0.3, 1.0)))
    objs.append(cyl("Float switch", (px - 0.12, py + 0.05, 0.22), 0.018, 0.04, float_m))
    objs.append(tube("Pump + float cables", [(px - 0.02, py - 0.02, 0.09), (px - 0.06, py - 0.04, 0.9),
                                             (px - 0.06, py - 0.04, BUTT_H + 0.1), (BOX_X + 0.1, 0.08, BUTT_H + 0.1),
                                             (BOX_X + 0.1, 0.08, BOX_Z - 0.12)], 0.004, cable_m, 0.05))
    g = group("G1 Pump", objs, (px, py, 0.5))
    pop_in(g, f, drop=0.6)
    return hose


def build_power(f):
    collection("02 Solar power")
    frame_m = mat("Panel frame", (0.75, 0.75, 0.78), 0.3, 1.0)
    cell_m = mat("Solar cells", (0.02, 0.04, 0.12), 0.15, 0.3)
    cable_m = mat("Cable black", (0.01, 0.01, 0.01), 0.5)
    tilt = math.radians(-35)
    objs = [
        box("Solar panel 10W frame", (BOX_X, -0.12, WALL_H + 0.22), (0.36, 0.26, 0.02), frame_m, rot=(tilt, 0, 0)),
        box("Solar panel 10W cells", (BOX_X, -0.12 + 0.004, WALL_H + 0.232), (0.34, 0.24, 0.01), cell_m, rot=(tilt, 0, 0)),
        box("Panel bracket L", (BOX_X - 0.15, -0.12, WALL_H + 0.14), (0.02, 0.2, 0.14), frame_m),
        box("Panel bracket R", (BOX_X + 0.15, -0.12, WALL_H + 0.14), (0.02, 0.2, 0.14), frame_m),
        tube("Panel cable", [(BOX_X + 0.12, -0.05, WALL_H + 0.12), (BOX_X + 0.12, 0.02, WALL_H + 0.09),
                             (BOX_X + 0.12, 0.02, BOX_Z + 0.13)], 0.004, cable_m, 0.03),
    ]
    g = group("G2 Solar", objs, (BOX_X, -0.1, WALL_H + 0.2))
    pop_in(g, f)
    return g


def build_enclosure(f):
    collection("03 Controller enclosure")
    grey = mat("Enclosure", (0.78, 0.79, 0.80), 0.35, 0.0, 0.0, 1.0)
    lidm = mat("Enclosure lid", (0.70, 0.75, 0.80), 0.1, 0.0, 0.0, 0.12)
    batt = mat("Battery", (0.05, 0.05, 0.05), 0.5)
    pcb = mat("PCB blue", (0.05, 0.2, 0.55), 0.4)
    pcb_g = mat("PCB green", (0.05, 0.35, 0.12), 0.4)
    red = mat("Button red", (0.8, 0.05, 0.05), 0.3)
    led = mat("LED green", (0.1, 1.0, 0.2), 0.3, 0, 4.0)
    W, D, H = 0.30, 0.12, 0.25
    y0 = D / 2 + 0.002
    objs = [
        box("Enclosure back", (BOX_X, y0 - D / 2 + 0.005, BOX_Z), (W, 0.01, H), grey),
        box("Enclosure L", (BOX_X - W / 2, y0, BOX_Z), (0.006, D, H), grey),
        box("Enclosure R", (BOX_X + W / 2, y0, BOX_Z), (0.006, D, H), grey),
        box("Enclosure top", (BOX_X, y0, BOX_Z + H / 2), (W, D, 0.006), grey),
        box("Enclosure bottom", (BOX_X, y0, BOX_Z - H / 2), (W, D, 0.006), grey),
        box("Enclosure clear lid", (BOX_X, y0 + D / 2, BOX_Z), (W, 0.006, H), lidm),
        box("Battery 12V 7Ah", (BOX_X - 0.09, y0 - 0.01, BOX_Z - 0.06), (0.10, 0.065, 0.095), batt),
        box("Charge controller", (BOX_X - 0.09, y0 - 0.03, BOX_Z + 0.06), (0.09, 0.03, 0.07), mat("Controller", (0.1, 0.25, 0.6))),
        box("ESP32", (BOX_X + 0.04, y0 - 0.035, BOX_Z + 0.07), (0.055, 0.008, 0.028), pcb),
        box("DS3231", (BOX_X + 0.10, y0 - 0.035, BOX_Z + 0.07), (0.035, 0.008, 0.022), pcb),
        box("Buck 12-5V", (BOX_X + 0.04, y0 - 0.035, BOX_Z + 0.025), (0.04, 0.008, 0.02), pcb_g),
        cyl("Test button", (BOX_X + 0.11, y0 + D / 2 + 0.01, BOX_Z - 0.08), 0.009, 0.02, red, rot=(math.pi / 2, 0, 0)),
        sphere("Status LED", (BOX_X + 0.11, y0 + D / 2 + 0.006, BOX_Z - 0.04), 0.005, led),
    ]
    for k in range(10):
        objs.append(box(f"MOSFET module {k + 1}", (BOX_X - 0.02 + (k % 5) * 0.034, y0 - 0.035,
                                                  BOX_Z - 0.03 - (k // 5) * 0.04), (0.028, 0.008, 0.032), pcb))
    for k in range(4):
        objs.append(cyl(f"Cable gland {k}", (BOX_X - 0.1 + k * 0.065, y0, BOX_Z - H / 2 - 0.01), 0.01, 0.02, grey))
    for sx in (-1, 1):
        for sz in (-1, 1):
            objs.append(cyl(f"Wall screw {sx}{sz}", (BOX_X + sx * (W / 2 - 0.02), 0.012, BOX_Z + sz * (H / 2 - 0.02)),
                            0.006, 0.004, mat("Steel", (0.7, 0.7, 0.7), 0.3, 1.0), rot=(math.pi / 2, 0, 0)))
    g = group("G3 Enclosure", objs, (BOX_X, y0, BOX_Z))
    pop_in(g, f)
    return led


def build_manifold(f):
    collection("04 Valve manifold")
    pvc = mat("Fitting grey", (0.55, 0.57, 0.58), 0.4)
    valve_m = mat("Valve body", (0.85, 0.85, 0.82), 0.4)
    coil_m = mat("Valve coil", (0.03, 0.03, 0.03), 0.4)
    brass = mat("Brass", (0.75, 0.55, 0.2), 0.3, 1.0)
    filt = mat("Filter blue", (0.1, 0.3, 0.75), 0.3)
    wire_m = mat("Valve wires", (0.6, 0.05, 0.05), 0.5)
    y = 0.09
    objs = []
    x0, x1 = VALVE_X[0] - 0.04, VALVE_X[-1] + 0.05
    objs.append(cyl("Manifold tee chain", ((x0 + x1) / 2, y, MAN_Z), 0.014, x1 - x0, pvc, rot=(0, math.pi / 2, 0)))
    objs.append(cyl("Manifold end cap", (x0 - 0.005, y, MAN_Z), 0.017, 0.02, pvc, rot=(0, math.pi / 2, 0)))
    objs.append(cyl("Screen filter", (x1 + 0.05, y, MAN_Z), 0.025, 0.08, filt, rot=(0, math.pi / 2, 0)))
    for k in range(2):
        objs.append(box(f"Manifold bracket {k}", (x0 + 0.1 + k * 0.45, 0.045, MAN_Z), (0.02, 0.09, 0.03), pvc))
    valves = []
    for i, x in enumerate(VALVE_X):
        objs.append(cyl(f"Tee {i + 1}", (x, y, MAN_Z + 0.025), 0.016, 0.03, pvc))
        v = cyl(f"Valve {i + 1} body", (x, y, MAN_Z + 0.06), 0.014, 0.04, valve_m)
        objs.append(v)
        c = box(f"Valve {i + 1} coil", (x, y + 0.022, MAN_Z + 0.06), (0.024, 0.026, 0.03), coil_m)
        objs.append(c)
        valves.append(c)
        objs.append(cyl(f"Valve {i + 1} 4mm barb", (x, y, MAN_Z + 0.095), 0.008, 0.03, brass))
        objs.append(tube(f"Valve {i + 1} wires", [(x, y + 0.035, MAN_Z + 0.06), (x, y + 0.04, MAN_Z + 0.2),
                                                   (BOX_X - 0.08 + i * 0.02, 0.07, BOX_Z - 0.13)], 0.0025, wire_m, 0.03))
    g = group("G4 Manifold", objs, ((x0 + x1) / 2, y, MAN_Z))
    pop_in(g, f, drop=0.4)
    return valves


def tube_path(i):
    """Route for micro-tube i: valve outlet -> up -> along wall in clips -> down -> into tyre."""
    xv, xt = VALVE_X[i], TYRE_X[i]
    z = TUBE_Z0 + TUBE_DZ * i
    yw = 0.012 + 0.0
    return [(xv, 0.09, MAN_Z + 0.11), (xv, 0.09, MAN_Z + 0.16), (xv, yw + 0.01, MAN_Z + 0.22),
            (xv, yw, z), (xt + 0.02, yw, z), (xt, yw, 0.36), (xt, 0.10, 0.25), (xt, TYRE_Y - 0.12, 0.215)]


def build_tubes(f0, f1):
    collection("05 Micro-tubes")
    tubes = []
    for i in range(9):
        m = mat(f"Tube T{i + 1}", (0.015, 0.015, 0.015), 0.4)
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Emission Color"].default_value = (0.1, 0.5, 1.0, 1)
        p.inputs["Emission Strength"].default_value = 0.0
        t = tube(f"Micro-tube T{i + 1}", tube_path(i), 0.0035, m, 0.03)
        # Draw the tube along its route
        t.data.bevel_factor_end = 0.0
        t.data.keyframe_insert("bevel_factor_end", frame=1)
        t.data.keyframe_insert("bevel_factor_end", frame=f0 + i * 8)
        t.data.bevel_factor_end = 1.0
        t.data.keyframe_insert("bevel_factor_end", frame=f0 + i * 8 + 45)
        tubes.append((t, m))
        # Tag tape at both ends
        tag = mat(f"Tag T{i + 1}", (1.0, 0.85, 0.1), 0.5)
        a = tube_path(i)
        for j, pt in enumerate((a[2], a[5])):
            b = box(f"Label tape T{i + 1}.{j}", (pt[0], pt[1] + 0.006, pt[2]), (0.012, 0.012, 0.02), tag)
            pop_in(b, f1, drop=0.0, dur=6)
    return tubes


def build_drippers(f):
    collection("06 Drippers")
    blk = mat("Tube T", (0.015, 0.015, 0.015), 0.4)
    dripper_m = mat("Dripper cap", (0.05, 0.55, 0.9), 0.4)
    stake_m = mat("Stake", (0.05, 0.05, 0.05), 0.5)
    drippers = []
    for i, x in enumerate(TYRE_X):
        objs = []
        ty = TYRE_Y - 0.12
        objs.append(box(f"T{i + 1} 4mm tee", (x, ty, 0.215), (0.02, 0.012, 0.012), blk))
        pts = []
        for s in (-1, 1):
            dx, dy = x + s * 0.11, TYRE_Y + 0.02
            objs.append(tube(f"T{i + 1} tail {s}", [(x + s * 0.01, ty, 0.215), (dx, ty + 0.02, 0.2), (dx, dy, 0.215)], 0.0035, blk, 0.02))
            objs.append(cyl(f"T{i + 1} stake {s}", (dx, dy, 0.17), 0.004, 0.12, stake_m, verts=8))
            objs.append(cyl(f"T{i + 1} dripper {s}", (dx, dy, 0.235), 0.016, 0.022, dripper_m))
            pts.append((dx, dy))
        g = group(f"G6 Drippers T{i + 1}", objs, (x, TYRE_Y, 0.2))
        pop_in(g, f + i * 6, drop=0.25)
        drippers.append(pts)
    return drippers


def build_bench(f):
    """Large exploded wiring diagram on a bench next to the roof (step 7)."""
    collection("07 Wiring bench")
    wood = mat("Bench", (0.45, 0.32, 0.2), 0.8)
    board = mat("Board", (0.035, 0.045, 0.04), 0.9)
    ink = emit_mat("Label ink", (1, 1, 1), 2.5)
    comp = {
        "panel": mat("Comp panel", (0.05, 0.08, 0.25), 0.3),
        "batt": mat("Comp battery", (0.06, 0.06, 0.06), 0.5),
        "ctrl": mat("Comp controller", (0.1, 0.25, 0.6), 0.4),
        "pcb": mat("Comp pcb", (0.05, 0.2, 0.55), 0.4),
        "pcbg": mat("Comp pcb green", (0.05, 0.35, 0.12), 0.4),
        "valve": mat("Comp valve", (0.85, 0.85, 0.82), 0.4),
        "fuse": mat("Comp fuse", (0.95, 0.6, 0.05), 0.4),
    }
    W = {"red": mat("Wire +12V", (0.85, 0.03, 0.03), 0.4), "blk": mat("Wire GND", (0.02, 0.02, 0.02), 0.4),
         "yel": mat("Wire signal", (0.95, 0.75, 0.0), 0.4), "org": mat("Wire 5V", (1.0, 0.4, 0.0), 0.4),
         "grn": mat("Wire I2C", (0.1, 0.6, 0.2), 0.4), "blu": mat("Wire input", (0.1, 0.3, 0.9), 0.4)}
    B = BENCH
    zt = B.z + 0.01
    objs = [box("Bench top", (B.x, B.y, B.z - 0.03), (1.8, 1.2, 0.05), wood),
            box("Wiring board", (B.x, B.y, B.z), (1.6, 1.05, 0.01), board)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box("Bench leg", (B.x + sx * 0.85, B.y + sy * 0.55, (B.z - 0.05) / 2), (0.05, 0.05, B.z - 0.05), wood))

    def P(x, y, z=0.0):
        return (B.x + x, B.y + y, zt + z)

    def comp_box(name, x, y, w, d, h, m, label, lsize=0.034):
        objs.append(box(name, P(x, y, h / 2), (w, d, h), m))
        objs.append(text(f"Lbl {name}", label, P(x - w / 2, y - d / 2 - 0.012, 0.001), lsize, ink))

    def wire(name, pts, colour, r=0.0045):
        objs.append(tube(name, [P(*p, 0.006) for p in pts], r, W[colour], 0.015))

    # Components (board coords: x -0.78..0.78, y -0.5..0.5)
    comp_box("B Solar panel", -0.62, 0.38, 0.22, 0.14, 0.01, comp["panel"], "10 W PANEL")
    comp_box("B Controller", -0.62, 0.10, 0.18, 0.12, 0.03, comp["ctrl"], "PWM CHARGE\nCONTROLLER")
    comp_box("B Battery", -0.62, -0.25, 0.20, 0.12, 0.08, comp["batt"], "12 V 7 Ah SLA")
    comp_box("B Fuse", -0.40, -0.12, 0.05, 0.03, 0.02, comp["fuse"], "5 A FUSE", 0.022)
    comp_box("B Buck", -0.30, 0.10, 0.08, 0.05, 0.015, comp["pcbg"], "BUCK 12->5V", 0.022)
    comp_box("B ESP32", -0.05, -0.12, 0.20, 0.08, 0.015, comp["pcb"], "ESP32 DevKit")
    comp_box("B RTC", -0.30, -0.33, 0.09, 0.06, 0.015, comp["pcb"], "DS3231", 0.022)
    comp_box("B Divider", -0.12, -0.36, 0.06, 0.03, 0.01, comp["pcbg"], "100k/27k", 0.02)
    comp_box("B Float", 0.18, -0.38, 0.05, 0.05, 0.03, comp["valve"], "FLOAT", 0.022)
    comp_box("B Button", 0.32, -0.38, 0.05, 0.05, 0.03, mat("Button red", (0.8, 0.05, 0.05), 0.3), "TEST BTN", 0.022)
    # Power rails
    wire("+12V rail", [(-0.40, 0.30), (0.75, 0.30)], "red")
    wire("GND rail", [(-0.40, 0.25), (0.75, 0.25)], "blk")
    wire("Panel +", [(-0.58, 0.31), (-0.58, 0.16)], "red")
    wire("Panel -", [(-0.66, 0.31), (-0.66, 0.16)], "blk")
    wire("Batt + via fuse", [(-0.56, -0.19), (-0.40, -0.12), (-0.40, 0.0), (-0.58, 0.04)], "red")
    wire("Batt -", [(-0.68, -0.19), (-0.68, 0.04)], "blk")
    wire("LOAD + to rail", [(-0.55, 0.16), (-0.48, 0.22), (-0.40, 0.30)], "red")
    wire("LOAD - to rail", [(-0.53, 0.14), (-0.45, 0.20), (-0.40, 0.25)], "blk")
    wire("Buck in +", [(-0.32, 0.30), (-0.32, 0.12)], "red")
    wire("Buck in -", [(-0.28, 0.25), (-0.28, 0.12)], "blk")
    wire("5V to VIN", [(-0.30, 0.075), (-0.30, -0.10), (-0.15, -0.10)], "org")
    wire("ESP GND", [(-0.26, 0.075), (-0.22, -0.14), (-0.15, -0.14)], "blk")
    wire("SDA 21", [(-0.33, -0.30), (-0.33, -0.20), (-0.10, -0.16)], "grn")
    wire("SCL 22", [(-0.27, -0.30), (-0.27, -0.22), (-0.06, -0.16)], "grn")
    wire("Div to 34", [(-0.12, -0.345), (-0.02, -0.16)], "blu")
    wire("Div from +12", [(-0.15, -0.345), (-0.36, -0.40), (-0.36, 0.30)], "red", 0.003)
    wire("Float to 32", [(0.18, -0.355), (0.02, -0.16)], "blu")
    wire("Button to 33", [(0.32, -0.355), (0.06, -0.16)], "blu")
    # 10 MOSFET modules + loads (9 valves + pump)
    ink_small = ink
    for k in range(10):
        x = 0.06 + k * 0.072
        objs.append(box(f"B MOSFET {k + 1}", P(x, 0.10, 0.008), (0.05, 0.06, 0.016), comp["pcb"]))
        objs.append(text(f"Lbl MOSFET {k + 1}", "M%d" % (k + 1), P(x - 0.018, 0.112, 0.017), 0.024, ink_small))
        sig = ["GPIO4", "GPIO13", "GPIO16", "GPIO17", "GPIO18", "GPIO19", "GPIO23", "GPIO25", "GPIO26", "GPIO27"][k]
        wire(f"Signal {k + 1}", [(0.0 + k * 0.012 - 0.05, -0.08), (0.0 + k * 0.012 - 0.05, 0.0), (x, 0.0), (x, 0.07)], "yel", 0.003)
        objs.append(text(f"Lbl sig {k + 1}", sig.replace("GPIO", "IO"), P(x - 0.026, 0.06, 0.001), 0.019, ink_small))
        wire(f"Mod GND {k + 1}", [(x + 0.018, 0.13), (x + 0.018, 0.25)], "blk", 0.003)
        # Load
        ly = 0.43
        name = "PUMP" if k == 9 else "V%d" % (k + 1)
        objs.append(box(f"B Load {name}", P(x, ly, 0.02), (0.045, 0.05, 0.04), comp["valve"] if k < 9 else comp["batt"]))
        objs.append(text(f"Lbl load {name}", name, P(x - 0.025, ly + 0.07, 0.001), 0.026, ink_small))
        wire(f"Load + {k + 1}", [(x - 0.012, 0.30), (x - 0.012, ly - 0.025)], "red", 0.003)
        wire(f"Load - {k + 1}", [(x + 0.008, 0.13), (x + 0.008, 0.20), (x + 0.008, ly - 0.025)], "blk", 0.003)
        # Flyback diode across load
        objs.append(cyl(f"Diode {k + 1}", P(x, ly - 0.04, 0.008), 0.004, 0.024, comp["batt"], rot=(0, math.pi / 2, 0)))
        objs.append(cyl(f"Diode band {k + 1}", P(x - 0.009, ly - 0.04, 0.008), 0.0045, 0.004, comp["valve"], rot=(0, math.pi / 2, 0)))
    objs.append(text("Lbl rails", "+12 V rail  /  GND rail", P(-0.33, 0.375, 0.001), 0.026, ink))
    objs.append(text("Lbl diode", "1N5819 diode across each load, band to +12 V", P(-0.76, 0.515, 0.001), 0.026, ink))
    g = group("G7 Bench", objs, (B.x, B.y, B.z))
    pop_in(g, f, drop=0.5, dur=24)


def build_hud(cam):
    """Step title + instructions pinned in front of the camera."""
    collection("99 On-screen instructions")
    hud = bpy.data.objects.new("HUD", None)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(hud)
    hud.parent = cam
    D = 0.2
    hud.location = (0, 0, -D)
    hud.scale = (D, D, D)
    white = emit_mat("HUD text", (1, 1, 1), 2.5)
    yellow = emit_mat("HUD title", (1.0, 0.82, 0.2), 2.5)
    panel = emit_mat("HUD panel", (0.0, 0.0, 0.0), 1.0, alpha=0.9)
    # 16:9, lens 30 mm, sensor 36 mm -> half width 0.6, half height 0.3375 at distance 1
    for k, (title, body, _) in enumerate(STEPS):
        f0 = STEP_START[k]
        f1 = STEP_START[k + 1] if k + 1 < len(STEPS) else None
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.265, -0.001))
        p = bpy.context.object
        p.name = f"HUD panel {k}"
        p.scale = (1.2, 0.145, 1)
        setmat(p, panel)
        p.parent = hud
        p.visible_shadow = False
        t = text(f"HUD title {k}", title, (-0.585, -0.198, 0), 0.026, yellow, parent=hud)
        b = text(f"HUD body {k}", "\n".join(body), (-0.585, -0.232, 0), 0.0185, white, parent=hud)
        for o in (p, t, b):
            show_between(o, f0, f1)
    # Progress bar of steps
    for k in range(len(STEPS)):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.56 + k * 0.034, 0.315, 0))
        dot = bpy.context.object
        dot.name = f"HUD step dot {k}"
        dot.scale = (0.026, 0.01, 1)
        dot.parent = hud
        dot.visible_shadow = False
        setmat(dot, emit_mat(f"HUD dot {k}", (0.35, 0.35, 0.35), 1.0))
        node = dot.active_material.node_tree.nodes["Emission"]
        key_value(node.inputs["Color"], [(1, (0.35, 0.35, 0.35, 1)),
                                         (STEP_START[k], (1.0, 0.82, 0.2, 1))])
        for fc in dot.active_material.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"
    return hud


def build_tags(f):
    """Floating per-tyre schedule tags, facing the camera."""
    collection("08 Schedule tags")
    cam = bpy.data.objects["Camera"]
    for i, (name, kind, every, litres) in enumerate(TYRES):
        if every == 0:
            sched = "valve OFF"
        else:
            sched = ("daily" if every == 1 else f"every {every} days") + f"\n{litres:.1f} L = {run_minutes(litres):.1f} min"
        bg = emit_mat("Tag bg", (0.02, 0.05, 0.1), 1.0, alpha=0.9)
        tm = emit_mat("Tag text", (1, 1, 1), 2.5)
        root = bpy.data.objects.new(f"Tag {name}", None)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(root)
        root.location = (TYRE_X[i], TYRE_Y + 0.05, 0.62)
        track_to(root, cam)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.045, -0.002))
        p = bpy.context.object
        p.name = f"Tag panel {i}"
        p.scale = (0.40, 0.17, 1)
        setmat(p, bg)
        p.parent = root
        p.visible_shadow = False
        t1 = text(f"Tag title {i}", name, (-0.185, 0.03, 0), 0.042, emit_mat("Tag title", (1.0, 0.82, 0.2), 2.5), parent=root)
        t2 = text(f"Tag sched {i}", sched, (-0.185, -0.025, 0), 0.034, tm, parent=root)
        for o in (p, t1, t2):
            show_between(o, f)


def part_labels():
    """Floating part labels per step (face the camera)."""
    collection("99 On-screen instructions")
    cam = bpy.data.objects["Camera"]
    ink = emit_mat("Part label", (1, 1, 1), 2.5)
    bg = emit_mat("Part label bg", (0.0, 0.0, 0.0), 1.0, alpha=0.9)
    # (step, text, anchor, size factor). Text runs to the right of the anchor on screen.
    labels = [
        (1, "12 V brushless submersible pump\n(5 m head, ~500 L/h) on the butt floor", (BUTT_X - 0.25, BUTT_Y + 0.25, 0.16), 1.5),
        (1, "Float switch 15 cm above intake", (BUTT_X - 0.25, BUTT_Y + 0.25, 0.46), 1.5),
        (1, "13 mm hose + cables out through lid", (BUTT_X - 0.25, BUTT_Y + 0.25, 1.18), 1.5),
        (2, "10 W 12 V solar panel on bracket", (BOX_X + 0.55, 0.20, WALL_H + 0.50), 2.2),
        (3, "IP65 box: battery, controller,\nESP32, RTC, 10 MOSFET modules", (BOX_X + 0.36, 0.35, BOX_Z + 0.16), 1.0),
        (3, "Test button + status LED", (BOX_X + 0.36, 0.35, BOX_Z - 0.10), 1.0),
        (4, "9 x 12 V NC solenoid valves\n(min 0.02 MPa) on 1/2\" tees", (8.02, 0.30, 0.47), 0.75),
        (4, "Screen filter (pump side)", (8.36, 0.30, 0.32), 0.75),
        (5, "9 separate 4/7 mm tubes\nin the existing wall clips", (5.6, 0.25, 1.0), 3.0),
        (6, "2 adjustable drippers on stakes\n(one each side of the plant)", (TYRE_X[3] + 0.32, TYRE_Y + 0.15, 0.50), 1.1),
    ]
    for k, (step, body, loc, sz) in enumerate(labels):
        root = bpy.data.objects.new(f"Label {k}", None)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(root)
        root.location = loc
        track_to(root, cam)
        root.scale = (sz, sz, sz)
        lines = body.split("\n")
        w = max(len(s) for s in lines) * 0.0105 + 0.03
        h = len(lines) * 0.026 + 0.018
        bpy.ops.mesh.primitive_plane_add(size=1, location=(w / 2 - 0.015, -h / 2 + 0.012, -0.002))
        p = bpy.context.object
        p.name = f"Label panel {k}"
        p.scale = (w, h, 1)
        setmat(p, bg)
        p.parent = root
        p.visible_shadow = False
        t = text(f"Label text {k}", body, (0, 0, 0), 0.02, ink, parent=root)
        f0 = STEP_START[step] + 20
        f1 = STEP_START[step + 1] if step + 1 < len(STEPS) else None
        for o in (p, t):
            show_between(o, f0, f1)


def build_camera():
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("Camera")
    cd.lens = 30
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cam = bpy.data.objects.new("Camera", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = bpy.data.objects.new("Camera target", None)
    sc.collection.objects.link(tgt)
    track_to(cam, tgt, "TRACK_NEGATIVE_Z")
    shots = [
        ((-1.6, 2.6, 2.4), (4.6, 0.3, 0.25)),            # 0 overview
        ((BUTT_X + 0.8, 1.55, 1.55), (BUTT_X - 0.1, 0.3, 0.22)),  # 1 butt / pump
        ((BOX_X + 0.3, 2.0, 1.7), (BOX_X - 0.05, 0.0, 0.95)),  # 2 solar
        ((BOX_X + 0.2, 1.05, 1.0), (BOX_X - 0.05, 0.05, 0.80)),  # 3 enclosure
        ((7.95, 0.85, 0.62), (7.80, 0.08, 0.27)),          # 4 manifold
        ((8.2, 1.7, 1.25), (4.3, 0.0, 0.45)),              # 5 tubes along wall
        ((TYRE_X[3] + 0.35, 1.15, 0.85), (TYRE_X[3] - 0.05, TYRE_Y - 0.05, 0.20)),  # 6 drippers (empty tyre T4)
        ((BENCH.x, BENCH.y - 1.1, BENCH.z + 1.95), (BENCH.x, BENCH.y - 0.24, BENCH.z)),  # 7 bench
        ((3.6, 3.3, 2.6), (3.8, 0.3, 0.25)),               # 8 programme + run
        ((-1.4, 3.0, 2.8), (4.6, 0.3, 0.3)),               # 9 done
    ]
    for k, (loc, aim) in enumerate(shots):
        f0 = STEP_START[k]
        f1 = (STEP_START[k + 1] - 1) if k + 1 < len(STEPS) else FRAME_END
        for f in ((f0 + 30) if k else 1, f1):
            cam.location = loc
            tgt.location = aim
            cam.keyframe_insert("location", frame=f)
            tgt.keyframe_insert("location", frame=f)
    # Gentle drift on the final shot
    cam.location = (0.4, 3.6, 3.0)
    cam.keyframe_insert("location", frame=FRAME_END)
    return cam


def animate_watering(tubes, drippers, soils, led, step_idx):
    """Water each enabled tyre in turn: tube glows blue, drips fall, soil darkens."""
    collection("08 Schedule tags")
    f0 = STEP_START[step_idx] + 40
    slot = 24
    drop_m = mat("Water drop", (0.3, 0.6, 1.0), 0.05, 0, 2.0)
    wet = mat("Wet soil", (0.04, 0.025, 0.015), 0.6)
    k = 0
    for i, (name, kind, every, litres) in enumerate(TYRES):
        if every == 0:
            continue
        a, b = f0 + k * slot, f0 + k * slot + slot - 4
        k += 1
        t, m = tubes[i]
        p = m.node_tree.nodes["Principled BSDF"]
        key_value(p.inputs["Emission Strength"], [(1, 0.0), (a - 1, 0.0), (a + 3, 6.0), (b, 6.0), (b + 3, 0.0)])
        for (dx, dy) in drippers[i]:
            d = sphere(f"Drop {name} {dx:.2f}", (dx, dy, 0.225), 0.008, drop_m, (1, 1, 1.5), sub=1)
            show_between(d, a, b)
            for f in range(a, b, 6):
                d.location.z = 0.225
                d.keyframe_insert("location", frame=f)
                d.location.z = 0.17
                d.keyframe_insert("location", frame=f + 5)
        patch = cyl(f"Wet patch {name}", (TYRE_X[i], TYRE_Y, 0.161), 0.20, 0.004, wet)
        patch.scale = (0.01, 0.01, 1)
        patch.keyframe_insert("scale", frame=1)
        patch.keyframe_insert("scale", frame=a)
        patch.scale = (1, 1, 1)
        patch.keyframe_insert("scale", frame=b)
    # Status LED flashes while running
    p = led.node_tree.nodes["Principled BSDF"]
    key_value(p.inputs["Emission Strength"], [(1, 0.5), (f0 - 1, 0.5), (f0, 6.0), (f0 + k * slot, 6.0), (f0 + k * slot + 1, 0.5)])


def fade_butt(butt, lid, s_in, s_out):
    """Make the butt see-through while the pump is installed."""
    m = bpy.data.materials.new("Water butt see-through")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.03, 0.04, 0.035, 1)
    p.inputs["Roughness"].default_value = 0.5
    key_value(p.inputs["Alpha"], [(1, 1.0), (s_in, 1.0), (s_in + 20, 0.18), (s_out - 15, 0.18), (s_out, 1.0)])
    m.blend_method = "BLEND"
    for o in (butt, lid):
        setmat(o, m)


# --------------------------------------------------------------------------
def build():
    reset_scene()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, FRAME_END
    sc.render.fps = 24
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = -0.6

    for k, (title, _, _) in enumerate(STEPS):
        sc.timeline_markers.new(title.replace("  -  ", ": ").replace("  ", " "), frame=STEP_START[k])

    build_world()
    cam = build_camera()
    build_roof()
    soils = build_tyres()
    butt, lid, water = build_butt()
    for o in build_old_system():
        show_between(o, 1, STEP_START[0] + 75)
    fade_butt(butt, lid, STEP_START[1], STEP_START[2])
    build_pump(STEP_START[1] + 25)
    build_power(STEP_START[2] + 30)
    led = build_enclosure(STEP_START[3] + 30)
    build_manifold(STEP_START[4] + 30)
    tubes = build_tubes(STEP_START[5] + 25, STEP_START[5] + 120)
    drippers = build_drippers(STEP_START[6] + 30)
    build_bench(STEP_START[7] + 20)
    build_tags(STEP_START[8] + 20)
    animate_watering(tubes, drippers, soils, led, 8)
    build_hud(cam)
    part_labels()
    sc.frame_set(1)
    return sc


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", help="write a .blend file here")
    ap.add_argument("--stills", help="render one PNG per step into this folder")
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--res", type=int, default=100, help="resolution percentage")
    args, _ = ap.parse_known_args(argv)

    sc = build()
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))
        print("saved", args.save)
    if args.stills:
        os.makedirs(args.stills, exist_ok=True)
        sc.cycles.samples = args.samples
        sc.render.resolution_percentage = args.res
        for k in range(len(STEPS)):
            nxt = STEP_START[k + 1] if k + 1 < len(STEPS) else FRAME_END
            frame = min(nxt - 5, STEP_START[k] + 100)
            if k == 8:
                frame = STEP_START[k] + 40 + 7 * 24 + 10   # mid-way through T8 watering
            sc.frame_set(frame)
            sc.render.filepath = os.path.join(os.path.abspath(args.stills), f"step_{k}.png")
            bpy.ops.render.render(write_still=True)
            print("rendered", sc.render.filepath)


if __name__ == "__main__":
    main()
