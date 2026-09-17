"""
Smali helpers — find and manipulate smali files programmatically.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def find_launcher_activity_smali(decompiled_dir: Path) -> Optional[Path]:
    """
    Locate the smali file for the main launcher activity by parsing
    AndroidManifest.xml for the LAUNCHER intent-filter.
    """
    manifest = decompiled_dir / "AndroidManifest.xml"
    if not manifest.exists():
        return None

    text = manifest.read_text(errors="replace")

    # Find the launcher activity name from the LAUNCHER intent-filter
    # Pattern: action android:name="android.intent.action.MAIN"
    #          category android:name="android.intent.category.LAUNCHER"
    # We walk backwards from LAUNCHER to find the enclosing <activity>
    launcher_match = re.search(
        r'<activity[^>]*android:name="([^"]+)"[^>]*>.*?'
        r'android\.intent\.category\.LAUNCHER',
        text,
        re.DOTALL,
    )
    if not launcher_match:
        return None

    activity_name = launcher_match.group(1)

    # Handle relative names like ".MainActivity"
    if activity_name.startswith("."):
        # Try to find the package name
        pkg_match = re.search(r'package="([^"]+)"', text)
        if pkg_match:
            activity_name = pkg_match.group(1) + activity_name
        else:
            return None

    # Convert com.example.MainActivity → com/example/MainActivity.smali
    smali_rel = activity_name.replace(".", "/") + ".smali"

    # Search for the smali file in smali directories
    for smali_dir in decompiled_dir.iterdir():
        if smali_dir.is_dir() and smali_dir.name.startswith("smali"):
            candidate = smali_dir / smali_rel
            if candidate.exists():
                return candidate

    return None


def find_all_smali_files(decompiled_dir: Path) -> list[Path]:
    """Return all .smali files in the decompiled directory."""
    smali_files: list[Path] = []
    for smali_dir in decompiled_dir.iterdir():
        if smali_dir.is_dir() and smali_dir.name.startswith("smali"):
            smali_files.extend(smali_dir.rglob("*.smali"))
    return smali_files


def inject_toast_after_super(smali_path: Path, toast_text: str = "Modded by APK Bot") -> bool:
    """
    Inject a Toast.makeText(...).show() call in the smali file
    right after the invoke-super call in the onCreate method.
    Returns True if injection was successful.
    """
    content = smali_path.read_text(errors="replace")

    # Find the onCreate method and its invoke-super
    # Pattern for invoke-super in onCreate
    pattern = re.compile(
        r'(\.method.*onCreate.*\n)'
        r'(.*?invoke-super.*\n)',
        re.DOTALL,
    )

    match = pattern.search(content)
    if not match:
        return False

    # Build the Toast smali code
    toast_smali = _build_toast_smali(toast_text)

    # Insert after the invoke-super line
    insert_pos = match.end()
    new_content = content[:insert_pos] + toast_smali + "\n" + content[insert_pos:]

    smali_path.write_text(new_content)
    return True


def _build_toast_smali(text: str) -> str:
    """
    Build smali code equivalent to:
        Toast.makeText(this, "text", Toast.LENGTH_SHORT).show();
    """
    # We use a simple approach: create the string constant and invoke Toast
    return f"""
    # --- APK Mod Bot: Toast injection ---
    const-string v0, "{text}"
    const/4 v1, 0x0
    invoke-static {{p0, v0, v1}}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {{v0}}, Landroid/widget/Toast;->show()V
    # --- End Toast injection ---
"""


def patch_package_name(manifest_path: Path, new_label: str) -> bool:
    """
    Change the android:label in AndroidManifest.xml.
    """
    if not manifest_path.exists():
        return False

    content = manifest_path.read_text(errors="replace")

    # Replace android:label on the <application> tag
    new_content = re.sub(
        r'android:label="[^"]*"',
        f'android:label="{new_label}"',
        content,
        count=1,  # Only replace the first occurrence (application label)
    )

    manifest_path.write_text(new_content)
    return True


def patch_strings_xml(strings_path: Path, app_name: str,
                       mod_name: str = "", mod_email: str = "",
                       mod_phone: str = "") -> bool:
    """
    Edit res/values/strings.xml to:
      - Update app_name string
      - Add mod_name, mod_email, mod_phone custom resources
    """
    if not strings_path.exists():
        return False

    content = strings_path.read_text(errors="replace")

    # Update existing app_name
    content = re.sub(
        r'(<string name="app_name">)[^<]*(</string>)',
        rf'\g<1>{app_name}\g<2>',
        content,
    )

    # Remove existing custom entries if present
    for name in ("mod_name", "mod_email", "mod_phone"):
        content = re.sub(rf'\s*<string name="{name}">[^<]*</string>', '', content)

    # Add new custom resources before closing </resources>
    custom = ""
    if mod_name:
        custom += f'\n    <string name="mod_name">{mod_name}</string>'
    if mod_email:
        custom += f'\n    <string name="mod_email">{mod_email}</string>'
    if mod_phone:
        custom += f'\n    <string name="mod_phone">{mod_phone}</string>'

    if custom:
        content = content.replace("</resources>", f"{custom}\n</resources>")

    strings_path.write_text(content)
    return True
