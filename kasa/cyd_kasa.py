"""CYD 2.8" (ESP32-2432S028R) el tipi kasa.

Parçalar (FDM, PLA/PETG, 0.4 nozul, 0.2 katman):
  - on_kasa     : ekran çerçevesi + yan duvarlar. Ön yüzü tablaya gelecek şekilde basılır.
  - arka_kapak  : pil yuvası, TP4056 (USB-C) yuvası, anahtar penceresi, havalandırma,
                  anahtarlık kulağı ve iki adet yerinde-basılan (print-in-place) ayak.
                  Dış yüzü tablaya gelecek şekilde basılır (arka_kapak_baski modeli).
Montaj: 4 x M3x16 vida arka kapaktan -> kart delikleri -> ön kasa boğazlarına (kendinden diş).

Koordinatlar: kart merkezi (0,0); ekran yüzü z=0, arka yüz +z yönünde. Birim mm.
Ölçüler: kart 86x50x1.6, ekran modülü 70x50, kartın 4 mm üstünde; arka bileşenler <= 4.8 mm.
Delik aralığı ve port konumları VARSAYIM: kartı kumpasla ölçüp parametreleri düzeltin.

Check: cad model dfm "$ID" --process printing --technology fdm --material petg
"""

import math

import build123d as bd
from cad import model

# ---------------------------------------------------------------- kart (CYD 2.8")
PCB_X, PCB_Y, PCB_T = 86.0, 50.0, 1.6
LCD_X, LCD_Y, LCD_T = 70.0, 50.0, 4.0
BACK_PARTS = 4.8                     # arka yüzdeki en uzun bileşen (BOOT/RST, hoparlör konn.)
HOLE_DX = model.param("delik_araligi_x", 78.0, min=70, max=82, unit="mm")
HOLE_DY = model.param("delik_araligi_y", 42.0, min=36, max=46, unit="mm")
VIEW_X, VIEW_Y = 57.6, 43.2          # 2.8" 320x240 aktif alan
VIEW_DX = model.param("ekran_kaydirma_x", 0.0, min=-6, max=6, unit="mm")

# ---------------------------------------------------------------- kasa
CLR = model.param("kart_boslugu", 0.3, min=0.1, max=0.8, unit="mm")
WALL = model.param("duvar", 2.0, min=1.2, max=3.0, unit="mm")
BEZEL = 1.6
R_OUT = 3.0
FLOOR = 4.6                          # arka kapak tabanı (ayak cebi 3.7 + 0.9)

# ön kasadaki port çentikleri (kartın arka yüzündeki konnektörler)
USB_Y = model.param("usb_y", 0.0, min=-18, max=18, unit="mm")      # +x kısa kenar: micro-USB/USB-C
USB_W = model.param("usb_genislik", 13.0, min=8, max=20, unit="mm")
SD_Y = model.param("sd_y", 0.0, min=-18, max=18, unit="mm")        # -x kısa kenar: microSD
SD_W = model.param("sd_genislik", 15.0, min=10, max=20, unit="mm")

# ---------------------------------------------------------------- pil + şarj
BAT_X = model.param("pil_x", 50.0, min=30, max=50, unit="mm")      # 503450: 50x34x5 ~1000 mAh
BAT_Y = model.param("pil_y", 34.0, min=20, max=36, unit="mm")
BAT_T = model.param("pil_kalinlik", 5.0, min=3, max=5.4, unit="mm")
TP_X, TP_Y, TP_PCB = 28.0, 17.2, 1.6  # TP4056 USB-C modülü
USBC_W, USBC_H = 9.0, 3.3

# ---------------------------------------------------------------- ayaklar
LEG_W, LEG_T = 10.0, 3.2
LEG_GAP = 0.5                        # yerinde-basılan menteşe boşluğu
STAND_ANGLE = model.param("ayak_acisi", 55.0, min=40, max=75, unit="deg")

# türetilmiş z seviyeleri
Z_LCD = BEZEL
Z_PCB = Z_LCD + LCD_T                # kartın ön yüzü
Z_PCB_B = Z_PCB + PCB_T              # kartın arka yüzü
Z_SPLIT = Z_PCB_B + BACK_PARTS + 0.6  # ön kasa / arka kapak ayrımı
Z_FLOOR_IN = Z_SPLIT + 0.4 + BAT_T   # arka kapak taban iç yüzü
Z_BACK = Z_FLOOR_IN + FLOOR          # cihazın arka yüzü

