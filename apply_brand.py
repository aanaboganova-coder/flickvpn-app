#!/usr/bin/env python3
"""
Применяет брендинг к исходникам open-source клиентов.

Android: 2dust/v2rayNG (VLESS + Reality, GPLv3)
iOS:     SagerNet/sing-box-for-apple (GPLv3)

Примеры:
  python apply_brand.py --platform android --path build/upstream
  python apply_brand.py --platform ios     --path build/sfi

Скрипт меняет только имя, applicationId, акцентный цвет и иконки.
Логика работы приложения не затрагивается.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Нужен Pillow: python -m pip install pillow")


ROOT = Path(__file__).resolve().parent
ANDROID_DENSITIES = {
    "mdpi": 1.0,
    "hdpi": 1.5,
    "xhdpi": 2.0,
    "xxhdpi": 3.0,
    "xxxhdpi": 4.0,
}


def hex_to_argb(value: str) -> str:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) == 8:
        return "0x" + value.upper()
    return "0xFF" + value.upper()


def load_brand(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("appName", "androidAppId", "accentColor", "backgroundColor"):
        if not data.get(key):
            sys.exit(f"В brand.json не задано поле {key}")
    return data


def patch_text(path: Path, replacements: list[tuple[str, str]], *, regex: bool = False) -> int:
    if not path.exists():
        print(f"  ! пропуск (нет файла): {path}")
        return 0
    text = path.read_text(encoding="utf-8")
    original = text
    count = 0
    for pattern, repl in replacements:
        if regex:
            text, n = re.subn(pattern, repl, text)
        else:
            n = text.count(pattern)
            text = text.replace(pattern, repl)
        count += n
    if text != original:
        path.write_text(text, encoding="utf-8")
    return count


# --------------------------------------------------------------------- Android
def resize(src: Path, dst: Path, size: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
        img.save(dst, "PNG")


def brand_android(project: Path, brand: dict) -> None:
    root = project / "V2rayNG" if (project / "V2rayNG").exists() else project
    app = root / "app"
    if not (app / "build.gradle.kts").exists():
        sys.exit(f"Не похоже на v2rayNG: {root}")

    name = brand["appName"]
    app_id = brand["androidAppId"]
    accent = hex_to_argb(brand["accentColor"])
    background = brand["backgroundColor"]

    print(f"Android: {root}")
    print(f"  имя: {name} | id: {app_id} | accent: {accent}")

    # 1. applicationId + versionName
    n = patch_text(
        app / "build.gradle.kts",
        [
            (r'applicationId\s*=\s*"[^"]*"', f'applicationId = "{app_id}"'),
            (r'versionName\s*=\s*"[^"]*"', f'versionName = "{brand.get("versionName", "1.0.0")}"'),
        ],
        regex=True,
    )
    print(f"  build.gradle.kts: изменено {n}")

    # 2. app_name во всех локалях + упоминания v2rayNG в строках
    strings = 0
    for path in (app / "src" / "main" / "res").glob("values*/strings.xml"):
        strings += patch_text(
            path,
            [
                (r'(<string\s+name="app_name"[^>]*>).*?(</string>)', rf"\g<1>{name}\g<2>"),
                (r"v2rayNG", name),
            ],
            regex=True,
        )
    print(f"  strings.xml: изменено {strings}")

    # 3. акцентный цвет в Compose-теме
    n = patch_text(
        app / "src/main/java/com/v2ray/ang/ui/compose/Theme.kt",
        [(r"0xFF[fF]97910", accent)],
        regex=True,
    )
    print(f"  Theme.kt: изменено {n}")

    # 4. цвет фона adaptive icon
    n = patch_text(
        app / "src/main/res/values/ic_launcher_background.xml",
        [(r"(<color\s+name=\"ic_launcher_background\">).*?(</color>)", rf"\g<1>{background}\g<2>")],
        regex=True,
    )
    print(f"  ic_launcher_background.xml: изменено {n}")

    # 5. иконки
    icon = ROOT / "assets" / "icon.png"
    foreground = ROOT / "assets" / "icon_foreground.png"
    if not icon.exists():
        sys.exit(f"Нет {icon}. Сначала запусти tools/make_icon.py")
    res = app / "src/main/res"
    for density, factor in ANDROID_DENSITIES.items():
        launcher = int(48 * factor)
        fg = int(108 * factor)
        resize(icon, res / f"mipmap-{density}" / "ic_launcher.png", launcher)
        resize(icon, res / f"mipmap-{density}" / "ic_launcher_round.png", launcher)
        resize(foreground, res / f"mipmap-{density}" / "ic_launcher_foreground.png", fg)
    resize(icon, app / "src/main/ic_launcher-web.png", 512)
    print("  иконки: обновлены")

    print("Готово (Android).")


# ------------------------------------------------------------------------- iOS
def brand_ios(project: Path, brand: dict) -> None:
    if not (project / "SFI").is_dir():
        sys.exit(f"Не похоже на sing-box-for-apple: {project}")

    name = brand["appName"]
    accent = brand["accentColor"].strip().lstrip("#")
    icon = ROOT / "assets" / "icon.png"

    print(f"iOS: {project}")
    print(f"  имя: {name} | bundle: {brand.get('iosBundleId')} | accent: #{accent}")

    # 1. Иконки приложения (SFI использует одиночные 1024px)
    appicon = project / "SFI/Assets.xcassets/AppIcon.appiconset"
    if not icon.exists():
        sys.exit(f"Нет {icon}. Сначала запусти tools/make_icon.py")
    if appicon.is_dir():
        resize(icon, appicon / "1024.png", 1024)
        resize(icon, appicon / "1024-dark.png", 1024)
        monochrome = ROOT / "assets" / "icon_monochrome.png"
        resize(monochrome if monochrome.exists() else icon, appicon / "1024-tinted.png", 1024)
        print("  AppIcon: обновлены 1024/1024-dark/1024-tinted")
    else:
        print("  ! AppIcon.appiconset не найден")

    # 2. Акцентный цвет
    accent_file = project / "SFI/Assets.xcassets/AccentColor.colorset/Contents.json"
    if accent_file.parent.is_dir():
        red = int(accent[0:2], 16) / 255
        green = int(accent[2:4], 16) / 255
        blue = int(accent[4:6], 16) / 255
        accent_file.write_text(
            json.dumps(
                {
                    "colors": [
                        {
                            "color": {
                                "color-space": "srgb",
                                "components": {
                                    "alpha": "1.000",
                                    "blue": f"{blue:.3f}",
                                    "green": f"{green:.3f}",
                                    "red": f"{red:.3f}",
                                },
                            },
                            "idiom": "universal",
                        }
                    ],
                    "info": {"author": "xcode", "version": 1},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print("  AccentColor: обновлён")

    # 3. Отображаемое имя (если Xcode берёт его из Info.plist)
    plist = project / "SFI/Info.plist"
    if plist.exists():
        text = plist.read_text(encoding="utf-8")
        if "CFBundleDisplayName" not in text:
            text = text.replace(
                "<dict>\n",
                "<dict>\n\t<key>CFBundleDisplayName</key>\n"
                f"\t<string>{name}</string>\n"
                "\t<key>CFBundleName</key>\n"
                f"\t<string>{name}</string>\n",
                1,
            )
            plist.write_text(text, encoding="utf-8")
            print("  Info.plist: добавлено CFBundleDisplayName")

    print("Готово (iOS). Bundle ID задаётся при сборке: BASE_PACKAGE_IDENTIFIER.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Брендирование VPN-клиентов")
    parser.add_argument("--platform", choices=["android", "ios"], required=True)
    parser.add_argument("--path", required=True, help="каталог с исходниками upstream")
    parser.add_argument("--brand", default=str(ROOT / "brand.json"))
    args = parser.parse_args()

    brand = load_brand(Path(args.brand))
    project = Path(args.path).resolve()

    if args.platform == "android":
        brand_android(project, brand)
    else:
        brand_ios(project, brand)


if __name__ == "__main__":
    main()
