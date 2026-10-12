"""Rule-based financial agent: understand -> plan -> execute, with clarification & fallback.
Deterministic = judges can replay scripted tasks. LLM hook optional via env LLM_ENDPOINT.
"""
from __future__ import annotations
import re
from fx_service import convert, quote_remittance, DEFAULT_RATES_CNY_PER_UNIT
from security import detect_injection, check_transfer, mask_pii, BlockedError
from i18n import t
from store import store

CURRENCIES = ["CNY", "USD", "BDT", "EUR", "GBP", "HKD", "SGD", "JPY", "RMB", "TAKA", "DOLLAR"]

def _extract_amount_currency(text: str):
    m = re.search(r"(\d[\d,]*\.?\d*)\s*([A-Za-z]+)?", text)
    if not m:
        return None, None
    amt = float(m.group(1).replace(",", ""))
    cur = (m.group(2) or "").upper()
    mapping = {"RMB": "CNY", "YUAN": "CNY", "TAKA": "BDT", "TK": "BDT", "DOLLAR": "USD", "DOLLARS": "USD", "$": "USD", "¥": "CNY"}
    cur = mapping.get(cur, cur if cur in DEFAULT_RATES_CNY_PER_UNIT else None)
    return amt, cur

def _extract_recipient(text: str):
    m = re.search(r"(?:to|给|send to|transfer to|pay)\s+([A-Z][A-Za-z .]{1,30}|\S+)", text, re.I)
    if m:
        return m.group(1).strip().strip(".,!?")
    # "to Mom" simple
    m2 = re.search(r"\bto\s+(\w+)", text, re.I)
    return m2.group(1) if m2 else None

def detect_lang(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u0980-\u09ff]", text):
        return "bn"
    return "en"

