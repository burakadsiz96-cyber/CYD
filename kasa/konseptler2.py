"""CYD kasa konseptleri, 2. tur: biçim/his/yüzey denemeleri (kaba, ölçü ve baskı için değil).

1 "Cakil"   : organik çakıl taşı, oyuncak hissi, buzlu şeffaf; arkada gömülü döner halka.
2 "Panel"   : çerçeve + yüzen ekran paneli, profesyonel; çizgi dokulu sırt, döner çubuk ayak.
3 "Retro"   : organik gövde + kalın CRT çerçevesi, retro-fütür; şeffaf renkli, ayrı kaide.
4 "Minimal" : ince çerçeve + yüzen panel; nokta dokulu sırt, köşede çapraz menteşeli üçgen kanat.
Etiketinde "buzlu" geçen parçalar render'da yarı saydam buzlu plastik olarak çizilir.
"""

import math

import build123d as bd
from cad import model

from konseptler import _box, _cyl, _floor_gap, _min_z, _place, _solve, _stand

W, H = 94.0, 58.0


def _rr(w, h, r, z0, z1):
    return bd.Pos(0, 0, z0) * bd.extrude(bd.RectangleRounded(w, h, r), amount=z1 - z0)


def _round_all(s, r):
    return s.fillet(r, s.edges().filter_by(bd.Plane.XY))


def _ref_inside(z_pcb, show_battery=True):
    """Şeffaf gövdelerde içeriden görünen kart + pil (kaba)."""
    pcb = _box(-43, 43, -25, 25, z_pcb, z_pcb + 1.6)
    pcb.label, pcb.color = "ic_kart", "#d9b81c"
    esp = _box(-40, -22, -9, 9, z_pcb + 1.6, z_pcb + 4.6)
    esp.label, esp.color = "ic_esp32", "#9aa0a6"
    parts = [pcb, esp]
    if show_battery:
        bat = _box(-10, 38, -16, 16, z_pcb + 2.2, z_pcb + 7.2)
        bat.label, bat.color = "ic_pil", "#c9ccd2"
        parts.append(bat)
    return parts


def _glass(w, h, r, z0=0.3, z1=1.3, x=0.0):
    g = bd.Pos(x, 0, 0) * _rr(w, h, r, z0, z1)
    g.label, g.color = "ekran", "#0b0d12"
    return g


# ================================================================== 1 Cakil
T1 = 21.0
RING_CY = -2.0


def c1_body():
    b = _rr(W + 10, H + 12, 26, 0, T1)
    b = _round_all(b, 9.5)
    b -= _rr(63, 49, 4, -5, 1.6)                                   # ekran yuvası (kavisli önü düzle)
    b -= _cyl(19.5, T1 - 2.6, T1 + 5, 0, RING_CY)                   # halka çanağı
    b = b - _rr(W + 2, H + 4, 20, 2.0, T1 - 2.0)                    # içi boş kabuk
    # anahtarlık: köşede gövdeden oyulmuş kulp (kordon geçer)
    b -= bd.Pos(W / 2 - 1, H / 2 + 1, T1 / 2) * bd.Cylinder(3.2, T1 + 2)
    b.label, b.color = "govde_buzlu", "#7fd3c6"
    return b


def c1_ring(angle):
    ring = _cyl(17.0, -1.5, 1.5, 0, -17) - _cyl(12.0, -2, 2, 0, -17)
    ring += bd.Rot(0, 90, 0) * bd.Cylinder(1.8, 10)
    ring = bd.Rot(-angle, 0, 0) * ring
    ring = bd.Pos(0, RING_CY + 17, T1 - 1.4) * ring
    ring.label, ring.color = "halka", "#ff7a59"
    return ring


def c1_disc():
    d = _cyl(18.6, T1 - 2.6, T1 - 1.6, 0, RING_CY)
    d.label, d.color = "tabla", "#ff7a59"
    return d


