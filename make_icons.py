#!/usr/bin/env python3
"""혈압 일지 PWA 아이콘 생성 (1024 초해상도로 그린 뒤 512/192로 축소)."""
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import math

S = 1024
SS = 2  # supersample factor on top of S
W = S * SS


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def vertical_gradient(size, top, bottom):
    g = Image.new("RGB", (1, size))
    px = g.load()
    for y in range(size):
        px[0, y] = lerp(top, bottom, y / (size - 1))
    return g.resize((size, size), Image.BILINEAR)


def heart_mask(size, cx, cy, width):
    """파라메트릭 하트 곡선으로 채운 마스크."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    pts = []
    # heart curve: x = 16 sin^3 t, y = 13cos t - 5cos2t - 2cos3t - cos4t
    steps = 720
    scale = width / 32.0  # 곡선 폭은 32 (x: -16..16)
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * scale, cy + y * scale - 0.6 * scale))
    d.polygon(pts, fill=255)
    return m


def pulse_points(cx, cy, width, amp):
    """심전도 맥박 라인 좌표."""
    x0, x1 = cx - width / 2, cx + width / 2
    w = x1 - x0
    pts = [
        (x0, cy),
        (x0 + 0.30 * w, cy),
        (x0 + 0.38 * w, cy - 0.35 * amp),
        (x0 + 0.46 * w, cy + 0.55 * amp),
        (x0 + 0.54 * w, cy - 1.00 * amp),
        (x0 + 0.62 * w, cy + 0.25 * amp),
        (x0 + 0.70 * w, cy),
        (x1, cy),
    ]
    return pts


def build():
    bg_top = (255, 255, 255)
    bg_bot = (255, 219, 229)  # 연분홍
    canvas = vertical_gradient(W, bg_top, bg_bot).convert("RGBA")

    # 둥근 사각형 안쪽만 남기고 바깥은 투명
    rmask = rounded_mask(W, radius=int(W * 0.235))
    canvas.putalpha(rmask)

    # 부드러운 안쪽 하이라이트
    hi = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.ellipse([-0.30 * W, -0.62 * W, 0.90 * W, 0.38 * W], fill=(255, 255, 255, 90))
    hi = hi.filter(ImageFilter.GaussianBlur(W * 0.06))
    canvas = Image.alpha_composite(canvas, Image.composite(hi, Image.new("RGBA", (W, W), (0, 0, 0, 0)), rmask))

    cx, cy = W / 2, W / 2
    hw = W * 0.50  # 하트 폭 (마스커블 안전영역 고려)

    # 하트 그림자
    shadow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    hm = heart_mask(W, cx, cy + W * 0.030, hw)
    sd = Image.new("RGBA", (W, W), (214, 70, 95, 62))
    shadow = Image.composite(sd, shadow, hm).filter(ImageFilter.GaussianBlur(W * 0.026))
    canvas = Image.alpha_composite(canvas, shadow)

    # 하트 본체 (코랄 레드 그라데이션)
    heart_grad = vertical_gradient(W, (255, 106, 128), (233, 42, 76)).convert("RGBA")
    canvas = Image.composite(heart_grad, canvas, hm)

    # 맥박 라인 (하트 안쪽에만 흰색으로)
    line_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line_layer)
    pts = pulse_points(cx, cy + W * 0.012, hw * 0.66, W * 0.085)
    ld.line(pts, fill=(255, 255, 255, 255), width=int(W * 0.032), joint="curve")
    # 라인 끝 둥글게
    for p in (pts[0], pts[-1], pts[1]):
        rr = W * 0.016
        ld.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=(255, 255, 255, 255))
    line_layer.putalpha(ImageChops.multiply(line_layer.getchannel("A"), hm))
    canvas = Image.alpha_composite(canvas, line_layer)

    # 살짝 선명하게
    canvas = canvas.filter(ImageFilter.UnsharpMask(radius=W * 0.004, percent=60, threshold=2))

    base = canvas.resize((S, S), Image.LANCZOS)
    for size in (512, 192):
        base.resize((size, size), Image.LANCZOS).save(f"work/bp-pwa/icon-{size}.png", "PNG", optimize=True)
    base.resize((512, 512), Image.LANCZOS).save("work/bp-pwa/icon-512.png", "PNG", optimize=True)


if __name__ == "__main__":
    build()
    print("icons done")
