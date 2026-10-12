"""FX + remittance quote logic. Static sandbox rates, fully deterministic for judging."""
from __future__ import annotations

# Rates quoted as CNY per 1 unit foreign currency (sandbox, 2026-10-01 snapshot)
# e.g. 1 USD = 7.12 CNY
DEFAULT_RATES_CNY_PER_UNIT = {
    "CNY": 1.0,
    "USD": 7.12,
    "BDT": 0.061,
    "EUR": 7.72,
    "GBP": 9.01,
    "HKD": 0.913,
    "SGD": 5.28,
    "JPY": 0.0477,
}

# Remittance routes: fee model + ETA (sandbox)
ROUTES = [
    {"id": "swift", "name": "SWIFT Bank Transfer", "fee_pct": 0.012, "flat_cny": 25.0, "eta": "2-4 business days", "reliability": 0.99},
    {"id": "fintech", "name": "Fintech Fast Rail (Wise-like)", "fee_pct": 0.006, "flat_cny": 8.0, "eta": "Same day / next day", "reliability": 0.97},
    {"id": "cips", "name": "CIPS Cross-border RMB Rail", "fee_pct": 0.004, "flat_cny": 5.0, "eta": "Same day (RMB)", "reliability": 0.96},
]

def convert(amount: float, src: str, dst: str, rates: dict | None = None) -> float:
    rates = rates or DEFAULT_RATES_CNY_PER_UNIT
    src = src.upper(); dst = dst.upper()
    if src not in rates or dst not in rates:
        raise ValueError(f"Unsupported currency {src}->{dst}")
    cny = amount * rates[src]
    return round(cny / rates[dst], 2)

def quote_remittance(amount: float, src: str, dst: str, rates: dict | None = None) -> list[dict]:
    """Return 3 route quotes sorted by total received."""
    rates = rates or DEFAULT_RATES_CNY_PER_UNIT
    gross_dst = convert(amount, src, dst, rates)
    # fee charged in src -> convert fee to dst for net calc (simplified: fee in CNY)
    amount_cny = amount * rates[src.upper()]
    out = []
    for r in ROUTES:
        fee_cny = amount_cny * r["fee_pct"] + r["flat_cny"]
        fee_dst = round(fee_cny / rates[dst.upper()], 2)
        net = round(gross_dst - fee_dst, 2)
        out.append({
            "route_id": r["id"],
            "route_name": r["name"],
            "gross": gross_dst,
            "fee": fee_dst,
            "net_received": net,
            "currency": dst.upper(),
            "eta": r["eta"],
            "reliability": r["reliability"],
        })
    out.sort(key=lambda x: x["net_received"], reverse=True)
    # mark best
    if out:
        out[0]["best"] = True
    return out
