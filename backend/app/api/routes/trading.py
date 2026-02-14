from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.schemas import TradeOrder, TradeStatus

router = APIRouter()


class ManualTradeRequest(BaseModel):
    user_id: UUID
    pair: str
    side: str
    size: float
    stop_loss: float | None = None
    take_profit: float | None = None


class TradeResponse(BaseModel):
    id: UUID
    pair: str
    side: str
    size: float
    entry_price: float | None
    status: str
    is_shadow: bool
    pnl: float | None

    model_config = {"from_attributes": True}


@router.post("/execute", response_model=TradeResponse)
async def execute_trade(trade: ManualTradeRequest, db: DbSession):
    """Execute a manual trade (goes through risk guardrails)."""
    from app.services.risk_guardrail import RiskGuardrail
    from app.services.executor import TradeExecutor

    guardrail = RiskGuardrail(db)
    is_allowed, reason = await guardrail.check_trade(
        user_id=trade.user_id,
        pair=trade.pair,
        side=trade.side,
        size=trade.size,
    )

    if not is_allowed:
        raise HTTPException(status_code=403, detail=f"Trade rejected by risk guardrail: {reason}")

    executor = TradeExecutor(db)
    order = await executor.execute(
        user_id=trade.user_id,
        pair=trade.pair,
        side=trade.side,
        size=trade.size,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
    )
    return order


@router.get("/positions/{user_id}", response_model=list[TradeResponse])
async def get_open_positions(user_id: UUID, db: DbSession):
    result = await db.execute(
        select(TradeOrder).where(
            TradeOrder.user_id == user_id,
            TradeOrder.status == TradeStatus.OPEN.value,
        )
    )
    return result.scalars().all()


@router.get("/history/{user_id}", response_model=list[TradeResponse])
async def get_trade_history(user_id: UUID, db: DbSession, limit: int = 50):
    result = await db.execute(
        select(TradeOrder)
        .where(TradeOrder.user_id == user_id)
        .order_by(TradeOrder.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/close/{trade_id}")
async def close_trade(trade_id: UUID, db: DbSession):
    from app.services.executor import TradeExecutor

    result = await db.execute(select(TradeOrder).where(TradeOrder.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    executor = TradeExecutor(db)
    closed = await executor.close_position(trade)
    return {"message": "Position closed", "pnl": closed.pnl}
