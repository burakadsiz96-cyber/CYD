"""VADE MECUM — CYD 2.8" (ESP32-2432S028R) için deri ciltli cep el kitabı kasası.

"Vade mecum" (Lat. "yanımda gel"): hekimlerin cepte taşıdığı başvuru kitabı. Cihaz, dik duran bir kitap:
  * Ön kapak (A): ekran, varak çerçeveli bir levha gibi kapakta; üstte yaldız başlık plakası,
    altta Asklepios asalı arma, ön kenar köşelerinde pirinç köşelikler.
  * Sayfa bloğu (C): krem; baş, kuyruk ve ön kenarda sayfa çizgileri. Ön kenardaki bazı "sayfa
    aralıkları" havalandırma yarığıdır. Portlar başta (USB, USB-C, anahtar), microSD kuyrukta.
  * Sırt (D): yuvarlak, kabartma bantlı; içinde kalem tüneli. Tepedeki kapitalbant = kalem başlığı.
  * Kırmızı kurdele ayraç: anahtarlık.
  * Arka kapak (B): çapraz şövale ayağı (fotoğraf çerçevesi gibi) kitabı dik ve yan durdurur.

Kitap koordinatları (dikey kullanım): X sırttan ön kenara, Y kuyruktan başa, Z arka kapaktan ön kapağa.
Ekran z=T'de +z'ye bakar. Birim mm. Baskı: FDM PETG/PLA, 0.4 nozul, destek yok.
Ölç ve düzelt: delik aralığı, ekran kayması, usb_x, sd_x, kalem çapı/boyu.

Check: cad model dfm "$ID" --process printing --technology fdm --material petg
"""

import math
from functools import lru_cache, reduce

import build123d as bd
from cad import model
from cad.build123d import memo

ENGRAVE = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"   # gravür levhası harfi

# ============================================================== CYD kartı (dikey: uzun kenar Y boyunca)
PCB_W, PCB_H, PCB_T = 50.0, 86.0, 1.6
LCD_W, LCD_H, LCD_T = 50.0, 70.0, 4.0
VIEW_W, VIEW_H = 43.2, 57.6
BACK_PARTS = 4.8
CLR = 0.3
HOLE_X = model.param("delik_araligi_kisa", 42.0, min=36, max=46, unit="mm")
HOLE_Y = model.param("delik_araligi_uzun", 78.0, min=70, max=82, unit="mm")
VIEW_DY = model.param("ekran_kaydirma", 0.0, min=-5, max=5, unit="mm")     # LCD'nin uzun eksende kayması
USB_X = model.param("usb_x", 30.0, min=22, max=34, unit="mm")              # baş kenarda kartın USB'si
SD_X = model.param("sd_x", 35.0, min=22, max=50, unit="mm")               # kuyrukta microSD
STYLUS_D = model.param("kalem_cap", 5.0, min=3.5, max=5.6, unit="mm")
STYLUS_L = model.param("kalem_boy", 87.0, min=60, max=98, unit="mm")
STRUT_STOP = model.param("ayak_acisi", 40.0, min=30, max=50, unit="deg")

# ============================================================== kitap
W, H, T = 66.0, 104.0, 21.8
SP = 8.5                                   # sırt genişliği
A_T, B_T, SQ = 2.8, 3.0, 2.0               # ön/arka kapak kalınlığı, kapak payı
ZC0, ZC1 = B_T, T - A_T                    # sayfa bloğu z: 3.0 .. 19.0
CX0, CX1, CY0, CY1 = SP, W - SQ, SQ, H - SQ
XB = CX0 + 1.6 + CLR + PCB_W / 2           # kart merkezi
YB = (CY0 + CY1) / 2
KX0, KX1 = CX0 + 1.6, XB + PCB_W / 2 + CLR # boşluk
KY0, KY1 = YB - PCB_H / 2 - CLR, YB + PCB_H / 2 + CLR
Z_PCB1 = ZC1 - LCD_T                       # kart ön yüzü 15.0
Z_PCB0 = Z_PCB1 - PCB_T                    # 13.4
WX, WY = XB, YB + VIEW_DY                  # ekran penceresi merkezi
WIN_W, WIN_H = VIEW_W + 0.8, VIEW_H + 0.8

BOARD_HOLES = [(XB + sx * HOLE_X / 2, YB + sy * HOLE_Y / 2) for sx in (-1, 1) for sy in (-1, 1)]
B_SCREWS = [(12.5, CY0 + 3.35), (12.5, CY1 - 3.35), (61.0, CY1 - 3.35)]   # havşa başlı M3x10, köşeliklerin altında
B_PIN = (58.0, CY0 + 3.35)
A_PINS = [(22.0, CY1 - 2.6), (48.0, CY1 - 2.6), (22.0, CY0 + 2.6), (48.0, CY0 + 2.6)]
D_PINS = [30.0, 52.0, 74.0]

