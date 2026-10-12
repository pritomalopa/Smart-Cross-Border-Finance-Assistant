# Smart Cross-Border Finance Assistant — Topic C (Submission 01: Technical Documentation)

**Competition:** 2026 Shenzhen International FinTech Competition — International Track (AI)
**Topic:** C — Cross-border & Student Finance Assistant
**Theme:** AI as a Financial Participant
**Language:** English (official)

## 1. Problem
International students face: high remittance fees, opaque FX, tuition deadlines, recurring-trap subscriptions, zero local credit history, language barriers.

## 2. Solution
A conversational agent that understands intent → plans → executes with guardrails, trilingual (EN/ZH/BN), sandbox-simulated banking rails.

Core flows:
- T1 Budget & bill analysis: multi-currency aggregation to CNY, anomaly flag (>30% budget single tx), recommendation.
- T2 FX: sandbox rates (2026-10-01), `convert()` deterministic.
- T3 Remittance quote: 3 routes (SWIFT / Fintech Fast / CIPS RMB), fee = pct + flat, sorted best-first.
- T4 Transfer with 2-step YES confirmation + trusted-beneficiary tiers.
- T5 Recurring detection (Counter by merchant) + one-click cancel simulation.
- T6 Tuition planner (split vs one-time) + reserve.
- Extras: credit-building guide, Shenzhen-vs-home cost compare.

## 3. System architecture
```
[frontend/index.html] --POST /api/chat--> [app.py FastAPI]
        |                                        |-- agent.py (intent router, 10 intents)
        |                                        |-- fx_service.py (convert + quotes)
        |                                        |-- security.py (injection shield, limits, PII mask)
        |                                        |-- store.py (seed.json sandbox + audit log)
        |                                        |-- i18n.py (en/zh/bn)
Demo: demo/run_demo.py replays 11 scripted tasks -> execution_logs.jsonl + audit_dump.json
```

## 4. Core algorithms
- Intent routing: ordered regex/keyword cascade (budget → fx → remit → tuition → recurring → transfer → credit → col → fallback). Deterministic, no LLM key needed; LLM hook point in `agent.chat()` for future upgrade.
- FX: CNY-normalized conversion; quotes compute fee_cny → fee_dst, net = gross − fee.
- Confirmation state machine: `pending_confirmations{}` dict; large/untrusted amounts require YES; executed tx appended with id + audit event.
- Anomaly: single expense > 30% monthly budget flagged.

## 5. Security design (summary, full in 05)
Permission tiers (direct ≤1000 CNY trusted; YES-confirm 1000+; block >daily limit; block untrusted large), 12 injection regexes, PII masking, full audit trail.

## 6. How to run / test
```
pip install -r requirements.txt
python tests_smoke.py        # 5 checks
python demo/run_demo.py      # 11 tasks -> demo/execution_logs.jsonl
python app.py                # http://127.0.0.1:8000, docs at /docs
```
