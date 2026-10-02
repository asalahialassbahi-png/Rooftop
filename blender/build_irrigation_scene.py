"""
Rooftop tyre-garden irrigation (low-cost college build, ~GBP 62): step-by-step 3D guide for Blender (4.2+).

Builds the rooftop walkway (parapet wall, tiled roof, 9 tyre planters, water butt)
and an animated, step-by-step install of a low-cost pumped drip system:

    water butt -> small 12 V brushless pump (tights over the intake as a filter)
    -> 1 mm anti-siphon hole -> ONE 13 mm main pipe along the wall
    -> at each tyre: 4 mm connector + micro-tube
    -> 1-3 ADJUSTABLE drippers per tyre (more drippers / more open = more water)
    A 12 V weekly timer switches the pump through the float switch (no relay);
    a 5 W solar panel keeps a small 12 V battery charged.

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
from mathutils import Vector

# --------------------------------------------------------------------------
# Per-tyre water. T1 is the tyre nearest the water butt.
# Every tyre is watered at the same time; the AMOUNT is set by how many drippers
# it has and how far their caps are opened (checked with a jug, in ml per minute).
# --------------------------------------------------------------------------
TYRES = [
    # name,               plant kind,   drippers, target ml/min (0 = caps closed)
    ("T1 Wildflowers",    "wildflower", 1,  60),
    ("T2 Thrift & grass", "grass",      1,  60),
    ("T3 Pansies",        "pansy",      2, 160),
    ("T4 Empty / new",    "empty",      1,   0),   # dripper caps closed
    ("T5 Lavender",       "lavender",   1,  30),
    ("T6 Geranium+nast.", "geranium2",  2, 100),
    ("T7 Geranium",       "geranium",   2, 100),
    ("T8 Strawberries",   "strawberry", 3, 300),
    ("T9 Gravel/succ.",   "gravel",     1,  15),
]
RUN_MINUTES = 10  # timer: 07:00-07:10, Mon/Wed/Fri/Sun


def litres_per_watering(ml_per_min):
    return ml_per_min * RUN_MINUTES / 1000.0


# --------------------------------------------------------------------------
# Layout (metres). X runs along the walkway, wall face at y=0, floor z=0.
# --------------------------------------------------------------------------
WALL_H = 1.02
TYRE_Y = 0.40
TYRE_X = [7.0 - i * 0.80 for i in range(9)]       # T1..T9
BUTT_X, BUTT_Y, BUTT_R, BUTT_H = 8.70, 0.30, 0.24, 1.0
BOX_X, BOX_Z = 7.85, 0.88                          # enclosure centre on wall
MAIN_Z = 0.62                                      # main pipe height on the wall
MAIN_Y = 0.025
MAIN_R = 0.008                                     # 13 mm pipe (~16 mm outside)
TOP_Z = 1.20                                       # pipe crest above the butt lid
HOLE_Z = BUTT_H - 0.04                             # 1 mm anti-siphon hole, inside the butt
DROP_X = 8.35                                      # where the main pipe comes down the wall
END_X = TYRE_X[-1] - 0.40
BENCH = Vector((13.0, 1.4, 0.80))                  # wiring bench

# Steps: (title, body lines, duration in frames)
STEPS = [
    ("STEP 0  -  What you have now",
     ["9 tyre planters, a 100 L water butt at the far end and one shared drip line.",
      "Gravity alone gives under 0.1 bar - too weak to push water evenly to 9 tyres.",
      "Plan (~GBP 62): a small 12 V pump on a timer feeds ONE main pipe, and each tyre",
      "gets its own number of adjustable drippers.  KEEP the white wall clips."],
     120),
    ("STEP 1  -  Pump + float switch in the water butt",
     ["Pull an old pair of tights over the pump intake (free filter), cable-tie it.",
      "Sit the small 12 V brushless pump (3 m head, under 5 W) flat on the butt floor.",
      "Fix the float switch ~15 cm above the intake. It is wired IN SERIES with the pump:",
      "float down = butt nearly empty = pump off.  Cables out through a hole in the lid."],
     150),
    ("STEP 2  -  Small solar panel + timer box",
     ["Fix the 5 W panel on the coping, tilted to face south-ish (bracket or cable ties).",
      "Lidded plastic box on the wall: 12 V 2.3 Ah battery, solar charge controller,",
      "12 V weekly timer, 3 A fuse.  Drill cable holes in the BOTTOM of the box only.",
      "Everything runs from the controller LOAD terminals (protects the battery)."],
     150),
    ("STEP 3  -  One 13 mm main pipe",
     ["Pipe from the pump up over the butt rim.  Just under the lid, drill a 1 mm hole",
      "in the pipe (a hot needle works): it squirts back into the butt while pumping and",
      "lets air in when the pump stops, so the butt can't siphon itself empty.",
      "Along the wall in the clips (cable ties), 30 cm past the last tyre, end stop."],
     170),
    ("STEP 4  -  A drop tube to every tyre",
     ["At each tyre make a hole in the SIDE of the main pipe (hot nail, bradawl or",
      "3 mm drill - no punch tool needed), push in a 4 mm barbed connector, then run",
      "4/7 mm micro-tube down the wall into the tyre.  No taps: to shut a tyre off",
      "(e.g. the empty one) just screw its dripper caps fully closed."],
     150),
    ("STEP 5  -  Drippers: more drippers = more water",
     ["Each tyre gets 1, 2 or 3 ADJUSTABLE drippers on stakes, joined with 4 mm tees:",
      "Strawberries 3  -  Pansies 2  -  Geraniums 2  -  Wildflowers, Thrift,",
      "Lavender, Succulent 1 each.  Empty tyre: fit 1, caps closed.",
      "Push the stakes in either side of the plant, not against the tyre wall."],
     150),
    ("STEP 6  -  Wiring (5 connections, no relay)",
     ["Panel -> controller PV.   Battery -> controller BAT (3 A fuse on +).",
      "Controller LOAD + / -  ->  timer DC+ / DC-.",
      "Timer COM <- LOAD +.   Timer NO -> float switch -> pump +.   Pump - -> LOAD -.",
      "Only works because the pump draws under 0.4 A (float switch limit ~0.5 A)."],
     180),
    ("STEP 7  -  Set the timer, then set each tyre's water",
     ["Timer: ON 07:00, OFF 07:10, on Mon / Wed / Fri / Sun (add 19:00 in a heatwave).",
      "Press the timer's MANUAL button, hold a jug under one tyre's drippers for 1 min.",
      "Turn the caps until each tyre gives its ml/min on the tags (strawberries 300).",
      "Can't reach a target?  Set the timer to 15 min and aim for 2/3 of each target."],
     260),
    ("DONE  -  Weekly 2-minute check",
     ["Weekly: glance at the butt level.  Monthly: rinse the tights filter and flick",
      "each dripper cap open and shut to clear grit.  Winter: lift the pump, drain the",
      "pipe, keep the battery indoors and charged.  Each watering uses ~8 L, so",
      "4 a week is ~33 L: a full 100 L butt lasts ~3 weeks without rain."],
     160),
]

STEP_START = []
_f = 1
for _t, _b, _d in STEPS:
    STEP_START.append(_f)
    _f += _d
FRAME_END = _f - 1
S_PUMP, S_POWER, S_MAIN, S_DROPS, S_DRIP, S_WIRE, S_TIMER, S_DONE = range(1, 9)


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
    tube("Rain diverter pipe", [(BUTT_X + 0.08, BUTT_Y - 0.12, BUTT_H + 0.02), (BUTT_X + 0.08, 0.08, 1.22),
                                (BUTT_X + 0.9, 0.08, 1.22)], 0.025, butt_m)
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



def build_power(f):
    collection("02 Solar power")
    frame_m = mat("Panel frame", (0.75, 0.75, 0.78), 0.3, 1.0)
    cell_m = mat("Solar cells", (0.02, 0.04, 0.12), 0.15, 0.3)
    cable_m = mat("Cable black", (0.01, 0.01, 0.01), 0.5)
    tilt = math.radians(-35)
    objs = [
        box("Solar panel 5W frame", (BOX_X, -0.12, WALL_H + 0.20), (0.26, 0.20, 0.02), frame_m, rot=(tilt, 0, 0)),
        box("Solar panel 5W cells", (BOX_X, -0.12 + 0.004, WALL_H + 0.212), (0.24, 0.18, 0.01), cell_m, rot=(tilt, 0, 0)),
        box("Panel bracket L", (BOX_X - 0.11, -0.12, WALL_H + 0.14), (0.02, 0.2, 0.14), frame_m),
        box("Panel bracket R", (BOX_X + 0.11, -0.12, WALL_H + 0.14), (0.02, 0.2, 0.14), frame_m),
        tube("Panel cable", [(BOX_X + 0.12, -0.05, WALL_H + 0.12), (BOX_X + 0.12, 0.02, WALL_H + 0.09),
                             (BOX_X + 0.12, 0.02, BOX_Z + 0.13)], 0.004, cable_m, 0.03),
    ]
    g = group("G2 Solar", objs, (BOX_X, -0.1, WALL_H + 0.2))
    pop_in(g, f)
    return g



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




def build_pump(f):
    collection("01 Pump + float switch")
    pump_m = mat("Pump body", (0.08, 0.08, 0.09), 0.4)
    blue = mat("Pump intake", (0.1, 0.2, 0.6), 0.5)
    cable_m = mat("Cable black", (0.01, 0.01, 0.01), 0.5)
    float_m = mat("Float", (0.9, 0.9, 0.85), 0.4)
    px, py = BUTT_X, BUTT_Y
    objs = [
        cyl("Pump", (px, py, 0.05), 0.045, 0.08, pump_m),
        cyl("Pump intake strainer", (px, py, 0.008), 0.05, 0.015, blue),
        sphere("Tights over intake", (px, py, 0.045), 0.06, mat("Tights", (0.55, 0.42, 0.33), 0.9, 0, 0, 0.6), (1, 1, 0.9)),
        cyl("Pump outlet", (px + 0.04, py, 0.07), 0.009, 0.05, pump_m, rot=(0, math.pi / 2, 0)),
        cyl("Float rod", (px - 0.12, py + 0.05, 0.3), 0.005, 0.6, mat("Rod", (0.6, 0.6, 0.6), 0.3, 1.0)),
        cyl("Float switch", (px - 0.12, py + 0.05, 0.22), 0.018, 0.04, float_m),
        tube("Pump + float cables", [(px - 0.02, py - 0.02, 0.09), (px - 0.06, py - 0.04, 0.9),
                                     (px - 0.06, py - 0.04, BUTT_H + 0.1), (BOX_X + 0.06, 0.09, BUTT_H + 0.1),
                                     (BOX_X + 0.06, 0.09, BOX_Z - 0.1)], 0.004, cable_m, 0.05),
    ]
    g = group("G1 Pump", objs, (px, py, 0.5))
    pop_in(g, f, drop=0.6)


def build_box(f):
    collection("02 Timer box")
    plastic = mat("Plastic box", (0.85, 0.87, 0.88), 0.3, 0.0, 0.0, 0.5)
    lidm = mat("Plastic box lid", (0.20, 0.45, 0.80), 0.3)
    batt = mat("Battery", (0.05, 0.05, 0.05), 0.5)
    W, D, H = 0.24, 0.12, 0.16
    y0 = D / 2 + 0.002
    objs = [
        box("Box back", (BOX_X, y0 - D / 2 + 0.003, BOX_Z), (W, 0.006, H), plastic),
        box("Box L", (BOX_X - W / 2, y0, BOX_Z), (0.004, D, H), plastic),
        box("Box R", (BOX_X + W / 2, y0, BOX_Z), (0.004, D, H), plastic),
        box("Box bottom", (BOX_X, y0, BOX_Z - H / 2), (W, D, 0.004), plastic),
        box("Box front", (BOX_X, y0 + D / 2, BOX_Z), (W, 0.004, H), plastic),
        box("Box lid", (BOX_X, y0, BOX_Z + H / 2 + 0.006), (W + 0.012, D + 0.012, 0.012), lidm),
        box("Battery 12V 2.3Ah", (BOX_X - 0.065, y0 - 0.01, BOX_Z - 0.03), (0.075, 0.035, 0.09), batt),
        box("Charge controller", (BOX_X + 0.005, y0 - 0.03, BOX_Z + 0.02), (0.06, 0.025, 0.05), mat("Controller", (0.1, 0.25, 0.6))),
        box("Timer", (BOX_X + 0.07, y0 - 0.025, BOX_Z + 0.02), (0.065, 0.035, 0.05), mat("Timer body", (0.92, 0.92, 0.9), 0.4)),
        box("Timer LCD", (BOX_X + 0.07, y0 - 0.006, BOX_Z + 0.028), (0.045, 0.003, 0.018), mat("LCD", (0.25, 0.45, 0.3), 0.2, 0, 1.5)),
        box("Fuse", (BOX_X + 0.03, y0 - 0.035, BOX_Z - 0.05), (0.03, 0.012, 0.015), mat("Fuse", (0.95, 0.6, 0.05), 0.4)),
    ]
    for sx in (-1, 1):
        objs.append(cyl(f"Wall screw {sx}", (BOX_X + sx * (W / 2 - 0.03), 0.008, BOX_Z + 0.04),
                        0.006, 0.004, mat("Steel", (0.7, 0.7, 0.7), 0.3, 1.0), rot=(math.pi / 2, 0, 0)))
    g = group("G2 Box", objs, (BOX_X, y0, BOX_Z))
    pop_in(g, f)


def main_path():
    px, py = BUTT_X, BUTT_Y
    return [(px + 0.06, py, 0.07), (px + 0.12, py, 0.07), (px + 0.12, py, TOP_Z),
            (px - 0.25, py, TOP_Z), (DROP_X, 0.08, TOP_Z), (DROP_X, 0.08, MAIN_Z + 0.05),
            (DROP_X - 0.08, MAIN_Y, MAIN_Z), (END_X, MAIN_Y, MAIN_Z)]


def build_mainline(f0, f1):
    collection("03 Main pipe")
    pipe_m = mat("Main pipe", (0.015, 0.015, 0.015), 0.4)
    p = pipe_m.node_tree.nodes["Principled BSDF"]
    p.inputs["Emission Color"].default_value = (0.1, 0.5, 1.0, 1)
    p.inputs["Emission Strength"].default_value = 0.0
    pipe = tube("Main pipe 13mm", main_path(), MAIN_R, pipe_m, 0.06)
    pipe.data.bevel_factor_end = 0.0
    pipe.data.keyframe_insert("bevel_factor_end", frame=1)
    pipe.data.keyframe_insert("bevel_factor_end", frame=f0)
    pipe.data.bevel_factor_end = 1.0
    pipe.data.keyframe_insert("bevel_factor_end", frame=f1)

    grey = mat("Fitting grey", (0.55, 0.57, 0.58), 0.4)
    hole_m = mat("Hole marker", (0.1, 0.6, 1.0), 0.3, 0, 3.0)
    hx, hy = BUTT_X + 0.12 - MAIN_R, BUTT_Y
    pop_in(group("G3 Hole", [sphere("Anti-siphon hole (1 mm)", (hx, hy, HOLE_Z), 0.006, hole_m)], (hx, hy, HOLE_Z)), f0 + 25, drop=0.0)
    pop_in(group("G3 End stop", [cyl("End stop", (END_X - 0.01, MAIN_Y, MAIN_Z), 0.011, 0.03, grey, rot=(0, math.pi / 2, 0))],
                 (END_X, MAIN_Y, MAIN_Z)), f1, drop=0.2)
    # Cable ties onto the existing clips
    tie_m = mat("Cable tie", (0.05, 0.05, 0.05), 0.5)
    for k in range(13):
        x = 0.2 + k * 0.62
        if x < END_X or x > DROP_X - 0.1:
            continue
        pop_in(group(f"G3 Tie {k}", [cyl(f"Cable tie {k}", (x, MAIN_Y, MAIN_Z), MAIN_R + 0.003, 0.006, tie_m,
                                         rot=(0, math.pi / 2, 0))], (x, MAIN_Y, MAIN_Z)), f1, drop=0.0, dur=8)
    return pipe_m


def drop_path(x):
    return [(x, MAIN_Y + 0.008, MAIN_Z - 0.004), (x, 0.045, MAIN_Z - 0.03), (x, 0.045, 0.33),
            (x, 0.13, 0.24), (x, TYRE_Y - 0.15, 0.215)]


def build_drops(f):
    collection("04 Drop tubes")
    blk = mat("Tube black", (0.015, 0.015, 0.015), 0.4)
    connector = mat("Barbed connector", (0.1, 0.1, 0.1), 0.4)
    for i in range(len(TYRES)):
        x = TYRE_X[i]
        objs = [
            cyl(f"T{i + 1} connector", (x, MAIN_Y + 0.01, MAIN_Z), 0.004, 0.02, connector, rot=(math.pi / 2, 0, 0)),
            tube(f"T{i + 1} drop tube", drop_path(x), 0.0035, blk, 0.03),
        ]
        pop_in(group(f"G4 Drop T{i + 1}", objs, (x, 0.05, 0.45)), f + i * 8, drop=0.25)


def dripper_spots(i, n):
    x = TYRE_X[i]
    if n == 1:
        return [(x + 0.12, TYRE_Y + 0.02)]
    if n == 2:
        return [(x - 0.12, TYRE_Y + 0.02), (x + 0.12, TYRE_Y + 0.02)]
    return [(x - 0.13, TYRE_Y - 0.02), (x + 0.13, TYRE_Y - 0.02), (x, TYRE_Y + 0.14)]


def build_drippers(f):
    collection("05 Drippers")
    blk = mat("Tube black", (0.015, 0.015, 0.015), 0.4)
    cap_m = mat("Dripper cap", (0.05, 0.55, 0.9), 0.4)
    stake_m = mat("Stake", (0.05, 0.05, 0.05), 0.5)
    spots = []
    for i, (name, kind, n, mlpm) in enumerate(TYRES):
        x = TYRE_X[i]
        hub = (x, TYRE_Y - 0.15, 0.215)
        objs = [box(f"T{i + 1} 4mm tee", hub, (0.02, 0.012, 0.012), blk)]
        pts = dripper_spots(i, n)
        for k, (dx, dy) in enumerate(pts):
            objs.append(tube(f"T{i + 1} tail {k}", [hub, ((hub[0] + dx) / 2, (hub[1] + dy) / 2, 0.205), (dx, dy, 0.215)], 0.0035, blk, 0.02))
            objs.append(cyl(f"T{i + 1} stake {k}", (dx, dy, 0.17), 0.004, 0.12, stake_m, verts=8))
            objs.append(cyl(f"T{i + 1} dripper {k}", (dx, dy, 0.235), 0.016, 0.022, cap_m))
        pop_in(group(f"G5 Drippers T{i + 1}", objs, (x, TYRE_Y, 0.2)), f + i * 6, drop=0.25)
        spots.append(pts)
    return spots


def build_bench(f):
    """Large wiring diagram on a bench next to the roof."""
    collection("06 Wiring bench")
    wood = mat("Bench", (0.45, 0.32, 0.2), 0.8)
    board = mat("Board", (0.035, 0.045, 0.04), 0.9)
    ink = emit_mat("Label ink", (1, 1, 1), 2.5)
    comp = {
        "panel": mat("Comp panel", (0.05, 0.08, 0.25), 0.3),
        "batt": mat("Comp battery", (0.06, 0.06, 0.06), 0.5),
        "ctrl": mat("Comp controller", (0.1, 0.25, 0.6), 0.4),
        "timer": mat("Comp timer", (0.85, 0.85, 0.82), 0.4),
        "relay": mat("Comp relay", (0.12, 0.12, 0.12), 0.4),
        "light": mat("Comp light", (0.85, 0.85, 0.82), 0.4),
        "fuse": mat("Comp fuse", (0.95, 0.6, 0.05), 0.4),
    }
    W = {"red": mat("Wire +12V", (0.85, 0.03, 0.03), 0.4), "blk": mat("Wire GND", (0.02, 0.02, 0.02), 0.4),
         "org": mat("Wire switched", (1.0, 0.4, 0.0), 0.4), "blu": mat("Wire float", (0.1, 0.3, 0.9), 0.4)}
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

    def note(body, x, y, size=0.026):
        objs.append(text(f"Note {body[:12]}", body, P(x, y, 0.001), size, ink))

    comp_box("B Solar panel", -0.62, 0.38, 0.18, 0.12, 0.01, comp["panel"], "5 W PANEL")
    comp_box("B Controller", -0.62, 0.10, 0.16, 0.11, 0.03, comp["ctrl"], "SOLAR CHARGE\nCONTROLLER")
    comp_box("B Battery", -0.62, -0.25, 0.14, 0.09, 0.07, comp["batt"], "12 V 2.3 Ah SLA")
    comp_box("B Fuse", -0.40, -0.12, 0.05, 0.03, 0.02, comp["fuse"], "3 A FUSE", 0.022)
    comp_box("B Timer", -0.05, 0.05, 0.22, 0.14, 0.03, comp["timer"], "12 V WEEKLY TIMER")
    objs.append(box("B Timer LCD", P(-0.05, 0.07, 0.032), (0.12, 0.05, 0.004), mat("LCD", (0.25, 0.45, 0.3), 0.2, 0, 1.5)))
    comp_box("B Float", 0.30, -0.30, 0.06, 0.06, 0.03, comp["light"], "FLOAT SWITCH\n(in the butt)", 0.024)
    comp_box("B Pump", 0.58, -0.05, 0.09, 0.09, 0.06, comp["relay"], "PUMP < 0.4 A\n(in the butt)", 0.024)
    # LOAD + / - rails
    wire("+12V rail", [(-0.40, 0.30), (0.72, 0.30)], "red")
    wire("GND rail", [(-0.40, 0.25), (0.72, 0.25)], "blk")
    note("LOAD +  /  LOAD -", -0.33, 0.375)
    # Solar + battery
    wire("Panel +", [(-0.58, 0.31), (-0.58, 0.16)], "red")
    wire("Panel -", [(-0.66, 0.31), (-0.66, 0.16)], "blk")
    wire("Batt + via fuse", [(-0.57, -0.21), (-0.40, -0.12), (-0.40, 0.0), (-0.58, 0.05)], "red")
    wire("Batt -", [(-0.67, -0.21), (-0.67, 0.05)], "blk")
    wire("LOAD + to rail", [(-0.55, 0.16), (-0.48, 0.22), (-0.40, 0.30)], "red")
    wire("LOAD - to rail", [(-0.53, 0.14), (-0.45, 0.20), (-0.40, 0.25)], "blk")
    # Timer power + contacts
    wire("Timer DC+", [(-0.13, 0.30), (-0.13, 0.12)], "red")
    wire("Timer DC-", [(-0.09, 0.25), (-0.09, 0.12)], "blk")
    wire("Timer COM", [(0.01, 0.30), (0.01, 0.12)], "red")
    note("DC+  DC-       COM", -0.16, 0.155, 0.018)
    note("NO", 0.04, -0.03, 0.018)
    wire("Timer NO to float", [(0.03, -0.02), (0.03, -0.30), (0.27, -0.30)], "org")
    wire("Float to pump +", [(0.33, -0.30), (0.45, -0.30), (0.555, -0.10)], "blu")
    wire("Pump - to GND", [(0.605, 0.00), (0.66, 0.10), (0.66, 0.25)], "blk")
    note("Float switch is in series with the pump.\nNo relay: OK because the pump draws\nunder 0.4 A (float limit ~0.5 A).", 0.10, 0.52, 0.024)
    note("ORANGE = timer output   BLUE = through float", -0.76, -0.42, 0.024)
    g = group("G6 Bench", objs, (B.x, B.y, B.z))
    pop_in(g, f, drop=0.5, dur=24)


def build_tags(f):
    """Floating per-tyre dripper count + jug target, facing the camera."""
    collection("07 Tyre tags")
    cam = bpy.data.objects["Camera"]
    bg = emit_mat("Tag bg", (0.02, 0.05, 0.1), 1.0, alpha=0.9)
    tm = emit_mat("Tag text", (1, 1, 1), 2.5)
    title_m = emit_mat("Tag title", (1.0, 0.82, 0.2), 2.5)
    for i, (name, kind, n, mlpm) in enumerate(TYRES):
        if mlpm == 0:
            sched = f"{n} dripper fitted\ncaps closed until planted"
        else:
            sched = f"{n} dripper{'s' if n > 1 else ''} - {mlpm} ml/min\n= {litres_per_watering(mlpm):.2f} L per watering"
        root = bpy.data.objects.new(f"Tag {name}", None)
        bpy.context.view_layer.active_layer_collection.collection.objects.link(root)
        root.location = (TYRE_X[i], TYRE_Y + 0.05, 0.66)
        track_to(root, cam)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.01, -0.045, -0.002))
        p = bpy.context.object
        p.name = f"Tag panel {i}"
        p.scale = (0.46, 0.17, 1)
        setmat(p, bg)
        p.parent = root
        p.visible_shadow = False
        t1 = text(f"Tag title {i}", name, (-0.205, 0.03, 0), 0.042, title_m, parent=root)
        t2 = text(f"Tag sched {i}", sched, (-0.205, -0.025, 0), 0.032, tm, parent=root)
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
        (S_PUMP, "12 V brushless pump, 3 m head, under 5 W\nold tights over the intake = filter", (BUTT_X - 0.25, BUTT_Y + 0.25, 0.16), 1.5),
        (S_PUMP, "Float switch 15 cm above intake", (BUTT_X - 0.25, BUTT_Y + 0.25, 0.46), 1.5),
        (S_PUMP, "Cables out through the lid", (BUTT_X - 0.25, BUTT_Y + 0.25, 1.18), 1.5),
        (S_POWER, "5 W 12 V solar panel", (BOX_X + 0.45, 0.20, WALL_H + 0.45), 2.0),
        (S_POWER, "Lidded plastic box: 2.3 Ah battery,\nsolar controller, 12 V timer, 3 A fuse", (BOX_X + 0.50, 0.30, BOX_Z + 0.12), 1.6),
        (S_MAIN, "1 mm hole just under the lid:\nstops the butt siphoning out", (BUTT_X - 0.02, BUTT_Y + 0.2, TOP_Z + 0.10), 1.5),
        (S_MAIN, "13 mm main pipe, cable-tied\nin the wall clips", (6.6, 0.25, 0.92), 1.8),
        (S_DROPS, "4 mm barbed connector", (TYRE_X[2] + 0.30, 0.25, 0.72), 1.1),
        (S_DROPS, "4/7 mm micro-tube into the tyre", (TYRE_X[2] + 0.30, 0.30, 0.42), 1.1),
        (S_DRIP, "3 adjustable drippers\nfor the strawberries", (TYRE_X[7] + 0.33, TYRE_Y + 0.15, 0.55), 1.1),
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
    # One (start, end) camera pose per step; the camera drifts from start to end.
    x3 = TYRE_X[2]
    x8 = TYRE_X[7]
    shots = [
        [((-1.6, 2.6, 2.4), (4.6, 0.3, 0.25))],                                       # 0 overview
        [((BUTT_X + 0.8, 1.55, 1.55), (BUTT_X - 0.1, 0.3, 0.22))],                    # 1 pump
        [((BOX_X + 0.6, 1.7, 1.5), (BOX_X + 0.1, 0.0, 0.95))],                        # 2 panel + box
        [((8.1, 2.3, 1.75), (8.1, 0.1, 0.72)), ((5.6, 2.3, 1.55), (5.6, 0.1, 0.55))],  # 3 main pipe
        [((x3 + 0.55, 1.0, 0.95), (x3 - 0.05, 0.05, 0.42))],                          # 4 drops
        [((x8 + 0.45, 1.15, 0.95), (x8 - 0.05, TYRE_Y - 0.05, 0.20))],                # 5 drippers
        [((BENCH.x, BENCH.y - 1.1, BENCH.z + 1.95), (BENCH.x, BENCH.y - 0.24, BENCH.z))],  # 6 wiring
        [((5.6, 3.0, 2.3), (5.6, 0.3, 0.25)), ((2.0, 3.0, 2.3), (2.0, 0.3, 0.25))],  # 7 timer + tags
        [((-1.4, 3.0, 2.8), (4.6, 0.3, 0.3)), ((0.4, 3.6, 3.0), (4.6, 0.3, 0.3))],   # 8 done
    ]
    for k, poses in enumerate(shots):
        f0 = STEP_START[k]
        f1 = (STEP_START[k + 1] - 1) if k + 1 < len(STEPS) else FRAME_END
        first = (f0 + 30) if k else 1
        start, end = poses[0], poses[-1]
        for f, (loc, aim) in ((first, start), (f1, end)):
            cam.location = loc
            tgt.location = aim
            cam.keyframe_insert("location", frame=f)
            tgt.keyframe_insert("location", frame=f)
    return cam


def animate_watering(pipe_m, spots, step_idx):
    """Everything waters together: pipe glows, drippers drip in proportion to their flow."""
    collection("07 Tyre tags")
    a = STEP_START[step_idx] + 40
    b = STEP_START[step_idx + 1] - 20
    drop_m = mat("Water drop", (0.3, 0.6, 1.0), 0.05, 0, 2.0)
    wet = mat("Wet soil", (0.04, 0.025, 0.015), 0.6)
    p = pipe_m.node_tree.nodes["Principled BSDF"]
    key_value(p.inputs["Emission Strength"], [(1, 0.0), (a - 1, 0.0), (a + 6, 5.0), (b, 5.0), (b + 6, 0.0)])
    for i, (name, kind, n, mlpm) in enumerate(TYRES):
        if mlpm == 0:
            continue
        per_dripper = mlpm / n
        period = max(4, int(round(400 / per_dripper)))  # busier drippers drip faster
        for k, (dx, dy) in enumerate(spots[i]):
            d = sphere(f"Drop {name} {k}", (dx, dy, 0.225), 0.008, drop_m, (1, 1, 1.5), sub=1)
            show_between(d, a, b)
            for f in range(a + k * 2, b, period):
                d.location.z = 0.225
                d.keyframe_insert("location", frame=f)
                d.location.z = 0.17
                d.keyframe_insert("location", frame=f + min(5, period - 1))
        patch = cyl(f"Wet patch {name}", (TYRE_X[i], TYRE_Y, 0.161), 0.21 * min(1.0, 0.35 + mlpm / 300), 0.004, wet)
        patch.scale = (0.01, 0.01, 1)
        patch.keyframe_insert("scale", frame=1)
        patch.keyframe_insert("scale", frame=a)
        patch.scale = (1, 1, 1)
        patch.keyframe_insert("scale", frame=b)


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
    build_tyres()
    butt, lid, water = build_butt()
    for o in build_old_system():
        show_between(o, 1, STEP_START[0] + 75)
    fade_butt(butt, lid, STEP_START[S_PUMP], STEP_START[S_POWER])
    build_pump(STEP_START[S_PUMP] + 25)
    build_power(STEP_START[S_POWER] + 25)
    build_box(STEP_START[S_POWER] + 55)
    pipe_m = build_mainline(STEP_START[S_MAIN] + 20, STEP_START[S_MAIN] + 120)
    build_drops(STEP_START[S_DROPS] + 25)
    spots = build_drippers(STEP_START[S_DRIP] + 25)
    build_bench(STEP_START[S_WIRE] + 20)
    build_tags(STEP_START[S_TIMER] + 20)
    animate_watering(pipe_m, spots, S_TIMER)
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
            frame = min(nxt - 5, STEP_START[k] + 110)
            sc.frame_set(frame)
            sc.render.filepath = os.path.join(os.path.abspath(args.stills), f"step_{k}.png")
            bpy.ops.render.render(write_still=True)
            print("rendered", sc.render.filepath)


if __name__ == "__main__":
    main()