# baş kenar portları
SW_X, USBC_X, RIB_X = 20.0, 45.6, 57.5
USBC_Z = B_T + 1.6 + 1.65                  # TP4056 arka kapağa yatık: USB-C ekseni
# iç düzen (dış görünüm sabit): pil kuyrukta enine, MT3608 ortada enine, TP4056 başta
BAT_T = 5.0                                # 503450 LiPo kalınlığı
BAT = (KX0 + 0.3, KX0 + 50.3, KY0 + 0.3, KY0 + 34.3)   # 503450 (x0, x1, y0, y1): 50 mm enine, kuyruk ve yan duvarlara yaslanır
BOOST_L, BOOST_W, BOOST_H = 36.0, 17.0, 7.0  # MT3608 yükseltici (trimpot ve alttaki pim uçları dahil yükseklik)
BOOST_REC = 1.5                            # arka kapağın iç yüzünde MT3608 yuvası (dış yüz değişmez)
BOOST = (KX1 - 0.2 - BOOST_L, KX1 - 0.2, 56.4, 56.4 + BOOST_W)       # menteşe bloğunun hemen üstü
TP_L, TP_OVER = 26.0, 0.6                  # TP4056 (HW-373) kart boyu, USB-C soketin kart kenarından taşması
TP_FRONT = CY1 - 1.2 - 0.5                 # soket ön yüzü: kablonun fişi dıştaki cepten sokete tam girer
TP = (37.0, 54.2, TP_FRONT - TP_OVER - TP_L, TP_FRONT - TP_OVER)   # TP4056 (USB-C başa bakar)

# sırt ve kalem
R_SP = ((T / 2) ** 2 + SP ** 2) / (2 * SP)
PEN_X, PEN_Z = 4.25, T / 2
BANDS = [22.0, 41.0, 60.0, 79.0]

# şövale ayağı
HINGE = (18.6, 52.0)
U = (math.sqrt(0.5), math.sqrt(0.5))       # menteşe ekseni (sırt düzleminde)
V = (math.sqrt(0.5), -math.sqrt(0.5))      # ayak yönü (ön kenar-kuyruk köşesine)
STRUT_L, TAIL = 62.0, 2.5
BARREL_R, BARREL_L = 1.8, 9.0
_b = math.radians(STRUT_STOP)
TAIL_G = TAIL * math.sin(_b) + BARREL_R * math.cos(_b) - BARREL_R
assert math.degrees(math.atan2(TAIL, BARREL_R)) > STRUT_STOP + 8

COL = {"on_kapak": "#4a2c1d", "arka_kapak": "#4a2c1d", "sirt": "#4a2c1d", "ayak": "#4a2c1d",
       "sayfa": "#efe8d8", "baslik": "#f5c518", "arma": "#f5c518", "kose": "#f5c518",
       "kurdele": "#c8202a", "kapitalbant": "#c8202a", "ekran": "#0b0d12", "kalem": "#f2f2ee", "pim": "#c9ccd2"}


# ============================================================== yardımcılar
def _box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _cyl(r, z0, z1, x=0.0, y=0.0):
    return bd.Pos(x, y, z0) * bd.Cylinder(r, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _ycyl(r, y0, y1, x, z):
    return bd.Pos(x, y0, z) * (bd.Rot(-90, 0, 0) * bd.Cylinder(r, y1 - y0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))


def _xcyl(r, x0, x1, y, z):
    return bd.Pos(x0, y, z) * (bd.Rot(0, 90, 0) * bd.Cylinder(r, x1 - x0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))


def _rrf(w, h, r, x=0.0, y=0.0):
    return bd.Pos(x, y) * bd.RectangleRounded(w, h, r)


def _slab(face, z0, z1):
    return bd.Pos(0, 0, z0) * bd.extrude(face, amount=z1 - z0)


def _lab(shape, label, color=None):
    shape.label = label
    shape.color = color or COL.get(label.rstrip("0123456789_"), "#888888")
    return shape


def _union(shapes):
    return reduce(lambda a, b: a + b, shapes)


def _tri(cx, cy, sx, sy, leg):
    """Köşe üçgeni: dik açı (cx,cy)'de, kollar sx,sy yönünde; her zaman saat yönü tersine (+z yüzlü)."""
    pts = [(cx, cy), (cx + sx * leg, cy), (cx, cy + sy * leg)]
    area = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1])
    if area < 0:
        pts = [pts[0], pts[2], pts[1]]
    return bd.Polygon(*pts, align=None)


