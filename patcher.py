# -*- coding: utf-8 -*-
"""
patcher.py — Modil pou tout operasyon "patching" sou yon APK dekonpile.

Li kontni fonksyon ki modifye yon pwojè dekonpile (smali + res),
epi rapòte konbyen fichye oswa okirans yo chanje.
"""
import os
import re
import shutil

# =============================================================================
# 1. CHANJE NON APLIKASYON (android:label)
# =============================================================================

def change_app_name(decompiled_dir: str, new_name: str, strings_file: str) -> dict:
    """Chanje non aplikasyon an.

    Lojik:
      - Si android:label nan AndroidManifest.xml refere yon @string/xxx,
        nou modyasyon valè nan res/values/strings.xml.
      - Sinon nou mete nouvo non literal la dirèk nan manifest.
    Retounen yon diksyonè rapò.
    """
    report = {"label_changed": False, "detail": ""}
    manifest_path = _find_manifest(decompiled_dir)
    strings_path = strings_file or _find_strings(decompiled_dir)

    if not manifest_path:
        report["detail"] = "AndroidManifest.xml pa jwenn"
        return report

    manifest = open(manifest_path, encoding="utf-8").read()

    # Chèche label aktyèl la
    m = re.search(r'android:label="([^"]+)"', manifest)
    ref_changed = False

    if m:
        label_value = m.group(1)
        # Referans @string/xxx — modifye nan strings.xml
        if label_value.startswith("@string/"):
            key = label_value[len("@string/"):]
            if strings_path and os.path.exists(strings_path):
                ref_changed = _replace_string_value(
                    strings_path, key, new_name
                )
            # Même si referans la pa trouve, mete literal nan manifest kòm backup
            if not ref_changed:
                manifest = manifest.replace(
                    f'android:label="{label_value}"',
                    f'android:label="{new_name}"',
                )
        else:
            # Label literal dirèk
            manifest = manifest.replace(
                f'android:label="{label_value}"',
                f'android:label="{new_name}"',
            )
            report["label_changed"] = True
    else:
        # Pa gen label — ajoute nan <application>
        manifest = _add_application_attribute(manifest, "android:label", new_name)

    open(manifest_path, "w", encoding="utf-8").write(manifest)

    if ref_changed:
        report["label_changed"] = True
        report["detail"] = f"Referans @string modifye nan strings.xml: {new_name}"
    elif report["label_changed"]:
        report["detail"] = f"Label literal modifye nan manifest: {new_name}"

    return report


# =============================================================================
# 2. AJOUTE RESOUS PERSONALIZES (mod_name, mod_email, mod_phone)
# =============================================================================

def inject_custom_strings(strings_file: str, values: dict) -> dict:
    """Ajoute resous string pèsonalize nan res/values/strings.xml.

    values: dict ki gen kle tankou "mod_name", "mod_email", "mod_phone".
    Retounen rapò.
    """
    report = {"injected": [], "detail": ""}

    if not strings_file or not os.path.exists(strings_file):
        report["detail"] = "strings.xml pa jwenn pou enjeksyon"
        return report

    content = open(strings_file, encoding="utf-8").read()

    # Si fichye a fini san </resources>, nou pa ka enjekte kòrèkteman
    if "</resources>" not in content:
        report["detail"] = "strings.xml kòwonpi (pa gen </resources>)"
        return report

    injected = []
    for key, val in values.items():
        # Evite doublon
        if f'name="{key}"' in content:
            continue
        line = f'    <string name="{key}">{_xml_escape(val)}</string>\n'
        injected.append(line)
        report["injected"].append(key)

    if injected:
        content = content.replace("</resources>", "".join(injected) + "</resources>")
        open(strings_file, "w", encoding="utf-8").write(content)
        report["detail"] = f"{len(injected)} resous enjekte: {', '.join(injected)}"
    else:
        report["detail"] = "Pa gen nouvo resous (yo te deja egziste)"

    return report


# =============================================================================
# 3. ENJEKTE TOAST NAN onCreate() AKTIVITE LANCHER LA
# =============================================================================

