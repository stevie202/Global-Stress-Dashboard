# api/quote.py

# Vercel Python serverless function — snapshots Activ Financial to avoid browser CORS restrictions.
# Handles: ^VIX  ^MOVE  V2TX.DE
#
# Usage: GET /api/quote?symbol=^VIX

import json
import os
import re
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import urlparse, parse_qs

# Add project root to path so common.py is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from activfinancial import *
from activfinancial.constants import *
import common

# Map frontend symbols to Activ Financial symbology
SYMBOL_MAP = {
    '^VIX':    '=VIX.WI',
    '^MOVE':   '=MOVE.NGI',
    'V2TX.DE': '=V2TX.XE',
}


def _parse_float(value: Optional[str]) -> Optional[float]:
    """Parse a float from an Activ field string, stripping trend indicators like '<-- >'."""
    if value is None or value == 'None':
        return None
    m = re.match(r'[-+]?\d*\.?\d+', str(value).strip())
    return float(m.group()) if m else None


def _get_field(mapping: dict[str, str], *names: str) -> Optional[str]:
    """Return the first non-empty, non-'None' match from a list of field names."""
    for name in names:
        val = mapping.get(name)
        if val is not None and val != '' and val != 'None':
            return val
    return None


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)  # No Content is idiomatic for preflight
        self._cors()
        self.end_headers()

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        symbol = params.get('symbol', [None])[0]

        print(f'[quote] GET symbol={symbol}')

        if not symbol:
            return self._json(400, {'error': 'Missing required parameter: symbol'})

        activ_symbol = SYMBOL_MAP.get(symbol)
        if not activ_symbol:
            return self._json(400, {'error': f'Unknown symbol: {symbol}'})

        session = None
        try:
            session = common.connect_session()
            msg = session.snapshot(activ_symbol)

            fields = {
                session.metadata.get_field_name(msg.data_source_id, fid): str(field)
                for fid, field in msg.fields.items()
            }

            # Extract with fallbacks — handles different field names per asset class
            price     = _parse_float(_get_field(fields, 'Trade', 'Close', 'Last'))
            prev      = _parse_float(_get_field(fields, 'PreviousClose', 'PrevClose'))
            high      = _parse_float(_get_field(fields, 'TradeHigh', 'High', 'DayHigh', 'SessionHigh', 'BestHigh', 'PreviousTradeHigh'))
            low       = _parse_float(_get_field(fields, 'TradeLow', 'Low', 'DayLow', 'SessionLow', 'BestLow', 'PreviousTradeLow'))
            change    = _parse_float(_get_field(fields, 'NetChange', 'Change'))
            changePct = _parse_float(_get_field(fields, 'PercentChange', 'PctChange'))

            if change is None and price is not None and prev is not None:
                change    = price - prev
                changePct = (change / prev) * 100 if prev != 0 else None

            # Derive market state from whether a live trade is present
            market_state = 'REGULAR' if _get_field(fields, 'Trade') else 'CLOSED'

            self._json(200, {
                'symbol':      symbol,
                'price':       price,
                'prevClose':   prev,
                'change':      change,
                'changePct':   changePct,
                'low':         low,
                'high':        high,
                'marketState': market_state,
                'timestamp':   _get_field(fields, 'TradeDate', 'Date'),
            })

        except Exception as e:
            print(f'[quote] ERROR for {activ_symbol}: {e}')
            traceback.print_exc()
            self._json(500, {'error': 'Internal proxy error'})

        finally:
            if session:
                try:
                    session.disconnect()
                except Exception:
                    pass

    # ── helpers ────────────────────────────────────────────────────────────

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=True).encode('utf-8')
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))

        # Only cache successful quotes at the edge; never cache errors
        if status == 200:
            self.send_header('Cache-Control', 's-maxage=60, stale-while-revalidate=120')
        else:
            self.send_header('Cache-Control', 'no-store')

        self.end_headers()
        self.wfile.write(body)
