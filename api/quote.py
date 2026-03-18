# api/quote.py
# Vercel Python serverless function — snapshots Activ Financial to avoid browser CORS restrictions.
# Handles: ^VIX  ^MOVE  V2TX.DE
#
# Usage: GET /api/quote?symbol=^VIX

import json
import os
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

def _field_float(fields, fid):
    """Return float value of a field or None if absent / undefined."""
    field = fields.get(fid)
    if field is None:
        return None
    if isinstance(field, Field) and not field.is_defined():
        return None
    try:
        return float(str(field))
    except (ValueError, TypeError):
        return None


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

            fields    = msg.fields
            price     = _field_float(fields, FID_TRADE)
            prev      = _field_float(fields, FID_CLOSE)
            low       = _field_float(fields, FID_LOW)
            high      = _field_float(fields, FID_HIGH)
            change    = (price - prev)          if (price is not None and prev is not None) else None
            changePct = (change / prev) * 100   if (change is not None and prev)            else None

            self._json(200, {
                'symbol':      symbol,
                'price':       price,
                'prevClose':   prev,
                'change':      change,
                'changePct':   changePct,
                'low':         low,
                'high':        high,
                'marketState': 'REGULAR',
                'timestamp':   str(msg.timestamp) if msg.timestamp else None,
            })

        except Exception as e:
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
