"""Action Layer — Trade Execution via CCXT.

The LLM never writes execution code. It invokes these pre-validated functions.
"""

import logging
from datetime import datetime
from uuid import UUID

import ccxt.async_support as ccxt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.schemas import TradeOrder, TradeLog, TradeStatus, UserProfile
from app.services.security import decrypt_api_key
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Executes trades on exchanges. Used as a tool by the LLM agent."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.notifier = NotificationService()

    async def _get_exchange(self, user: UserProfile) -> ccxt.Exchange:
        """Create an authenticated exchange instance for a user."""
        exchange_class = getattr(ccxt, user.exchange)
        config = {"enableRateLimit": True}

        if not user.shadow_mode and user.encrypted_api_key:
            config["apiKey"] = decrypt_api_key(user.encrypted_api_key)
            config["secret"] = decrypt_api_key(user.encrypted_api_secret)

        return exchange_class(config)

    async def execute(
        self,
        user_id: UUID,
        pair: str,
        side: str,
        size: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        strategy_id: UUID | None = None,
        reasoning: str = "",
    ) -> TradeOrder:
        """
        Execute a trade — the core function called by the agent.

        In shadow mode, the trade is simulated (recorded but not sent to exchange).
        In production mode, it places a real order via CCXT.
        """
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        exchange = await self._get_exchange(user)

        try:
            ticker = await exchange.fetch_ticker(pair)
            entry_price = ticker["last"]

            order = TradeOrder(
                user_id=user_id,
                strategy_id=strategy_id,
                exchange=user.exchange,
                pair=pair,
                side=side,
                size=size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status=TradeStatus.OPEN.value,
                is_shadow=user.shadow_mode,
                metadata_={"reasoning": reasoning},
            )

            if not user.shadow_mode:
                # Real execution
                order_type = "market"
                exchange_order = await exchange.create_order(
                    symbol=pair,
                    type=order_type,
                    side="buy" if side == "long" else "sell",
                    amount=size,
                )
                order.exchange_order_id = exchange_order.get("id")
                logger.info(f"LIVE order placed: {pair} {side} size={size}")
            else:
                logger.info(f"SHADOW order recorded: {pair} {side} size={size}")

            self.db.add(order)

            # Log the trade event
            log = TradeLog(
                trade_id=order.id,
                event="opened",
                details={
                    "entry_price": entry_price,
                    "size": size,
                    "side": side,
                    "shadow": user.shadow_mode,
                    "reasoning": reasoning,
                },
            )
            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(order)

            # Notify
            mode = "SHADOW" if user.shadow_mode else "LIVE"
            await self.notifier.send_trade_alert(
                f"[{mode}] {side.upper()} {pair}\n"
                f"Size: {size} @ ${entry_price:,.2f}\n"
                f"SL: {stop_loss or 'None'} | TP: {take_profit or 'None'}\n"
                f"Reason: {reasoning[:200]}"
            )

            return order

        finally:
            await exchange.close()

    async def close_position(self, trade: TradeOrder) -> TradeOrder:
        """Close an existing position."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.id == trade.user_id)
        )
        user = result.scalar_one_or_none()
        exchange = await self._get_exchange(user)

        try:
            ticker = await exchange.fetch_ticker(trade.pair)
            exit_price = ticker["last"]

            if trade.side == "long":
                pnl = (exit_price - trade.entry_price) * trade.size
            else:
                pnl = (trade.entry_price - exit_price) * trade.size

            pnl_pct = pnl / (trade.entry_price * trade.size) * 100

            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_pct = pnl_pct
            trade.status = TradeStatus.CLOSED.value
            trade.closed_at = datetime.utcnow()

            if not user.shadow_mode and trade.exchange_order_id:
                opposite_side = "sell" if trade.side == "long" else "buy"
                await exchange.create_order(
                    symbol=trade.pair,
                    type="market",
                    side=opposite_side,
                    amount=trade.size,
                )

            log = TradeLog(
                trade_id=trade.id,
                event="closed",
                details={
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                },
            )
            self.db.add(log)
            await self.db.commit()

            emoji = "+" if pnl >= 0 else ""
            await self.notifier.send_trade_alert(
                f"CLOSED {trade.pair}\n"
                f"PnL: {emoji}${pnl:,.2f} ({emoji}{pnl_pct:.2f}%)"
            )

            return trade

        finally:
            await exchange.close()
