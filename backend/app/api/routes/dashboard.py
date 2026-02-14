from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, func

from app.api.deps import DbSession
from app.models.schemas import TradeOrder, TradeStatus, AgentThought

router = APIRouter()


class PortfolioSummary(BaseModel):
    total_trades: int
    open_positions: int
    total_pnl: float
    win_rate: float
    shadow_trades: int


class ThoughtLog(BaseModel):
    id: str
    step: str
    content: str
    context: dict | None
    timestamp: str

    model_config = {"from_attributes": True}


@router.get("/portfolio/{user_id}", response_model=PortfolioSummary)
async def get_portfolio_summary(user_id: UUID, db: DbSession):
    # Total trades
    total_result = await db.execute(
        select(func.count(TradeOrder.id)).where(TradeOrder.user_id == user_id)
    )
    total_trades = total_result.scalar() or 0

    # Open positions
    open_result = await db.execute(
        select(func.count(TradeOrder.id)).where(
            TradeOrder.user_id == user_id,
            TradeOrder.status == TradeStatus.OPEN.value,
        )
    )
    open_positions = open_result.scalar() or 0

    # Total PnL
    pnl_result = await db.execute(
        select(func.coalesce(func.sum(TradeOrder.pnl), 0.0)).where(
            TradeOrder.user_id == user_id,
            TradeOrder.status == TradeStatus.CLOSED.value,
        )
    )
    total_pnl = float(pnl_result.scalar() or 0)

    # Win rate
    wins_result = await db.execute(
        select(func.count(TradeOrder.id)).where(
            TradeOrder.user_id == user_id,
            TradeOrder.status == TradeStatus.CLOSED.value,
            TradeOrder.pnl > 0,
        )
    )
    wins = wins_result.scalar() or 0

    closed_result = await db.execute(
        select(func.count(TradeOrder.id)).where(
            TradeOrder.user_id == user_id,
            TradeOrder.status == TradeStatus.CLOSED.value,
        )
    )
    closed_total = closed_result.scalar() or 0
    win_rate = (wins / closed_total * 100) if closed_total > 0 else 0.0

    # Shadow trades
    shadow_result = await db.execute(
        select(func.count(TradeOrder.id)).where(
            TradeOrder.user_id == user_id,
            TradeOrder.is_shadow.is_(True),
        )
    )
    shadow_trades = shadow_result.scalar() or 0

    return PortfolioSummary(
        total_trades=total_trades,
        open_positions=open_positions,
        total_pnl=total_pnl,
        win_rate=win_rate,
        shadow_trades=shadow_trades,
    )


@router.get("/thoughts/{user_id}", response_model=list[ThoughtLog])
async def get_agent_thoughts(user_id: UUID, db: DbSession, limit: int = 100):
    """Get the AI agent's thought log — its reasoning for each decision."""
    result = await db.execute(
        select(AgentThought)
        .where(AgentThought.user_id == user_id)
        .order_by(AgentThought.timestamp.desc())
        .limit(limit)
    )
    thoughts = result.scalars().all()
    return [
        ThoughtLog(
            id=str(t.id),
            step=t.step,
            content=t.content,
            context=t.context,
            timestamp=t.timestamp.isoformat(),
        )
        for t in thoughts
    ]
