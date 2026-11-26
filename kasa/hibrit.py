"""CYD hibrit kasa konsepti: Çakıl gövde + yüzen Panel + döner çubuk ayak + gömülü anahtarlık tüneli.

Parçalar (her biri tek filament): on_govde, panel, arka_kapak (şeffaf), tabla, cubuk.
Renkler render'da palete göre verilir (render.py 6. argüman); burada nötr varsayılanlar var.
Kaba konsept: ölçü ve baskı detayları (vida, port, tolerans) seçimden sonra işlenecek.
"""

import build123d as bd
from cad import model

from konseptler import _box, _cyl, _floor_gap, _stand
from konseptler2 import _ref_inside, _rr

W, H, T, R = 102.0, 66.0, 21.0, 17.0
Z_SPLIT = 8.5                     # ön gövde / arka kapak ayrımı
PANEL_W, PANEL_H, PANEL_R = 76.0, 54.0, 5.0
GAP = 0.9                         # panel çevresindeki gölge boşluğu
TT_Y = -2.0                       # döner tabla merkezi
BAR_HINGE_Y = TT_Y + 12.0
KEY = (W / 2 - 9.0, H / 2 - 9.0)  # anahtarlık tüneli köşesi


def outer():
    s = _rr(W, H, R, 0, T)
    s = s.fillet(8.0, s.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[-1])   # şişkin sırt
    return s.fillet(2.5, s.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[0])  # yumuşak ön kenar


def front_body():
    b = outer() & _box(-W, W, -H, H, -1, Z_SPLIT)
    b -= _rr(PANEL_W + 2 * GAP, PANEL_H + 2 * GAP, PANEL_R + GAP, -0.1, 2.6)       # panel yuvası
    b -= _rr(W - 5, H - 5, R - 2.5, 2.6, Z_SPLIT + 0.1)                            # iç boşluk
    b.label, b.color = "on_govde", "#1a1a1a"
    return b


def panel():
    p = _rr(PANEL_W, PANEL_H, PANEL_R, 0.6, 2.6)
    p -= _rr(62, 48, 2.0, 0.5, 1.5)                                                # ekran penceresi
    p.label, p.color = "panel", "#8a8d91"
    return p


def screen():
    g = _rr(61.6, 47.6, 1.8, 0.9, 1.5)
    g.label, g.color = "ekran", "#0b0d12"
    return g


def back_cover():
    b = outer() & _box(-W, W, -H, H, Z_SPLIT, T + 1)
    b -= _rr(W - 5, H - 5, R - 2.5, Z_SPLIT - 0.1, T - 2.2)                        # iç boşluk
    b -= _cyl(15.5, T - 1.4, T + 1, 0, TT_Y)                                       # tabla yuvası
    for k in range(5):                                                             # eş merkezli yivler
        r0 = 20.0 + k * 3.2
        b -= _cyl(r0 + 0.55, T - 0.7, T + 1, 0, TT_Y) - _cyl(r0 - 0.55, T - 2, T + 2, 0, TT_Y)
    # gömülü anahtarlık tüneli: sırttan girip yandan çıkan iki kanal + köşede dolu boğaz
    boss = _cyl(5.5, Z_SPLIT + 3.5, T, *KEY) & outer()
    b += boss
    b -= _cyl(2.0, T - 8.0, T + 1, *KEY)
    side = bd.Pos(KEY[0], KEY[1], T - 6.5) * (bd.Rot(0, 0, 45) * (bd.Rot(0, 90, 0) * bd.Cylinder(2.0, 24, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))))
    b -= side
    b.label, b.color = "arka_kapak", "#e8eef0"
    return b


def turntable():
    d = _cyl(15.0, T - 1.4, T + 0.4, 0, TT_Y)
    d -= _cyl(12.5, T - 0.2, T + 1, 0, TT_Y)
    d.label, d.color = "tabla", "#f5c518"
    return d


def bar(angle):
    b = _box(-3.6, 3.6, -34, 0, -1.3, 1.3)
    b = b.fillet(1.2, b.edges().filter_by(bd.Axis.Y))
    b += bd.Rot(0, 90, 0) * bd.Cylinder(2.2, 14)
    b = bd.Rot(-angle, 0, 0) * b
    b = bd.Pos(0, BAR_HINGE_Y, T + 0.9) * b
    b.label, b.color = "cubuk", "#f5c518"
    return b


@model
def hibrit():
    fb, bc = front_body(), back_cover()
    a = _floor_gap(bc, bar, 16.0)
    parts = [fb, panel(), screen(), bc, turntable(), *_ref_inside(4.0)]
    return bd.Compound(children=_stand(parts, [bar(a)], 16.0), label="hibrit")


if __name__ == "__main__":
    hibrit()
