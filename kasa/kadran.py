"""KADRAN — CYD 2.8" (ESP32-2432S028R) için cep saati esintili el enstrümanı kasası.

Fikir
  * Ekran, dakika ölçeği taşıyan "yüzer" bir kadran panelinde; çevresinde ince gölge boşluğu.
    Ölçek çizgileri panelde boydan boya yarık: arkadaki koyu boşluk onları boyar (tek renk baskı).
  * Sağ alttaki kurma kolu, dokunmatik kalemin başlığıdır: çekince kalem tünelden çıkar.
  * Tepedeki saat kulpunun deliği anahtarlık deliğidir (cihaz dengeli asılır).
  * Arkadaki dişli çark döner (yatay/dikey için 90° tırnak); dişli halkası açılır: masada ayak,
    elde parmak halkası. Halka yalnızca iki doğru konumda açılır ve açıkken çark dönmez.
  * Vida başlarında ve çark merkezinde şeffaf kırmızı "yakut" kapaklar; sağda saat itici
    gibi duran açma/kapama düğmesi.

Koordinatlar: X sağ, Y yukarı (ekrana bakan kişiye göre); ekran yüzü z=T'de +z'ye bakar, sırt z=0.
d = ekran yüzünden içeri derinlik (z = T - d). Birim mm.
Baskı: FDM PETG/PLA, 0.4 nozul. Ön kasa ve panel yüzü tablada; arka kapak sırtı tablada.
Ölç ve düzelt (parametreler): kart delik aralığı, ekran kaydırma, usb_y, sd_y, kalem çapı/boyu.

Check: cad model dfm "$ID" --process printing --technology fdm --material petg
"""

import math
from functools import lru_cache, reduce

import build123d as bd
from cad import model
from cad.build123d import memo

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"

# ============================================================== CYD kartı (varsayımlar)
PCB_X, PCB_Y, PCB_T = 86.0, 50.0, 1.6
LCD_X, LCD_Y, LCD_T = 70.0, 50.0, 4.0
VIEW_X, VIEW_Y = 57.6, 43.2               # 2.8" 320x240 aktif alan
BACK_PARTS = 4.8                          # kart sırtındaki en uzun bileşen
CLR = 0.3
HOLE_DX = model.param("delik_araligi_x", 78.0, min=70, max=82, unit="mm")
HOLE_DY = model.param("delik_araligi_y", 42.0, min=36, max=46, unit="mm")
VIEW_DX = model.param("ekran_kaydirma_x", 0.0, min=-5, max=5, unit="mm")
USB_Y = model.param("usb_y", 0.0, min=-14, max=2, unit="mm")        # sağ kenar: kartın USB'si
SD_Y = model.param("sd_y", 0.0, min=-14, max=12, unit="mm")         # sol kenar: microSD
STYLUS_D = model.param("kalem_cap", 5.0, min=3.5, max=6.0, unit="mm")
STYLUS_L = model.param("kalem_boy", 87.0, min=60, max=92, unit="mm")
STAND = model.param("ayak_acisi", 37.0, min=28, max=46, unit="deg")  # halkanın açılma durdurağı

# ============================================================== gövde
W, H, RC = 106.0, 72.0, 9.0
PENDANT_R, PENDANT_Y = 9.0, H / 2 - 5.0   # saat kulpu
KEY, KEY_R = (0.0, 33.0), 2.75            # anahtarlık deliği
T = 21.5
WALL, FLOOR = 2.2, 2.6
BEVEL_F, BEVEL_B = 2.5, 3.0               # ön ve arka 45° pahlar (baskıda tabla kenarı)

D_PANEL = 1.6
D_LEDGE = 2.4                             # LCD ön yüzü
D_PCB = D_LEDGE + LCD_T                   # 6.4
D_PCB_B = D_PCB + PCB_T                   # 8.0
D_SPLIT = D_PCB_B + BACK_PARTS + 0.4      # 13.2  ön kasa / arka kapak ayrımı
D_FLOOR = T - FLOOR                       # 18.9  arka taban iç yüzü

WIN_W, WIN_H = VIEW_X + 0.8, VIEW_Y + 0.8
TICK_OFF, PANEL_OFF = 4.1, 5.6
PANEL_W, PANEL_H, PANEL_R = WIN_W + 2 * PANEL_OFF, WIN_H + 2 * PANEL_OFF, 6.0
GAP, LEDGE = 0.8, 2.4

