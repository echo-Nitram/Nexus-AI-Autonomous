"""Risk Guardrail — Hard-coded safety layer (NO AI, pure deterministic logic).

This module blocks any trade that violates the user's risk parameters.
The AI agent CANNOT override these rules.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import TradeOrder, TradeStatus, UserProfile, RiskProfile

logger = logging.getLogger(__name__)


class RiskGuardrail:
    """Deterministic risk management — the AI cannot bypass this layer."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_trade(
        self,
        user_id: UUID,
        pair: str,
        side: str,
        size: float,
        entry_price: float | None = None,
    ) -> tuple[bool, str]:
        """
        Validate a proposed trade against all risk rules.
        Returns (is_allowed, reason).
        """
        user = await self._get_user(user_id)
        if not user:
            return False, "User not found"

        risk_profile = await self._get_risk_profile(user_id)
        if not risk_profile:
            return False, "Risk profile not configured"

        checks = [
            self._check_position_size(user, risk_profile, size, entry_price),
            await self._check_max_open_positions(user_id, risk_profile),
            await self._check_daily_loss_limit(user_id, user),
            await self._check_daily_trade_count(user_id, risk_profile),
            self._check_valid_pair(pair),
        ]

        for passed, reason in checks:
            if not passed:
                logger.warning(f"Trade BLOCKED for user {user_id}: {reason}")
                return False, reason

        logger.info(f"Trade APPROVED for user {user_id}: {pair} {side} size={size}")
        return True, "Trade approved"

    async def _get_user(self, user_id: UUID) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_risk_profile(self, user_id: UUID) -> RiskProfile | None:
        result = await self.db.execute(
            select(RiskProfile).where(RiskProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _check_position_size(
        self,
        user: UserProfile,
        risk: RiskProfile,
        size: float,
        entry_price: float | None,
    ) -> tuple[bool, str]:
        """Ensure position doesn't exceed max allowed % of capital."""
        max_size = user.max_capital * risk.max_position_size_pct
        position_value = size * (entry_price or 1)

        if position_value > max_size:
            return False, (
                f"Position value ${position_value:.2f} exceeds max "
                f"${max_size:.2f} ({risk.max_position_size_pct*100}% of capital)"
            )
        return True, ""

    async def _check_max_open_positions(
        self, user_id: UUID, risk: RiskProfile
    ) -> tuple[bool, str]:
        """Ensure user doesn't have too many open positions."""
        result = await self.db.execute(
            select(func.count(TradeOrder.id)).where(
                TradeOrder.user_id == user_id,
                TradeOrder.status == TradeStatus.OPEN.value,
            )
        )
        open_count = result.scalar() or 0

        if open_count >= risk.max_open_positions:
            return False, f"Max open positions reached ({risk.max_open_positions})"
        return True, ""

    async def _check_daily_loss_limit(
        self, user_id: UUID, user: UserProfile
    ) -> tuple[bool, str]:
        """Ensure daily losses haven't exceeded the limit."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.coalesce(func.sum(TradeOrder.pnl), 0.0)).where(
                TradeOrder.user_id == user_id,
                TradeOrder.status == TradeStatus.CLOSED.value,
                TradeOrder.closed_at >= today,
                TradeOrder.pnl < 0,
            )
        )
        daily_loss = abs(float(result.scalar() or 0))
        max_loss = user.max_capital * user.max_daily_loss_pct

        if daily_loss >= max_loss:
            return False, (
                f"Daily loss limit reached: ${daily_loss:.2f} / ${max_loss:.2f}"
            )
        return True, ""

    async def _check_daily_trade_count(
        self, user_id: UUID, risk: RiskProfile
    ) -> tuple[bool, str]:
        """Ensure daily trade count hasn't exceeded the limit."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.count(TradeOrder.id)).where(
                TradeOrder.user_id == user_id,
                TradeOrder.created_at >= today,
            )
        )
        count = result.scalar() or 0

        if count >= risk.max_daily_trades:
            return False, f"Daily trade limit reached ({risk.max_daily_trades})"
        return True, ""

    @staticmethod
    def _check_valid_pair(pair: str) -> tuple[bool, str]:
        """Basic validation of trading pair format."""
        if "/" not in pair or len(pair) < 5:
            return False, f"Invalid trading pair format: {pair}"
        return True, ""
