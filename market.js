// WAL market-list integration
async function walLoadTop250(){const r=await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false&price_change_percentage=24h');if(!r.ok)throw new Error('CoinGecko unavailable');return await r.json();}
async function walSearchCoins(q){const r=await fetch('https://api.coingecko.com/api/v3/search?query='+encodeURIComponent(q));if(!r.ok)throw new Error('Search unavailable');const d=await r.json();return d.coins||[];}
