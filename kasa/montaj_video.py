"""Vade Mecum montaj videosu: render4.py'nin karelerine altyazı ekler, ffmpeg ile MP4 yapar.

python3 montaj_video.py KARE_KLASORU CIKTI.mp4
"""

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

src, out = Path(sys.argv[1]), Path(sys.argv[2])
info = json.loads((src / "zaman.json").read_text())
FPS, N = info["fps"], info["kare"]
g = info["genel"]
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
GOLD, CREAM = (232, 185, 35), (244, 236, 218)

adimlar = list(info["adimlar"])
total = len(adimlar)
caps = []                                   # (bas, bit, baslik, alt, sira)
for i, a in enumerate(adimlar, 1):
    caps.append((a["bas"], a["bit"], a["baslik"], a["alt"], i))
caps.append((g["cevirme"] + 0.1, g["cevirme"] + 1.6, "Arka yüze geçelim", "Şimdi arka kapağın parçaları", None))
caps.append((g["son_cevirme"] + 0.2, info["sure"] - 0.3, "Vade Mecum hazır",
             "Ayak açılınca dikeyde 24°, yatayda 18° yaslanır", None))
intro = (0.2, g["patlama"][1] + 0.3, "Vade Mecum", "Parçalarına ayrılıyor, sırayla yerine giriyor", None)
caps.append(intro)


def fade(t, a, b, d=0.25):
    return max(0.0, min(1.0, (t - a) / d, (b - t) / d))


def draw_caption(im, title, sub, step, alpha):
    w, h = im.size
    k = w / 720
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ft, fs = ImageFont.truetype(BOLD, int(27 * k)), ImageFont.truetype(REG, int(16 * k))
    pad = int(16 * k)
    tw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs))
    bw, bh = int(min(w - 2 * pad, tw + 2 * pad)), int(76 * k)
    x0, y0 = (w - bw) // 2, h - bh - int(30 * k)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(14 * k), fill=(24, 16, 10, int(205 * alpha)))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(14 * k), outline=GOLD + (int(230 * alpha),), width=max(1, int(1.5 * k)))
    d.text((w // 2, y0 + int(24 * k)), title, font=ft, fill=GOLD + (int(255 * alpha),), anchor="mm")
    d.text((w // 2, y0 + int(54 * k)), sub, font=fs, fill=CREAM + (int(240 * alpha),), anchor="mm")
    if step:
        fp = ImageFont.truetype(BOLD, int(15 * k))
        label = f"{step} / {total}"
        lw = d.textlength(label, font=fp) + 2 * pad
        d.rounded_rectangle((pad, pad, pad + lw, pad + int(34 * k)), radius=int(17 * k), fill=(24, 16, 10, int(205 * alpha)))
        d.text((pad + lw / 2, pad + int(17 * k)), label, font=fp, fill=GOLD + (int(255 * alpha),), anchor="mm")
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


frames = out.with_suffix("") .parent / (out.stem + "_kareler")
frames.mkdir(parents=True, exist_ok=True)
for f in range(1, N + 1):
    p = src / f"kare_{f:04d}.png"
    if not p.exists():
        raise SystemExit(f"eksik kare: {p.name}")
    t = (f - 1) / FPS
    im = Image.open(p).convert("RGB")
    best = max(caps, key=lambda c: fade(t, c[0], c[1]))
    a = fade(t, best[0], best[1])
    if a > 0:
        im = draw_caption(im, best[2], best[3], best[4], a)
    im.save(frames / f"k_{f:04d}.png")

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "k_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "slow",
                "-movflags", "+faststart", str(out)], check=True)
print("yazildi", out, f"{N / FPS:.1f} sn")