def chat(message: str, lang: str = "auto") -> dict:
    raw = message.strip()
    use_lang = detect_lang(raw) if lang == "auto" else lang
    masked = mask_pii(raw)
    store.audit("chat_in", {"msg": masked, "lang": use_lang})

    # 1) injection shield
    hit = detect_injection(raw)
    if hit:
        store.audit("blocked_injection", {"reason": hit})
        return {"reply": t(use_lang, "blocked").format(reason=hit), "blocked": True, "lang": use_lang}

    low = raw.lower()

    # 2) greetings
    if low in ("hi", "hello", "hey", "你好", "হ্যালো", "help", "帮助"):
        return {"reply": t(use_lang, "greet"), "lang": use_lang, "intent": "greet"}

    # 3) budget summary
    if any(k in low for k in ["budget", "spending", "spend summary", "bill analysis", "账单", "预算", "খরচ", "বাজেট"]):
        totals = store.spending_by_category("CNY")
        total = round(sum(totals.values()), 2)
        budget = store.user["monthly_budget_cny"]
        pct = round(total / budget * 100, 1) if budget else 0
        # anomaly: any single tx > 30% of budget
        anomalies = [x for x in store.transactions if x.get("kind") == "expense" and convert(x["amount"], x["currency"], "CNY", store.fx_rates) > budget * 0.3]
        lines = [f"- {k}: {v} CNY" for k, v in sorted(totals.items(), key=lambda x: -x[1])]
        rec = "Within budget. " if pct <= 100 else "Over budget! Cut shopping/food next week. "
        if anomalies:
            rec += f"Unusual: {anomalies[0]['note']} ({anomalies[0]['amount']} {anomalies[0]['currency']}) flagged."
        reply = f"Monthly spend: {total} CNY / {budget} CNY ({pct}%).\n" + "\n".join(lines) + f"\nRecommendation: {rec}"
        store.audit("budget_summary", {"total_cny": total})
        return {"reply": reply, "lang": use_lang, "intent": "budget", "data": {"totals": totals, "total": total}}

    # 4) FX rate
    if any(k in low for k in ["fx", "exchange rate", "汇率", "rate", "রেট", "ডলার", "convert"]):
        amt, cur = _extract_amount_currency(raw)
        # pattern "USD to CNY" / "美元"
        m = re.search(r"(USD|CNY|BDT|EUR|HKD|SGD|JPY|GBP)\s*(?:to|->|换|到)\s*(USD|CNY|BDT|EUR|HKD|SGD|JPY|GBP)", raw.upper())
        if m:
            a, b = m.group(1), m.group(2)
            r = convert(1, a, b, store.fx_rates)
            return {"reply": f"1 {a} = {r} {b} (sandbox 2026-10-01). {amt or 100} {a} = {convert(amt or 100, a, b, store.fx_rates)} {b}.", "lang": use_lang, "intent": "fx"}
        return {"reply": f"Sandbox rates (CNY per unit): " + ", ".join([f"1 {k}={v}" for k, v in store.fx_rates.items() if k in ("USD","BDT","EUR","HKD")]) + ". Ask e.g. '100 USD to CNY'.", "lang": use_lang, "intent": "fx"}

    # 5) remittance quote
    if any(k in low for k in ["remit", "remittance", "汇款", "quote", "cheapest", "wise", "swift", "汇", "রেমিট্যান্স", "পাঠাও"]):
        amt, cur = _extract_amount_currency(raw)
        if not amt or not cur:
            return {"reply": "How much and in which currency? E.g. 'Quote 50000 BDT to CNY'.", "lang": use_lang, "intent": "remit_clarify", "need_clarify": True}
        # detect target: default study currency CNY unless stated
        m = re.search(r"to\s+(USD|CNY|BDT|EUR|HKD|SGD|JPY|GBP)", raw.upper())
        dst = m.group(1) if m else store.user["study_currency"]
        quotes = quote_remittance(amt, cur, dst, store.fx_rates)
        best = quotes[0]
        lines = [f"{'✅ ' if q.get('best') else ''}{q['route_name']}: net {q['net_received']} {dst} (fee {q['fee']}), ETA {q['eta']}" for q in quotes]
        reply = f"Remittance {amt} {cur} -> {dst}:\n" + "\n".join(lines) + f"\nBest: {best['route_name']}. Reply 'Send {amt} {cur} to <name> via {best['route_id']}' to proceed."
        store.audit("remit_quote", {"amt": amt, "cur": cur, "dst": dst, "best": best["route_id"]})
        return {"reply": reply, "lang": use_lang, "intent": "remit_quote", "data": {"quotes": quotes}}

    # 6) tuition plan
    if any(k in low for k in ["tuition", "学费", "টিউশন", "semester fee"]):
        reply = ("Tuition plan (Shenzhen University, sandbox): Total 16000 CNY/semester.\n"
                 "Paid: 8000 CNY. Remaining: 8000 CNY due 2026-11-15.\n"
                 "Options: (a) one-time via CIPS (fee ~69 CNY), (b) 2x split 4000+4000 (fee ~2x21 CNY, easier cashflow).\n"
                 "I can set a reminder + reserve funds from budget. Reply 'Reserve 8000 CNY for tuition'.")
        return {"reply": reply, "lang": use_lang, "intent": "tuition"}

    # 7) recurring / subscription detection
    if any(k in low for k in ["recurring", "subscription", "订阅", "代扣", "সাবস্ক্রিপশন", "renewal"]):
        # group by merchant
        from collections import Counter
        c = Counter([x.get("merchant") for x in store.transactions if x.get("category") == "subscription"])
        rec = ", ".join([f"{k} x{v}" for k, v in c.items()]) or "none"
        reply = (f"Detected recurring: {rec}.\n"
                 "Apple iCloud 15 CNY x3 months — cancel? Tencent Video 68 CNY — renews soon.\n"
                 "Reply 'Cancel iCloud' to simulate one-click cancellation.")
        return {"reply": reply, "lang": use_lang, "intent": "recurring"}

    if "cancel icloud" in low or "cancel" in low and "icloud" in low:
        store.audit("subscription_cancel", {"merchant": "Apple"})
        return {"reply": "Done (sandbox): iCloud subscription cancelled, you save 180 CNY/year. Confirmation ID CAN-2026-1013.", "lang": use_lang, "intent": "cancel"}

    # 8) reserve / transfer execution with confirmation state machine
    if any(k in low for k in ["send", "transfer", "pay", "reserve", "汇", "转账", "পাঠা"]):
        amt, cur = _extract_amount_currency(raw)
        to = _extract_recipient(raw) or ("Mom" if "mom" in low or "妈妈" in raw else None)
        route = "fintech"
        for r in ("swift", "fintech", "cips"):
            if r in low:
                route = r
        if not amt or not cur or not to:
            return {"reply": t(use_lang, "clarify_transfer"), "lang": use_lang, "intent": "transfer_clarify", "need_clarify": True}
        cny = convert(amt, cur, "CNY", store.fx_rates)
        # YES confirmation handling: if message contains YES and matches pending
        if "yes" in low and store.pending_confirmations:
            # execute oldest pending
            key = next(iter(store.pending_confirmations))
            pend = store.pending_confirmations.pop(key)
            try:
                check_transfer(pend["cny"], pend["to"], store, confirmed=True)
            except BlockedError as e:
                return {"reply": t(use_lang, "blocked").format(reason=str(e)), "blocked": True, "lang": use_lang}
            tx = store.add_transaction({"kind": "expense", "category": "remittance", "amount": pend["amt"], "currency": pend["cur"], "note": f"Remit to {pend['to']} via {pend['route']}", "merchant": pend["to"]})
            return {"reply": f"Executed: {pend['amt']} {pend['cur']} (~{pend['cny']} CNY) to {pend['to']} via {pend['route']}. Tx {tx['id']}.", "lang": use_lang, "intent": "transfer_done", "data": tx}
        try:
            check_transfer(cny, to, store, confirmed=("yes" in low))
        except BlockedError as e:
            msg = str(e)
            if msg.startswith("need_confirm"):
                # stash pending
                store.pending_confirmations[f"{amt}{cur}{to}"] = {"amt": amt, "cur": cur, "to": to, "cny": cny, "route": route}
                return {"reply": t(use_lang, "confirm_transfer").format(amt=amt, cur=cur, cny=cny, to=to, route=route), "lang": use_lang, "intent": "transfer_confirm", "need_confirm": True}
            return {"reply": t(use_lang, "blocked").format(reason=msg), "blocked": True, "lang": use_lang}
        # small trusted -> direct execute
        tx = store.add_transaction({"kind": "expense", "category": "remittance", "amount": amt, "currency": cur, "note": f"Remit to {to} via {route}", "merchant": to})
        return {"reply": f"Executed: {amt} {cur} (~{cny} CNY) to {to} via {route}. Tx {tx['id']}.", "lang": use_lang, "intent": "transfer_done", "data": tx}

    if low.strip() == "yes" and store.pending_confirmations:
        key = next(iter(store.pending_confirmations))
        pend = store.pending_confirmations.pop(key)
        try:
            check_transfer(pend["cny"], pend["to"], store, confirmed=True)
        except BlockedError as e:
            return {"reply": t(use_lang, "blocked").format(reason=str(e)), "blocked": True, "lang": use_lang}
        tx = store.add_transaction({"kind": "expense", "category": "remittance", "amount": pend["amt"], "currency": pend["cur"], "note": f"Remit to {pend['to']} via {pend['route']}", "merchant": pend["to"]})
        return {"reply": f"Executed: {pend['amt']} {pend['cur']} to {pend['to']}. Tx {tx['id']}.", "lang": use_lang, "intent": "transfer_done", "data": tx}

    # 9) credit building
    if any(k in low for k in ["credit", "信用", "ক্রেডিট", "芝麻", "sesame"]):
        return {"reply": ("Credit building (newcomer, no local history):\n"
                          "1. Keep campus card + phone bill autopay 6 months.\n"
                          "2. Small secured deposit 2000 CNY -> builds record.\n"
                          "3. Never exceed 30% utilization.\n"
                          "Sandbox score now: 620 -> projected 680 in 6 mo if on-time."), "lang": use_lang, "intent": "credit"}

    # 10) cost of living compare
    if any(k in low for k in ["cost of living", "living cost", "生活费", "compare", "深圳", "dhaka", "达卡", "জীবনযাত্রা"]):
        return {"reply": "Shenzhen vs Dhaka (student, sandbox): Shenzhen ~5500 CNY/mo (rent 2200+food 1500+other 1800); Dhaka ~35000 BDT (~2135 CNY). Shenzhen 2.6x. Tip: cook 3x/week saves ~600 CNY/mo.", "lang": use_lang, "intent": "col"}

    return {"reply": t(use_lang, "fallback"), "lang": use_lang, "intent": "fallback"}
