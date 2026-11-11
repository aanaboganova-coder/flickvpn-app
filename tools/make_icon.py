#!/usr/bin/env python3
"""
Генерирует иконки приложения из brand.json.

Создаёт:
  assets/icon.png             — полная иконка 1024x1024 (для стора и старых Android)
  assets/icon_foreground.png  — прозрачный foreground для adaptive icon (Android 8+)
  assets/icon_monochrome.png  — одноцветный слой (Android 13+ themed icons)

Запуск:
  python tools/make_icon.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.exit("Нужен Pillow: python -m pip install pillow")


ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        color = mix(top, bottom, y / max(1, size - 1))
        for x in range(size):
            px[x, y] = color
    return img


def shield_points(cx: float, cy: float, w: float, h: float) -> list[tuple[float, float]]:
    """Щит: сверху плоская грань, снизу остриё."""
    left, right = cx - w / 2, cx + w / 2
    top, bottom = cy - h / 2, cy + h / 2
    shoulder = top + h * 0.18
    return [
        (cx, top),
        (right, shoulder),
        (right, cy + h * 0.10),
        (cx, bottom),
        (left, cy + h * 0.10),
        (left, shoulder),
    ]


def bolt_points(cx: float, cy: float, w: float, h: float) -> list[tuple[float, float]]:
    left, right = cx - w / 2, cx + w / 2
    top, bottom = cy - h / 2, cy + h / 2
    return [
        (cx + w * 0.16, top),
        (left - w * 0.06, cy + h * 0.02),
        (cx - w * 0.02, cy + h * 0.02),
        (cx - w * 0.16, bottom),
        (right + w * 0.06, cy - h * 0.04),
        (cx + w * 0.02, cy - h * 0.04),
    ]


def draw_logo(draw: ImageDraw.ImageDraw, size: int, scale: float, color: tuple[int, int, int, int]) -> None:
    cx = cy = size / 2
    w = size * 0.46 * scale
    h = size * 0.56 * scale

    shield = shield_points(cx, cy, w, h)
    draw.polygon(shield, fill=color)

    # Вырез-молния цветом фона (рисуем поверх щита прозрачным «ластиком»)
    # Для этого используем отдельный слой, поэтому здесь только контур.


def make_full(accent: tuple[int, int, int], background: tuple[int, int, int]) -> Image.Image:
    base = gradient(SIZE, mix(accent, (255, 255, 255), 0.05), mix(background, (0, 0, 0), 0.25))
    base = base.convert("RGBA")

    # мягкое свечение по центру
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((SIZE * 0.16, SIZE * 0.10, SIZE * 0.84, SIZE * 0.90), fill=(*accent, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    base = Image.alpha_composite(base, glow)

    logo = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ld = ImageDraw.Draw(logo)
    draw_logo(ld, SIZE, 1.0, (255, 255, 255, 255))

    # вырезаем молнию из щита: рисуем её цветом фона
    cx = cy = SIZE / 2
    bolt = bolt_points(cx, cy, SIZE * 0.17, SIZE * 0.30)
    ld.polygon(bolt, fill=(*mix(background, (0, 0, 0), 0.15), 255))

    base = Image.alpha_composite(base, logo)

    # скруглённая маска (для красоты в превью; Android/iOS всё равно маскируют сами)
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE, SIZE), radius=int(SIZE * 0.22), fill=255)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(base, (0, 0), mask)
    return out


def make_foreground(accent: tuple[int, int, int], monochrome: bool = False) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (255, 255, 255, 255) if monochrome else (255, 255, 255, 255)
    draw_logo(d, SIZE, 0.62, color)

    # молния «вырезается» прозрачностью
    cx = cy = SIZE / 2
    bolt = bolt_points(cx, cy, SIZE * 0.17 * 0.62, SIZE * 0.30 * 0.62)
    d.polygon(bolt, fill=(0, 0, 0, 0))
    return img


def main() -> None:
    brand_path = ROOT / "brand.json"
    brand = json.loads(brand_path.read_text(encoding="utf-8"))
    accent = hex_to_rgb(brand.get("accentColor", "#3B82F6"))
    background = hex_to_rgb(brand.get("backgroundColor", "#0B1220"))

    assets = ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    make_full(accent, background).save(assets / "icon.png")
    make_foreground(accent).save(assets / "icon_foreground.png")
    make_foreground(accent, monochrome=True).save(assets / "icon_monochrome.png")
    print(f"Готово: {assets}")


if __name__ == "__main__":
    main()