def _frame_line(w, h, r, x, y, width=0.5):
    return _rrf(w + width, h + width, r + width / 2, x, y) - _rrf(w - width, h - width, max(r - width / 2, 0.1), x, y)


# ============================================================== ön kapak (A)
TITLE_Y, CART_Y = 92.0, 12.6


def _title_plate_outline():
    return _rrf(42.0, 8.4, 1.4, WX, TITLE_Y)


def _cartouche_outline(grow=0.0):
    return bd.Pos(WX, CART_Y) * bd.Ellipse(10.0 + grow, 5.9 + grow)


FRONT_CORNERS = [(W, 0.0, -1, 1), (W, H, -1, -1)]
BACK_CORNERS = [(SP, 0.0, 1, 1), (SP, H, 1, -1), (W, H, -1, -1)]


@memo
def front_cover():
    a = _slab(_rrf(W - SP, H, 1.2, (SP + W) / 2, H / 2), ZC1, T)
    a = a.fillet(0.6, a.faces().sort_by(bd.Axis.Z)[-1].outer_wire().edges())
    win = bd.Pos(WX, WY, T + 0.01) * (bd.Rot(180, 0, 0) * bd.extrude(_rrf(WIN_W + 2.0, WIN_H + 2.0, 2.0), amount=1.0, taper=45))
    win += _slab(_rrf(WIN_W, WIN_H, 1.0, WX, WY), ZC1 - 0.1, T + 0.1)
    engr = _frame_line(WIN_W + 5.2, WIN_H + 5.2, 2.5, WX, WY)                       # varak çerçeve
    engr += _frame_line(W - SP - 8.0, H - 8.0, 1.6, (SP + W) / 2, H / 2)             # kenar süsü
    recess = _title_plate_outline() + _cartouche_outline(0.2)
    recess = bd.offset(recess, 0.2)
    for cx, cy, sx, sy in FRONT_CORNERS:
        recess += _tri(cx, cy, sx, sy, 11.2)
    cuts = [win, _slab(engr, T - 0.35, T + 0.1), _slab(recess, T - 0.6, T + 0.1)]
    adds = [_cyl(2.75, Z_PCB1, ZC1 + 0.01, x, y) for x, y in BOARD_HOLES]           # kart ayakları
    adds += [_cyl(1.1, ZC1 - 1.8, ZC1 + 0.01, x, y) for x, y in A_PINS]            # sayfa bloğu pimleri
    for s in adds:
        a += s
    cuts += [_cyl(1.25, Z_PCB1 - 0.1, ZC1 + 1.6, x, y) for x, y in BOARD_HOLES]
    for c in cuts:
        a -= c
    cover = _lab(a, "on_kapak")
    return cover


