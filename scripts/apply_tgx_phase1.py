#!/usr/bin/env python3
"""Apply the narrowly-scoped TGX Studio Phase 1 branding patch to a clean NimarkoGram checkout."""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

def replace_once(relative_path, old, new, label):
    path = root / relative_path
    if not path.is_file():
        raise SystemExit(f"[ERROR] Required upstream file is missing: {relative_path}")
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[ERROR] {label}: expected exactly one match in {relative_path}, found {count}; refusing unsafe patch.")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"[OK] {label}")

replace_once(
    "TMessagesProj/src/main/java/app/nimarkogram/messenger/AppConfig.java",
    'public static final String APP_NAME = "NimarkoGram";',
    'public static final String APP_NAME = "TGX Studio";',
    "runtime app name",
)
replace_once(
    "TMessagesProj/src/main/res/values/strings.xml",
    '<string name="AppName">NimarkoGram</string>',
    '<string name="AppName">TGX Studio</string>',
    "launcher label",
)
replace_once(
    "TMessagesProj/src/main/res/values/strings.xml",
    '<string name="AppNameBeta">NimarkoGram Beta</string>',
    '<string name="AppNameBeta">TGX Studio Beta</string>',
    "beta label",
)
replace_once(
    "TMessagesProj_AppStandalone/build.gradle",
    "defaultConfig.applicationId = 'app.nimarkogram.messenger'",
    "defaultConfig.applicationId = 'app.tgxstudio.messenger'",
    "application ID",
)
manifest = "TMessagesProj/config/release/AndroidManifest_standalone.xml"
replace_once(manifest, 'android:icon="@mipmap/ic_launcher_sa"', 'android:icon="@mipmap/tgx_launcher"', "launcher icon")
replace_once(manifest, 'android:roundIcon="@mipmap/ic_launcher_sa"', 'android:roundIcon="@mipmap/tgx_launcher"', "round launcher icon")

color_path = root / "TMessagesProj/src/main/res/values/colors.xml"
colors = color_path.read_text(encoding="utf-8")
if colors.count("</resources>") != 1:
    raise SystemExit("[ERROR] Could not safely add TGX icon color.")
if 'name="tgx_icon_background"' not in colors:
    color_path.write_text(colors.replace("</resources>", '    <color name="tgx_icon_background">#0B1220</color>\n</resources>'), encoding="utf-8")

icon_dir = root / "TMessagesProj/src/main/res/mipmap-anydpi-v26"
icon_dir.mkdir(parents=True, exist_ok=True)
(icon_dir / "tgx_launcher.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/tgx_icon_background" />
    <foreground android:drawable="@drawable/tgx_launcher_foreground" />
</adaptive-icon>
""", encoding="utf-8")
foreground_dir = root / "TMessagesProj/src/main/res/drawable"
foreground_dir.mkdir(parents=True, exist_ok=True)
(foreground_dir / "tgx_launcher_foreground.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FF38BDF8"
        android:pathData="M24,27 C24,21 29,16 35,16 L73,16 C79,16 84,21 84,27 L84,61 C84,67 79,72 73,72 L54,72 L39,88 L39,72 L35,72 C29,72 24,67 24,61 Z" />
    <path
        android:fillColor="#FF0B1220"
        android:pathData="M37,33 L71,33 L71,41 L59,41 L59,61 L49,61 L49,41 L37,41 Z" />
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M37,33 L71,33 L71,41 L59,41 L59,61 L49,61 L49,41 L37,41 Z" />
</vector>
""", encoding="utf-8")
print("[OK] TGX adaptive launcher icon added (chat bubble + T monogram).")
print("[NOTE] This Phase 1 workflow currently changes app name, application ID, and launcher icon only; theme selector and splash redesign are not implemented by this patch.")
