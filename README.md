# WAL — Whale Analysis Live

A Persian RTL-first market-monitoring prototype with a small optional FastAPI backend.

## Web version
GitHub Pages publishes the static frontend from the repository root. The frontend currently fetches reference FX rates and selected crypto prices directly from public APIs. Some listed markets do not yet have a live provider. The interface should show missing data instead of fabricating it.

## Backend (optional)
- `backend/main.py`: FastAPI health check, CoinGecko price proxy, and Ethereum ERC-20 transfer feed through Etherscan API V2.
- Install with `pip install -r backend/requirements.txt`.
- Run with `uvicorn main:app --host 0.0.0.0 --port 8000` from the backend directory.
- Configure `ETHERSCAN_API_KEY` as a secret/environment variable on the hosting platform. Never commit API keys.
- Endpoints: `/health`, `/prices`, `/whales/ethereum`, `/signals`.

## Important limitations
- Raw token transfers are not proof of independent whale accumulation, net buying, or intent. Exchange, bridge, contract, staking and project wallets need labeling and clustering before making those claims.
- `/signals` intentionally returns WAIT until a validated candle-based strategy and out-of-sample backtest are implemented.
- This repository does not contain a built Android APK. GitHub Pages hosts a website, not an Android app.
- Public APIs have rate limits and may fail in some regions/networks. A backend deployment is needed to hide keys and normalize data.