# ============================================================== sayfa bloğu (C)
@memo
def page_block():
    c = _box(CX0, CX1, CY0, CY1, ZC0, ZC1)
    c = c.fillet(1.2, c.edges().filter_by(bd.Axis.Z).filter_by_position(bd.Axis.X, CX1 - 0.1, CX1 + 0.1))
    c -= _box(KX0, KX1, KY0, KY1, ZC0 - 1, ZC1 + 1)
    # sayfa çizgileri (ön kenar, baş, kuyruk)
    lines = []
    z = ZC0 + 0.6
    k = 0
    vents = []
    while z < ZC1 - 0.8:
        lines += [_box(CX1 - 0.35, CX1 + 1, CY0 - 1, CY1 + 1, z, z + 0.4),
                  _box(CX0 - 1, CX1 + 1, CY1 - 0.35, CY1 + 1, z, z + 0.4),
                  _box(CX0 - 1, CX1 + 1, CY0 - 1, CY0 + 0.35, z, z + 0.4)]
        if k in (8, 11, 14):                                                        # havalandırma "sayfa aralıkları"
            vents.append(_box(KX1 - 0.5, CX1 + 1, 30.0, 76.0, z, z + 1.2))
        z += 0.8
        k += 1
    cuts = [_union(lines), *vents]
    # baş: anahtar cebi + kol yarığı, kartın USB'si, USB-C, kurdele yuvası
    cuts.append(_box(SW_X - 4.6, SW_X + 4.6, KY1 - 0.2, CY1 - 2.7, ZC0 + 1.0, ZC0 + 8.0))
    cuts.append(_box(SW_X - 2.6, SW_X + 2.6, CY1 - 2.9, CY1 + 1, ZC0 + 3.4, ZC0 + 5.6))
    cuts.append(_box(USB_X - 6.0, USB_X + 6.0, KY1 - 0.5, CY1 + 1, Z_PCB0 - 5.4, Z_PCB0 + 2.6))
    usbc = _box(USBC_X - 3.1, USBC_X + 3.1, KY1 - 0.5, CY1 + 1, USBC_Z - 2.1, USBC_Z + 2.1)
    usbc += _ycyl(2.1, KY1 - 0.5, CY1 + 1, USBC_X - 3.1, USBC_Z) + _ycyl(2.1, KY1 - 0.5, CY1 + 1, USBC_X + 3.1, USBC_Z)
    cuts.append(usbc)
    tx0, tx1, ty0, ty1 = TP
    cuts.append(_box(tx0 - 0.3, tx1 + 0.3, KY1 - 0.5, ty1 + 0.3, ZC0 - 0.1, B_T + 1.6 + 0.2))   # TP4056 kart ucu yarığı (içte)
    cuts.append(_box(USBC_X - 6.4, USBC_X + 6.4, CY1 - 1.2, CY1 + 1, ZC0 - 0.6, ZC0 + 0.6 + 8 * 0.8 + 0.4))
    cuts.append(_box(RIB_X - 3.2, RIB_X + 3.2, KY1 - 0.5, CY1 + 1, 11.2, 13.0))
    cuts.append(_box(RIB_X - 5.2, RIB_X + 5.2, KY1 - 0.5, KY1 + 2.4, 10.7, 13.5))
    # kuyruk: microSD
    cuts.append(_box(SD_X - 7.5, SD_X + 7.5, CY0 - 1, KY0 + 0.5, Z_PCB0 - 4.4, Z_PCB0 + 1.2))
    # vida pilotları (arka kapak), pim delikleri (ön kapak, arka kapak, sırt)
    cuts += [_cyl(1.25, ZC0 - 0.1, ZC0 + 7.5, x, y) for x, y in B_SCREWS]
    cuts += [_cyl(1.2, ZC1 - 2.0, ZC1 + 0.1, x, y) for x, y in A_PINS]
    cuts.append(_cyl(1.2, ZC0 - 0.1, ZC0 + 2.0, *B_PIN))
    cuts += [_xcyl(1.2, CX0 - 0.1, KX0 + 0.2, y, PEN_Z) for y in D_PINS]
    for cut in cuts:
        c -= cut
    block = _lab(c, "sayfa")
    return block


# ============================================================== sırt (D)
def _spine_profile(grow=0.0):
    """Sırt kesiti (u=x, v=z): yay (SP,0)-(0,T/2)-(SP,T); grow>0 kabartma bant için dışa büyütür."""
    circ = bd.Pos(R_SP, T / 2) * bd.Circle(R_SP + grow)
    return circ & (bd.Pos((SP - 5.0) / 2, T / 2) * bd.Rectangle(SP + 5.0, T + 6))


def _spine_extrude(face, y0, y1):
    return bd.Pos(0, y0, 0) * bd.extrude(bd.Plane.XZ * face, amount=-(y1 - y0))


@memo
def spine():
    d = _spine_extrude(_spine_profile(), 0.0, H)
    d = d & _box(-1, SP, -1, H + 1, 0, T)
    for yb in BANDS:
        band = _spine_extrude(_spine_profile(0.9) - _spine_profile(-0.01), yb - 1.3, yb + 1.3) & _box(-2, SP, -1, H + 1, 0.4, T - 0.4)
        try:
            band = band.chamfer(0.8, None, band.edges().filter_by(bd.GeomType.CIRCLE).filter_by_position(bd.Axis.X, -1.5, 0.5))
        except Exception:
            pass
        d += band
    d -= _ycyl(STYLUS_D / 2 + 0.3, 8.0, H + 1, PEN_X, PEN_Z)                      # kalem tüneli
    d -= _ycyl(3.45, H - 2.0, H + 1, PEN_X, PEN_Z)                                   # kapitalbant yuvası (et 0.8)
    for y in D_PINS:
        d += _xcyl(1.05, SP - 0.01, SP + 1.4, y, PEN_Z)
    s = _lab(d, "sirt")
    return s


# ============================================================== arka kapak (B) ve şövale ayağı
def _strut_plane(open_angle=0.0):
    """Ayağın yerel çerçevesi: X menteşe ekseni, -Y ayak yönü, +Z dışarı (dünyada -z)."""
    ex = bd.Vector(-U[0], -U[1], 0)
    ez = bd.Vector(0, 0, -1)
    return bd.Plane(origin=(HINGE[0], HINGE[1], 0.0), x_dir=ex, z_dir=ez)


