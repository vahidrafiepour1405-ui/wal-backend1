"""
WAL (Whale Analysis Live) minimal API.
Real on-chain transfer observations, not guaranteed identification of "whales".
Run: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from datetime import datetime, timezone
from typing import Optional
import os
import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WAL API", version="0.2.0")
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
    return {"app": "WAL", "status": "online", "version": "0.2.0",
            "note": "On-chain transfer feed requires ETHERSCAN_API_KEY."}

@app.get("/health")
async def health():
    return {"ok": True, "utc": datetime.now(timezone.utc).isoformat()}

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
