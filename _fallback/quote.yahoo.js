// api/quote.js
// Vercel serverless function — proxies Yahoo Finance to avoid browser CORS restrictions.
// Handles: ^VIX  ^MOVE  ^V2TX (VSTOXX)
//
// Usage: GET /api/quote?symbol=^VIX

export default async function handler(req, res) {
  const { symbol } = req.query;

  if (!symbol) {
    return res.status(400).json({ error: 'Missing required parameter: symbol' });
  }

  // CORS — allow any origin so the widget can be embedded anywhere
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  // Cache at the Vercel edge for 60 s; serve stale for up to 2 min while revalidating
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');

  try {
    const encoded  = encodeURIComponent(symbol);
    const url      = `https://query1.finance.yahoo.com/v8/finance/chart/${encoded}?interval=1d&range=2d`;

    const upstream = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; global-stress-dashboard/1.0)',
        'Accept':     'application/json',
      },
    });

    if (!upstream.ok) {
      return res.status(502).json({ error: `Yahoo Finance returned ${upstream.status}` });
    }

    const json   = await upstream.json();
    const result = json?.chart?.result?.[0];

    if (!result) {
      return res.status(502).json({ error: 'Unexpected response structure from Yahoo Finance' });
    }

    const meta      = result.meta;
    const price     = meta.regularMarketPrice     ?? null;
    const prevClose = meta.chartPreviousClose      ?? meta.previousClose ?? null;
    const change    = (price != null && prevClose != null) ? price - prevClose             : null;
    const changePct = (change != null && prevClose)        ? (change / prevClose) * 100    : null;

    return res.status(200).json({
      symbol,
      price,
      prevClose,
      change,
      changePct,
      low:         meta.regularMarketDayLow  ?? null,
      high:        meta.regularMarketDayHigh ?? null,
      marketState: meta.marketState          ?? 'UNKNOWN',
      timestamp:   meta.regularMarketTime    ?? null,
    });

  } catch (err) {
    console.error('[quote] proxy error:', err);
    return res.status(500).json({ error: 'Internal proxy error', detail: err.message });
  }
}
