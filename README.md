# 🌍 Smart Cross-Border Finance Assistant — FinTechathon 2026 Intl Track · Topic C

AI as a Financial Participant for international students: budgeting, FX, remittance quotes, tuition planning, recurring detection, credit guidance — trilingual (EN/ZH/BN) with security guardrails.

## Quickstart (judges, 2 min)
```bash
pip install -r requirements.txt
python tests_smoke.py      # expect ALL SMOKE TESTS PASSED
python demo/run_demo.py    # -> demo/execution_logs.jsonl + audit_dump.json
python app.py              # open http://127.0.0.1:8000  (API docs: /docs)
```
Click quick-task buttons 1–5 in UI; use 🛡 Attack test to see injection block.

## Repo layout
- `agent.py` intent router · `fx_service.py` FX+quotes · `security.py` guardrails
- `store.py` + `data/seed.json` sandbox · `i18n.py` EN/ZH/BN
- `app.py` FastAPI (`/api/chat /remittance/quote /budget/summary /transactions /audit`)
- `frontend/index.html` demo UI · `demo/run_demo.py` 11 scripted tasks
- `docs/` 01 technical · 05 security · deck outline · video script · checklist

## Submission
See `docs/SUBMISSION_CHECKLIST.md`. Email pack to `wangyr@pbcsf.tsinghua.edu.cn` before Oct 20 23:59 Beijing (UTC+8), English only.
