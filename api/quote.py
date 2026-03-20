# api/quote.py
# Vercel Python serverless function — snapshots Activ Financial to avoid browser CORS restrictions.
# Handles: ^VIX  ^MOVE  V2TX.DE
#
# Usage: GET /api/quote?symbol=^VIX

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler
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

def _parse_float(value):
    """Parse a float from an Activ field string, stripping trend indicators like '<-- >'."""
    if value is None or value == 'None':
        return None
    m = re.match(r'[-+]?\d*\.?\d+', str(value).strip())
    return float(m.group()) if m else None


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        symbol = params.get('symbol', [None])[0]

        if not symbol:
            return self._json(400, {'error': 'Missing required parameter: symbol'})

        activ_symbol = SYMBOL_MAP.get(symbol)
        if not activ_symbol:
            return self._json(400, {'error': f'Unknown symbol: {symbol}'})

        session = None
        try:
            session = common.connect_session()
            msg     = session.snapshot(activ_symbol)

            f = {
                session.metadata.get_field_name(msg.data_source_id, fid): str(field)
                for fid, field in msg.fields.items()
            }

            price     = _parse_float(f.get('Trade'))
            prev      = _parse_float(f.get('PreviousClose'))
            high      = _parse_float(f.get('TradeHigh'))
            low       = _parse_float(f.get('TradeLow'))
            change    = _parse_float(f.get('NetChange'))
            changePct = _parse_float(f.get('PercentChange'))
            print(f'[quote] {activ_symbol} → price={price} prev={prev} change={change} changePct={changePct}')

            self._json(200, {
                'symbol':      symbol,
                'price':       price,
                'prevClose':   prev,
                'change':      change,
                'changePct':   changePct,
                'low':         low,
                'high':        high,
                'marketState': 'REGULAR',
                'timestamp':   f.get('TradeDate'),
            })

        except Exception as e:
            import traceback
            print(f'[quote] ERROR for {activ_symbol}: {e}')
            traceback.print_exc()
            self._json(500, {'error': 'Internal proxy error', 'detail': str(e)})

        finally:
            if session:
                try:
                    session.disconnect()
                except Exception:
                    pass

    # ── helpers ────────────────────────────────────────────────────────────

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')

    def _json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type',   'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control',  's-maxage=60, stale-while-revalidate=120')
        self.end_headers()
        self.wfile.write(body)
