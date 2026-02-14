"""Perception Layer — Market Data Ingestion via WebSockets and CCXT."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable

import ccxt.async_support as ccxt
import websockets
import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands

logger = logging.getLogger(__name__)


class MarketDataService:
    """Handles real-time market data streaming and technical analysis."""

    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        self.exchange: ccxt.Exchange | None = None
        self._ws_connections: dict[str, websockets.WebSocketClientProtocol] = {}
        self._subscribers: dict[str, list[Callable]] = {}

    async def initialize(self, api_key: str = "", api_secret: str = ""):
        exchange_class = getattr(ccxt, self.exchange_id)
        config = {"enableRateLimit": True}
        if api_key:
            config["apiKey"] = api_key
            config["secret"] = api_secret
        self.exchange = exchange_class(config)

    async def close(self):
        if self.exchange:
            await self.exchange.close()
        for ws in self._ws_connections.values():
            await ws.close()

    async def get_ohlcv(
        self, symbol: str, timeframe: str = "15m", limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV candle data from exchange."""
        if not self.exchange:
            await self.initialize()

        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    async def get_ticker(self, symbol: str) -> dict:
        """Get current ticker data."""
        if not self.exchange:
            await self.initialize()
        return await self.exchange.fetch_ticker(symbol)

    async def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get current order book."""
        if not self.exchange:
            await self.initialize()
        return await self.exchange.fetch_order_book(symbol, limit)

    def compute_indicators(self, df: pd.DataFrame) -> dict:
        """Compute technical indicators on OHLCV data."""
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # RSI
        rsi = RSIIndicator(close, window=14)
        current_rsi = float(rsi.rsi().iloc[-1])

        # MACD
        macd = MACD(close)
        macd_line = float(macd.macd().iloc[-1])
        signal_line = float(macd.macd_signal().iloc[-1])
        macd_histogram = float(macd.macd_diff().iloc[-1])

        # Bollinger Bands
        bb = BollingerBands(close, window=20)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        bb_middle = float(bb.bollinger_mavg().iloc[-1])

        # EMAs
        ema_9 = float(EMAIndicator(close, window=9).ema_indicator().iloc[-1])
        ema_21 = float(EMAIndicator(close, window=21).ema_indicator().iloc[-1])
        ema_50 = float(EMAIndicator(close, window=50).ema_indicator().iloc[-1])

        # Volume analysis
        avg_volume = float(volume.rolling(20).mean().iloc[-1])
        current_volume = float(volume.iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # Price action
        current_price = float(close.iloc[-1])
        price_change_pct = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)

        return {
            "current_price": current_price,
            "price_change_pct": round(price_change_pct, 4),
            "rsi": round(current_rsi, 2),
            "macd": {
                "line": round(macd_line, 4),
                "signal": round(signal_line, 4),
                "histogram": round(macd_histogram, 4),
            },
            "bollinger": {
                "upper": round(bb_upper, 2),
                "middle": round(bb_middle, 2),
                "lower": round(bb_lower, 2),
            },
            "ema": {
                "ema_9": round(ema_9, 2),
                "ema_21": round(ema_21, 2),
                "ema_50": round(ema_50, 2),
            },
            "volume_ratio": round(volume_ratio, 2),
            "trend": "bullish" if ema_9 > ema_21 > ema_50 else (
                "bearish" if ema_9 < ema_21 < ema_50 else "sideways"
            ),
        }

    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """Subscribe to real-time ticker updates via WebSocket."""
        ws_symbol = symbol.replace("/", "").lower()
        url = f"wss://stream.binance.com:9443/ws/{ws_symbol}@ticker"

        async def _listen():
            try:
                async with websockets.connect(url) as ws:
                    self._ws_connections[symbol] = ws
                    logger.info(f"WebSocket connected for {symbol}")
                    async for message in ws:
                        data = json.loads(message)
                        tick = {
                            "symbol": symbol,
                            "price": float(data.get("c", 0)),
                            "volume_24h": float(data.get("v", 0)),
                            "price_change_pct": float(data.get("P", 0)),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        await callback(tick)
            except Exception as e:
                logger.error(f"WebSocket error for {symbol}: {e}")

        asyncio.create_task(_listen())

    async def get_market_snapshot(self, symbol: str, timeframe: str = "15m") -> dict:
        """Get a comprehensive market snapshot for the agent."""
        df = await self.get_ohlcv(symbol, timeframe)
        indicators = self.compute_indicators(df)
        ticker = await self.get_ticker(symbol)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "indicators": indicators,
            "ticker": {
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask"),
                "last": ticker.get("last"),
                "volume": ticker.get("baseVolume"),
                "change_24h": ticker.get("percentage"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