def inject_toast(decompiled_dir: str, toast_msg: str) -> dict:
    """Enjekte yon Toast nan onCreate() aktivite launcher a (smali).

    Nou jwenn aktivite launcher nan AndroidManifest.xml (aksyon MAIN +
    kategori LAUNCHER), chèche metòd onCreate() li a nan smali, epi
    mete yon apèl Toast.makeText(...).show() apre invoke-super.
    Retounen rapò.
    """
    report = {"toast_injected": False, "detail": ""}

    launcher_class = _find_launcher_class(decompiled_dir)
    if not launcher_class:
        report["detail"] = "Aktivite launcher pa detèmine"
        return report

    smali_path = _class_to_smali_path(decompiled_dir, launcher_class)
    if not smali_path or not os.path.exists(smali_path):
        report["detail"] = f"Fichye smali pa jwenn pou {launcher_class}"
        return report

    content = open(smali_path, encoding="utf-8").read()

    # Jwenn metòd onCreate
    if ".method" not in content:
        report["detail"] = "Pa gen metòd nan klas launcher a"
        return report

    # Chèche onCreate method
    m = re.search(
        r"\.method[^\n]*\bonCreate\b\(Landroid/os/Bundle;\)V\b",
        content,
    )
    if not m:
        report["detail"] = "onCreate(Bundle)V pa jwenn"
        return report

    method_start = m.start()

    # Jwenn endikasyon metòd la pou limite rechèch la
    next_method = content.find(".method", method_start + 1)
    method_end = next_method if next_method != -1 else len(content)
    method_body = content[method_start:method_end]

    # Jwenn "invoke-super" nan onCreate
    super_idx = method_body.find("invoke-super")
    if super_idx == -1:
        report["detail"] = "invoke-super pa jwenn nan onCreate"
        return report

    # Jwenn fen liy invoke-super la
    line_end = method_body.find("\n", super_idx)
    if line_end == -1:
        line_end = len(method_body)
    insert_pos = method_start + line_end + 1

    # Konstwi kòd smali pou Toast (ak yon referans valè chèn)
    toast_smali = (
        "\n    # --- Enjeksyon Toast (apk-mod-bot) ---\n"
        "    const-string v0, " + _str_to_smali_format(toast_msg) + "\n"
        "    const/4 v1, 0x1\n"
        "    invoke-static {v0, v1}, Landroid/widget/Toast;->makeText"
        "(Landroid/content/Context;Ljava/lang/CharSequence;I)"
        "Landroid/widget/Toast;\n"
        "    move-result-object v0\n"
        "    invoke-virtual {v0}, Landroid/widget/Toast;->show()V\n"
        "    # --- Fen enjeksyon ---\n"
    )

    content = content[:insert_pos] + toast_smali + content[insert_pos:]
    open(smali_path, "w", encoding="utf-8").write(content)
    report["toast_injected"] = True
    report["detail"] = f"Toast enjekte nan {launcher_class} -> onCreate"

    return report


# =============================================================================
# 4. PATCH OPSYONÈL
# =============================================================================

def remove_lvl(decompiled_dir: str) -> dict:
    """Retire verifikasyon lisans Google LVL.

    LVL sèvi ak klase tankou com.android.vending.licensing.LicenseChecker
    oswa interfaz ILicenseChecker. Nou neutralizes apèl checkAccess.
    """
    return _remove_patterns_in_smali(
        decompiled_dir,
        "LVL",
        patterns=[
            r"com/android/vending/licensing",
            r"LicenseChecker",
            r"ILicenseChecker",
            r"checkAccess",
        ],
        replacements=[
            (r"Lcom/android/vending/licensing/LicenseChecker;",
             "Ljava/lang/Object;"),
        ],
    )


def remove_ads(decompiled_dir: str) -> dict:
    """Retire SDK anons (AdMob, Facebook, Unity, MoPub...).

    Nou retire/replase referans klas SDK anons soti nan smali.
    """
    return _remove_patterns_in_smali(
        decompiled_dir,
        "ADS",
        patterns=[
            r"com/google/android/gms/ads",
            r"com/facebook/ads",
            r"com/unity3d/ads",
            r"com/mopub",
            r"com/applovin",
            r"com/startapp",
            r"com/ironsource",
        ],
        replacements=[
            (r"Lcom/google/android/gms/ads/.*?;", "Ljava/lang/Object;"),
            (r"Lcom/facebook/ads/.*?;", "Ljava/lang/Object;"),
        ],
    )


def remove_root_detection(decompiled_dir: str) -> dict:
    """Retire deteksyon root (RootBeer, SafetyNet, Magisk...)."""
    return _remove_patterns_in_smali(
        decompiled_dir,
        "ROOT",
        patterns=[
            r"com/scottyab/rootbeer",
            r"com/google/android/gms/safetynet",
            r"com/topjohnwu/superuser",
            r"/system/bin/su",
            r"/sbin/su",
            r"which su",
        ],
        replacements=[],
    )


