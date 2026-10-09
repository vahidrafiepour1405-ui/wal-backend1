// WAL backend v0.1
const http = require('node:http');
const crypto = require('node:crypto');

const PORT = process.env.PORT || 8080;
const API_TOKEN = process.env.WAL_API_TOKEN || '';
const HL_URL = process.env.HL_INFO_URL || 'https://api.hyperliquid.xyz/info';
const TTL_MS = 10000;
const MAX_REQ_PER_MIN = 60;

const hits = new Map();
let cache = null;

function log(msg) { console.log(new Date().toISOString(), msg); }

function authOk(req) {
  if (!API_TOKEN) return false;
  const got = (req.headers.authorization || '').replace(/^Bearer /, '');
  const a = Buffer.from(got), b = Buffer.from(API_TOKEN);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function limited(ip) {
  const now = Date.now();
  const arr = (hits.get(ip) || []).filter(t => now - t < 60000);
  arr.push(now); hits.set(ip, arr);
  return arr.length > MAX_REQ_PER_MIN;
}

async function getPrices() {
  if (cache && Date.now() - cache.at < TTL_MS) return cache.data;
  const t0 = Date.now();
  try {
    const r = await fetch(HL_URL, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ type: 'allMids' }), signal: AbortSignal.timeout(5000),
    });
    if (r.status === 429) return { status: 'RATE LIMITED', provider: 'hyperliquid' };
    if (!r.ok) return { status: 'DEGRADED', provider: 'hyperliquid', httpStatus: r.status };
    const mids = await r.json();
    if (!mids || typeof mids !== 'object' || !Object.keys(mids).length)
      return { status: 'INSUFFICIENT DATA', provider: 'hyperliquid' };
    const data = { status: 'LIVE', provider: 'hyperliquid', fetchedAt: new Date().toISOString(),
      latencyMs: Date.now() - t0, mids };
    cache = { at: Date.now(), data };
    log(`prices ok latency=${data.latencyMs}ms`);
    return data;
  } catch (e) {
    log(`prices error ${e.name}`);
    return { status: 'OFFLINE', provider: 'hyperliquid' };
  }
}

const routes = {
  '/health': async () => ({ ok: true, service: 'wal-backend', version: '0.1.0' }),
  '/providers': async () => { const p = await getPrices(); return { providers: [{ name: 'hyperliquid', status: p.status }] }; },
  '/prices': getPrices,
  '/orders': async () => ({ status: 'NOT CONFIGURED' }),
};

const server = http.createServer(async (req, res) => {
  const send = (code, obj) => { res.writeHead(code, { 'content-type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(obj)); };
  const path = new URL(req.url, 'http://x').pathname;
  if (path === '/health') return send(200, await routes['/health']());
  if (limited(req.socket.remoteAddress)) return send(429, { error: 'RATE LIMITED' });
  if (!authOk(req)) return send(401, { error: 'UNAUTHORIZED' });
  if (req.method !== 'GET') return send(405, { error: 'METHOD NOT ALLOWED' });
  const h = routes[path];
  if (!h) return send(404, { error: 'NOT FOUND' });
  send(200, await h());
});

if (require.main === module) server.listen(PORT, () => log(`WAL backend on :${PORT}`));
module.exports = { server, getPrices };