@model
def k1_cakil():
    body = c1_body()
    a = _floor_gap(body, c1_ring, 16.0)
    parts = [body, c1_disc(), _glass(62, 48, 3.5, 0.6, 1.6), *_ref_inside(3.0)]
    return bd.Compound(children=_stand(parts, [c1_ring(a)], 16.0), label="k1_cakil")


# ================================================================== 2 Panel
T2 = 20.0
GAP = 1.0


def c2_frame():
    f = _rr(W, H, 4, 0, T2)
    f = f.fillet(0.8, f.edges().filter_by(bd.Plane.XY))
    f -= _rr(W - 6, H - 6, 2.2, -0.1, 3.0)                          # panel için ön boşluk
    # sırt dokusu: ince yatay yivler
    for i in range(-11, 12):
        f -= _box(-W / 2 + 6, W / 2 - 6, i * 2.2 - 0.45, i * 2.2 + 0.45, T2 - 0.6, T2 + 0.1)
    f -= _cyl(13.5, T2 - 1.0, T2 + 0.1)                             # tabla yuvası
    # anahtarlık: çerçeve köşesinde ince yarık
    f -= bd.Pos(-W / 2 + 4.5, H / 2 - 4.5, T2 / 2) * (bd.Rot(0, 0, 45) * bd.Box(6, 2.2, T2 + 2))
    f.label, f.color = "cerceve", "#b9bcc0"
    return f


def c2_panel():
    p = _rr(W - 6 - 2 * GAP, H - 6 - 2 * GAP, 1.4, 0.8, 3.0)
    p -= _rr(62, 48, 1.0, 0.7, 1.4)
    p.label, p.color = "panel", "#26282c"
    return p


def c2_bar(angle):
    bar = _box(-3.5, 3.5, -30, 0, -1.2, 1.2)
    bar = bar.fillet(1.1, bar.edges().filter_by(bd.Axis.Y))
    bar += bd.Rot(0, 90, 0) * bd.Cylinder(2.0, 13)
    bar = bd.Rot(-angle, 0, 0) * bar
    bar = bd.Pos(0, 10, T2 + 1.0) * bar
    bar.label, bar.color = "cubuk_ayak", "#e2552d"
    return bar


def c2_disc():
    d = _cyl(13.0, T2 - 1.0, T2 + 0.3)
    d.label, d.color = "tabla", "#26282c"
    return d


@model
def k2_panel():
    frame = c2_frame()
    a = _floor_gap(frame, c2_bar, 15.0)
    parts = [frame, c2_panel(), c2_disc(), _glass(61.6, 47.6, 0.8, 0.9, 1.3)]
    return bd.Compound(children=_stand(parts, [c2_bar(a)], 15.0), label="k2_panel")


# ================================================================== 3 Retro
T3 = 23.0


def c3_outer():
    b = _rr(W + 4, H + 6, 16, 0, T3)
    b = b.fillet(7.0, b.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[-1])
    return b.fillet(2.0, b.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[0])


def c3_body():
    b = c3_outer()
    b -= _rr(72, 56, 12, -0.1, 2.5)                                  # CRT çerçeve yuvası
    b = b - _rr(W - 4, H - 2, 12, 3.0, T3 - 3.0)
    # hoparlör nokta ızgarası (sağ şerit)
    for i in range(3):
        for j in range(5):
            b -= _cyl(0.9, -0.1, 3.5, W / 2 - 4.5 - i * 3.2, -6 + j * 3.0)
    b.label, b.color = "govde_buzlu", "#8e6bd6"
    return b


def c3_bezel():
    z = _rr(71.6, 55.6, 12, 0.0, 2.5)
    z -= _rr(62, 48, 6, -0.1, 3)
    z = z.fillet(1.0, z.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[0])
    z.label, z.color = "crt_cerceve", "#f2efe6"
    return z


