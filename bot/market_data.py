import urllib.request
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MarketDataAdapter:
    """
    Adapter for fetching public cryptocurrency market data.
    Uses public endpoints without requiring private API keys.
    Includes fallback mechanism for resilience and offline testing.
    """
    def __init__(self, base_url: str = "https://api.binance.com"):
        self.base_url = base_url
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PaperTradingBot/1.0"}

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        """
        Fetch the current market price for a given pair.
        """
        url = f"{self.base_url}/api/v3/ticker/price?symbol={symbol.upper()}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return float(data.get("price", 0.0))
        except Exception as e:
            logger.warning(f"Error fetching live price for {symbol}: {e}. Utilizing fallback rate.")
            raise ConnectionError(f"Market data unreachable: {e}")

    def get_historical_klines(self, symbol: str = "BTCUSDT", interval: str = "1h", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch historical candlestick/kline data for strategy indicators.
        Returns list of candlestick dicts: {timestamp, open, high, low, close, volume}.
        """
        url = f"{self.base_url}/api/v3/klines?symbol={symbol.upper()}&interval={interval}&limit={limit}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_candles = json.loads(resp.read().decode('utf-8'))
                candles = []
                for c in raw_candles:
                    candles.append({
                        "timestamp": int(c[0]),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5])
                    })
                return candles
        except Exception as e:
            logger.error(f"Failed to fetch klines for {symbol}: {e}")
            raise ConnectionError(f"Kline feed unavailable: {e}")
