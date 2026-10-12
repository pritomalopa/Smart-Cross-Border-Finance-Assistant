"""In-memory sandbox store for Topic C demo. No DB needed for judges."""
from __future__ import annotations
import json
import os
from copy import deepcopy
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "seed.json")

# Default sandbox user
DEFAULT_USER = {
    "user_id": "stu_demo01",
    "name": "Ayesha Rahman",
    "home_country": "Bangladesh",
    "study_country": "China",
    "home_currency": "BDT",
    "study_currency": "CNY",
    "monthly_budget_cny": 6000.0,
    "daily_transfer_limit_cny": 20000.0,
    "trusted_beneficiaries": ["Shenzhen University", "Mom", "Landlord Li"],
}

def load_seed():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class Store:
    def __init__(self):
        seed = load_seed()
        self.user = deepcopy(seed.get("user", DEFAULT_USER))
        self.transactions = deepcopy(seed.get("transactions", []))
        self.fx_rates = deepcopy(seed.get("fx_rates", {}))
        self.audit_logs: list[dict] = []
        self.pending_confirmations: dict[str, dict] = {}

    def audit(self, event: str, detail: dict) -> None:
        self.audit_logs.append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "detail": detail,
        })

    def add_transaction(self, tx: dict) -> dict:
        tx = deepcopy(tx)
        tx["id"] = f"tx_{len(self.transactions)+1:04d}"
        tx["ts"] = datetime.utcnow().isoformat() + "Z"
        self.transactions.append(tx)
        self.audit("tx_created", {"id": tx["id"], "amount": tx.get("amount"), "currency": tx.get("currency")})
        return tx

    def spending_by_category(self, currency: str = "CNY") -> dict:
        from fx_service import convert
        totals: dict[str, float] = {}
        for t in self.transactions:
            if t.get("kind") != "expense":
                continue
            amt = convert(t["amount"], t["currency"], currency, self.fx_rates)
            totals[t.get("category", "other")] = round(totals.get(t.get("category", "other"), 0) + amt, 2)
        return totals

store = Store()
