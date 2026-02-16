"""Shared test fixtures for Nexus AI Trader tests."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "risk_level": "moderate",
        "max_capital": 5000.0,
        "exchange": "binance",
    }


@pytest.fixture
def sample_strategy_data():
    return {
        "name": "RSI Divergence",
        "description": "Buy BTC when RSI < 30 on 1h timeframe. Take profit at +5%, stop loss at -2%",
        "timeframe": "1h",
        "pairs": ["BTC/USDT"],
    }


@pytest.fixture
def sample_market_snapshot():
    return {
        "pair": "BTC/USDT",
        "timeframe": "1h",
        "candles": [],
        "indicators": {
            "current_price": 97250.0,
            "rsi": 42.3,
            "macd": {"macd": 150.0, "signal": 120.0, "histogram": 30.0},
            "bollinger": {"upper": 98000.0, "middle": 96500.0, "lower": 95000.0},
            "ema_9": 97100.0,
            "ema_21": 96800.0,
            "ema_50": 96000.0,
            "volume_ratio": 1.45,
            "price_change_pct": 0.85,
            "trend": "sideways",
        },
    }
