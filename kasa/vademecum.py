"""VADE MECUM — CYD 2.8" (ESP32-2432S028R) için deri ciltli cep el kitabı kasası.

"Vade mecum" (Lat. "yanımda gel"): hekimlerin cepte taşıdığı başvuru kitabı. Cihaz, dik duran bir kitap:
  * Ön kapak (A): ekran, varak çerçeveli bir levha gibi kapakta; üstte yaldız başlık plakası,
    altta Asklepios asalı arma, ön kenar köşelerinde pirinç köşelikler.
  * Sayfa bloğu (C): krem; baş, kuyruk ve ön kenarda sayfa çizgileri. Ön kenardaki bazı "sayfa
    aralıkları" havalandırma yarığıdır. Portlar başta (USB, USB-C, anahtar), microSD kuyrukta.
  * Sırt (D): yuvarlak, kabartma bantlı; içinde kalem tüneli. Tepedeki kapitalbant = kalem başlığı.
  * Kırmızı kurdele ayraç: anahtarlık.
  * Pil hattı: TP4056 OUT → USB-C kablo → kartın USB-C girişi. Kablonun fişi baştaki pencereden çıkar (pil devre dışı,
    güncelleme için PC kablosu aynı girişe takılır); pencere sayfa çizgili bir kapakla kapanır.
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
PLUG_L = model.param("fis_boy", 16.0, min=8, max=26, unit="mm")          # kartın USB-C girişine takılı fişin gövdesi (kart kenarından dışarı)
CABLE_ROOM = model.param("kablo_payi", 5.0, min=3, max=14, unit="mm")    # fişin arkasında kablonun kıvrılacağı boşluk

# ============================================================== kitap
W, T = 66.0, 21.8
SP = 8.5                                   # sırt genişliği
A_T, B_T, SQ = 2.8, 3.0, 2.0               # ön/arka kapak kalınlığı, kapak payı
ZC0, ZC1 = B_T, T - A_T                    # sayfa bloğu z: 3.0 .. 19.0
TAIL_WALL, HEAD_WALL = 6.7, 2.4            # kuyruk duvarı (vida, pim, microSD) ve ince baş duvarı
PLUG_W, PLUG_H = 13.0, 7.2                 # kablolu USB-C fişin gövdesi: genişlik, yükseklik
CX0, CX1, CY0 = SP, W - SQ, SQ
XB = CX0 + 1.6 + CLR + PCB_W / 2           # kart merkezi
KY0 = CY0 + TAIL_WALL                      # boşluğun kuyruk ucu
YB = KY0 + CLR + PCB_H / 2
BY1 = YB + PCB_H / 2                       # kartın baş kenarı
PLUG_Y0 = BY1 + 0.8                        # fiş gövdesinin ön yüzü (ucu karttaki USB-C'de)
PLUG_Y1 = PLUG_Y0 + PLUG_L                 # fiş gövdesinin arka ucu, kablonun çıktığı yer
KY1 = PLUG_Y1 + CABLE_ROOM                 # boşluğun baş ucu: baş duvarının iç yüzü
CY1 = KY1 + HEAD_WALL
H = CY1 + SQ                               # kitabın boyu: fiş ve kablo payı kadar uzar
KX0, KX1 = CX0 + 1.6, XB + PCB_W / 2 + CLR # boşluk
Z_PCB1 = ZC1 - LCD_T                       # kart ön yüzü 15.0
Z_PCB0 = Z_PCB1 - PCB_T                    # 13.4
WX, WY = XB, YB + VIEW_DY                  # ekran penceresi merkezi
WIN_W, WIN_H = VIEW_W + 0.8, VIEW_H + 0.8

BOARD_HOLES = [(XB + sx * HOLE_X / 2, YB + sy * HOLE_Y / 2) for sx in (-1, 1) for sy in (-1, 1)]
B_SCREWS = [(12.5, CY0 + 3.35), (12.5, CY1 - 3.35), (61.0, CY1 - 3.35)]   # havşa başlı M3x10, köşeliklerin altında
B_PIN = (58.0, CY0 + 3.35)
A_PINS = [(16.5, CY1 - 2.6), (58.0, CY1 - 2.6), (22.0, CY0 + 2.6), (48.0, CY0 + 2.6)]
D_PINS = [30.0, 52.0, 74.0, round(CY1 - 20.0, 1)]

# baş kenar portları
SW_X, USBC_X, RIB_X = 15.9, 45.6, 58.4
HEAD_BLOCK = 6.7                           # baş kenarda yerel kalın bloklar (anahtar, kurdele, vida, pim): eski baş duvarı kalınlığı
BLK_Y0 = CY1 - HEAD_BLOCK
TP_Z0 = B_T + 0.8                          # TP4056 yatağı: fiş gövdesi arka kapağa değmesin
USBC_Z = TP_Z0 + 1.6 + 1.65                # TP4056 arka kapağa yatık: USB-C ekseni
TP_W, TP_L = 17.2, 28.0
TP_FRONT = KY1 - 0.8                       # TP4056 USB-C soketinin ön yüzü: fiş sokete tam oturur, gövdesi pencerede kalır
TP = (USBC_X - TP_W / 2, USBC_X + TP_W / 2, TP_FRONT - 0.2 - TP_L, TP_FRONT - 0.2)   # TP4056 (USB-C başa bakar)
BAT = (26.0, 60.0, 10.6, 60.6)             # 503450 LiPo (x0, x1, y0, y1); sağda boşluk duvarına yaslanır
Z_PLUG = Z_PCB0 - 1.6                      # karttaki USB-C soketinin ekseni (kartın arka yüzünde)
WIN_PW, WIN_PH = PLUG_W + 1.4, 8.8         # fiş penceresi (baş duvarı)
WIN_PZ0 = ZC0 + 0.6 + 0.8 * 5              # sayfa çizgileriyle hizalı: 7.6 .. 16.4
TPW_Z1 = ZC0 + 0.6 + 0.8 * 10              # TP4056 USB-C penceresinin üstü: 11.6

# sırt ve kalem
R_SP = ((T / 2) ** 2 + SP ** 2) / (2 * SP)
PEN_X, PEN_Z = 4.25, T / 2
BANDS = [round(H * k / 6, 1) for k in range(1, 6)]

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
       "kurdele": "#c8202a", "kapitalbant": "#c8202a", "usb_kapagi": "#efe8d8", "ekran": "#0b0d12", "kalem": "#f2f2ee", "pim": "#c9ccd2"}


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
CART_Y = 12.6
TITLE_Y = round((WY + WIN_H / 2 + 2.6 + H - 4.0) / 2, 1)          # pencere çerçevesi ile kenar süsü arasındaki bandın ortası


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
    # baş duvarı ince; anahtar, kurdele, vida ve pimler için yerel kalın bloklar (eski baş duvarı kalınlığında)
    c += _box(KX0, SW_X + 5.8, BLK_Y0, KY1 + 0.01, ZC0, ZC1)
    c += _box(RIB_X - 4.7, KX1, BLK_Y0, KY1 + 0.01, 8.2, ZC1) + _box(56.0, KX1, BLK_Y0, KY1 + 0.01, ZC0, 8.4)
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
    # baş: anahtar cebi + kol yarığı, kartın USB-C fişi için pencere (kapaklı), TP4056 USB-C penceresi, kurdele yuvası
    cuts.append(_box(SW_X - 4.6, SW_X + 4.6, BLK_Y0 - 0.2, CY1 - 2.7, ZC0 + 1.0, ZC0 + 8.0))
    cuts.append(_box(SW_X - 2.6, SW_X + 2.6, CY1 - 2.9, CY1 + 1, ZC0 + 3.4, ZC0 + 5.6))
    cuts.append(_box(USB_X - WIN_PW / 2, USB_X + WIN_PW / 2, KY1 - 0.5, CY1 + 1, WIN_PZ0, WIN_PZ0 + WIN_PH))
    cuts.append(_box(USBC_X - 7.0, USBC_X + 7.0, KY1 - 0.5, CY1 + 1, ZC0 - 0.1, TPW_Z1))
    cuts.append(_box(RIB_X - 2.6, RIB_X + 2.6, BLK_Y0 - 0.5, CY1 + 1, 11.2, 13.0))
    cuts.append(_box(RIB_X - 3.9, RIB_X + 3.9, BLK_Y0 - 0.5, BLK_Y0 + 2.4, 10.7, 13.5))
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
    x0, x1, y0, y1 = BAT
    for cx, sx in ((x0 - 0.4, -1),):
        for cy, sy in ((y0 - 0.4, -1), (y1 + 0.4, 1)):
            b += _box(*sorted((cx, cx + sx * 1.2)), *sorted((cy + sy * 1.2, cy - sy * 6)), B_T - 0.01, B_T + 2.6)
            b += _box(*sorted((cx + sx * 1.2, cx - sx * 6)), *sorted((cy, cy + sy * 1.2)), B_T - 0.01, B_T + 2.6)
    tx0, tx1, ty0, ty1 = TP
    ty1 = min(ty1, KY1 - 0.2)                                                  # yatak baş duvarına girmez
    b += _box(tx0, tx1, ty0, ty1, B_T - 0.01, TP_Z0)
    b += _box(tx0 - 1.4, tx0 - 0.2, ty0, ty1, B_T - 0.01, TP_Z0 + 2.4)
    b += _box(tx1 + 0.2, tx1 + 1.4, ty0, ty1, B_T - 0.01, TP_Z0 + 2.4)
    b += _box(tx0, tx1, ty0 - 1.4, ty0 - 0.2, B_T - 0.01, TP_Z0 + 2.4)
    b += _cyl(1.1, B_T - 0.01, B_T + 1.8, *B_PIN)
    # ayak cebi (dış yüz), menteşe silindiri ve kuyruk cebi, pim deliği, parmak oyuğu
    cuts = [loc * bd.Pos(0, 0, 0.1) * bd.extrude(_strut_region_local(), amount=-2.1)]
    cuts.append(loc * _box(-BARREL_L / 2 - 0.3, BARREL_L / 2 + 0.3, -BARREL_R - 0.6, TAIL + 0.6, -(2 * BARREL_R + TAIL_G), 0.1))
    cuts.append(loc * _xcyl(0.95, -BARREL_L / 2 - 2.8, BARREL_L / 2 + 2.8, 0.0, -BARREL_R))
    foot = loc * bd.Pos(0, -STRUT_L + 2.0, 0) * bd.Cylinder(5.0, 3.0)
    cuts.append(foot & _box(0, W, 0, H, -1, 1.6))
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
    strip = _box(-2.5, 2.5, -HEAD_BLOCK - 0.2, 11.0, 0.0, 1.6)
    strip += _box(-3.7, 3.7, -HEAD_BLOCK - 0.2, -HEAD_BLOCK + 2.0, 0.0, 2.2)
    strip -= bd.Pos(0, 11.0, -1) * bd.extrude(bd.Polygon((-2.6, 0.01), (0, -2.6), (2.6, 0.01), align=None), amount=4)
    strip -= _cyl(1.6, -1, 3, 0.0, 6.0)
    return strip


def headband_cap():
    """Kapitalbant görünümlü kalem başlığı: alt 2 mm sırttaki yuvaya oturur, kalemin arka ucunu 3.2 mm sıkar."""
    cap = _cyl(3.4, 0.0, 5.0)
    cap = cap.fillet(0.7, cap.edges().group_by(bd.Axis.Z)[-1])
    cap -= _cyl(3.6, 3.6, 4.0) - _cyl(3.05, 0, 6)
    cap -= _cyl(STYLUS_D / 2 + 0.08, -0.1, 3.2)
    return cap


def usb_cover_local():
    """Baş kenardaki fiş penceresinin kapağı. Yerel: dış yüz z=0 (sayfa çizgili), gövde -z'ye, x genişlik, y yukarı (dünyada -z)."""
    w, h = WIN_PW - 0.2, WIN_PH - 0.2
    t = HEAD_WALL + 0.6
    body = _slab(_rrf(w, h, 0.8), -t, 0.0)
    zc = WIN_PZ0 + WIN_PH / 2
    for k in range(0, 12):                                                         # sayfa bloğundakiyle aynı çizgiler
        zl = ZC0 + 0.6 + 0.8 * k
        if WIN_PZ0 + 0.15 < zl and zl + 0.4 < WIN_PZ0 + WIN_PH - 0.15:
            body -= _box(-w / 2 - 1, w / 2 + 1, -(zl + 0.4 - zc), -(zl - zc), -0.35, 0.1)
    body -= bd.Pos(0, 0, 0) * bd.Sphere(1.8)                                       # parmak ucu çukuru
    return body