HOLES = [(sx * HOLE_DX / 2, sy * HOLE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]
HIDDEN = (-HOLE_DX / 2, -HOLE_DY / 2)     # çarkın altında kalan vida (kart deliğinden)
PRESSERS = [p for p in HOLES if p != HIDDEN]
MARGIN = [(46.8, 20.0), (46.8, -20.0), (-46.8, 20.0)]   # görünen vidalar (yakut kapaklı)

TUBE_Y, TUBE_D, TUBE_X0, CROWN_X = -29.6, 6.8, -42.0, 49.0
SW_Y, SW_D = 12.0, D_SPLIT        # itici ekseni ayrım düzleminde: her kabukta yarım delik                  # itici (kilitli basmalı anahtar 7x7)
TP_X0, TP_X1, TP_Y0, TP_Y1 = 16.5, 33.7, 5.8, 33.6
USBC_X, USBC_D = (TP_X0 + TP_X1) / 2, D_FLOOR - 1.6 - 1.65
BAT_X0, BAT_X1, BAT_Y0, BAT_Y1 = -20.5, 13.5, -25.0, 25.0    # 503450 LiPo
D_BAT0, D_BAT1 = D_SPLIT + 0.2, D_SPLIT + 5.2

# ============================================================== çark (ayak)
C = (-27.0, -10.0)
R_RING_O, R_RING_I, R_DISC = 20.0, 13.0, 12.6
DIAL_T, HINGE_R, PIN_Z = 4.4, 17.0, 2.2
GAP_HALF, TAB_HALF = 3.2, 2.8
_TAIL = math.sqrt(R_RING_O ** 2 - GAP_HALF ** 2) - HINGE_R
_A = math.radians(STAND)
TAIL_DEPTH = _TAIL * math.sin(_A) + PIN_Z * math.cos(_A) - PIN_Z
assert math.degrees(math.atan2(_TAIL, PIN_Z)) > STAND + 8, "durdurak tepe açısına çok yakın"
assert STYLUS_L <= CROWN_X + 4.4 - TUBE_X0 - 1.0, "kalem tünele sığmıyor"

COL = {
    "on_kasa": "#8a8d91", "panel": "#f2f2ee", "arka_kapak": "#8a8d91", "cark_gobek": "#f5c518",
    "cark_halka": "#f5c518", "yakut": "#c8202a", "pip": "#c8202a", "kurma_kolu": "#f5c518",
    "itici": "#f5c518", "burc": "#c9ccd2", "ekran": "#0b0d12", "kalem": "#f2f2ee",
}


# ============================================================== yardımcılar
def _box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _cyl(r, z0, z1, x=0.0, y=0.0):
    return bd.Pos(x, y, z0) * bd.Cylinder(r, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _bd(x0, x1, y0, y1, d0, d1):
    return _box(x0, x1, y0, y1, T - d1, T - d0)


def _cd(r, d0, d1, x=0.0, y=0.0):
    return _cyl(r, T - d1, T - d0, x, y)


def _xcyl(r, x0, x1, y, z):
    return bd.Pos(x0, y, z) * (bd.Rot(0, 90, 0) * bd.Cylinder(
        r, x1 - x0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))


def _ycyl(r, y0, y1, x, z):
    return bd.Pos(x, y0, z) * (bd.Rot(-90, 0, 0) * bd.Cylinder(
        r, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))


def _rrf(w, h, r, x=0.0, y=0.0):
    return bd.Pos(x, y) * bd.RectangleRounded(w, h, r)


def _slab(face, z0, z1):
    return bd.Pos(0, 0, z0) * bd.extrude(face, amount=z1 - z0)


def _slab_d(face, d0, d1):
    return _slab(face, T - d1, T - d0)


def _lab(shape, label, color=None):
    shape.label = label
    shape.color = color or COL.get(label.split("_")[0] if label.startswith("yakut") else label, "#888888")
    return shape


@lru_cache(maxsize=None)
def _outline():
    """Köşeleri yuvarlatılmış dikdörtgen + tepede saat kulpu çıkıntısı (iç köşeler yumuşatılmış)."""
    with bd.BuildSketch() as sk:
        bd.RectangleRounded(W, H, RC)
        with bd.Locations((0, PENDANT_Y)):
            bd.Circle(PENDANT_R)
        vs = [v for v in sk.vertices() if abs(v.Y - H / 2) < 0.05 and abs(v.X) < 20]
        bd.fillet(vs, radius=3.5)
    return sk.sketch


@lru_cache(maxsize=None)
def _inset(d):
    return bd.offset(_outline(), amount=-d, kind=bd.Kind.ARC)


def _teardrop_x(r, x0, x1, y, z):
    """X boyunca damla kesitli delik; ucu -z'de (ön kasa yüzü tablada basılınca tavan köprülenmez)."""
    s = r * math.sqrt(0.5)
    prof = bd.Pos(y, z) * bd.Circle(r) + bd.Polygon((y - s, z - s), (y, z - r * math.sqrt(2)), (y + s, z - s), align=None)
    return bd.Pos(x0, 0, 0) * bd.extrude(bd.Plane.YZ * prof, amount=x1 - x0)


def _text(txt, size, x, y, mirror=False):
    sk = bd.Pos(x, y) * bd.Text(txt, font_size=size, font_path=FONT, align=(bd.Align.CENTER, bd.Align.CENTER))
    return bd.mirror(sk, about=bd.Plane.YZ.offset(x)) if mirror else sk


@lru_cache(maxsize=None)
def _outer_proxy():
    s = _slab(_outline(), 0, T)
    s = s.chamfer(BEVEL_F, None, s.faces().sort_by(bd.Axis.Z)[-1].outer_wire().edges())
    return s.chamfer(BEVEL_B, None, s.faces().sort_by(bd.Axis.Z)[0].outer_wire().edges())


# ============================================================== kadran paneli
def _tick_frames():
    """Yuvarlatılmış dikdörtgen yol üzerinde 60 eşit aralık: (x, y, dış normal açısı)."""
    a, b, r = WIN_W / 2 + TICK_OFF, WIN_H / 2 + TICK_OFF, 5.0
    segs = [
        ("L", (0.0, b), (a - r, b), 90.0),
        ("A", (a - r, b - r), 90.0, 0.0),
        ("L", (a, b - r), (a, -(b - r)), 0.0),
        ("A", (a - r, -(b - r)), 0.0, -90.0),
        ("L", (a - r, -b), (-(a - r), -b), -90.0),
        ("A", (-(a - r), -(b - r)), -90.0, -180.0),
        ("L", (-a, -(b - r)), (-a, b - r), 180.0),
        ("A", (-(a - r), b - r), 180.0, 90.0),
        ("L", (-(a - r), b), (0.0, b), 90.0),
    ]
    lens = [math.dist(s[1], s[2]) if s[0] == "L" else math.radians(abs(s[2] - s[3])) * r for s in segs]
    total = sum(lens)
    out = []
    for i in range(60):
        u = i * total / 60
        for s, ln in zip(segs, lens):
            if u <= ln + 1e-9:
                if s[0] == "L":
                    f = u / ln if ln else 0
                    x = s[1][0] + (s[2][0] - s[1][0]) * f
                    y = s[1][1] + (s[2][1] - s[1][1]) * f
                    ang = s[3]
                else:
                    ang = s[2] + (s[3] - s[2]) * (u / ln)
                    x = s[1][0] + r * math.cos(math.radians(ang))
                    y = s[1][1] + r * math.sin(math.radians(ang))
                out.append((x + VIEW_DX, y, ang))
                break
            u -= ln
    return out


def _pip_profile(shrink=0.0):
    b = WIN_H / 2 + TICK_OFF
    return bd.Polygon((-1.8 + shrink, b - shrink * 0.5), (0.0, b - 2.5 + shrink), (1.8 - shrink, b - shrink * 0.5), align=None)


def panel_body():
    p = _slab_d(_rrf(PANEL_W, PANEL_H, PANEL_R, VIEW_DX), 0, D_PANEL)
    p -= _slab_d(_rrf(WIN_W, WIN_H, 1.5, VIEW_DX), -0.1, D_PANEL + 0.1)
    bevel = bd.extrude(_rrf(WIN_W + 1.6, WIN_H + 1.6, 2.3), amount=0.8, taper=45)
    p -= bd.Pos(VIEW_DX, 0, T + 0.01) * (bd.Rot(180, 0, 0) * bevel)
    ticks = []
    for i, (x, y, ang) in enumerate(_tick_frames()):
        if i == 0:
            continue
        major = i % 5 == 0
        ln, wd = (2.1, 1.2) if major else (1.2, 0.8)
        t = _box(-ln, 0, -wd / 2, wd / 2, T - D_PANEL - 0.1, T + 0.1)
        ticks.append(bd.Pos(x, y, 0) * (bd.Rot(0, 0, ang) * t))
    p -= reduce(lambda u, v: u + v, ticks)
    p -= bd.Pos(VIEW_DX, 0, T - D_PANEL - 0.1) * bd.extrude(_pip_profile(), amount=D_PANEL + 0.2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p += _cd(0.6, D_PANEL - 0.01, D_LEDGE - 0.05, VIEW_DX + sx * 34.0, sy * 12.0)
    return _lab(p, "panel")


def pip_body():
    p = bd.Pos(VIEW_DX, 0, T - D_PANEL) * bd.extrude(_pip_profile(0.12), amount=D_PANEL)
    return _lab(p, "pip")


# ============================================================== ön kasa
def _usbc_overmold():
    return _bd(USBC_X - 6.4, USBC_X + 6.4, H / 2 - 0.8, H / 2 + 2, USBC_D - 3.7, USBC_D + 3.7)


@memo
def front_shell():
    o = _outline()
    s = _slab_d(o, 0, D_SPLIT)
    s = s.chamfer(BEVEL_F, None, s.faces().sort_by(bd.Axis.Z)[-1].outer_wire().edges())
    env = s
    # yüzer panel yuvası ve panel rafı
    s -= _slab_d(_rrf(PANEL_W + 2 * GAP, PANEL_H + 2 * GAP, PANEL_R + GAP, VIEW_DX), -0.1, D_PANEL)
    s -= _slab_d(_rrf(PANEL_W - 2 * LEDGE, PANEL_H - 2 * LEDGE, PANEL_R - LEDGE, VIEW_DX), D_PANEL - 0.1, D_LEDGE + 0.01)
    # LCD cebi (FPC payıyla), kart ön boşluğu, iç boşluk
    s -= _bd(-36.0, 36.0, -LCD_Y / 2 - CLR, LCD_Y / 2 + CLR, D_LEDGE, D_PCB + 0.01)
    s -= _bd(-PCB_X / 2 - CLR, PCB_X / 2 + CLR, -PCB_Y / 2 - CLR, PCB_Y / 2 + CLR, D_PCB - 0.8, D_PCB + 0.01)
    s -= _slab_d(_inset(WALL), D_PCB, D_SPLIT + 0.1)
    adds = [_cd(2.75, D_PCB - 0.9, D_PCB, x, y) for x, y in HOLES]
    adds += [_cd(1.35, D_PCB - 0.1, D_PCB + 1.3, x, y) for x, y in PRESSERS]          # konum pimleri
    adds += [_cd(3.2, D_PCB - 1.0, D_SPLIT, x, y) for x, y in MARGIN]
    adds.append(_cd(5.0, 0, D_SPLIT, *KEY) & env)
    tube = _xcyl(4.0, TUBE_X0 - 1.5, CROWN_X + 1.0, TUBE_Y, T - TUBE_D)
    tube += _bd(TUBE_X0 - 1.5, CROWN_X + 1.0, -H / 2 - 1, TUBE_Y, TUBE_D - 4.0, TUBE_D + 4.8)   # duvara ağ
    tube += _bd(TUBE_X0 - 1.5, CROWN_X + 1.0, TUBE_Y - 2.6, TUBE_Y + 2.6, TUBE_D, TUBE_D + 4.8)   # damla ucu üstü
    adds.append(tube & env)    # kalem tüneli gövdesi
    for a in adds:
        s += a
    cuts = [_cd(1.25, 2.6, D_PCB + 0.1, *HIDDEN)]
    cuts += [_cd(1.25, 3.0, D_SPLIT + 0.1, x, y) for x, y in MARGIN]
    cuts.append(_cd(KEY_R, -0.1, D_SPLIT + 0.1, *KEY))
    cuts.append(_teardrop_x(STYLUS_D / 2 + 0.3, TUBE_X0, CROWN_X + 0.1, TUBE_Y, T - TUBE_D))
    cuts.append(_teardrop_x(5.3, CROWN_X, CROWN_X + 14, TUBE_Y, T - TUBE_D))           # kurma kolu yuvası
    cuts.append(_xcyl(3.5, CROWN_X - 1.6, CROWN_X + 0.1, TUBE_Y, T - TUBE_D))          # boyun yuvası
    cuts.append(_bd(W / 2 - WALL - 0.6, W / 2 + 1, USB_Y - 6.0, USB_Y + 6.0, D_PCB - 0.6, D_SPLIT + 0.1))
    cuts.append(_bd(-W / 2 - 1, -W / 2 + WALL + 0.6, SD_Y - 7.5, SD_Y + 7.5, D_PCB_B - 0.4, D_SPLIT + 0.1))
    cuts.append(_usbc_overmold())
    cuts += [_cd(0.7, D_PANEL - 0.1, D_LEDGE + 0.1, VIEW_DX + sx * 34.0, sy * 12.0) for sx in (-1, 1) for sy in (-1, 1)]
    cuts.append(_xcyl(2.2, W / 2 - WALL - 1, W / 2 + 1, SW_Y, T - SW_D))                 # itici yarım deliği
    for c in cuts:
        s -= c
    shell = _lab(s, "on_kasa")
    return shell


# ============================================================== arka kapak
def _tail_pocket(theta, tol=8.0):
    """Halka kuyruğunun döndüğü sığ cep; ±tol derece hizasızlığa izin verir (açıkken çark ±tol oynar)."""
    seg = bd.Circle(R_RING_O + 0.3) & (bd.Pos(0, HINGE_R - 1.1 + 10) * bd.Rectangle(60, 20))
    wide = reduce(lambda u, v: u + v, [bd.Rot(0, 0, a) * seg for a in (-tol, -tol / 2, 0.0, tol / 2, tol)])
    wide = bd.Pos(C[0], C[1]) * (bd.Rot(0, 0, theta) * wide)
    return bd.Pos(0, 0, -0.01) * bd.extrude(wide, amount=TAIL_DEPTH + 0.01)


def _rot2(x, y, theta):
    a = math.radians(theta)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _icon(w, h, x, y):
    return _rrf(w, h, 0.6, x, y) - _rrf(w - 1.4, h - 1.4, 0.2, x, y)


def _pointer(theta):
    tri = bd.Polygon((-1.3, 26.4), (0.0, 24.6), (1.3, 26.4), align=None)
    return bd.Pos(*C) * (bd.Rot(0, 0, theta) * tri)


def _back_decor():
    """Sırt yüzü (z=0) gravürleri: Cenevre dalgaları, çark halkası, yön simgeleri, yazı, havalandırma."""
    region = _inset(BEVEL_B + 1.6)
    lx, ly = C[0], C[1] + 30.8
    px, py = C[0] + 30.8, C[1]
    pts = [_rot2(0.0, 25.5, th) for th in (0.0, -90.0)]
    masks = [bd.Pos(*C) * bd.Circle(23.75), bd.Pos(*KEY) * bd.Circle(5.4),
             *[bd.Pos(C[0] + qx, C[1] + qy) * bd.Circle(2.8) for qx, qy in pts],
             _rrf(10.6, 8.0, 1.0, lx, ly), _rrf(8.0, 10.6, 1.0, px, py)]
    masks += [bd.Pos(x, y) * bd.Circle(5.0) for x, y in MARGIN]
    for m in masks:
        region = region - m
    G, step = (190.0, 230.0), 5.5
    dmin = min(math.dist(G, (sx * W / 2, sy * H / 2)) for sx in (-1, 1) for sy in (-1, 1))
    dmax = max(math.dist(G, (sx * W / 2, sy * H / 2)) for sx in (-1, 1) for sy in (-1, 1))
    stripes, vents = [], []
    r = dmin - (dmin % step)
    while r < dmax + step:
        ann = bd.Pos(*G) * (bd.Circle(r + 0.35) - bd.Circle(r - 0.35))
        piece = ann & region
        if piece.area > 0.01:
            stripes.append(piece)
        ven = (bd.Pos(*G) * (bd.Circle(r + 0.65) - bd.Circle(r - 0.65))) & _rrf(8.0, 22.0, 1.6, 38.5, 0.0)
        if ven.area > 0.01:
            vents.append(ven)
        r += step
    engr = reduce(lambda u, v: u + v, stripes)
    engr += bd.Pos(*C) * (bd.Circle(24.1) - bd.Circle(23.4))
    engr += _icon(7.6, 5.0, lx, ly) + _icon(5.0, 7.6, px, py)
    engr += _pointer(0.0) + _pointer(-90.0)
    cuts = [bd.Pos(0, 0, -0.01) * bd.extrude(engr, amount=0.46)]
    cuts.append(bd.Pos(0, 0, -0.01) * bd.extrude(reduce(lambda u, v: u + v, vents), amount=FLOOR + 0.3))
    return cuts


@memo
def back_cover():
    o = _outline()
    s = _slab_d(o, D_SPLIT, T)
    s = s.chamfer(BEVEL_B, None, s.faces().sort_by(bd.Axis.Z)[0].outer_wire().edges())
    env = s
    s -= _slab_d(_inset(WALL), D_SPLIT - 0.1, D_FLOOR)
    # hizalama dili (ön kasanın içine girer), port ve kolon bölgelerinde kesik
    tongue = _slab_d(_inset(WALL + 0.2), D_SPLIT - 1.4, D_SPLIT + 0.01) - _slab_d(_inset(WALL + 1.4), D_SPLIT - 2, D_SPLIT + 1)
    tongue += _slab_d(_inset(WALL - 0.6), D_SPLIT, D_SPLIT + 1.2) - _slab_d(_inset(WALL + 1.4), D_SPLIT - 1, D_SPLIT + 2)   # duvara bağlayan iç dudak
    for cut in (
        _bd(W / 2 - 8, W / 2 + 1, USB_Y - 6.6, USB_Y + 6.6, 0, T),
        _bd(-W / 2 - 1, -W / 2 + 8, SD_Y - 8.1, SD_Y + 8.1, 0, T),
        _bd(42.5, W / 2 + 1, SW_Y - 5.5, SW_Y + 5.5, 0, T),
        _bd(42.0, W / 2 + 1, -H / 2 - 1, -23.5, 0, T),
        _bd(USBC_X - 7.0, USBC_X + 7.0, H / 2 - 8, H / 2 + 5, 0, T),
        _cd(5.6, 0, T, *KEY),
        *[_cd(4.6, 0, T, x, y) for x, y in MARGIN],
    ):
        tongue -= cut
    adds = [tongue]
    adds += [_cd(4.2, D_SPLIT, D_FLOOR + 0.01, x, y) for x, y in MARGIN]           # duvara kaynar, havşa etrafında 1 mm et
    adds.append(_cd(3.2, D_PCB_B + 0.05, D_FLOOR + 0.01, *HIDDEN))
    adds += [_cd(2.4, D_PCB_B + 0.05, D_FLOOR + 0.01, x, y) for x, y in PRESSERS]      # kartı bastıran borular
    adds.append(_cd(5.0, D_SPLIT, T, *KEY) & env)
    adds.append(_cd(5.0, T - 6.8, D_FLOOR + 0.01, *C))                                 # çark vidası kolonu
    # pil köşe tırnakları
    bx0, bx1, by0, by1 = BAT_X0 - 0.4, BAT_X1 + 0.4, BAT_Y0 - 0.4, BAT_Y1 + 0.4
    for cx, sx in ((bx0, -1), (bx1, 1)):
        for cy, sy in ((by0, -1), (by1, 1)):
            adds.append(_bd(*sorted((cx, cx + sx * 1.2)), *sorted((cy + sy * 1.2, cy - sy * 6)), 16.0, D_FLOOR + 0.01))
            adds.append(_bd(*sorted((cx + sx * 1.2, cx - sx * 6)), *sorted((cy, cy + sy * 1.2)), 16.0, D_FLOOR + 0.01))
    # TP4056 rayları + uç dayama
    adds.append(_bd(TP_X0 - 1.4, TP_X0 - 0.2, TP_Y0, TP_Y1, 16.8, D_FLOOR + 0.01))
    adds.append(_bd(TP_X1 + 0.2, TP_X1 + 1.4, TP_Y0, TP_Y1, 16.8, D_FLOOR + 0.01))
    adds.append(_bd(TP_X0, TP_X1, TP_Y0 - 1.4, TP_Y0 - 0.2, 17.0, D_FLOOR + 0.01))
    # itici anahtar yatağı
    adds.append(_bd(44.0, W / 2 - WALL + 0.01, SW_Y - 3.5 - 1.4, SW_Y - 3.5 - 0.2, D_SPLIT + 0.2, D_FLOOR + 0.01))
    adds.append(_bd(44.0, W / 2 - WALL + 0.01, SW_Y + 3.5 + 0.2, SW_Y + 3.5 + 1.4, D_SPLIT + 0.2, D_FLOOR + 0.01))
    for a in adds:
        s += a
    cuts = []
    for x, y in MARGIN:
        cuts += [_cd(1.7, D_SPLIT - 0.1, T + 0.1, x, y), _cd(3.2, T - 3.6, T + 0.1, x, y), _cd(3.8, T - 1.0, T + 0.1, x, y)]
    cuts += [_cd(1.7, D_PCB_B, T + 0.1, *HIDDEN), _cd(3.1, T - 2.7, T + 0.1, *HIDDEN)]
    cuts += [_cd(1.6, D_PCB_B, D_FLOOR - 0.6, x, y) for x, y in PRESSERS]
    cuts.append(_cd(KEY_R, D_SPLIT - 0.1, T + 0.1, *KEY))
    cuts += [_cd(2.85, T - 1.0, T + 0.1, *C), _cd(1.25, T - 6.6, T + 0.1, *C)]           # burç yuvası + pilot
    for th in (0.0, -90.0):
        cuts.append(_tail_pocket(th))
    # USB-C (üst yüz), fiş cebi, itici deliği
    cuts.append(_ycyl(2.1, H / 2 - WALL - 1, H / 2 + 2, USBC_X - 3.1, T - USBC_D)
                + _ycyl(2.1, H / 2 - WALL - 1, H / 2 + 2, USBC_X + 3.1, T - USBC_D)
                + _box(USBC_X - 3.1, USBC_X + 3.1, H / 2 - WALL - 1, H / 2 + 2, T - USBC_D - 2.1, T - USBC_D + 2.1))
    cuts.append(_usbc_overmold())
    cuts.append(_xcyl(2.2, W / 2 - WALL - 1, W / 2 + 1, SW_Y, T - SW_D))
    cuts += _back_decor()
    for c in cuts:
        s -= c
    cover = _lab(s, "arka_kapak")
    return cover


# ============================================================== çark parçaları (yerel: z=0 sırt yüzü, +z dışarı)
def _tooth(ang):
    prof = bd.Polygon((-0.8, R_RING_O - 0.3), (0.8, R_RING_O - 0.3), (0.42, R_RING_O + 1.0), (-0.42, R_RING_O + 1.0), align=None)
    return bd.Rot(0, 0, math.degrees(ang) - 90.0) * bd.extrude(prof, amount=DIAL_T)


def gear_disc_local():
    t = DIAL_T
    d = _cyl(R_DISC, 0, t) - _cyl(R_DISC - 2.2, -1, t + 1)
    d += _cyl(5.6, 0, t)
    for k in range(5):
        d += bd.Rot(0, 0, -180.0 + k * 72.0) * _box(-1.1, 1.1, 5.0, R_DISC - 1.6, 0, t)
    d += _box(-TAB_HALF, TAB_HALF, R_DISC - 1.0, HINGE_R + 2.6, 0, t)
    d -= _cyl(2.95, -1, 1.4)
    d -= _cyl(3.7, 1.4, t + 1)
    d -= _xcyl(0.95, -TAB_HALF - 1, TAB_HALF + 1, HINGE_R, PIN_Z)
    return d


def gear_ring_local():
    t = DIAL_T
    r = _cyl(R_RING_O, 0, t) - _cyl(R_RING_I, -1, t + 1)
    r -= _box(-GAP_HALF, GAP_HALF, R_RING_I - 2, R_RING_O + 3, -1, t + 1)
    for k in range(56):
        ang = 2 * math.pi * k / 56
        if (R_RING_O + 1.0) * math.sin(ang) > HINGE_R - 1.4:
            continue
        r += _tooth(ang)
    for sx in (-1, 1):
        r -= _box(*sorted((sx * 10.0, sx * 13.0)), HINGE_R - 2.2, HINGE_R + 3.5, -1, t + 1)   # pim çıkışında düz yüz
    r -= _xcyl(0.95, -R_RING_O - 1.5, R_RING_O + 1.5, HINGE_R, PIN_Z)
    return r


def ruby_local(radius, skirt, dome):
    """Yakut kapak: etek z<0 (deliğe girer), kubbe z>0 (dışarı)."""
    rs = (radius ** 2 + dome ** 2) / (2 * dome)
    cap = (bd.Pos(0, 0, dome - rs) * bd.Sphere(rs)) & _box(-radius - 1, radius + 1, -radius - 1, radius + 1, 0, dome + 1)
    return cap + _cyl(radius, -skirt, 0.01)


def bushing_local():
    """Üstü göbeğin basamağıyla aynı hizada: pul göbeği hafifçe sıkar, çark sürtünmeyle döner."""
    return _cyl(2.8, -1.0, 1.4) - _cyl(1.65, -2, 3)


def dial_parts(theta=0.0, alpha=0.0):
    ring = gear_ring_local()
    if alpha:
        ring = bd.Pos(0, HINGE_R, PIN_Z) * (bd.Rot(-alpha, 0, 0) * (bd.Pos(0, -HINGE_R, -PIN_Z) * ring))
    pin = _xcyl(0.85, -10.0, 10.0, HINGE_R, PIN_Z)
    local = [
        (gear_disc_local(), "cark_gobek"),
        (ring, "cark_halka"),
        (bushing_local(), "burc"),
        (bd.Pos(0, 0, DIAL_T) * ruby_local(3.68, 0.7, 0.9), "yakut_merkez"),
        (pin, "pim"),
    ]
    out = []
    for shape, lab in local:
        placed = bd.Pos(C[0], C[1], 0) * (bd.Rot(0, 0, theta) * (bd.Rot(0, 180, 0) * shape))
        out.append(_lab(placed, lab, COL["yakut"] if lab.startswith("yakut") else (COL["burc"] if lab == "pim" else None)))
    return out


# ============================================================== küçük parçalar (yerinde)
def crown_local():
    """X boyunca: boyun x∈[-1.6,0], tırtıllı gövde x∈[0,6.5]; kalem yuvası boyundan 6 mm."""
    body = _xcyl(5.0, 0, 6.5, 0, 0)
    body = body.chamfer(0.6, None, body.edges().group_by(bd.Axis.X)[-1])
    for k in range(16):
        body -= bd.Rot(k * 22.5, 0, 0) * _box(0.8, 7.0, 4.6, 5.4, -0.35, 0.35)
    body += _xcyl(3.4, -1.6, 0.01, 0, 0)
    body -= _xcyl(STYLUS_D / 2 + 0.075, -1.7, 4.4, 0, 0)
    return body


def pusher_local():
    """İtici başlığı: duvarın 0.2 mm dışında durur; anahtarın milini yuvasına alır."""
    p = _xcyl(3.2, 0.0, 3.0, 0, 0)
    p = p.fillet(0.8, p.edges().group_by(bd.Axis.X)[-1])
    return p - _xcyl(1.7, -0.1, 1.8, 0, 0)


def small_parts():
    crown = bd.Pos(CROWN_X, TUBE_Y, T - TUBE_D) * crown_local()
    pusher = bd.Pos(W / 2 + 0.2, SW_Y, T - SW_D) * pusher_local()
    rubies = [bd.Pos(x, y, 0) * (bd.Rot(180, 0, 0) * ruby_local(3.75, 1.0, 0.8)) for x, y in MARGIN]
    out = [_lab(crown, "kurma_kolu"), _lab(pusher, "itici")]
    out += [_lab(r, f"yakut_{i}", COL["yakut"]) for i, r in enumerate(rubies)]
    return out


def internals():
    pcb = _bd(-PCB_X / 2, PCB_X / 2, -PCB_Y / 2, PCB_Y / 2, D_PCB, D_PCB_B)
    for x, y in HOLES:
        pcb -= _cd(1.6, D_PCB - 0.1, D_PCB_B + 0.1, x, y)
    lcd = _bd(-LCD_X / 2, LCD_X / 2, -LCD_Y / 2, LCD_Y / 2, D_LEDGE + 0.02, D_PCB)
    glass = _bd(VIEW_DX - VIEW_X / 2, VIEW_DX + VIEW_X / 2, -VIEW_Y / 2, VIEW_Y / 2, D_LEDGE, D_LEDGE + 0.02)
    bat = _bd(BAT_X0, BAT_X1, BAT_Y0, BAT_Y1, D_BAT0, D_BAT1)
    tp = _bd(TP_X0, TP_X1, TP_Y0, TP_Y1, D_FLOOR - 1.6, D_FLOOR - 0.02)
    tp += _bd(USBC_X - 4.5, USBC_X + 4.5, TP_Y1 - 7.4, TP_Y1 + 0.1, USBC_D - 1.6, USBC_D + 1.6)
    sw = _bd(44.0, 50.8, SW_Y - 3.5, SW_Y + 3.5, SW_D - 3.5, SW_D + 3.5)
    stylus = _xcyl(STYLUS_D / 2, CROWN_X + 4.4 - STYLUS_L + 3.0, CROWN_X + 4.4, TUBE_Y, T - TUBE_D)
    stylus += bd.Pos(CROWN_X + 4.4 - STYLUS_L + 3.0, TUBE_Y, T - TUBE_D) * (bd.Rot(0, -90, 0) * bd.Cone(
        STYLUS_D / 2, 0.6, 3.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
    return [_lab(pcb, "ic_kart", "#d9b81c"), _lab(lcd, "ic_lcd", "#151515"), _lab(glass, "ekran"),
            _lab(bat, "ic_pil", "#b9c3cf"), _lab(tp, "ic_tp4056", "#1f6fd1"), _lab(sw, "ic_anahtar", "#202020"),
            _lab(stylus, "kalem")]


def device(theta=0.0, alpha=0.0, inside=True, pen_out=0.0):
    parts = [front_shell(), _lab(panel_body(), "panel"), pip_body(), back_cover(), *small_parts(), *dial_parts(theta, alpha)]
    if inside:
        parts += internals()
    if pen_out:
        parts = [_lab(bd.Pos(pen_out, 0, 0) * p, p.label, p.color) if p.label in ("kalem", "kurma_kolu") else p for p in parts]
    return parts


# ============================================================== duruş (ayakta)
def _stand_xf(shape, tilt, portrait):
    s = bd.Rot(0, 0, 90) * shape if portrait else shape
    return bd.Rot(90 - tilt, 0, 0) * s


def stance(portrait):
    """Halka durdurakta açıkken, gövde kenarı ve halka ayağı aynı zemine değecek eğimi çözer."""
    theta = -90.0 if portrait else 0.0
    ring = dial_parts(theta, STAND)[1]
    prox = _outer_proxy()

    def gap(t):
        return _stand_xf(ring, t, portrait).bounding_box().min.Z - _stand_xf(prox, t, portrait).bounding_box().min.Z

    lo, hi = 1.0, 75.0
    glo = gap(lo)
    for _ in range(30):
        mid = (lo + hi) / 2
        gm = gap(mid)
        if (gm > 0) == (glo > 0):
            lo, glo = mid, gm
        else:
            hi = mid
    return (lo + hi) / 2


def standing(portrait, pen_out=0.0):
    t = stance(portrait)
    parts = device(-90.0 if portrait else 0.0, STAND, pen_out=pen_out)
    placed = [_stand_xf(p, t, portrait) for p in parts]
    z0 = _stand_xf(_outer_proxy(), t, portrait).bounding_box().min.Z
    out = []
    for src, p in zip(parts, placed):
        q = bd.Pos(0, 0, -z0) * p
        out.append(_lab(q, src.label, src.color))
    return out, t


# ============================================================== modeller
@model
def kadran():
    return bd.Compound(children=device(), label="kadran")


@model
def kadran_yatay():
    parts, t = standing(False)
    return bd.Compound(children=parts, label=f"kadran_yatay_{round(t)}deg")


@model
def kadran_dikey():
    parts, t = standing(True)
    return bd.Compound(children=parts, label=f"kadran_dikey_{round(t)}deg")


@model
def kadran_kalem():
    """Kurma kolu çekilmiş: kalem tünelden yarı yarıya çıkmış (sunum)."""
    parts, _ = standing(False, pen_out=46.0)
    return bd.Compound(children=parts, label="kadran_kalem")


@model
def kadran_patlatma():
    off = {"panel": 26, "pip": 30, "on_kasa": 14, "ekran": 7, "ic_lcd": 7, "ic_kart": 2, "kalem": 14,
           "kurma_kolu": 14, "ic_pil": -6, "ic_tp4056": -6, "ic_anahtar": -6, "itici": -6, "arka_kapak": -18,
           "burc": -28, "cark_gobek": -34, "pim": -40, "cark_halka": -40, "yakut_merkez": -48}
    xoff = {"kurma_kolu": 16, "kalem": 34, "itici": 10}
    parts = []
    for p in device():
        dz = off.get(p.label, -26 if p.label.startswith("yakut") else 0)
        q = bd.Pos(xoff.get(p.label, 0), 0, dz) * p
        parts.append(_lab(q, p.label, p.color))
    z0 = min(q.bounding_box().min.Z for q in parts)
    parts = [_lab(bd.Pos(0, 0, -z0) * q, q.label, q.color) for q in parts]
    return bd.Compound(children=parts, label="kadran_patlatma")


# ---- baskı yönünde tek parçalar (DFM ve dışa aktarım için)
def _flip_z(shape, top):
    return bd.Pos(0, 0, top) * (bd.Rot(180, 0, 0) * shape)


@model
def p_on_kasa():
    return _lab(_flip_z(front_shell(), T), "on_kasa")


@model
def p_panel():
    return _lab(_flip_z(panel_body(), T), "panel")


@model
def p_arka_kapak():
    return back_cover()


@model
def p_cark_gobek():
    return _lab(_flip_z(gear_disc_local(), DIAL_T), "cark_gobek")


@model
def p_cark_halka():
    return _lab(gear_ring_local(), "cark_halka")


@model
def p_kurma_kolu():
    return _lab(bd.Pos(0, 0, 6.5) * (bd.Rot(0, 90, 0) * crown_local()), "kurma_kolu")


@model
def p_yakut():
    return _lab(bd.Pos(0, 0, 1.0) * ruby_local(3.75, 1.0, 0.8), "yakut", COL["yakut"])


@model
def p_yakut_merkez():
    return _lab(bd.Pos(0, 0, 0.7) * ruby_local(3.68, 0.7, 0.9), "yakut", COL["yakut"])


@model
def p_pip():
    return _lab(bd.Pos(0, 0, -(T - D_PANEL)) * pip_body(), "pip")


@model
def p_itici():
    return _lab(bd.Pos(0, 0, 3.0) * (bd.Rot(0, 90, 0) * pusher_local()), "itici")


@model
def p_burc():
    return _lab(bd.Pos(0, 0, 1.0) * bushing_local(), "burc")


if __name__ == "__main__":
    for m in (kadran, kadran_yatay, kadran_dikey, kadran_kalem, kadran_patlatma, p_on_kasa, p_panel, p_arka_kapak,
              p_cark_gobek, p_cark_halka, p_kurma_kolu, p_yakut, p_yakut_merkez, p_pip, p_itici, p_burc):
        m()
