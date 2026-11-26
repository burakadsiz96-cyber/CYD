"""CYD kasa konseptleri: biçim ve tek-ayak fikirlerini görmek için kaba modeller (ölçü/baskı için değil).

A "Halka"   : yumuşak köşeli retro cep cihazı, arkada döner tabla üzerinde tek halka-ayak.
B "Tampon"  : köşe tamponlu endüstriyel gövde, çapraz menteşeli tek ayak (iki yönde de çalışır).
C "Kalem"   : pahlı/kama yüzlü ince gövde, yan kanalda saklanan çubuk = ayak + dokunmatik kalem.
Her model ayakta duran pozda kurulur: ayak ucu ve gövdenin alt kenarı aynı zemine (z=0) değer.
"""

import math

import build123d as bd
from cad import model

W, H, T = 94.0, 58.0, 21.0
TILT = 18.0  # ekranın dikeyden geriye yatışı (A ve B için)


# ------------------------------------------------------------------ ortak yardımcılar
def _box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _cyl(r, z0, z1, x=0.0, y=0.0):
    return bd.Pos(x, y, z0) * bd.Cylinder(r, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _slab(w, h, r, z0, z1, fillet=0.0):
    s = bd.Pos(0, 0, z0) * bd.extrude(bd.RectangleRounded(w, h, r), amount=z1 - z0)
    if fillet:
        s = s.fillet(fillet, s.edges().filter_by(bd.GeomType.LINE, reverse=True).filter_by(bd.Plane.XY)
                     + s.edges().filter_by(bd.GeomType.LINE).filter_by(bd.Plane.XY))
    return s


def _screen(win_w=60.0, win_h=46.0, r=2.0):
    glass = _slab(win_w - 0.3, win_h - 0.3, r, 0.25, 1.2)
    glass.label, glass.color = "ekran", "#0b0d12"
    return glass


def _place(shape, tilt):
    """Yerel (ekran z=0'da -z'ye bakar) -> dünya: ekran izleyiciye (-y) bakar, alt kenar aşağıda."""
    return bd.Rot(90 - tilt, 0, 0) * (bd.Rot(0, 180, 0) * shape)


def _min_z(shape):
    return shape.bounding_box().min.Z


def _solve(f, lo, hi, n=40):
    flo = f(lo)
    for _ in range(n):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def _stand(parts, legs, tilt):
    """parts/legs: yerel şekiller. Hepsini yerleştirir, en alçak noktayı z=0'a indirir."""
    placed = [_place(p, tilt) for p in parts] + [_place(l, tilt) for l in legs]
    z0 = min(_min_z(p) for p in placed)
    out = []
    for src, p in zip(parts + legs, placed):
        q = bd.Pos(0, 0, -z0) * p
        q.label, q.color = src.label, src.color
        out.append(q)
    return out


def _floor_gap(body, leg_fn, tilt, lo=3, hi=88):
    """Ayak açısını, ayak ucu gövde alt kenarıyla aynı yüksekliğe gelene kadar çözer."""
    zb = _min_z(_place(body, tilt))
    return _solve(lambda a: _min_z(_place(leg_fn(a), tilt)) - zb, lo, hi)


# ------------------------------------------------------------------ A: Halka
A_RING_HINGE_Y = 12.0
A_RING_R, A_RING_r, A_RING_T = 17.0, 11.5, 3.0


def a_body():
    b = _slab(W, H, 13, 0, T, fillet=4.5)
    b -= _slab(61, 47, 2.5, -0.1, 1.2)                         # ekran yuvası
    # arka: döner tabla yuvası + halka cebi
    b -= _cyl(21.5, T - 1.2, T + 0.1, 0, A_RING_HINGE_Y - A_RING_R)
    # yan: kordon/anahtarlık için köşeden geçen kavisli delik
    b -= _cyl(2.3, -0.1, T + 0.1, W / 2 - 7.5, H / 2 - 7.5)
    # alt kenarda ince yatay yiv (retro çizgi)
    for i in range(3):
        b -= _box(-W / 2 - 1, W / 2 + 1, -H / 2 - 1, -H / 2 + 0.6, 5 + i * 3.2, 5.9 + i * 3.2)
    b.label, b.color = "govde", "#ece4d4"
    return b


def a_turntable():
    d = _cyl(21.0, T - 1.2, T + 0.6, 0, A_RING_HINGE_Y - A_RING_R)
    d -= _cyl(17.8, T, T + 0.7, 0, A_RING_HINGE_Y - A_RING_R)
    for k in range(12):                                         # tırtıl
        a = 2 * math.pi * k / 12
        d -= _cyl(1.0, T - 1.3, T + 0.7, 21 * math.cos(a), A_RING_HINGE_Y - A_RING_R + 21 * math.sin(a))
    d.label, d.color = "tabla", "#2a2a2e"
    return d


def a_ring(angle):
    cy = -A_RING_R
    ring = _cyl(A_RING_R, -A_RING_T / 2, A_RING_T / 2, 0, cy) - _cyl(A_RING_r, -1.6, 1.6, 0, cy)
    ring += bd.Rot(0, 90, 0) * bd.Cylinder(2.2, 12)              # menteşe silindiri
    ring = bd.Rot(-angle, 0, 0) * ring
    ring = bd.Pos(0, A_RING_HINGE_Y, T + A_RING_T / 2 - 0.4) * ring
    ring.label, ring.color = "halka", "#e8742c"
    return ring


@model
def konsept_a_halka():
    body, table = a_body(), a_turntable()
    a = _floor_gap(body, a_ring, TILT)
    return bd.Compound(children=_stand([body, table, _screen()], [a_ring(a)], TILT), label="konsept_a")


# ------------------------------------------------------------------ B: Tampon
B_AXIS_ANGLE = 45.0
B_LEG_L, B_LEG_W, B_LEG_T = 36.0, 12.0, 3.4


def b_body():
    b = _slab(W - 2, H - 2, 4, 0, T, fillet=1.2)
    b -= _slab(64, 50, 1.0, -0.1, 1.4)
    # arka ızgara: altıgen delik dizisi (sığ)
    hexes = []
    for i in range(-3, 4):
        for j in range(-2, 3):
            x = 18 + i * 4.6 + (2.3 if j % 2 else 0)
            y = j * 4.0
            if abs(x) < 40:
                hexes.append(bd.Pos(x, y, T - 1.0) * bd.extrude(bd.RegularPolygon(1.9, 6), amount=1.2))
    for h in hexes:
        b -= h
    # yan vida başları görünümü
    b.label, b.color = "govde", "#33363c"
    return b


def b_bumpers():
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner = _box(*sorted((sx * (W / 2 - 13), sx * (W / 2 + 2))), *sorted((sy * (H / 2 - 13), sy * (H / 2 + 2))), -0.8, T + 0.8)
            shell = _slab(W + 1.6, H + 1.6, 7, -0.8, T + 0.8, fillet=2.5)
            c = shell & corner
            if sx > 0 and sy > 0:
                c -= _cyl(2.6, -1, T + 1, W / 2 - 4.5, H / 2 - 4.5)   # anahtarlık deliği
            c.label, c.color = f"tampon_{'s' if sx > 0 else 'l'}{'u' if sy > 0 else 'd'}", "#ff6a13"
            out.append(c)
    return out


def b_leg(angle):
    """Çapraz eksenli tek ayak: eksen arka yüzde 45°; ayak sol-alt köşeye doğru açılır."""
    h = B_LEG_T / 2
    leg = _box(-B_LEG_W / 2, B_LEG_W / 2, -B_LEG_L, 0, -h, h)
    leg = leg.fillet(2.5, leg.edges().filter_by(bd.Axis.Z).group_by(bd.Axis.Y)[0])
    leg += bd.Rot(0, 90, 0) * bd.Cylinder(2.6, B_LEG_W + 6)
    leg = bd.Rot(-angle, 0, 0) * leg
    leg = bd.Rot(0, 0, B_AXIS_ANGLE) * leg     # ekseni çapraza çevir (yerel çerçevede ayak -x,-y'ye)
    leg = bd.Pos(6, 6, T + h - 0.3) * leg
    leg.label, leg.color = "ayak", "#ff6a13"
    return leg


@model
def konsept_b_tampon():
    body = b_body()
    a = _floor_gap(body, b_leg, TILT)
    return bd.Compound(children=_stand([body, *b_bumpers(), _screen(62, 48, 0.8)], [b_leg(a)], TILT),
                       label="konsept_b")


# ------------------------------------------------------------------ C: Kalem
C_STICK_R, C_STICK_L = 2.6, 74.0
C_SOCKET = (0.0, 6.0)          # arka yüzde soket konumu
C_SOCKET_ANGLE = 74.0          # çubuğun arka yüzle açısı


def c_body():
    b = bd.extrude(bd.RectangleRounded(W, H, 6), amount=T)
    b = b.chamfer(5.5, None, b.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[-1])   # arka kenarlar kama
    b = b.chamfer(1.2, None, b.edges().filter_by(bd.Plane.XY).group_by(bd.Axis.Z)[0])
    b -= _slab(62, 48, 3, -0.1, 1.0)
    # üst kenar boyunca çubuk kanalı
    b -= bd.Pos(0, H / 2 - 4.5, T - 2.0) * (bd.Rot(0, 90, 0) * bd.Cylinder(C_STICK_R + 0.2, C_STICK_L + 1))
    # iki soket (yatay ve dikey duruş): çubuğun girdiği eğik delikler
    for rotz in (0, -90):
        s = bd.Rot(90 - C_SOCKET_ANGLE, 0, 0) * bd.Cylinder(C_STICK_R + 0.25, 24)
        b -= bd.Rot(0, 0, rotz) * (bd.Pos(C_SOCKET[0], C_SOCKET[1], T) * s)
    # köşe: anahtarlık yarığı (pahın içinden)
    b -= bd.Pos(-W / 2 + 6, H / 2 - 6, T / 2) * (bd.Rot(0, 0, 45) * bd.Box(9, 3.2, T + 2))
    b.label, b.color = "govde", "#9fb39a"
    return b


def c_stick():
    s = bd.Cylinder(C_STICK_R, C_STICK_L - 6, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    s = s.fillet(0.8, s.edges().group_by(bd.Axis.Z)[0])
    s.label, s.color = "cubuk", "#202224"
    tip = bd.Pos(0, 0, C_STICK_L - 6) * bd.Cone(C_STICK_R, 1.2, 6, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    tip.label, tip.color = "kalem_ucu", "#e9e9e6"
    return s, tip


def c_stick_placed():
    """Yatay soketteki çubuk: 10 mm içerde, dışarı doğru aşağı (-y) eğik."""
    s, tip = c_stick()
    out = []
    for p in (s, tip):
        q = bd.Pos(C_SOCKET[0], C_SOCKET[1], T) * (bd.Rot(90 - C_SOCKET_ANGLE, 0, 0) * (bd.Pos(0, 0, -10) * p))
        q.label, q.color = p.label, p.color
        out.append(q)
    return out


@model
def konsept_c_kalem():
    body = c_body()
    stick = c_stick_placed()
    zb = lambda t: _min_z(_place(body, t))
    t = _solve(lambda t: min(_min_z(_place(p, t)) for p in stick) - zb(t), 2, 60)
    return bd.Compound(children=_stand([body, _screen(61.5, 47.5, 2.5)], stick, t), label="konsept_c")


if __name__ == "__main__":
    konsept_a_halka()
    konsept_b_tampon()
    konsept_c_kalem()