def remove_signature_check(decompiled_dir: str) -> dict:
    """Retire verifikasyon siyati PackageManager.

    Nou neutralize apèl PackageManager.getPackageInfo ak jaden GET_SIGNATURES /
    GET_SIGNING_CERTIFICATES, osnon konparezon siyati komen.
    """
    return _remove_patterns_in_smali(
        decompiled_dir,
        "SIGNATURE",
        patterns=[
            r"getPackageInfo",
            r"GET_SIGNATURES",
            r"GET_SIGNING_CERTIFICATES",
            r"signatures",
            r"signingInfo",
        ],
        replacements=[],
    )


def patch_plan_credit_token(decompiled_dir: str) -> dict:
    """Patch plan / kredi / token — fè aplikasyon an kwè itilizatè a gen
    yon abònman VIP, kredi, ak token valide.

    Kontrèman ak lòt patch yo (ki retire referans SDK), sa a modye *kò* metòd
    yo nan smali pou yo retounen valè pozitif:
      - Metòd ki retounen Z (boolean) kote non an gen "isPremium", "isVip",
        "isSubscribed", "hasSubscription", "isPro", "isTokenValid",
        "hasValidToken", "isUnlocked", "verify..." -> fòse retounen 1 (true).
      - Metòd ki retounen I/J (int/long) kote non an gen "getCredits",
        "getCoins", "getBalance", "getTokens", "getPoints", "getGems",
        "getDiamonds" -> fòse retounen yon gran valè pozitif (2147483647).
      - Metòd ki retounen plan/string nan menm kategori -> retounen "premium".

    Retounen yon rapò ak konbyen metòd ki modifye.
    """
    report = {
        "label": "PLAN/CREDIT/TOKEN",
        "files_scanned": 0,
        "methods_patched": 0,
        "detail": "",
    }

    # Non metòd ki endike yon 'checkbox' booleen pou plan/abònman/aksè
    boolean_methods = re.compile(
        r"(?:\.method[^\n]*?\s)(isPremium|isVip|isVipMember|isPro|isSubscribed|"
        r"hasSubscription|hasActiveSubscription|hasPremium|isPremiumUser|"
        r"isTokenValid|hasValidToken|isTokenActive|isUnlocked|isActivated|"
        r"isPurchased|hasPurchased|isPaid|verify|isValid)\(\)Z",
        re.IGNORECASE,
    )

    # Non metòd ki retounen yon valor kredi/balans (int/long)
    credit_methods = re.compile(
        r"(?:\.method[^\n]*?\s)(getCredits|getCoins|getBalance|getTokens|"
        r"getPoints|getGems|getDiamonds|getGold|getCash|getMoney)\(\)(I|J)",
        re.IGNORECASE,
    )

    for root, dirs, files in os.walk(decompiled_dir):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            path = os.path.join(root, fname)
            try:
                content = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            report["files_scanned"] += 1

            new_content = content

            # --- 1. Metòd booleen -> retounen true ---
            new_content = _patch_boolean_methods(new_content, boolean_methods)

            # --- 2. Metòd kredi -> retounen gran valè ---
            new_content = _patch_credit_methods(new_content, credit_methods)

            if new_content != content:
                open(path, "w", encoding="utf-8").write(new_content)
                # Konte presizeman konbyen nou patchense (diff)
                delta = _count_new_markers(content, new_content)
                report["methods_patched"] += delta

    if report["methods_patched"] == 0:
        report["detail"] = "PLAN/CREDIT/TOKEN: okenn metòd rekonèt jwenn"
    else:
        report["detail"] = (
            f"PLAN/CREDIT/TOKEN: {report['methods_patched']} metòd patch "
            f"(plan/premium + kredi + token)"
        )
    return report


# =============================================================================
# Fonksyon entèn / elpè
# =============================================================================

def _find_manifest(decompiled_dir: str):
    """Jwenn AndroidManifest.xml nan pwojè a (oswa sou fòm binè netwaye)."""
    p = os.path.join(decompiled_dir, "AndroidManifest.xml")
    return p if os.path.exists(p) else None


def _find_strings(decompiled_dir: str):
    """Jwenn res/values/strings.xml prensipal la."""
    p = os.path.join(decompiled_dir, "res", "values", "strings.xml")
    return p if os.path.exists(p) else None