def c3_antenna():
    a = _cyl(2.0, 0, 10)
    a = bd.Pos(-W / 2 + 10, H / 2 + 2, T3 / 2) * (bd.Rot(-90, 0, 0) * a)
    ball = bd.Pos(-W / 2 + 10, H / 2 + 12.5, T3 / 2) * bd.Sphere(3.6)
    ball -= bd.Pos(-W / 2 + 10, H / 2 + 12.5, T3 / 2) * bd.Cylinder(1.6, 10)
    out = a + ball
    out.label, out.color = "anten_anahtarlik", "#f2efe6"
    return out


@model
def k3_retro():
    body = c3_body()
    tilt = 14.0
    parts = [body, c3_bezel(), c3_antenna(), _glass(61.6, 47.6, 6, 0.6, 1.6), *_ref_inside(4.0)]
    placed = [_place(p, tilt) for p in parts]
    zb = _min_z(placed[0])
    lift = 5.0 - zb
    out = []
    for src, p in zip(parts, placed):
        q = bd.Pos(0, 0, lift) * p
        q.label, q.color = src.label, src.color
        out.append(q)
    # kaide: oval taban, cihazın alt kenarının oturduğu eğik yuva
    base = bd.extrude(bd.Ellipse(58, 22), amount=9.0)
    base = base.fillet(3.5, base.edges().group_by(bd.Axis.Z)[-1])
    base = bd.Pos(0, 2, 0) * base
    base -= bd.Pos(0, 0, lift) * _place(c3_outer(), tilt)   # cihazın dış biçimi kaideye yuva olur
    base.label, base.color = "kaide", "#f2efe6"
    return bd.Compound(children=[*out, base], label="k3_retro")


# ================================================================== 4 Minimal
T4 = 18.0


def c4_frame():
    f = _rr(W, H, 6, 0, T4)
    f = f.chamfer(3.0, None, f.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[-1])
    f -= _rr(W - 5, H - 5, 3.5, -0.1, 2.4)
    # nokta dokusu
    for i in range(-8, 9):
        for j in range(-4, 5):
            if (i + j) % 2 == 0:
                f -= _cyl(0.75, T4 - 0.7, T4 + 0.1, i * 4.6, j * 4.6)
    f -= _cyl(2.4, -1, T4 + 1, W / 2 - 6.5, H / 2 - 6.5)            # anahtarlık deliği
    f.label, f.color = "cerceve", "#d8cfc0"
    return f


def c4_panel():
    p = _rr(W - 5 - 1.6, H - 5 - 1.6, 2.7, 0.9, 2.4)
    p -= _rr(62, 48, 1.0, 0.8, 1.4)
    p.label, p.color = "panel", "#1d1e20"
    return p


def c4_flap(angle):
    """Sol-alt köşede üçgen kanat; menteşe köşegene dik, iki yönde de destekler."""
    tri = bd.extrude(bd.Polygon((-15, 0), (15, 0), (0, -26), align=None), amount=2.4)
    tri = bd.Pos(0, 0, -1.2) * tri
    tri = tri.fillet(1.0, tri.edges().filter_by(bd.Axis.Z))
    tri += bd.Rot(0, 90, 0) * bd.Cylinder(1.6, 26)
    tri = bd.Rot(-angle, 0, 0) * tri
    tri = bd.Rot(0, 0, 45) * tri
    tri = bd.Pos(-4, -4, T4 + 1.0) * tri
    tri.label, tri.color = "kanat_ayak", "#1d1e20"
    return tri


@model
def k4_minimal():
    frame = c4_frame()
    a = _floor_gap(frame, c4_flap, 14.0)
    parts = [frame, c4_panel(), _glass(61.6, 47.6, 0.8, 1.0, 1.4)]
    return bd.Compound(children=_stand(parts, [c4_flap(a)], 14.0), label="k4_minimal")


if __name__ == "__main__":
    k1_cakil()
    k2_panel()
    k3_retro()
    k4_minimal()
