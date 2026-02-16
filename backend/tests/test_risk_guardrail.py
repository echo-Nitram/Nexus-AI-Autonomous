"""Tests for the Risk Guardrail — the deterministic safety layer."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.risk_guardrail import RiskGuardrail


def _make_user(max_capital=5000.0, max_daily_loss_pct=0.02):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.max_capital = max_capital
    user.max_daily_loss_pct = max_daily_loss_pct
    return user


def _make_risk_profile(
    max_position_size_pct=0.05,
    max_open_positions=5,
    max_daily_trades=20,
):
    profile = MagicMock()
    profile.max_position_size_pct = max_position_size_pct
    profile.max_open_positions = max_open_positions
    profile.max_daily_trades = max_daily_trades
    return profile


class TestRiskGuardrail:
    """Test suite for deterministic risk checks."""

    def test_check_position_size_within_limit(self):
        user = _make_user(max_capital=10000.0)
        risk = _make_risk_profile(max_position_size_pct=0.05)
        guardrail = RiskGuardrail(AsyncMock())

        # Position value = 0.01 * 97000 = $970 <= $500 max → should fail
        passed, reason = guardrail._check_position_size(user, risk, 0.005, 97000.0)
        assert passed is True

    def test_check_position_size_exceeds_limit(self):
        user = _make_user(max_capital=1000.0)
        risk = _make_risk_profile(max_position_size_pct=0.05)
        guardrail = RiskGuardrail(AsyncMock())

        # Position value = 1.0 * 97000 = $97,000 >> $50 max
        passed, reason = guardrail._check_position_size(user, risk, 1.0, 97000.0)
        assert passed is False
        assert "exceeds max" in reason

    def test_check_valid_pair_format(self):
        assert RiskGuardrail._check_valid_pair("BTC/USDT") == (True, "")
        assert RiskGuardrail._check_valid_pair("ETH/BTC") == (True, "")

    def test_check_invalid_pair_format(self):
        passed, reason = RiskGuardrail._check_valid_pair("BTCUSDT")
        assert passed is False
        assert "Invalid" in reason

        passed, reason = RiskGuardrail._check_valid_pair("A/B")
        assert passed is False

    @pytest.mark.asyncio
    async def test_check_max_open_positions_within_limit(self, mock_db):
        risk = _make_risk_profile(max_open_positions=5)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_db.execute.return_value = mock_result

        guardrail = RiskGuardrail(mock_db)
        passed, reason = await guardrail._check_max_open_positions(uuid.uuid4(), risk)
        assert passed is True

    @pytest.mark.asyncio
    async def test_check_max_open_positions_at_limit(self, mock_db):
        risk = _make_risk_profile(max_open_positions=5)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        guardrail = RiskGuardrail(mock_db)
        passed, reason = await guardrail._check_max_open_positions(uuid.uuid4(), risk)
        assert passed is False
        assert "Max open positions" in reason

    @pytest.mark.asyncio
    async def test_check_daily_loss_within_limit(self, mock_db):
        user = _make_user(max_capital=10000.0, max_daily_loss_pct=0.02)
        mock_result = MagicMock()
        mock_result.scalar.return_value = -50.0  # $50 loss, limit is $200
        mock_db.execute.return_value = mock_result

        guardrail = RiskGuardrail(mock_db)
        passed, reason = await guardrail._check_daily_loss_limit(uuid.uuid4(), user)
        assert passed is True

    @pytest.mark.asyncio
    async def test_check_daily_loss_at_limit(self, mock_db):
        user = _make_user(max_capital=5000.0, max_daily_loss_pct=0.02)
        mock_result = MagicMock()
        mock_result.scalar.return_value = -100.0  # $100 loss, limit is $100
        mock_db.execute.return_value = mock_result

        guardrail = RiskGuardrail(mock_db)
        passed, reason = await guardrail._check_daily_loss_limit(uuid.uuid4(), user)
        assert passed is False
        assert "Daily loss limit" in reason