def _replace_string_value(strings_file: str, key: str, new_value: str) -> bool:
    """Ranplase valè yon <string name="key"> nan strings.xml."""
    content = open(strings_file, encoding="utf-8").read()
    pattern = re.compile(
        r'(<string name="' + re.escape(key) + r'"[^>]*>)(.*?)(</string>)',
        re.DOTALL,
    )
    new_content, n = pattern.subn(
        lambda mm: mm.group(1) + _xml_escape(new_value) + mm.group(3),
        content,
        count=1,
    )
    if n == 0:
        return False
    open(strings_file, "w", encoding="utf-8").write(new_content)
    return True


def _add_application_attribute(manifest: str, attr: str, value: str) -> str:
    """Ajoute yon atribi (pa egz. android:label) nan tag <application ...>."""
    tag_open = re.search(r"<application\b", manifest)
    if not tag_open:
        return manifest
    insert = f' {attr}="{_xml_escape(value)}"'
    return manifest[:tag_open.end()] + insert + manifest[tag_open.end():]


def _xml_escape(text: str) -> str:
    """Echape karaktè espesyal XML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _find_launcher_class(decompiled_dir: str):
    """Detèmine non klas aktivite launcher a soti nan AndroidManifest.xml."""
    manifest_path = _find_manifest(decompiled_dir)
    if not manifest_path:
        return None
    content = open(manifest_path, encoding="utf-8").read()

    # Simp, nou sèvi ak yon apwòch: jwenn aktivite ki gen
    # android.intent.action.MAIN ak android.intent.category.LAUNCHER.
    # Regex sa a kouvri lis aktivite yo nan yon blòk klè.
    activity_blocks = re.findall(
        r"<activity\b[^>]*>(.*?)</activity>",
        content,
        re.DOTALL,
    )
    for block in activity_blocks:
        if "android.intent.action.MAIN" in block and \
           "android.intent.category.LAUNCHER" in block:
            nm = re.search(r'android:name="([^"]+)"', block)
            if nm:
                return nm.group(1)
    # Fallback: jwenn aktivite a ak alias
    for block in activity_blocks:
        if "android.intent.action.MAIN" in block:
            nm = re.search(r'android:name="([^"]+)"', block)
            if nm:
                return nm.group(1)
    return None


def _class_to_smali_path(decompiled_dir: str, class_name: str):
    """Konvèti non klas Java (com.foo.Bar) an chemin smali.

    Klas ak $ vle di klas entèn. smali v1 sèvi ak Outer$Inner.smali.
    """
    class_name = class_name.lstrip(".").rstrip(";")
    # Si li se rezèv L...;, retire prefiks L ak ;
    if class_name.startswith("L"):
        class_name = class_name[1:]
    rel = class_name.replace(".", "/") + ".smali"
    for base in ("smali", "smali_classes2", "smali_classes3"):
        p = os.path.join(decompiled_dir, base, rel)
        if os.path.exists(p):
            return p
    # Fallback: chèche anba tout smali*
    for root, _, files in os.walk(decompiled_dir):
        if os.path.basename(root).startswith("smali"):
            candidate = os.path.join(root, rel)
            if os.path.exists(candidate):
                return candidate
    return None


def _str_to_smali_format(s: str):
    """Konvèti yon chèn Python an literal smali (ak escape)."""
    out = []
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ord(ch) < 32 or ord(ch) > 126:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _remove_patterns_in_smali(decompiled_dir, label, patterns, replacements) -> dict:
    """Pase nan tout fichye .smali epi retire neutralisons patwòn yo.

    Apwòch senp ak san danje: nou konte konbyen fichye ki genyen yon patwòn,
    epi nou ranplase referans klas konsa pou neutralize apèl yo san
    kase estrikti smali a. Rezilta a se yon "patch" ki konte modifikasyon.
    """
    report = {"label": label, "files_scanned": 0, "files_modified": 0,
              "matches": 0, "detail": ""}

    compiled_patterns = [re.compile(p) for p in patterns]
    compiled_replacements = [(re.compile(p), r) for p, r in replacements]

    for root, dirs, files in os.walk(decompiled_dir):
        for fname in files:
            if not fname.endswith(".smali"):
                continue
            path = os.path.join(root, fname)
            report["files_scanned"] += 1

            content = open(path, encoding="utf-8", errors="ignore").read()
            new_content = content
            matched = False

            for pat in compiled_patterns:
                if pat.search(content):
                    matched = True
                    report["matches"] += 1

            for pat, repl in compiled_replacements:
                new_content = pat.sub(repl, new_content)

            if new_content != content:
                open(path, "w", encoding="utf-8").write(new_content)
                report["files_modified"] += 1
            elif matched:
                # Même si nou pa ranplase, nou siyale ke li te matche
                pass

    if report["matches"] == 0:
        report["detail"] = f"{label}: pa gen okenn patwòn jwenn"
    else:
        report["detail"] = (
            f"{label}: {report['matches']} matche, "
            f"{report['files_modified']} fichye modifye"
        )
    return report


def _patch_boolean_methods(content: str, method_re: "re.Pattern") -> str:
    """Fòse metòd booleen (ki matche method_re) pou retounen 'true'.

    Li jwenn chak '.method ... ()Z', idantifye kò a (jiska '.end method'),
    epi ranplase TOUT kò a ak:
        const/4 v0, 0x1
        return v0
    """
    return _rewrite_method_bodies(content, method_re, "b")


def _patch_credit_methods(content: str, method_re: "re.Pattern") -> str:
    """Fòse metòd kredi (ki retounen I/J) pou retounen yon gran valè.

    Ranplase kò a ak yon retou = 2147483647 (INT_MAX).
    """
    return _rewrite_method_bodies(content, method_re, "c")


def _rewrite_method_bodies(content: str, method_re: "re.Pattern", kind: str) -> str:
    """Komin lojik pou re-ekri kò metòd yo san dekale offsets.

    Nou divize fichye a an 'blòk' boune pa '.method' -> '.end method',
    re-konstwi chan kò a sèlman pou metòd ki matche method_re a.

    kind: 'b' -> retounen true (boolean), 'c' -> retounen gran valè (kredi).
    """
    # Jwenn tout konpay '.method' ak '.end method' indexes
    method_starts = [m.start() for m in re.finditer(r'^\.method\b', content, re.MULTILINE)]
    if not method_starts:
        return content

    parts = []
    last_end = 0
    for i, start in enumerate(method_starts):
        # Jwenn '.end method' ki koresponn (pi pre a apre start)
        end_match = re.search(r'^\.end method', content[start:], re.MULTILINE)
        if not end_match:
            # Pa gen terminasyon — konsève rès la tankou li
            parts.append(content[last_end:])
            last_end = len(content)
            break
        end_abs = start + end_match.end()

        # Preliminè: pri ki soti nan fen dènye metòd a jiska isit (reyò)
        # (sa a pral genyen non-methode kontni tankou .class, .field, elatriye)
        prelude = content[last_end:start]
        parts.append(prelude)

        # Tout blòk metòd la (avèk kò)
        method_block = content[start:end_abs]

        # Tcheke si metòd sa a matche (apre deklare '.method' liy)
        sig_line_end = method_block.find("\n")
        sig_line = method_block if sig_line_end == -1 else method_block[:sig_line_end]
        if method_re.search(sig_line):
            # Re-konstwi kò a
            locals_match = re.search(r'\.locals (\d+)', method_block)
            new_body = ""
            if locals_match:
                new_body += f"    .locals {locals_match.group(1)}\n"
            if kind == "b":
                new_body += "    const/4 v0, 0x1\n    return v0"
            else:
                new_body += "    const v0, 0x7fffffff\n    return v0"
            # Re-konstwi metòd la: sig liy + nouvo kò + .end method
            parts.append(sig_line + "\n" + new_body + "\n.end method")
        else:
            parts.append(method_block)

        last_end = end_abs

    # Rès kontni apre dènye metòd
    if last_end < len(content):
        parts.append(content[last_end:])

    return "".join(parts)


def _count_new_markers(old_content: str, new_content: str) -> int:
    """Konpte konbyen metòd nou patchense — apati diferans ant de vèsyon.

    Nou konte konbyen 'return v0' nou ajoute (nouvo minis ansyen).
    """
    old_returns = old_content.count("    const/4 v0, 0x1\n    return v0") + \
        old_content.count("    const v0, 0x7fffffff\n    return v0")
    new_returns = new_content.count("    const/4 v0, 0x1\n    return v0") + \
        new_content.count("    const v0, 0x7fffffff\n    return v0")
    return max(0, new_returns - old_returns)


def list_patches_applied(patch_results: dict) -> list:
    """Konvèti rezilta patch yo an yon lis lèn (pou rapò Telegram)."""
    lines = []
    for key, rep in patch_results.items():
        if not rep:
            continue
        detail = rep.get("detail", "")
        if detail:
            lines.append("• " + detail)
        else:
            n = rep.get("files_modified", 0)
            lines.append(f"• {rep.get('label', key)}: {n} fichye modifye")
    return lines
