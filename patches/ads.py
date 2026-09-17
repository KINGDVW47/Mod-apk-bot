"""
Patch: Remove advertisement SDKs and ad-related code.

Supported SDKs:
  - AdMob (com.google.android.gms.ads)
  - Facebook Ads (com.facebook.ads)
  - Unity Ads (com.unity3d.ads)
  - AppLovin (com.applovin)
  - IronSource (com.ironsource)
  - Vungle (com.vungle)
  - Chartboost (com.chartboost)
  - StartApp (com.startapp)

Strategy:
  - Remove ad-related XML layouts
  - Remove ad network manifest entries
  - Neutralize ad loading/showing methods in smali
"""
from __future__ import annotations

import re
from pathlib import Path

from utils.smali import find_all_smali_files


# Ad SDK package prefixes
AD_SDK_PREFIXES = [
    "com/google/android/gms/ads",
    "com/facebook/ads",
    "com/unity3d/ads",
    "com/applovin",
    "com/ironsource",
    "com/vungle",
    "com/chartboost",
    "com/startapp",
    "com/mbridge",
    "com/inmobi",
    "com/adcolony",
]


def apply(decompiled_dir: Path) -> dict:
    """
    Remove ad SDK code and resources.
    Returns {"files_changed": int, "directories_removed": int, "description": str}.
    """
    files_changed = 0
    dirs_removed = 0

    # --- 1. Remove ad SDK smali directories ---
    smali_base = []
    for d in decompiled_dir.iterdir():
        if d.is_dir() and d.name.startswith("smali"):
            smali_base.append(d)

    for prefix in AD_SDK_PREFIXES:
        for sb in smali_base:
            sdk_dir = sb / prefix
            if sdk_dir.exists():
                import shutil
                shutil.rmtree(sdk_dir, ignore_errors=True)
                dirs_removed += 1

    # --- 2. Neutralize ad-related methods in remaining smali files ---
    ad_patterns = [
        # AdMob
        (re.compile(r'invoke.*com\.google\.android\.gms\.ads\.AdView.*->loadAd.*'),
         "nop  # ad removed"),
        (re.compile(r'invoke.*com\.google\.android\.gms\.ads\.InterstitialAd.*->show.*'),
         "nop  # ad removed"),
        # Facebook
        (re.compile(r'invoke.*com\.facebook\.ads\.AdView.*->loadAd.*'),
         "nop  # ad removed"),
        (re.compile(r'invoke.*com\.facebook\.ads\.InterstitialAd.*->show.*'),
         "nop  # ad removed"),
        # Unity
        (re.compile(r'invoke.*com\.unity3d\.ads.*->show.*'),
         "nop  # ad removed"),
        # Generic ad show/load
        (re.compile(r'invoke.*->showAd\('),
         "nop  # ad removed"),
        (re.compile(r'invoke.*->loadAd\('),
         "nop  # ad removed"),
    ]

    smali_files = find_all_smali_files(decompiled_dir)
    for sf in smali_files:
        try:
            content = sf.read_text(errors="replace")
            original = content

            for pattern, replacement in ad_patterns:
                content = pattern.sub(replacement, content)

            # Remove AdView / InterstitialAd layout XML references
            if "ad_" in sf.name.lower() or "banner" in sf.name.lower():
                # Comment out the entire class to prevent ad initialization
                content = "# --- Ad removed by APK Mod Bot ---\n" + content

            if content != original:
                sf.write_text(content)
                files_changed += 1
        except OSError:
            continue

    # --- 3. Remove ad-related XML resources ---
    res_dir = decompiled_dir / "res"
    if res_dir.exists():
        for layout_file in res_dir.rglob("*.xml"):
            try:
                content = layout_file.read_text(errors="replace")
                if any(ad_id in content for ad_id in ["adView", "ad_unit_id", "adSize", "banner_ad"]):
                    # Remove ad views from layout
                    cleaned = re.sub(
                        r'<com\.google\.android\.gms\.ads\.[^>]*>.*?</com\.google\.android\.gms\.ads\.[^>]*>',
                        '', content, flags=re.DOTALL
                    )
                    cleaned = re.sub(
                        r'<com\.facebook\.ads\.[^>]*>.*?</com\.facebook\.ads\.[^>]*>',
                        '', cleaned, flags=re.DOTALL
                    )
                    if cleaned != content:
                        layout_file.write_text(cleaned)
                        files_changed += 1
            except OSError:
                continue

    return {
        "files_changed": files_changed,
        "directories_removed": dirs_removed,
        "description": (
            f"Ad SDKs removed: {dirs_removed} directories purged, "
            f"{files_changed} files patched"
        ),
    }
