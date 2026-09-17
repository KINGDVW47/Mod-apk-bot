"""
Patch: Bypass server-side subscription, plan, token, and credit checks.

Strategy:
  - Neutralize subscription/plan verification methods in smali
  - Bypass token validation and credit balance checks
  - Override billing/subscription status methods to return "premium"
  - Clear server-side paywall checks

This targets common patterns:
  - SharedPreferences subscription flags
  - HTTP response parsing for plan/subscription status
  - Billing library integration
  - Token validation endpoints
  - Credit/balance checking methods
"""
from __future__ import annotations

import re
from pathlib import Path

from utils.smali import find_all_smali_files


# Keywords that indicate subscription/plan/token/credit checks
_SUBSCRIPTION_KEYWORDS = [
    "isSubscribed", "isPremium", "isActive", "isPro", "isVIP",
    "getPlan", "checkPlan", "getSubscription", "checkSubscription",
    "isSubscriptionActive", "hasActivePlan", "isPlanActive",
    "checkPremium", "getPremiumStatus", "isPaidUser",
]

_TOKEN_KEYWORDS = [
    "getToken", "validateToken", "checkToken", "verifyToken",
    "isTokenValid", "getTokenCredits", "checkCredits",
    "getBalance", "checkBalance", "hasCredits", "getCreditBalance",
    "isTrialExpired", "isTrialActive", "getTrialStatus",
]

_BILLING_KEYWORDS = [
    "BillingClient", "Purchase", "SkuDetails", "BillingFlowParams",
    "querySkuDetailsAsync", "launchBillingFlow", "acknowledgePurchase",
    "subscribe", "purchase", "INAPP", "SUBS",
]

# SharedPreferences keys that commonly store subscription/plan status
_PREFS_PATTERNS = [
    "is_subscribed", "is_premium", "is_pro", "is_vip",
    "subscription_active", "plan_type", "user_plan",
    "token_valid", "has_credits", "credit_balance",
    "premium_status", "paid_user", "trial_active",
]


def apply(decompiled_dir: Path) -> dict:
    """
    Bypass server-side subscription, plan, token, and credit checks.
    Returns {files_changed: int, description: str}.
    """
    changed = 0
    smali_files = find_all_smali_files(decompiled_dir)

    # --- Pattern sets ---

    # 1. Methods that check subscription/plan — make them always return true
    sub_return_true = []
    for kw in _SUBSCRIPTION_KEYWORDS:
        sub_return_true.append((
            re.compile(
                rf'(\.method.*{re.escape(kw)}.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL | re.IGNORECASE,
            ),
            r'\1'
            r'    const/4 v0, 0x1\n'
            r'    return v0\n',
        ))

    # 2. Methods that check token/credit validity — make them always return true
    token_return_true = []
    for kw in _TOKEN_KEYWORDS:
        token_return_true.append((
            re.compile(
                rf'(\.method.*{re.escape(kw)}.*\n)'
                r'(.*?return.*\n)',
                re.DOTALL | re.IGNORECASE,
            ),
            r'\1'
            r'    const/4 v0, 0x1\n'
            r'    return v0\n',
        ))

    # 3. SharedPreferences getBoolean for subscription keys — force true
    prefs_patterns = []
    for key in _PREFS_PATTERNS:
        prefs_patterns.append((
            re.compile(
                rf'const-string\s+v\d+,\s*"{key}"\n'
                r'(.*?)'
                r'invoke.*SharedPreferences.*getBoolean.*\n'
                r'(\s*move-result.*\n)',
                re.DOTALL,
            ),
            rf'const-string v0, "{key}"\n'
            r'\1'
            r'const/4 v0, 0x1  # server bypass\n'
            r'\2',
        ))

    # 4. HTTP response subscription/plan parsing — return positive status
    http_patterns = [
        # JSON field checks for subscription status
        (re.compile(r'const-string\s+v\d+,\s*"subscribed"\s*'),
         'const-string v0, "subscribed"  # server bypass'),
        (re.compile(r'const-string\s+v\d+,\s*"is_active"\s*'),
         'const-string v0, "is_active"  # server bypass'),
        (re.compile(r'const-string\s+v\d+,\s*"plan"\s*'),
         'const-string v0, "plan"  # server bypass'),
        # Boolean comparison for "active" status — force true
        (re.compile(
            r'const/4\s+v\d+,\s*0x0\s*#.*(?:inactive|expired|free|trial)',
            re.IGNORECASE),
         'const/4 v0, 0x1  # forced active (server bypass)'),
    ]

    # 5. Billing — neutralize billing flow launch
    billing_patterns = [
        # Make billing queries return empty (no upsell)
        (re.compile(r'invoke.*BillingClient.*->querySkuDetails.*'),
         'return-void  # billing bypassed'),
        (re.compile(r'invoke.*BillingClient.*->launchBillingFlow.*'),
         'const/4 v0, 0x0\n    return v0  # billing bypassed'),
        (re.compile(r'invoke.*BillingClient.*->connect.*'),
         'return-void  # billing bypassed'),
        # Neutralize purchase result checks
        (re.compile(
            r'(\.method.*onPurchasesUpdated.*\n)'
            r'(.*?return.*\n)',
            re.DOTALL),
         r'\1    return-void  # billing bypassed\n'),
    ]

    # 6. Generic server validation bypass patterns
    generic_patterns = [
        # "unauthorized" or "forbidden" HTTP status checks — skip error path
        (re.compile(
            r'const/(?:16|32)\s+v\d+,\s*0x(?:191|193|194|195|1F[4-9A-F]|1F[3-9])\s*#.*(?:401|403|404|405|500)',
            re.IGNORECASE),
         'nop  # HTTP status bypass'),
        # Server response code comparison — skip error branches
        (re.compile(
            r'const/4\s+v\d+,\s*0x0\s*#.*(?:error|fail|denied|expired)',
            re.IGNORECASE),
         'const/4 v0, 0x1  # server bypass'),
    ]

    all_patterns = (
        sub_return_true + token_return_true + prefs_patterns
        + http_patterns + billing_patterns + generic_patterns
    )

    for sf in smali_files:
        try:
            content = sf.read_text(errors="replace")
            original = content

            for pattern, replacement in all_patterns:
                content = pattern.sub(replacement, content)

            if content != original:
                sf.write_text(content)
                changed += 1
        except OSError:
            continue

    # --- Also patch SharedPreferences XML default values ---
    prefs_xml = decompiled_dir / "res" / "xml" / "preferences.xml"
    if prefs_xml.exists():
        try:
            px_content = prefs_xml.read_text(errors="replace")
            for key in _PREFS_PATTERNS:
                px_content = re.sub(
                    rf'(<CheckBoxPreference[^>]*android:key="{key}"[^>]*?)'
                    rf'android:defaultValue="false"',
                    r'\1android:defaultValue="true"',
                    px_content,
                )
            prefs_xml.write_text(px_content)
        except OSError:
            pass

    return {
        "files_changed": changed,
        "description": (
            f"Server-side bypass: {changed} file(s) patched "
            f"(subscription, token, credits, billing)"
        ),
    }
