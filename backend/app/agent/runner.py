"""Agent Runner — Orchestrates the trading agent lifecycle.

This module manages the continuous execution loop of the agent,
running it on a schedule and handling the interaction between
the user's strategy and the agent graph.
"""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import create_trading_agent
from app.models.schemas import Strategy, UserProfile
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class AgentRunner:
    """Manages the lifecycle of a trading agent for a user."""

    def __init__(self, db: AsyncSession, user_id: UUID, strategy_id: UUID):
        self.db = db
        self.user_id = user_id
        self.strategy_id = strategy_id
        self.agent = create_trading_agent()
        self.notifier = NotificationService()
        self._running = False

    async def run_single_cycle(self) -> dict:
        """Run one complete perception → execution cycle."""
        user = await self._get_user()
        strategy = await self._get_strategy()

        if not user or not strategy:
            return {"error": "User or strategy not found"}

        initial_state = {
            "user_id": str(self.user_id),
            "strategy_id": str(self.strategy_id),
            "risk_level": user.risk_level,
            "shadow_mode": user.shadow_mode,
            "pairs": strategy.pairs or ["BTC/USDT"],
            "strategy_rules": strategy.parsed_rules or {},
            "market_data": {},
            "sentiment_data": {},
            "evaluation": {},
            "past_lessons": [],
            "should_trade": False,
            "trade_direction": "none",
            "confidence": 0.0,
            "reasoning": "",
            "trade_params": {},
            "trade_result": {},
            "risk_check": {},
            "thoughts": [],
            "current_step": "init",
            "error": "",
        }

        try:
            result = await self.agent.ainvoke(initial_state)
            logger.info(
                f"Agent cycle complete for user {self.user_id}: "
                f"traded={result.get('should_trade')}, "
                f"confidence={result.get('confidence', 0):.2f}"
            )
            return result
        except Exception as e:
            logger.error(f"Agent cycle failed: {e}")
            await self.notifier.send_risk_alert(f"Agent error: {e}")
            return {"error": str(e)}

    async def run_continuous(self, interval_seconds: int = 60):
        """Run the agent continuously on a schedule."""
        self._running = True
        logger.info(
            f"Starting continuous agent for user {self.user_id}, "
            f"interval={interval_seconds}s"
        )

        while self._running:
            try:
                await self.run_single_cycle()
            except Exception as e:
                logger.error(f"Continuous cycle error: {e}")
                await self.notifier.send_risk_alert(
                    f"Continuous agent error: {e}"
                )
            await asyncio.sleep(interval_seconds)

    def stop(self):
        """Stop the continuous agent loop."""
        self._running = False
        logger.info(f"Agent stopped for user {self.user_id}")

    async def _get_user(self) -> UserProfile | None:
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.id == self.user_id)
        )
        return result.scalar_one_or_none()

    async def _get_strategy(self) -> Strategy | None:
        result = await self.db.execute(
            select(Strategy).where(Strategy.id == self.strategy_id)
        )
        return result.scalar_one_or_none()
