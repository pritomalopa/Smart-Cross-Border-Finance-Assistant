"""Security & compliance guardrails — this file is 30% of your score. Keep it explicit."""
from __future__ import annotations
import re

INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"ignore.*system prompt",
    r"disregard.*policy",
    r"jailbreak",
    r"dan mode",
    r"transfer all (money|funds|balance)",
    r"send everything",
    r"delete (all )?(logs|audit|history)",
    r"reveal (system|secret|password|api key)",
    r"show me.*other users",
    r"act as .* (admin|root|bank)",
    r"override.*limit",
]

PII_RE = [
    (re.compile(r"\b\d{6}\d{6,12}\b"), "[ID_MASKED]"),
    (re.compile(r"\b1[3-9]\d{9}\b"), "[PHONE_MASKED]"),
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"), "[EMAIL_MASKED]"),
]

class BlockedError(Exception):
    pass

def detect_injection(text: str) -> str | None:
    low = text.lower()
    for p in INJECTION_PATTERNS:
        if re.search(p, low):
            return f"prompt-injection pattern matched: `{p}`"
    # classic "do X and don't ask" coercion
    if "don't ask" in low and "transfer" in low:
        return "coerced transfer without confirmation"
    if "without confirmation" in low and "transfer" in low:
        return "transfer without confirmation requested"
    return None

def mask_pii(text: str) -> str:
    for rx, rep in PII_RE:
        text = rx.sub(rep, text)
    return text

def check_transfer(amount_cny: float, to: str, store, confirmed: bool = False) -> None:
    """Permission-tier + limit checks. Raises BlockedError on violation."""
    if amount_cny <= 0:
        raise BlockedError("amount must be positive")
    if amount_cny > store.user.get("daily_transfer_limit_cny", 20000):
        raise BlockedError(f"exceeds daily limit {store.user['daily_transfer_limit_cny']} CNY — requires manual review")
    # large transfer to untrusted beneficiary needs confirmation
    trusted = store.user.get("trusted_beneficiaries", [])
    if amount_cny > 5000 and to not in trusted and not confirmed:
        raise BlockedError(f"untrusted beneficiary '{to}' for large amount — explicit YES required (need_confirm)")
    if not confirmed and amount_cny > 1000:
        raise BlockedError("need_confirm: reply YES to execute")
