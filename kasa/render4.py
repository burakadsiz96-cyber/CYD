"""Vade Mecum montaj animasyonu (Blender/Cycles, CPU): parçalar ayrılır, sırayla yerine girer.

cad run render4.py montaj.glb KARE_KLASORU --palet "$(cat render/vademecum/palet_konyak.json)" --ekran
        [--genislik 864 --yukseklik 1080] [--ornek 12] [--fps 20] [--kareler 0-99 | 12,200,400]

Kareler KARE_KLASORU/kare_0001.png ... olarak yazılır, zamanlama zaman.json'a. Altyazı ve MP4 montaj_video.py'nin işi.
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
ap.add_argument("--ornek", type=int, default=12)
ap.add_argument("--palet", default="{}")
ap.add_argument("--ekran", action="store_true")
ap.add_argument("--genislik", type=int, default=720)
ap.add_argument("--yukseklik", type=int, default=900)
ap.add_argument("--lens", type=float, default=85.0)
ap.add_argument("--pozlama", type=float, default=-0.9)
ap.add_argument("--fps", type=int, default=20)
ap.add_argument("--kareler", default="", help="'12-40' ya da '5,90,300'; boşsa hepsi")
ap.add_argument("--gorunum", default="on")
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




# ------------------------------------------------------------------ zaman çizelgesi ve sahne ölçüleri
FPS = args.fps
MM = 0.001
LIFT = 80.0                                   # model zeminden yükseltilir: alttaki parçalar zemine girmesin
C_MM = c / MM                                  # kitap merkezi (mm), model çerçevesinde
CEN = Vector((C_MM.x, C_MM.y, C_MM.z))
R = size.length / 2 * 1.6                      # ışık ve fon ölçeği: ayrılmış yığın montajdan büyük
FRONT = Vector((-0.62, -1.0, 0.36)).normalized()
STAGE = Vector((-0.70, -1.0, 0.85)).normalized()
SIDE = Vector((-0.92, -0.70, 0.62)).normalized()
TOPD = Vector((-0.45, -1.0, 0.80)).normalized()
HEAD = Vector((-0.30, -1.0, 0.80)).normalized()


def W(p, flipped=False):
    """Model çerçevesindeki bir noktayı (mm) dünyaya (m) çevirir; ters çevrilmiş kitapta x ve z aynalanır."""
    v = Vector(p) - CEN
    if flipped:
        v = Vector((-v.x, v.y, -v.z))
    return (CEN + v + Vector((0, 0, LIFT))) * MM


# parçaların ayrık duruşu: model çerçevesinde, nihai yerinden mm cinsinden sapma
HOVER = {
    "ic_pil": (0, 0, 40), "ic_tp4056": (0, 0, 40),
    "sayfa": (0, 0, 96),
    "ic_anahtar": (0, 0, 126),
    "ic_kart": (0, 0, 152), "ic_lcd": (0, 0, 162), "ekran": (0, 0, 172),
    "on_kapak": (0, 0, 204),
    "baslik": (0, 0, 236), "arma": (0, 0, 236), "kose0": (0, 0, 236), "kose1": (0, 0, 236),
    "sirt": (-62, 0, 0),
    "kurdele": (0, 58, 0),
    "kalem": (0, 82, 0), "kapitalbant": (0, 104, 0),
    "ayak": (0, 0, -52), "pim": (24, 24, -52),
    "kose2": (0, 0, -80), "kose3": (0, 0, -80), "kose4": (0, 0, -80),
}
# (parçalar, başlık, alt başlık, kamera: (hedef mm, uzaklık mm, yön, ters çevrilmiş mi), ters çevir mi)
STEPS = [
    (["ic_pil", "ic_tp4056"], "Pil ve şarj kartı", "Arka kapağın tırnakları ve rayları arasına",
     ((40, 52, 5), 250, TOPD, False)),
    (["sayfa"], "Sayfa bloğu", "Arka kapağın üstüne oturur, pil bölmesini örter",
     ((36, 52, 11), 330, STAGE, False)),
    (["ic_anahtar"], "Açma anahtarı", "Sayfa bloğunun baş kenarındaki cebe",
     ((20, 97, 8), 170, HEAD, False)),
    (["ic_kart", "ic_lcd", "ekran"], "CYD kartı ve ekran", "Ekran öne bakacak şekilde bloğun içine",
     ((35, 52, 17), 330, STAGE, False)),
    (["on_kapak"], "Ön kapak", "Dört pimle sayfa bloğunun önüne",
     ((37, 52, 19), 360, STAGE, False)),
    (["baslik", "arma", "kose0", "kose1"], "Başlık levhası, arma, köşelikler", "Kapaktaki oyuklara yapıştırılır",
     ((37, 52, 21), 380, STAGE, False)),
    (["sirt"], "Yuvarlak sırt", "Sayfa bloğunun sol yüzüne",
     ((6, 52, 11), 340, SIDE, False)),
    (["kurdele"], "Kırmızı kurdele", "Baştaki yarıktan geçer: anahtarlık deliği",
     ((57, 100, 12), 190, HEAD, False)),
    (["kalem", "kapitalbant"], "Kalem ve kırmızı başlık", "Sırttaki tünele; başlık kalemin ucuna",
     ((6, 92, 10), 340, SIDE, False)),
    None,  # çevirme
    (["ayak", "pim"], "Şövale ayağı ve pimi", "Arka kapaktaki cebe; filament pimi menteşeden geçer",
     ((40, 32, 2), 280, STAGE, True)),
    (["kose2", "kose3", "kose4"], "Arka köşelikler", "Vida başlarının üstüne bastırılır",
     ((37, 52, 1), 380, STAGE, True)),
]

T_HERO, T_EXPL0, T_EXPL1 = 1.6, 1.6, 4.0
T_STEP0, STEP_D = 4.4, 2.1
T_MOVE0, T_MOVE1 = 0.4, 1.4                  # adım içinde parçanın hareket aralığı
FLIP_D = 1.7
timeline = []
t = T_STEP0
step_times = []
for st in STEPS:
    if st is None:
        step_times.append((t, FLIP_D, None))
        t += FLIP_D
    else:
        step_times.append((t, STEP_D, st))
        t += STEP_D
T_FLIPBACK = t
T_SPIN0 = T_FLIPBACK + 1.8
T_END = T_SPIN0 + 3.8 + 0.6
N_FRAMES = int(round(T_END * FPS))


def fr(sec):
    return int(round(sec * FPS)) + 1


# ------------------------------------------------------------------ kamera ve ışıklar
scene.render.resolution_x, scene.render.resolution_y = args.genislik, args.yukseklik
scene.render.fps = FPS
half = math.tan(math.atan(18.0 / args.lens)) * min(1, args.yukseklik / args.genislik)
aim = bpy.data.objects.new("aim", None)
cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
cam.data.lens = args.lens
cam.data.dof.use_dof = False
cam.constraints.new("TRACK_TO").target = aim
scene.collection.objects.link(aim)
scene.collection.objects.link(cam)
scene.camera = cam


def cam_pose(aim_m, dist_mm, direction):
    return aim_m, aim_m + direction.normalized() * (dist_mm * MM)


HERO_DIST = 350.0
HERO = Vector((-0.55, -1.0, 0.62)).normalized()
aim.location, cam.location = cam_pose(W(CEN), HERO_DIST, HERO)
vdir = FRONT

cl = W(CEN)
k = (R / 0.096) ** 2


def area(name, loc, energy, size_m, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size, light.color = energy, size_m, color
    ob = bpy.data.objects.new(name, light)
    ob.location = cl + Vector(loc) * R
    ob.constraints.new("TRACK_TO").target = aim
    scene.collection.objects.link(ob)


side = Vector((FRONT.x, FRONT.y, 0)).normalized()
perp = Vector((-side.y, side.x, 0))
area("anahtar", tuple(2.2 * side - 1.8 * perp + Vector((0, 0, 3.4))), 5.2 * k, R * 3.2)
area("dolgu", tuple(2.0 * side + 2.6 * perp + Vector((0, 0, 1.2))), 1.8 * k, R * 5.0, (0.92, 0.95, 1.0))
area("kontur", tuple(-2.6 * side + 0.6 * perp + Vector((0, 0, 3.0))), 5.0 * k, R * 2.2, (1.0, 0.95, 0.9))
area("tepe", (0, 0, 4.2), 2.4 * k, R * 4.0)

scene.world = bpy.data.worlds.new("world")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = srgb("#e7e7ea")
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.10
c = Vector((CEN.x, CEN.y, 0.0)) * MM
sweep(Vector((0.0, 1.0, 0.0)))

# ------------------------------------------------------------------ açık ekran: kitabın bir sayfası
ui_objs = []

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
            ui_objs.append(ob)

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
            return ob

        def leader(x0, x1, dv, r, step, color):
            # Kitap tablosundaki noktalı yol: noktalar sağ kenardan ortak bir ızgarada, satırlar arasında hizalı.
            me = bpy.data.meshes.new("l")
            bm = bmesh.new()
            x = x1
            while x >= x0:
                bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=r,
                                        matrix=Matrix.Translation((x, r * 1.1, 0.0)))
                x -= step
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new("l", me)
            ob.data.materials.append(material("l_m", color, emit=color, emit_strength=0.3))
            place(ob, dv=dv)

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
        text("Erişkin, istirahatte", s * 0.050, L, top - s * 0.235, "#5e4a36", SERIF_R)
        rows = [("Nabız", "60–100 /dk"), ("Tansiyon", "120/80 mmHg"), ("Solunum", "12–20 /dk"),
                ("SpO2", "%95–100"), ("Ateş", "36,5–37,5 °C")]
        gap = (top - s * 0.33 - (-h / 2 + s * 0.2)) / (len(rows) - 0.5)
        for i, (k, v) in enumerate(rows):
            dv = top - s * 0.34 - i * gap
            a = text(k, s * 0.062, L, dv, "#2b1d12", SERIF_R)
            b = text(v, s * 0.062, R_, dv, "#3a2a1c", SERIF_B, "RIGHT")
            bpy.context.view_layer.update()
            step = s * 0.026
            x1 = R_ - b.dimensions.x - s * 0.03
            x1 = R_ - step * math.ceil((R_ - x1) / step)         # ortak ızgara
            leader(L + a.dimensions.x + s * 0.03, x1, dv, s * 0.0052, step, "#9c8566")
        text("— 42 —", s * 0.045, 0.0, -h / 2 + s * 0.08, "#8a6a3a", SERIF_R, "CENTER")



bpy.context.view_layer.update()

# ------------------------------------------------------------------ model bir pivota bağlanır (ters çevirme ve dönüş için)
pivot = bpy.data.objects.new("pivot", None)
pivot.location = Vector(CEN) * MM            # önce özgün merkezde bağla, sonra yükselt
scene.collection.objects.link(pivot)
bpy.context.view_layer.update()
inv = pivot.matrix_world.inverted()
for rt in model.roots:
    rt.parent = pivot
    rt.matrix_parent_inverse = inv
scr = next((o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ekran")), None)
if scr is not None:
    bpy.context.view_layer.update()
    for ob in ui_objs:
        ob.parent = scr
        ob.matrix_parent_inverse = scr.matrix_world.inverted()
# kitabı yükselt (kamera, ışıklar ve fon dünyada kalır)
bpy.context.view_layer.update()
pivot.location = W(CEN)
bpy.context.view_layer.update()

# ------------------------------------------------------------------ parça hareketleri (delta_location, ebeveyn uzayında)
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH" and o.name not in ("fon",) and o not in ui_objs}
base = {}


def local_delta(ob, d_mm):
    pm = (ob.parent.matrix_world @ ob.matrix_parent_inverse).to_3x3() if ob.parent else Matrix.Identity(3)
    return pm.inverted() @ (Vector(d_mm) * MM)


def key_delta(name, sec, d_mm):
    ob = objs[name]
    ob.delta_location = local_delta(ob, d_mm)
    ob.keyframe_insert("delta_location", frame=fr(sec))


timing = {}
for st_t, st_d, st in step_times:
    if st is None:
        continue
    for nm in st[0]:
        timing[nm] = st_t
for nm in HOVER:
    if nm not in objs or nm not in timing:
        print("UYARI parça yok:", nm, nm in objs, nm in timing)
        continue
    h = HOVER[nm]
    key_delta(nm, 0.0, (0, 0, 0))
    key_delta(nm, T_EXPL0, (0, 0, 0))
    key_delta(nm, T_EXPL1, h)
    key_delta(nm, timing[nm] + T_MOVE0, h)
    key_delta(nm, timing[nm] + T_MOVE1, (0, 0, 0))

# pivot: ters çevirme (Y ekseni, kitap yüzü çevrilir; baş yukarıda kalır) ve son dönüş (Z)
t_flip = next(tt for tt, dd, st in step_times if st is None)
pivot.rotation_euler = (0, 0, 0)
for sec, ry, rz in ((0, 0, 0), (t_flip, 0, 0), (t_flip + FLIP_D, math.pi, 0), (T_FLIPBACK, math.pi, 0),
                    (T_FLIPBACK + 1.6, 2 * math.pi, 0), (T_SPIN0, 2 * math.pi, 0), (T_SPIN0 + 3.8, 2 * math.pi, -2 * math.pi)):
    pivot.rotation_euler = (0, ry, rz)
    pivot.keyframe_insert("rotation_euler", frame=fr(sec))
# kamera: (saniye, hedef noktası (mm), uzaklık (mm), yön, ters çevrilmiş mi)
cams = [(0.0, CEN, HERO_DIST, HERO, False), (T_HERO - 0.1, CEN, HERO_DIST * 0.96, HERO, False),
        (T_EXPL1 - 0.2, (CEN.x, CEN.y, CEN.z + 70), 780.0, STAGE, False)]
caps = []
for st_t, st_d, st in step_times:
    if st is None:
        cams.append((st_t + 0.1, CEN, 360.0, STAGE, False))
        cams.append((st_t + st_d, CEN, 360.0, STAGE, True))
        continue
    pt, dist, dr, fl = st[3]
    cams.append((st_t, pt, dist, dr, fl))
    cams.append((st_t + st_d - 0.35, pt, dist * 0.96, dr, fl))
    caps.append({"bas": st_t + 0.1, "bit": st_t + st_d - 0.1, "baslik": st[1], "alt": st[2], "parca": st[0]})
cams.append((T_FLIPBACK + 0.0, CEN, 360.0, STAGE, True))
cams.append((T_FLIPBACK + 1.8, CEN, 340.0, HERO, False))
cams.append((T_END, CEN, 330.0, HERO, False))
for sec, pt, dist, dr, fl in cams:
    a, cpos = cam_pose(W(pt, fl), dist, Vector(dr))
    aim.location, cam.location = a, cpos
    aim.keyframe_insert("location", frame=fr(sec))
    cam.keyframe_insert("location", frame=fr(sec))
scene.frame_start, scene.frame_end = 1, N_FRAMES

# ------------------------------------------------------------------ motor
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.ornek
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 3
scene.cycles.transmission_bounces = 2
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.compositor_device = "CPU"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.view_settings.exposure = args.pozlama

outdir = Path(args.out).resolve()
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "zaman.json").write_text(json.dumps({
    "fps": FPS, "kare": N_FRAMES, "sure": T_END, "adimlar": caps,
    "genel": {"patlama": [T_EXPL0, T_EXPL1], "cevirme": t_flip, "son_cevirme": T_FLIPBACK, "donus": T_SPIN0}},
    ensure_ascii=False, indent=1))

if args.kareler:
    wanted = []
    for part in args.kareler.split(","):
        if "-" in part:
            a, b = part.split("-")
            wanted += list(range(int(a), int(b) + 1))
        else:
            wanted.append(int(part))
else:
    wanted = list(range(1, N_FRAMES + 1))
for f in wanted:
    out = outdir / f"kare_{f:04d}.png"
    if out.exists():
        continue
    scene.frame_set(f)
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
print("yazildi", outdir, N_FRAMES)