def usb_cover():
    return _lab(bd.Location(bd.Plane(origin=(USB_X, CY1, WIN_PZ0 + WIN_PH / 2), x_dir=(1, 0, 0), z_dir=(0, 1, 0))) * usb_cover_local(),
                "usb_kapagi")


def small_parts():
    out = [_lab(bd.Pos(0, 0, T - 0.6) * title_plate(), "baslik"), _lab(bd.Pos(0, 0, T - 0.6) * cartouche(), "arma")]
    for i, (cx, cy, sx, sy) in enumerate(FRONT_CORNERS):
        piece = bd.Pos(cx, cy, T - 0.6) * _corner_place(corner_piece(11.2), sx, sy)
        out.append(_lab(piece, f"kose{i}"))
    for i, (cx, cy, sx, sy) in enumerate(BACK_CORNERS):
        piece = bd.Pos(cx, cy, 0.6) * (bd.Rot(180, 0, 0) * _corner_place(corner_piece(15.2), sx, -sy))
        out.append(_lab(piece, f"kose{i + 2}"))
    out.append(_lab(bd.Pos(RIB_X, CY1, 11.25) * ribbon(), "kurdele"))
    out.append(usb_cover())
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
    bat = _box(x0, x1, y0, y1, B_T + 0.2, B_T + 5.2)
    tx0, tx1, ty0, ty1 = TP
    tp = _box(tx0, tx1, ty0, ty1, TP_Z0, TP_Z0 + 1.6) + _box(USBC_X - 4.5, USBC_X + 4.5, ty1 - 7.4, ty1 + 0.2, TP_Z0 + 1.6, TP_Z0 + 4.9)
    sw = _box(SW_X - 4.3, SW_X + 4.3, BLK_Y0, BLK_Y0 + 3.6, ZC0 + 2.5, ZC0 + 6.0)
    fis = _box(USB_X - PLUG_W / 2, USB_X + PLUG_W / 2, PLUG_Y0, PLUG_Y1, Z_PLUG - PLUG_H / 2, Z_PLUG + PLUG_H / 2)
    kablo = _ycyl(1.8, PLUG_Y1, PLUG_Y1 + CABLE_ROOM - 0.8, USB_X, Z_PLUG)
    pen = _ycyl(STYLUS_D / 2, H + 1.2 - STYLUS_L + 3.0, H + 1.2, PEN_X, PEN_Z)
    pen += bd.Pos(PEN_X, H + 1.2 - STYLUS_L + 3.0, PEN_Z) * (bd.Rot(90, 0, 0) * bd.Cone(
        STYLUS_D / 2, 0.6, 3.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
    pin = loc_pin()
    return [_lab(pcb, "ic_kart", "#d9b81c"), _lab(lcd, "ic_lcd", "#151515"), _lab(glass, "ekran"),
            _lab(bat, "ic_pil", "#b9c3cf"), _lab(tp, "ic_tp4056", "#1f6fd1"), _lab(sw, "ic_anahtar", "#202020"),
            _lab(fis, "ic_fis", "#2a2a2e"), _lab(kablo, "ic_kablo", "#2a2a2e"), _lab(pen, "kalem"), pin]


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
           "sayfa": 0, "ic_pil": -8, "ic_tp4056": -8, "ic_fis": -8, "ic_kablo": -8, "ic_anahtar": 0, "arka_kapak": -16, "ayak": -24, "pim": -24,
           "kose2": -22, "kose3": -22, "kose4": -22}
    dx = {"sirt": -14, "kalem": -14, "kapitalbant": -14}
    dy = {"kurdele": 10, "kapitalbant": 10, "usb_kapagi": 14}
    parts = [_lab(bd.Pos(dx.get(p.label, 0), dy.get(p.label, 0), off.get(p.label, 0)) * p, p.label, p.color) for p in book()]
    z0 = min(q.bounding_box().min.Z for q in parts)
    return bd.Compound(children=[_lab(bd.Pos(0, 0, -z0) * q, q.label, q.color) for q in parts], label="vm_patlatma")


@model
def vm_ic():
    """İç düzen görünümü: ön kapak, ekran ve kart yok; pil hattı, fiş, kablo payı, TP4056 ve anahtar görünür."""
    keep = ("arka_kapak", "sayfa", "ic_pil", "ic_tp4056", "ic_anahtar", "ic_fis", "ic_kablo", "usb_kapagi", "kurdele", "pim", "ayak")
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
def p_usb_kapagi():
    # kenar üstü basılır: sayfa çizgileri katman çizgileriyle aynı yönde, ince çıkıntılar yatay kalır
    return _lab(bd.Pos(0, 0, (WIN_PH - 0.2) / 2) * (bd.Rot(90, 0, 0) * usb_cover_local()), "usb_kapagi")


@model
def p_kapitalbant():
    return _lab(bd.Pos(0, 0, 5.0) * (bd.Rot(180, 0, 0) * headband_cap()), "kapitalbant")


if __name__ == "__main__":
    for m in (vademecum, vm_dikey, vm_yatay, vm_kalem, vm_patlatma, vm_ic, p_on_kapak, p_arka_kapak, p_sayfa, p_sirt, p_ayak,
              p_baslik, p_arma, p_kose_on, p_kose_arka, p_kurdele, p_usb_kapagi, p_kapitalbant):
        m()