IN_X, IN_Y = PCB_X + 2 * CLR, PCB_Y + 2 * CLR
OUT_X, OUT_Y = IN_X + 2 * WALL, IN_Y + 2 * WALL
HOLES = [(sx * HOLE_DX / 2, sy * HOLE_DY / 2) for sx in (-1, 1) for sy in (-1, 1)]

SLOT_DEPTH = LEG_T + LEG_GAP
Z_PIVOT = Z_BACK - LEG_T / 2
# Durdurucu kuyruk: menteşenin arkasındaki uç, ayak STAND_ANGLE açısına gelince cebin tabanına
# dayanır. Temas köşesi (TAIL, -TAIL_H) eksene yakın tutulur ki derinliği STAND_ANGLE'dan sonra da
# artsın (tepe noktası ~74°): ayak bu açıyı geçemez. Pah başlangıcı (CHAMFER_S) hiçbir açıda tabana değmez.
TAIL_H = 0.6
_th = math.radians(STAND_ANGLE)
TAIL = (SLOT_DEPTH - LEG_T / 2 - TAIL_H * math.cos(_th)) / math.sin(_th)
CHAMFER_S = 1.0
assert math.hypot(CHAMFER_S, LEG_T / 2) < SLOT_DEPTH - LEG_T / 2, "pah başı tabana sürter"
assert math.degrees(math.atan2(TAIL, TAIL_H)) > STAND_ANGLE + 10, "durdurucu tepe noktası açıya çok yakın"
LEG_FOOT_IN = 0.5                    # ayak ucu dış çizginin bu kadar içinde
LEG_LEN = 24.8


def _slab(w, h, r, z0, z1):
    return bd.Pos(0, 0, z0) * bd.extrude(bd.RectangleRounded(w, h, r), amount=z1 - z0)


def _box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * bd.Box(
        x1 - x0, y1 - y0, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


def _cyl(r, z0, z1, x=0.0, y=0.0):
    return bd.Pos(x, y, z0) * bd.Cylinder(r, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))


# ================================================================= ön kasa
def front_shell_body():
    body = _slab(OUT_X, OUT_Y, R_OUT, 0, Z_SPLIT)
    body -= _slab(IN_X, IN_Y, 1.0, BEZEL, Z_SPLIT)

    # ekran penceresi, dışa doğru 45° pah
    win = bd.Pos(VIEW_DX, 0, 0) * bd.extrude(bd.Rectangle(VIEW_X + 2.0, VIEW_Y + 2.0), amount=1.0, taper=45)
    win += _box(VIEW_DX - VIEW_X / 2, VIEW_DX + VIEW_X / 2, -VIEW_Y / 2, VIEW_Y / 2, 0, BEZEL)
    body -= win

    # kart boğazları: ekranın iki yanındaki şeritte, kartı ekran yüksekliğinde tutar
    for x, y in HOLES:
        body += _cyl(2.75, BEZEL, Z_PCB, x, y)
        body -= _cyl(1.3, 0.8, Z_PCB, x, y)          # M3 kendinden diş pilotu

    # port çentikleri (üstten açık)
    body -= _box(OUT_X / 2 - WALL - 0.1, OUT_X / 2 + 0.1, USB_Y - USB_W / 2, USB_Y + USB_W / 2, Z_PCB - 0.6, Z_SPLIT + 0.1)
    body -= _box(-OUT_X / 2 - 0.1, -OUT_X / 2 + WALL + 0.1, SD_Y - SD_W / 2, SD_Y + SD_W / 2, Z_PCB_B - 0.4, Z_SPLIT + 0.1)
    body.label = "on_kasa"
    body.color = "#2b2f36"
    return body


# ================================================================= ayaklar
def _leg(axis):
    """Ayak, yerel koordinatlarda: menteşe ekseni x boyunca orijinde, ayak -y yönünde uzanır."""
    h = LEG_T / 2
    prof = bd.Polygon((-LEG_LEN, -h), (-LEG_LEN, h), (TAIL, h), (TAIL, -TAIL_H), (CHAMFER_S, -h), align=None)
    leg = bd.extrude(bd.Plane.YZ * prof, amount=LEG_W / 2, both=True)
    leg = leg.fillet(1.2, leg.edges().filter_by(bd.Axis.Z).group_by(bd.Axis.Y)[0])
    pin_len = LEG_W / 2 + LEG_GAP + 1.6
    pin = bd.Rot(0, 90, 0) * bd.Cylinder(0.6, 2 * pin_len)
    leg += pin
    leg.label = f"ayak_{axis}"
    leg.color = "#e0a526"
    return leg


