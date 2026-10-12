"""FastAPI entry for Topic C — Smart Cross-Border Finance Assistant.
Run: pip install -r requirements.txt; python app.py  (serves API + frontend)
"""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import chat
from fx_service import quote_remittance
from store import store

app = FastAPI(title="Smart Cross-Border Finance Assistant (Topic C)", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

class ChatIn(BaseModel):
    message: str
    lang: str = "auto"

class QuoteIn(BaseModel):
    amount: float
    src: str
    dst: str = "CNY"

@app.get("/api/health")
def health():
    return {"ok": True, "track": "International-AI", "topic": "C-cross-border-student", "lang": "en"}

@app.post("/api/chat")
def api_chat(body: ChatIn):
    out = chat(body.message, body.lang)
    return out

@app.post("/api/remittance/quote")
def api_quote(body: QuoteIn):
    quotes = quote_remittance(body.amount, body.src.upper(), body.dst.upper(), store.fx_rates)
    store.audit("api_remit_quote", {"amt": body.amount, "src": body.src, "dst": body.dst})
    return {"quotes": quotes}

@app.get("/api/budget/summary")
def budget():
    totals = store.spending_by_category("CNY")
    return {"totals": totals, "total_cny": round(sum(totals.values()), 2), "budget_cny": store.user["monthly_budget_cny"]}

@app.get("/api/transactions")
def txs():
    return {"transactions": store.transactions[-20:]}

@app.get("/api/audit")
def audit():
    return {"logs": store.audit_logs[-50:]}

# serve frontend if present
FRONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "index.html")
if os.path.exists(os.path.dirname(FRONT)):
    app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")), name="static")

@app.get("/")
def root():
    if os.path.exists(FRONT):
        return FileResponse(FRONT)
    return {"msg": "API running. See /docs", "frontend": "coming in commit 3"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
