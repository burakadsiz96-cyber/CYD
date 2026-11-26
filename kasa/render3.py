"""Vade Mecum stüdyo render'ı (Blender/Cycles, CPU): render2 ile aynı sahne, ekranda kitap sayfası.

cad run render2.py MODEL.glb CIKTI.png --gorunum on|arka|yan|ust|patlatma|detay|"x,y,z"
                   --ornek 64 --palet '{"on_kasa": "#1f4d2e", ..., "seffaf": ["yakut", "pip"]}'
                   [--ekran] [--genislik 1600 --yukseklik 1100] [--odak 1.0]

- Sonsuz stüdyo fonu (zemin + kavisli duvar, kameranın karşısında).
- Palet: parça adı başına renk; "seffaf" listesindeki parçalar ışık geçiren (yakut) plastik.
- --ekran: "ekran" parçasının üstüne saat arayüzü (10:09, tarih, kırmızı nokta) yerleştirir;
  arayüz dünya yukarısına göre döner, dikey duruşta da düz okunur.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: E402  (bmesh, bpy yüklendikten sonra bulunur)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector

from cad.blender import load

ap = argparse.ArgumentParser()
ap.add_argument("glb")
ap.add_argument("out")
ap.add_argument("--gorunum", default="on")
ap.add_argument("--ornek", type=int, default=64)
ap.add_argument("--palet", default="{}")
ap.add_argument("--ekran", action="store_true")
ap.add_argument("--genislik", type=int, default=1600)
ap.add_argument("--yukseklik", type=int, default=1100)
ap.add_argument("--odak", type=float, default=1.0, help="kadraj çarpanı: küçük = yakın")
ap.add_argument("--lens", type=float, default=85.0)
ap.add_argument("--pozlama", type=float, default=-0.9)
ap.add_argument("--donen", type=int, default=0, help="kare sayısı: model kendi ekseninde 360° döner, kareler OUT klasörüne")
args = ap.parse_args(sys.argv[1:])

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
FONT_LIGHT = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
model = load(Path(args.glb).resolve())
c, size = model.center, model.size
R = size.length / 2


def srgb(h):
    h = h.lstrip("#")
    v = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v) + (1.0,)


def material(name, color, rough=0.45, transmit=0.0, emit=None, emit_strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = srgb(color) if isinstance(color, str) else color
    p.inputs["Roughness"].default_value = rough
    if transmit:
        p.inputs["Transmission Weight"].default_value = transmit
        p.inputs["IOR"].default_value = 1.52
    if coat:
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.08
    if emit:
        p.inputs["Emission Color"].default_value = srgb(emit) if isinstance(emit, str) else emit
        p.inputs["Emission Strength"].default_value = emit_strength
    return m


# ------------------------------------------------------------------ parça malzemeleri
palette = json.loads(args.palet)
clear = set(palette.pop("seffaf", []))
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    key = next((k for k in sorted(palette, key=len, reverse=True) if ob.name.startswith(k)), None)
    if ob.name.startswith("ekran"):
        mat = material("ekran_cam", "#07080a", rough=0.05, coat=1.0)
    elif key is None:
        continue
    elif key in clear:
        mat = material(ob.name + "_m", palette[key], rough=0.12, transmit=0.92)
    else:
        mat = material(ob.name + "_m", palette[key], rough=0.42)
        if key in ("on_kapak", "arka_kapak"):                 # dokulu PEI tablanın verdiği deri benzeri yüzey
            nt = mat.node_tree
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = 900.0
            tex.inputs["Detail"].default_value = 6.0
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.18
            bump.inputs["Distance"].default_value = 0.00006
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
            nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = False

# ------------------------------------------------------------------ kamera yönü
views = {
    "on": Vector((-0.62, -1.0, 0.36)),
    "arka": Vector((0.78, 1.0, 0.42)),
    "yan": Vector((-1.0, -0.35, 0.22)),
    "ust": Vector((0.0, -0.18, 1.0)),
    "patlatma": Vector((-0.75, -1.0, 0.95)),
    "detay": Vector((1.0, -0.85, 0.32)),
}
if args.gorunum in views:
    vdir = views[args.gorunum].normalized()
else:
    vdir = Vector([float(t) for t in args.gorunum.split(",")]).normalized()

# ------------------------------------------------------------------ sonsuz fon (kameranın karşısında kavisli duvar)
def sweep(depth_dir):
    L, Rb, Hh, Ww = R * 40, R * 6, R * 30, R * 60
    prof = [(-L, 0.0)]
    back = R * 4
    prof.append((back, 0.0))
    for i in range(1, 17):
        a = (math.pi / 2) * i / 16
        prof.append((back + Rb * math.sin(a), Rb * (1 - math.cos(a))))
    prof.append((back + Rb, Hh))
    me = bpy.data.meshes.new("fon")
    bm = bmesh.new()
    rows = []
    for x in (-Ww, Ww):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new("fon", me)
    ang = math.atan2(depth_dir.x, depth_dir.y)
    ob.matrix_world = Matrix.Translation((c.x, c.y, 0.0)) @ Matrix.Rotation(-ang, 4, "Z")
    ob.data.materials.append(material("fon_m", "#e7e7ea", rough=0.85))
    scene.collection.objects.link(ob)


away = Vector((-vdir.x, -vdir.y, 0.0))
if away.length < 1e-3:
    away = Vector((0.0, 1.0, 0.0))
sweep(away.normalized())

# ------------------------------------------------------------------ kamera
scene.render.resolution_x, scene.render.resolution_y = args.genislik, args.yukseklik
aim = bpy.data.objects.new("aim", None)
aim.location = c
cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
cam.data.lens = args.lens
half = math.tan(cam.data.angle / 2) * min(1, scene.render.resolution_y / scene.render.resolution_x)
cam.location = c + (R / half * 0.86 * args.odak) * vdir
cam.constraints.new("TRACK_TO").target = aim
cam.data.dof.use_dof = True
cam.data.dof.focus_object = aim
cam.data.dof.aperture_fstop = 11.0
scene.collection.objects.link(aim)
scene.collection.objects.link(cam)
scene.camera = cam

# ------------------------------------------------------------------ ışıklar (model ölçeğine göre)
k = (R / 0.06) ** 2


def area(name, loc, energy, size_m, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size, light.color = energy, size_m, color
    ob = bpy.data.objects.new(name, light)
    ob.location = c + Vector(loc) * R
    ob.constraints.new("TRACK_TO").target = aim
    scene.collection.objects.link(ob)


side = Vector((vdir.x, vdir.y, 0)).normalized() if Vector((vdir.x, vdir.y)).length > 1e-3 else Vector((0, -1, 0))
perp = Vector((-side.y, side.x, 0))
area("anahtar", tuple(2.6 * side - 2.4 * perp + Vector((0, 0, 3.6))), 5.2 * k, R * 4.0)
area("dolgu", tuple(2.2 * side + 3.2 * perp + Vector((0, 0, 1.2))), 1.6 * k, R * 6.0, (0.92, 0.95, 1.0))
area("kontur", tuple(-3.0 * side + 0.6 * perp + Vector((0, 0, 3.2))), 5.5 * k, R * 2.5, (1.0, 0.95, 0.9))
area("tepe", (0, 0, 5.0), 2.0 * k, R * 5.0)

scene.world = bpy.data.worlds.new("world")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = srgb("#e7e7ea")
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.10

# ------------------------------------------------------------------ açık ekran: kitabın bir sayfası (krem kâğıt, serif)
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
if args.ekran:
    scr = next((o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ekran")), None)
    if scr is not None:
        pts = [scr.matrix_world @ v.co for v in scr.data.vertices]
        cen = sum(pts, Vector()) / len(pts)
        big = max(scr.data.polygons, key=lambda p: p.area)
        n = (scr.matrix_world.to_3x3() @ big.normal).normalized()
        if n.dot(cam.location - cen) < 0:
            n = -n
        up = Vector((0, 0, 1)) - n * n.z
        up = up.normalized() if up.length > 1e-3 else Vector((0, 1, 0))
        right = up.cross(n).normalized()
        w = max((p - cen).dot(right) for p in pts) - min((p - cen).dot(right) for p in pts)
        h = max((p - cen).dot(up) for p in pts) - min((p - cen).dot(up) for p in pts)
        basis = Matrix((right, up, n)).transposed()

        def place(ob, du=0.0, dv=0.0, lift=0.00006):
            m = basis.to_4x4()
            m.translation = cen + right * du + up * dv + n * lift
            ob.matrix_world = m
            scene.collection.objects.link(ob)

        bpy.ops.mesh.primitive_plane_add(size=1.0)
        plane = bpy.context.active_object
        scene.collection.objects.unlink(plane)
        plane.data.transform(Matrix.Diagonal((w, h, 1.0, 1.0)))
        plane.data.materials.append(material("sayfa_ekran", "#f3ead6", rough=0.6, emit="#f3ead6", emit_strength=0.55))
        place(plane, lift=0.00004)

        def text(body, size, du, dv, color, font_path, align="LEFT"):
            cu = bpy.data.curves.new("t", "FONT")
            cu.body = body
            cu.font = bpy.data.fonts.load(font_path)
            cu.size = size
            cu.align_x, cu.align_y = align, "BOTTOM_BASELINE"
            ob = bpy.data.objects.new("t", cu)
            ob.data.materials.append(material("t_m", color, rough=0.7, emit=color, emit_strength=0.25))
            place(ob, du=du, dv=dv)

        def rule(dv, length, color="#8a6a3a", thick=0.00018):
            me = bpy.data.meshes.new("r")
            bm = bmesh.new()
            bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
            bm.to_mesh(me)
            bm.free()
            me.transform(Matrix.Diagonal((length, thick, 1.0, 1.0)))
            ob = bpy.data.objects.new("r", me)
            ob.data.materials.append(material("r_m", color, emit=color, emit_strength=0.3))
            place(ob, dv=dv)

        s = min(w, h)
        L, R_ = -w / 2 + s * 0.09, w / 2 - s * 0.09
        top = h / 2 - s * 0.11
        text("VADE MECUM", s * 0.050, 0.0, top, "#8a6a3a", SERIF_B, "CENTER")
        rule(top - s * 0.045, w - s * 0.18)
        text("Vital Bulgular", s * 0.095, L, top - s * 0.15, "#2b1d12", SERIF_B)
        text("Erişkin, istirahatte", s * 0.050, L, top - s * 0.235, "#7a6650", SERIF_R)
        rows = [("Nabız", "60–100 /dk"), ("Tansiyon", "120/80 mmHg"), ("Solunum", "12–20 /dk"),
                ("SpO2", "%95–100"), ("Ateş", "36,5–37,5 °C")]
        gap = (top - s * 0.33 - (-h / 2 + s * 0.2)) / (len(rows) - 0.5)
        for i, (k, v) in enumerate(rows):
            dv = top - s * 0.34 - i * gap
            text(k, s * 0.062, L, dv, "#3a2a1c", SERIF_R)
            text(v, s * 0.062, R_, dv, "#3a2a1c", SERIF_B, "RIGHT")
            rule(dv - gap * 0.45, w - s * 0.18, "#d8cbb0", 0.00010)
        text("— 42 —", s * 0.045, 0.0, -h / 2 + s * 0.08, "#8a6a3a", SERIF_R, "CENTER")

# ------------------------------------------------------------------ dönen kayıt (model + ekran arayüzü bir pivotta döner)
if args.donen:
    pivot = bpy.data.objects.new("pivot", None)
    pivot.location = (c.x, c.y, 0.0)
    scene.collection.objects.link(pivot)
    bpy.context.view_layer.update()
    keep = {"fon", "camera", "aim", "pivot", "anahtar", "dolgu", "kontur", "tepe"}
    for ob in list(scene.objects):
        if ob.name in keep or ob.parent is not None:
            continue
        mw = ob.matrix_world.copy()
        ob.parent = pivot
        ob.matrix_world = mw
    pivot_ob = pivot

# ------------------------------------------------------------------ motor
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.ornek
scene.cycles.use_denoising = True
scene.render.compositor_device = "CPU"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = args.pozlama
if args.donen:
    outdir = Path(args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    for f in range(1, args.donen + 1):
        pivot_ob.rotation_euler = (0.0, 0.0, 2 * math.pi * (f - 1) / args.donen)
        bpy.context.view_layer.update()
        scene.render.filepath = str(outdir / f"kare_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
    print("yazildi", outdir)
else:
    scene.render.filepath = str(Path(args.out).resolve())
    bpy.ops.render.render(write_still=True)
    print("yazildi", args.out)