def _place_leg(leg, which, angle=0.0):
    """which='yatay': -y kenarına açılır; 'dikey': -x kenarına açılır."""
    opened = bd.Rot(-angle, 0, 0) * leg   # ayak ucunu dışarı (+z) kaldırır
    if which == "yatay":
        pivot_y = -OUT_Y / 2 + LEG_FOOT_IN + LEG_LEN
        return bd.Pos(0, pivot_y, Z_PIVOT) * opened
    pivot_x = -OUT_X / 2 + LEG_FOOT_IN + LEG_LEN
    return bd.Pos(pivot_x, 0, Z_PIVOT) * bd.Rot(0, 0, -90) * opened


def _leg_pocket(which):
    """Ayak cebi + pim delikleri, yatay ayağın yerel çerçevesinde kurulup yerleştirilir."""
    w = LEG_W + 2 * LEG_GAP
    pocket = _box(-w / 2, w / 2, -LEG_LEN - 5, math.hypot(TAIL, LEG_T / 2) + 0.6, -LEG_T / 2 - LEG_GAP, LEG_T / 2 + 1)
    pin_hole = bd.Rot(0, 90, 0) * bd.Cylinder(1.2, w + 2 * 2.2)
    pocket += pin_hole
    if which == "yatay":
        return bd.Pos(0, -OUT_Y / 2 + LEG_FOOT_IN + LEG_LEN, Z_PIVOT) * pocket
    return bd.Pos(-OUT_X / 2 + LEG_FOOT_IN + LEG_LEN, 0, Z_PIVOT) * bd.Rot(0, 0, -90) * pocket


# ================================================================= arka kapak
BAT_CX = -OUT_X / 2 + WALL + 6.3 + BAT_X / 2   # pil sola yaslı, boğazlardan uzak
TP_X0 = IN_X / 2 - TP_X                       # TP4056 +x duvarına yaslı


def back_cover_body():
    body = _slab(OUT_X, OUT_Y, R_OUT, Z_SPLIT, Z_BACK)
    body -= _slab(IN_X, IN_Y, 1.0, Z_SPLIT - 0.1, Z_FLOOR_IN)

    # anahtarlık kulağı (+x,+y köşesi: hem yatay hem dikey dururken üstte)
    ex, ey = OUT_X / 2 + 2.2, OUT_Y / 2 + 2.2
    ear = bd.Pos(0, 0, Z_BACK - 4.0) * bd.extrude(
        bd.make_hull(bd.Circle(5.0).moved(bd.Location((ex, ey))).edges()
                     + bd.Circle(5.0).moved(bd.Location((ex - 6, ey - 6))).edges()), amount=4.0)
    body += ear
    body -= _cyl(2.2, Z_BACK - 4.1, Z_BACK + 0.1, ex + 0.6, ey + 0.6)

    # vida kolonları: kartın arka yüzüne basar
    for x, y in HOLES:
        body += _cyl(3.9, Z_PCB_B, Z_SPLIT + 0.01, x, y)        # ön kasa içinde: duvarlara değmez
        body += _cyl(4.4, Z_SPLIT, Z_FLOOR_IN + 0.01, x, y)     # kapak içinde: duvarlarla birleşir
        body -= _cyl(1.7, Z_PCB_B - 0.1, Z_BACK + 0.1, x, y)
        body -= _cyl(3.0, Z_BACK - 5.4, Z_BACK + 0.1, x, y)   # M3 silindir baş yuvası (M3x16)

    # pil köşe tutucuları
    bx0, bx1 = BAT_CX - BAT_X / 2 - 0.5, BAT_CX + BAT_X / 2 + 0.5
    by0, by1 = -BAT_Y / 2 - 0.5, BAT_Y / 2 + 0.5
    zr0 = Z_FLOOR_IN - 2.5
    for cx, sx in ((bx0, -1), (bx1, 1)):
        for cy, sy in ((by0, -1), (by1, 1)):
            xa, xb = sorted((cx, cx + sx * 1.2))
            ya, yb = sorted((cy, cy + sy * 1.2))
            body += _box(xa, xb, *sorted((cy + sy * 1.2, cy - sy * 6)), zr0, Z_FLOOR_IN + 0.01)
            body += _box(*sorted((cx + sx * 1.2, cx - sx * 6)), ya, yb, zr0, Z_FLOOR_IN + 0.01)

    # TP4056 rayları
    for sy in (-1, 1):
        y0 = sy * (TP_Y / 2 + 0.3)
        body += _box(TP_X0 + 1, IN_X / 2 - 1, *sorted((y0, y0 + sy * 1.2)), Z_FLOOR_IN - 3.0, Z_FLOOR_IN + 0.01)

    # USB-C girişi (+x duvarı): modül kartı tabana yaslı, konnektör altında
    # alttan açık çentik + dışta fiş kalıbı için 0.8 mm cep (duvar ince kalır, fiş tam oturur)
    z_top = Z_FLOOR_IN - TP_PCB + 0.45
    body -= _box(IN_X / 2 - 0.1, OUT_X / 2 + 0.1, -(USBC_W + 1.0) / 2, (USBC_W + 1.0) / 2, Z_SPLIT - 0.1, z_top)
    body -= _box(OUT_X / 2 - 0.8, OUT_X / 2 + 0.1, -6.5, 6.5, Z_SPLIT - 0.1, z_top + 1.6)

    # açma/kapama anahtarı penceresi (SS12D00, +y duvarı)
    body -= _box(22.0 - 3.75, 22.0 + 3.75, OUT_Y / 2 - WALL - 0.1, OUT_Y / 2 + 0.1, Z_FLOOR_IN - 3.6, Z_FLOOR_IN - 0.6)

    # havalandırma: TP4056 üstünde iki sıra yarık
    for i in range(6):
        x = 17.0 + i * 3.2
        for sy in (-1, 1):
            body -= _box(x - 0.8, x + 0.8, *sorted((sy * 10.5, sy * 18.0)), Z_FLOOR_IN - 0.1, Z_BACK + 0.1)

    # ayak cepleri
    body -= _leg_pocket("yatay")
    body -= _leg_pocket("dikey")

    body.label = "arka_kapak"
    body.color = "#3b4250"
    return body


