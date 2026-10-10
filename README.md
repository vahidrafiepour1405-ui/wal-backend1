# WAL — Whale Analysis Live

A Persian RTL-first market-monitoring prototype with a small optional FastAPI backend.

## Web version
GitHub Pages publishes the static frontend from the repository root. The frontend currently fetches reference FX rates and selected crypto prices directly from public APIs. Some listed markets do not yet have a live provider. The interface should show missing data instead of fabricating it.

## Backend (optional)
- `backend/main.py`: FastAPI health check, CoinGecko price proxy, and Ethereum ERC-20 transfer feed through Etherscan API V2.
- Install with `pip install -r backend/requirements.txt`.
- Run with `uvicorn main:app --host 0.0.0.0 --port 8000` from the backend directory.
- Configure `ETHERSCAN_API_KEY` and `DEBANK_ACCESS_KEY` as secret/environment variables on the hosting platform. Never commit API keys.
- Endpoints: `/health`, `/status` (safe diagnostics; never returns secrets), `/prices`, `/whales/ethereum`, `/wallet/debank?id=0x...`, `/onchain/hypurrscan/recent`, `/onchain/hypurrscan/whale-transfers`, `/signals`.
- `/wallet/debank` reads a wallet's total portfolio balance using DeBank's AccessKey; never put the key in frontend JavaScript.
- The HyperEVM feed uses HypurrTrace's public recent-activity endpoint. Provider paths and CORS/rate limits can change; check `/onchain/hypurrscan/recent` after deployment before relying on it.
- Deploy backend via Render Blueprint using `render.yaml`, then configure both API keys in the Render service Environment. Do not enter keys into GitHub files or this chat.

## Important limitations
- Raw token transfers are not proof of independent whale accumulation, net buying, or intent. Exchange, bridge, contract, staking and project wallets need labeling and clustering before making those claims.
- `/signals` intentionally returns WAIT until a validated candle-based strategy and out-of-sample backtest are implemented.
- This repository does not contain a built Android APK. GitHub Pages hosts a website, not an Android app.
- Public APIs have rate limits and may fail in some regions/networks. A backend deployment is needed to hide keys and normalize data.
