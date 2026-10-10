"""
WAL (Whale Analysis Live) minimal API.
Real on-chain transfer observations, not guaranteed identification of "whales".
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from datetime import datetime, timezone
from typing import Optional
import os
from pathlib import Path
import httpx
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WAL API", version="0.3.0")
ROOT_DIR = Path(__file__).resolve().parent.parent
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["GET"], allow_headers=["*"],
)

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "").strip()
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

@app.get("/")
async def root():
    # Serve the phone-friendly Persian web app and its same-origin scripts.
    return FileResponse(ROOT_DIR / "index.html")

@app.get("/market.js")
async def market_script():
    return FileResponse(ROOT_DIR / "market.js", media_type="application/javascript")

@app.get("/onchain.js")
async def onchain_script():
    return FileResponse(ROOT_DIR / "onchain.js", media_type="application/javascript")

@app.get("/health")
async def health():
    return {"ok": True, "utc": datetime.now(timezone.utc).isoformat()}

@app.get("/status")
async def status():
    """Safe deployment diagnostics; reports configuration without exposing credentials."""
    return {
        "app": "WAL",
        "ok": True,
        "version": app.version,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "CoinGecko": {"configured": True, "mode": "public API"},
            "HypurrTrace": {"configured": True, "mode": "public read-only API"},
            "DeBank": {"configured": bool(DEBANK_ACCESS_KEY), "mode": "server-side key"},
            "Etherscan": {"configured": bool(ETHERSCAN_API_KEY), "mode": "server-side key"},
        },
        "signals": {"status": "WAIT", "enabled": False,
                    "reason": "No validated strategy/backtest is configured; no synthetic signals are emitted."},
    }

@app.get("/prices")
async def prices(ids: str = Query("bitcoin,ethereum,solana,hyperliquid,worldcoin-wld,compound-governance-token")):
    wanted = [x.strip() for x in ids.split(",") if x.strip()][:50]
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{COINGECKO_BASE}/simple/price",
            params={"ids": ",".join(wanted), "vs_currencies": "usd",
                    "include_24hr_change": "true"})
        r.raise_for_status()
        return {"source": "CoinGecko", "as_of_utc": datetime.now(timezone.utc).isoformat(),
                "data": r.json()}

@app.get("/whales/ethereum")
async def ethereum_transfers(
    contract: Optional[str] = None,
    page: int = Query(1, ge=1, le=100),
    offset: int = Query(100, ge=1, le=100),
):
    if not ETHERSCAN_API_KEY:
        return {"ok": False, "configured": False,
                "error": "ETHERSCAN_API_KEY is not configured on the hosting service.",
                "source": "Etherscan API V2"}
    params = {"chainid": 1, "module": "account", "action": "tokentx",
              "page": page, "offset": offset, "sort": "desc",
              "apikey": ETHERSCAN_API_KEY}
    if contract:
        params["contractaddress"] = contract
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(ETHERSCAN_BASE, params=params)
        r.raise_for_status()
        payload = r.json()
    if payload.get("status") == "0" and payload.get("message") != "No transactions found":
        return {"ok": False, "source": "Etherscan API V2",
                "error": payload.get("result", payload.get("message", "API error"))}
    rows = payload.get("result", [])
    if not isinstance(rows, list):
        rows = []
    transfers = []
    for tx in rows:
        try:
            decimals = int(tx.get("tokenDecimal") or 0)
            raw = int(tx.get("value") or 0)
            amount = raw / (10 ** decimals) if decimals >= 0 else 0
            transfers.append({
                "hash": tx.get("hash"), "token": tx.get("tokenSymbol"),
                "token_name": tx.get("tokenName"), "contract": tx.get("contractAddress"),
                "from": tx.get("from"), "to": tx.get("to"),
                "amount": amount, "timestamp": int(tx.get("timeStamp") or 0),
                "utc": datetime.fromtimestamp(int(tx.get("timeStamp") or 0), timezone.utc).isoformat(),
                "block": tx.get("blockNumber")
            })
        except (ValueError, TypeError, OverflowError):
            continue
    # Transfer size alone cannot prove a wallet is an independent whale or that it is buying.
    return {"ok": True, "configured": True, "source": "Etherscan API V2",
            "chain": "Ethereum", "count": len(transfers),
            "as_of_utc": datetime.now(timezone.utc).isoformat(),
            "warning": "Transfers are raw on-chain movements. They do not by themselves prove accumulation, wallet independence, or buy/sell intent.",
            "transfers": transfers}

@app.get("/signals")
async def signals():
    return {"ok": True, "signals": [],
            "status": "WAIT",
            "reason": "No validated OHLCV strategy and no labeled backtest are configured. WAL will not invent BUY/SELL signals."}


DEBANK_ACCESS_KEY = os.getenv("DEBANK_ACCESS_KEY", "").strip()
DEBANK_BASE = "https://pro-openapi.debank.com/v1"
HYPURRTRACE_BASE = "https://trace.hypurrscan.io/api/v1"

@app.get("/wallet/debank")
async def debank_wallet(id: str = Query(..., min_length=42, max_length=42)):
    """Fetch real wallet portfolio from DeBank. Requires a server-side DeBank AccessKey."""
    if not DEBANK_ACCESS_KEY:
        return {"ok": False, "configured": False, "source": "DeBank",
                "error": "DEBANK_ACCESS_KEY is not configured on the hosting service."}
    if not (id.startswith("0x") and all(c in "0123456789abcdefABCDEF" for c in id[2:])):
        return {"ok": False, "error": "Wallet must be a valid 40-hex-character EVM address."}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{DEBANK_BASE}/user/total_balance",
            params={"id": id},
            headers={"AccessKey": DEBANK_ACCESS_KEY, "accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
    return {"ok": True, "source": "DeBank", "wallet": id, "data": data,
            "as_of_utc": datetime.now(timezone.utc).isoformat()}

@app.get("/onchain/hypurrscan/recent")
async def hypurrscan_recent():
    """Public recent HyperEVM transactions; these are activity records, not automatically whales."""
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{HYPURRTRACE_BASE}/recent")
        response.raise_for_status()
        data = response.json()
    return {"ok": True, "source": "HypurrTrace / Hypurrscan",
            "warning": "Recent transactions are not proof of whale accumulation or buy intent.",
            "data": data, "as_of_utc": datetime.now(timezone.utc).isoformat()}

@app.get("/onchain/hypurrscan/whale-transfers")
async def hypurrscan_whale_transfers():
    """Proxy HypurrTrace indexed large transfers, preserving provider output and failures."""
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(f"{HYPURRTRACE_BASE}/indexed/whale-transfers")
        if response.is_error:
            return {"ok": False, "source": "HypurrTrace / Hypurrscan",
                    "http_status": response.status_code,
                    "error": "Provider rejected the request; endpoint may require query parameters or indexing may be unavailable."}
        data = response.json()
    return {"ok": True, "source": "HypurrTrace / Hypurrscan",
            "warning": "Large transfers are not necessarily independent whale buying.",
            "data": data, "as_of_utc": datetime.now(timezone.utc).isoformat()}