def back_cover_parts(angle=0.0):
    cover = back_cover_body()
    leg_l = _place_leg(_leg("yatay"), "yatay", angle)
    leg_p = _place_leg(_leg("dikey"), "dikey", angle)
    return cover, leg_l, leg_p


# ================================================================= referans parçalar
def reference_parts():
    pcb = _box(-PCB_X / 2, PCB_X / 2, -PCB_Y / 2, PCB_Y / 2, Z_PCB, Z_PCB_B)
    for x, y in HOLES:
        pcb -= _cyl(1.6, Z_PCB - 0.1, Z_PCB_B + 0.1, x, y)
    pcb.label, pcb.color = "ref_kart", "#d9c21c"
    lcd = _box(-LCD_X / 2, LCD_X / 2, -LCD_Y / 2 + CLR, LCD_Y / 2 - CLR, Z_LCD, Z_PCB)
    lcd.label, lcd.color = "ref_ekran", "#111111"
    bat = _box(BAT_CX - BAT_X / 2, BAT_CX + BAT_X / 2, -BAT_Y / 2, BAT_Y / 2, Z_FLOOR_IN - BAT_T, Z_FLOOR_IN)
    bat.label, bat.color = "ref_pil", "#6b8fb5"
    tp = _box(TP_X0, IN_X / 2, -TP_Y / 2, TP_Y / 2, Z_FLOOR_IN - TP_PCB, Z_FLOOR_IN)
    tp += _box(IN_X / 2 - 7.4, IN_X / 2, -USBC_W / 2, USBC_W / 2, Z_FLOOR_IN - TP_PCB - USBC_H, Z_FLOOR_IN - TP_PCB)
    tp.label, tp.color = "ref_tp4056", "#1f6fd1"
    return [pcb, lcd, bat, tp]


# ================================================================= modeller
@model
def on_kasa():
    return front_shell_body()


@model
def arka_kapak():
    cover, leg_l, leg_p = back_cover_parts()
    return bd.Compound(children=[cover, leg_l, leg_p], label="arka_kapak_grubu")


@model
def arka_kapak_baski():
    """Baskı yönü: dış yüz tablada (z=0)."""
    cover, leg_l, leg_p = back_cover_parts()
    flip = bd.Pos(0, 0, Z_BACK) * bd.Rot(180, 0, 0)
    parts = []
    for p in (cover, leg_l, leg_p):
        q = flip * p
        q.label, q.color = p.label, p.color
        parts.append(q)
    return bd.Compound(children=parts, label="arka_kapak_baski")


@model
def montaj():
    cover, leg_l, leg_p = back_cover_parts()
    return bd.Compound(children=[front_shell_body(), cover, leg_l, leg_p, *reference_parts()], label="cyd_kasa")


@model
def montaj_ayak_acik():
    cover, leg_l, leg_p = back_cover_parts(STAND_ANGLE)
    return bd.Compound(children=[front_shell_body(), cover, leg_l, leg_p, *reference_parts()], label="cyd_kasa_acik")


if __name__ == "__main__":
    on_kasa()
    arka_kapak()
    arka_kapak_baski()
    montaj()
    montaj_ayak_acik()