def strut_local():
    """Yerel: menteşe ekseni X boyunca (y=0, z=-BARREL_R); plaka -Y yönünde, dış yüz z=0."""
    w0, w1 = BARREL_L, 7.0
    plate = bd.extrude(bd.Polygon((-w0 / 2, 0), (-w1 / 2, -STRUT_L), (w1 / 2, -STRUT_L), (w0 / 2, 0), align=None), amount=-1.8)
    plate = plate.fillet(3.0, plate.edges().filter_by(bd.Axis.Z).group_by(bd.Axis.Y)[0])
    barrel = bd.Pos(-BARREL_L / 2, 0, -BARREL_R) * (bd.Rot(0, 90, 0) * bd.Cylinder(
        BARREL_R, BARREL_L, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
    tail = _box(-BARREL_L / 2, BARREL_L / 2, 0.0, TAIL, -2 * BARREL_R, 0.0)
    s = plate + barrel + tail
    s -= _xcyl(0.95, -BARREL_L, BARREL_L, 0.0, -BARREL_R)
    # süs: kenara paralel ince çizgi (dış yüz)
    groove = bd.Polygon((-w0 / 2 + 1.4, -3), (-w1 / 2 + 1.4, -STRUT_L + 4), (w1 / 2 - 1.4, -STRUT_L + 4), (w0 / 2 - 1.4, -3), align=None)
    groove = groove - bd.offset(groove, -0.5)
    s -= bd.Pos(0, 0, -0.3) * bd.extrude(groove, amount=0.4)
    return s


def strut(open_angle=0.0):
    s = strut_local()
    if open_angle:
        s = bd.Pos(0, 0, -BARREL_R) * (bd.Rot(-open_angle, 0, 0) * (bd.Pos(0, 0, BARREL_R) * s))
    return _lab(bd.Location(_strut_plane()) * s, "ayak")


def _strut_region_local(pad=0.5):
    w0, w1 = BARREL_L + 2 * pad, 7.0 + 2 * pad
    return bd.Polygon((-w0 / 2, 0), (-w1 / 2, -STRUT_L - pad), (w1 / 2, -STRUT_L - pad), (w0 / 2, 0), align=None)


@memo
def back_cover():
    loc = bd.Location(_strut_plane())
    b = _slab(_rrf(W - SP, H, 1.2, (SP + W) / 2, H / 2), 0.0, B_T)
    b = b.fillet(0.6, b.faces().sort_by(bd.Axis.Z)[0].outer_wire().edges())
    # menteşe bloğu (iç yüzde, sayfa bloğunun boşluğuna girer)
    block = loc * _box(-BARREL_L / 2 - 2.6, BARREL_L / 2 + 2.6, -3.2, TAIL + 2.0, -(2 * BARREL_R + TAIL_G + 1.4), -B_T + 0.01)
    b += block
    # pil ve TP4056 tırnakları
    x0, x1, y0, y1 = BAT                                                       # pil: kuyruk ve yan duvarlar + baş tarafta iki tırnak
    b += _box(x0 + 1.0, x0 + 9.0, y1 + 0.3, y1 + 1.5, B_T - 0.01, B_T + 2.6)
    b += _box(x1 - 9.0, x1 - 1.0, y1 + 0.3, y1 + 1.5, B_T - 0.01, B_T + 2.6)
    tx0, tx1, ty0, ty1 = TP                                                    # TP4056 rayları; içe itilince MT3608'e dayanır
    b += _box(tx0 - 1.4, tx0 - 0.2, ty0, KY1 - 0.2, B_T - 0.01, B_T + 2.4)
    b += _box(tx1 + 0.2, tx1 + 1.4, ty0, KY1 - 0.2, B_T - 0.01, B_T + 2.4)
    b += _cyl(1.1, B_T - 0.01, B_T + 1.8, *B_PIN)
    # ayak cebi (dış yüz), menteşe silindiri ve kuyruk cebi, pim deliği, parmak oyuğu
    cuts = [loc * bd.Pos(0, 0, 0.1) * bd.extrude(_strut_region_local(), amount=-2.1)]
    cuts.append(loc * _box(-BARREL_L / 2 - 0.3, BARREL_L / 2 + 0.3, -BARREL_R - 0.6, TAIL + 0.6, -(2 * BARREL_R + TAIL_G), 0.1))
    cuts.append(loc * _xcyl(0.95, -BARREL_L / 2 - 2.8, BARREL_L / 2 + 2.8, 0.0, -BARREL_R))
    foot = loc * bd.Pos(0, -STRUT_L + 2.0, 0) * bd.Cylinder(5.0, 3.0)
    cuts.append(foot & _box(0, W, 0, H, -1, 1.6))
    bx0, bx1, by0, by1 = BOOST                                                 # MT3608 yuvası (iç yüz)
    cuts.append(_box(bx0 - 0.3, bx1 + 0.3, by0 - 0.3, by1 + 0.3, B_T - BOOST_REC, B_T + 0.1))
    # vidalar (havşa), köşelik ve süs yuvaları
    for x, y in B_SCREWS:
        cuts.append(_cyl(1.7, -0.1, B_T + 0.1, x, y))
        cuts.append(bd.Pos(x, y, 0.6) * bd.Cone(3.15, 1.5, 1.65, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
    recess = _union([_tri(cx, cy, sx, sy, 15.2) for cx, cy, sx, sy in BACK_CORNERS])
    cuts.append(_slab(recess, -0.1, 0.6))
    engr = _frame_line(W - SP - 8.0, H - 8.0, 1.6, (SP + W) / 2, H / 2)
    cuts.append(_slab(engr, -0.1, 0.35))
    for c in cuts:
        b -= c
    cover = _lab(b, "arka_kapak")
    return cover


# ============================================================== süs ve küçük parçalar
def title_plate():
    """Yaldız başlık levhası: kalın gravür harfleri ve 0.9 mm kenar (FDM'de 2 iz)."""
    p = _slab(_title_plate_outline(), 0.0, 0.6)
    txt = bd.Pos(WX, TITLE_Y) * bd.Text("VADE MECUM", font_size=5.0, font_path=ENGRAVE, align=(bd.Align.CENTER, bd.Align.CENTER))
    p += _slab(bd.offset(txt, 0.11), 0.59, 1.1)                                     # çizgiler >= 0.8 mm
    p += _slab(_title_plate_outline() - _rrf(40.2, 6.6, 0.6, WX, TITLE_Y), 0.59, 1.0)
    return p


def _rod_of_asclepius(cx, cy, s=1.0):
    staff = _rrf(1.0 * s, 9.6 * s, 0.45 * s, cx, cy)
    staff += bd.Pos(cx, cy + 4.9 * s) * bd.Circle(0.75 * s)
    snake = []
    n = 26
    for i in range(n):
        t = i / (n - 1)
        y = cy - 3.6 * s + 7.0 * s * t
        x = cx + 1.7 * s * math.sin(2 * math.pi * 1.6 * t + 0.4) * (1.0 - 0.25 * t)
        snake.append(bd.Pos(x, y) * bd.Circle(0.6 * s))
    head = bd.Pos(cx + 1.7 * s * math.sin(2 * math.pi * 1.6 + 0.4) * 0.75 + 0.6 * s, cy + 3.7 * s) * bd.Ellipse(1.0 * s, 0.65 * s)
    return staff + _union(snake) + head


def cartouche():
    p = _slab(_cartouche_outline(), 0.0, 0.6)
    rim = _cartouche_outline() - (bd.Pos(WX, CART_Y) * bd.Ellipse(9.0, 4.9))
    p += _slab(rim, 0.59, 1.1)
    p += _slab(_rod_of_asclepius(WX, CART_Y, 0.9), 0.59, 1.1)
    return p


def corner_piece(leg):
    t = _slab(_tri(0, 0, 1, 1, leg - 0.25), 0.0, 1.0)
    t = t.chamfer(0.4, None, t.edges().filter_by(bd.Axis.Z, reverse=True).group_by(bd.Axis.Z)[-1])
    return t


def ribbon():
    """Kurdele ayraç: iç uçta T çapası, dışta V kesik ve anahtarlık deliği. Yerel: y=0 baş yüzü."""
    strip = _box(-3.0, 3.0, -(CY1 - KY1) - 0.2, 11.0, 0.0, 1.6)
    strip += _box(-5.0, 5.0, -(CY1 - KY1) - 0.2, -(CY1 - KY1) + 2.0, 0.0, 2.2)
    strip -= bd.Pos(0, 11.0, -1) * bd.extrude(bd.Polygon((-3.5, 0.01), (0, -2.6), (3.5, 0.01), align=None), amount=4)
    strip -= _cyl(1.6, -1, 3, 0.0, 6.0)
    return strip


def headband_cap():
    """Kapitalbant görünümlü kalem başlığı: alt 2 mm sırttaki yuvaya oturur, kalemin arka ucunu 3.2 mm sıkar."""
    cap = _cyl(3.4, 0.0, 5.0)
    cap = cap.fillet(0.7, cap.edges().group_by(bd.Axis.Z)[-1])
    cap -= _cyl(3.6, 3.6, 4.0) - _cyl(3.05, 0, 6)
    cap -= _cyl(STYLUS_D / 2 + 0.08, -0.1, 3.2)
    return cap


def small_parts():
    out = [_lab(bd.Pos(0, 0, T - 0.6) * title_plate(), "baslik"), _lab(bd.Pos(0, 0, T - 0.6) * cartouche(), "arma")]
    for i, (cx, cy, sx, sy) in enumerate(FRONT_CORNERS):
        piece = bd.Pos(cx, cy, T - 0.6) * _corner_place(corner_piece(11.2), sx, sy)
        out.append(_lab(piece, f"kose{i}"))
    for i, (cx, cy, sx, sy) in enumerate(BACK_CORNERS):
        piece = bd.Pos(cx, cy, 0.6) * (bd.Rot(180, 0, 0) * _corner_place(corner_piece(15.2), sx, -sy))
        out.append(_lab(piece, f"kose{i + 2}"))
    out.append(_lab(bd.Pos(RIB_X, CY1, 11.25) * ribbon(), "kurdele"))
    out.append(_lab(bd.Pos(PEN_X, H - 2.0, PEN_Z) * (bd.Rot(-90, 0, 0) * headband_cap()), "kapitalbant"))
    return out


def _corner_place(piece, sx, sy):
    """corner_piece +x,+y kollu: işaretlere göre aynala (z yönü korunur)."""
    if sx < 0:
        piece = bd.mirror(piece, about=bd.Plane.YZ)
    if sy < 0:
        piece = bd.mirror(piece, about=bd.Plane.XZ)
    return piece


def internals():
    pcb = _box(XB - PCB_W / 2, XB + PCB_W / 2, YB - PCB_H / 2, YB + PCB_H / 2, Z_PCB0, Z_PCB1)
    for x, y in BOARD_HOLES:
        pcb -= _cyl(1.6, Z_PCB0 - 0.1, Z_PCB1 + 0.1, x, y)
    lcd = _box(XB - LCD_W / 2, XB + LCD_W / 2, YB - LCD_H / 2 + VIEW_DY, YB + LCD_H / 2 + VIEW_DY, Z_PCB1, ZC1 - 0.03)
    glass = _box(WX - VIEW_W / 2, WX + VIEW_W / 2, WY - VIEW_H / 2, WY + VIEW_H / 2, ZC1 - 0.03, ZC1 - 0.01)
    x0, x1, y0, y1 = BAT
    bat = _box(x0, x1, y0, y1, B_T + 0.2, B_T + 0.2 + BAT_T)
    tx0, tx1, ty0, ty1 = TP
    tp = _box(tx0, tx1, ty0, ty1, B_T, B_T + 1.6) + _box(USBC_X - 4.45, USBC_X + 4.45, ty1 - 7.4 + TP_OVER, ty1 + TP_OVER,
                                                        USBC_Z - 1.6, USBC_Z + 1.6)
    bx0, bx1, by0, by1 = BOOST
    zb = B_T - BOOST_REC
    boost = _box(bx0, bx1, by0, by1, zb + 1.0, zb + 2.6)                         # kart (altta 1 mm pim ucu payı)
    boost += _box(bx1 - 12.0, bx1 - 2.0, by0 + 2.0, by0 + 12.0, zb + 2.6, zb + BOOST_H)   # trimpot
    boost += _box(bx0 + 12.0, bx0 + 18.0, by0 + 5.0, by0 + 11.0, zb + 2.6, zb + 7.0 - 0.1)  # bobin
    sw = _box(SW_X - 4.3, SW_X + 4.3, KY1, KY1 + 3.6, ZC0 + 2.5, ZC0 + 6.0)
    pen = _ycyl(STYLUS_D / 2, H + 1.2 - STYLUS_L + 3.0, H + 1.2, PEN_X, PEN_Z)
    pen += bd.Pos(PEN_X, H + 1.2 - STYLUS_L + 3.0, PEN_Z) * (bd.Rot(90, 0, 0) * bd.Cone(
        STYLUS_D / 2, 0.6, 3.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
    pin = loc_pin()
    return [_lab(pcb, "ic_kart", "#d9b81c"), _lab(lcd, "ic_lcd", "#151515"), _lab(glass, "ekran"),
            _lab(bat, "ic_pil", "#b9c3cf"), _lab(tp, "ic_tp4056", "#1f6fd1"), _lab(sw, "ic_anahtar", "#202020"),
            _lab(boost, "ic_yukseltici", "#1f5fc0"), _lab(pen, "kalem"), pin]


def loc_pin():
    p = bd.Location(_strut_plane()) * _xcyl(0.85, -BARREL_L / 2 - 2.6, BARREL_L / 2 + 2.6, 0.0, -BARREL_R)
    return _lab(p, "pim")


def book(open_angle=0.0, inside=True, pen_out=0.0):
    parts = [front_cover(), page_block(), spine(), back_cover(), strut(open_angle), *small_parts()]
    if inside:
        parts += internals()
    if pen_out:
        parts = [_lab(bd.Pos(0, pen_out, 0) * p, p.label, p.color) if p.label in ("kalem", "kapitalbant") else p for p in parts]
    return parts


# ============================================================== duruş
def _stand_xf(shape, tilt, landscape):
    s = bd.Rot(0, 0, -90) * shape if landscape else shape
    return bd.Rot(90 - tilt, 0, 0) * s


@lru_cache(maxsize=None)
def _proxy():
    return _box(0, W, 0, H, 0, T)


def stance(landscape):
    leg = strut(STRUT_STOP)

    def gap(t):
        return _stand_xf(leg, t, landscape).bounding_box().min.Z - _stand_xf(_proxy(), t, landscape).bounding_box().min.Z

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


def standing(landscape, pen_out=0.0):
    t = stance(landscape)
    parts = book(STRUT_STOP, pen_out=pen_out)
    z0 = _stand_xf(_proxy(), t, landscape).bounding_box().min.Z
    return [_lab(bd.Pos(0, 0, -z0) * _stand_xf(p, t, landscape), p.label, p.color) for p in parts], t


# ============================================================== modeller
@model
def vademecum():
    return bd.Compound(children=book(), label="vademecum")


@model
def vm_dikey():
    parts, t = standing(False)
    return bd.Compound(children=parts, label=f"vm_dikey_{round(t)}deg")


@model
def vm_yatay():
    parts, t = standing(True)
    return bd.Compound(children=parts, label=f"vm_yatay_{round(t)}deg")


@model
def vm_kalem():
    parts, _ = standing(False, pen_out=40.0)
    return bd.Compound(children=parts, label="vm_kalem")


@model
def vm_patlatma():
    off = {"on_kapak": 16, "baslik": 22, "arma": 22, "kose0": 22, "kose1": 22, "ekran": 8, "ic_lcd": 8, "ic_kart": 4,
           "sayfa": 0, "ic_pil": -8, "ic_tp4056": -8, "ic_yukseltici": -8, "ic_anahtar": 0, "arka_kapak": -16, "ayak": -24, "pim": -24,
           "kose2": -22, "kose3": -22, "kose4": -22}
    dx = {"sirt": -14, "kalem": -14, "kapitalbant": -14}
    dy = {"kurdele": 10, "kapitalbant": 10}
    parts = [_lab(bd.Pos(dx.get(p.label, 0), dy.get(p.label, 0), off.get(p.label, 0)) * p, p.label, p.color) for p in book()]
    z0 = min(q.bounding_box().min.Z for q in parts)
    return bd.Compound(children=[_lab(bd.Pos(0, 0, -z0) * q, q.label, q.color) for q in parts], label="vm_patlatma")


@model
def vm_ic():
    """İç düzen görünümü: ön kapak, ekran ve kart yok; pil, MT3608, TP4056, anahtar ve menteşe görünür."""
    keep = ("arka_kapak", "sayfa", "ic_pil", "ic_tp4056", "ic_yukseltici", "ic_anahtar", "kurdele", "pim", "ayak")
    return bd.Compound(children=[q for q in book() if q.label in keep], label="vm_ic")


def _flip(shape, top):
    return bd.Pos(0, 0, top) * (bd.Rot(180, 0, 0) * shape)


@model
def p_on_kapak():
    return _lab(_flip(front_cover(), T), "on_kapak")


@model
def p_arka_kapak():
    return back_cover()


@model
def p_sayfa():
    return _lab(bd.Pos(0, 0, -ZC0) * page_block(), "sayfa")


@model
def p_sirt():
    return _lab(bd.Rot(90, 0, 0) * spine(), "sirt")


@model
def p_ayak():
    return _lab(bd.Rot(180, 0, 0) * strut_local(), "ayak")


@model
def p_baslik():
    return _lab(title_plate(), "baslik")


@model
def p_arma():
    return _lab(cartouche(), "arma")


@model
def p_kose_on():
    return _lab(corner_piece(11.2), "kose")


@model
def p_kose_arka():
    return _lab(corner_piece(15.2), "kose")


@model
def p_kurdele():
    return _lab(ribbon(), "kurdele")


@model
def p_kapitalbant():
    return _lab(bd.Pos(0, 0, 5.0) * (bd.Rot(180, 0, 0) * headband_cap()), "kapitalbant")


if __name__ == "__main__":
    for m in (vademecum, vm_dikey, vm_yatay, vm_kalem, vm_patlatma, vm_ic, p_on_kapak, p_arka_kapak, p_sayfa, p_sirt, p_ayak,
              p_baslik, p_arma, p_kose_on, p_kose_arka, p_kurdele, p_kapitalbant):
        m()
