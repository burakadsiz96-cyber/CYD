"""Stüdyo ürün render'ı: cad run render.py MODEL.glb CIKTI.png [on|arka|yan] [ornek_sayisi]

Model z=0 zemininde durur; kamera ve ışıklar modelin kutusuna göre kurulur.
Ekran kartı olmayan sunucuda Cycles (CPU) + OIDN gürültü giderme kullanır.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

from cad.blender import load

glb, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
view = sys.argv[3] if len(sys.argv) > 3 else "on"
samples = int(sys.argv[4]) if len(sys.argv) > 4 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
model = load(glb)
c, size = model.center, model.size
r = size.length / 2

# --- zemin: sonsuz görünen yumuşak beyaz fon (kavisli değil, büyük düzlem + gölge yakalayıcı ton)
bpy.ops.mesh.primitive_plane_add(size=r * 60, location=(c.x, c.y, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("zemin")
fm.use_nodes = True
bsdf = fm.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.55, 0.55, 0.57, 1)
bsdf.inputs["Roughness"].default_value = 0.55
floor.data.materials.append(fm)

# plastik görünüm: model malzemelerini mat-saten baskı plastiğine yaklaştır, ekranı cam yap
for m in bpy.data.materials:
    if m.name == "zemin" or not m.use_nodes:
        continue
    p = m.node_tree.nodes.get("Principled BSDF")
    if p is None:
        continue
    col = p.inputs["Base Color"].default_value
    if max(col[:3]) < 0.02:          # ekran: koyu parlak cam
        p.inputs["Roughness"].default_value = 0.18
        p.inputs["Coat Weight"].default_value = 0.4
    else:
        p.inputs["Roughness"].default_value = 0.42
        p.inputs["Metallic"].default_value = 0.0

# etiketinde "buzlu" geçen parçalar: yarı saydam buzlu plastik (rengi kendi rengi)
for ob in bpy.data.objects:
    if "buzlu" not in ob.name or ob.type != "MESH":
        continue
    src = ob.active_material
    base = src.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:] if src else (0.6, 0.8, 0.8, 1)
    fm2 = bpy.data.materials.new(ob.name + "_buzlu")
    fm2.use_nodes = True
    q = fm2.node_tree.nodes["Principled BSDF"]
    q.inputs["Base Color"].default_value = base
    q.inputs["Transmission Weight"].default_value = 0.92
    q.inputs["Roughness"].default_value = 0.38
    q.inputs["IOR"].default_value = 1.5
    q.inputs["Subsurface Weight"].default_value = 0.08
    ob.data.materials.clear()
    ob.data.materials.append(fm2)

# --- kamera
dirs = {
    "on": Vector((-0.55, -1.0, 0.42)),
    "arka": Vector((0.75, 1.0, 0.55)),
    "yan": Vector((-1.0, 0.15, 0.25)),
}
scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
aim = bpy.data.objects.new("aim", None)
aim.location = c
cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
cam.data.lens = 70
half = math.tan(cam.data.angle / 2) * min(1, scene.render.resolution_y / scene.render.resolution_x)
cam.location = c + (r / half * 0.8) * dirs[view].normalized()
cam.constraints.new("TRACK_TO").target = aim
scene.collection.objects.link(aim)
scene.collection.objects.link(cam)
scene.camera = cam


def area(name, loc, energy, size_m, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy, light.size, light.color = energy, size_m, color
    ob = bpy.data.objects.new(name, light)
    ob.location = c + Vector(loc) * r
    ob.constraints.new("TRACK_TO").target = aim
    scene.collection.objects.link(ob)


k = (r / 0.06) ** 2  # enerjiyi model boyutuna göre ölçekle
area("anahtar", (-3.0, -3.0, 4.0), 5 * k, r * 4)
area("dolgu", (4.0, -2.0, 1.5), 2.0 * k, r * 6, (0.92, 0.95, 1.0))
area("kontur", (1.0, 5.0, 3.5), 6 * k, r * 3, (1.0, 0.96, 0.9))

scene.world = bpy.data.worlds.new("world")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.92, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
scene.render.compositor_device = "CPU"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = str(out)
bpy.ops.render.render(write_still=True)
print("yazildi", out)
