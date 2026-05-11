# Global Stress Dashboard

Real-time global market stress monitor tracking three key volatility indices — VIX, MOVE, and VSTOXX — with a weighted composite score. Built as a companion to the VIX Fear Gauge widget, sharing the same design language and deployment approach.

---

## Indices tracked

| Index | Market | Weight |
|-------|--------|--------|
| **VIX** | US equity (S&P 500) implied volatility | 50% |
| **MOVE** | US Treasury bond implied volatility | 30% |
| **VSTOXX** | European equity (Euro Stoxx 50) implied volatility | 20% |

The **composite score** normalises MOVE onto the VIX scale (÷5) before weighting, so all three indices are comparable and the output sits on the same `<15 → ≥35` fear scale used by the VIX widget.

## Fear scale

| Score | Level | Meaning |
|-------|-------|---------|
| < 15 | **CALM** | Low volatility, markets are tranquil |
| 15 – 19 | **NEUTRAL** | Normal market conditions |
| 20 – 24 | **CAUTIOUS** | Elevated uncertainty, watch closely |
| 25 – 34 | **CONCERN** | Significant stress, risk-off building |
| ≥ 35 | **REACT** | Extreme fear, review and take action |

---

## Project structure

```
global-stress-dashboard/
├── index.html        # Dashboard UI
├── api/
│   └── quote.js      # Vercel serverless proxy → Options AtlasFeed API
├── vendor/
│   └── activfinancial-1.11.2-py3-none-any.whl      # The Options AtlasFeed (previously Activ) wheel
├── vercel.json       # Vercel routing config
├── .gitignore
└── README.md
```

---

## Local development

No build step required. Use the [Vercel CLI](https://vercel.com/docs/cli) to run locally with the serverless function:

```bash
npm i -g vercel
vercel dev
```

Then open [http://localhost:3000](http://localhost:3000).

> Without `vercel dev`, the `/api/quote` route won't work and the dashboard will show "Unavailable". You can temporarily hardcode a fetch to a deployed URL for testing.

---

## Deploy to Vercel

### Option 1 — Vercel dashboard (recommended)

1. Push this repo to GitHub
2. Go to [vercel.com/new](https://vercel.com/new)
3. Import the `global-stress-dashboard` repo
4. Leave all settings as default — Vercel auto-detects the serverless function in `/api`
5. Click **Deploy**

### Option 2 — Vercel CLI

```bash
vercel          # preview deploy
vercel --prod   # production deploy
```

---

## Data source

Live data is fetched from the *Options AtlasFeed* via a lightweight serverless proxy (`/api/quote.js`). The proxy caches responses for 60 seconds at the Vercel edge.

Tickers used:
- `^VIX` — CBOE Volatility Index
- `^MOVE` — ICE BofA MOVE Index
- `^V2TX` — VSTOXX (Euro Stoxx 50 Volatility)

> Data is indicative only and subject to Options availability. Not financial advice.

---

## Related

- [VIX Fear Gauge](../vix-widget) — the single-index widget this dashboard is built alongside
