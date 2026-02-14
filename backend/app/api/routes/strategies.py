from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.schemas import Strategy
from app.services.strategy_engine import StrategyEngine

router = APIRouter()


class StrategyCreate(BaseModel):
    user_id: UUID
    name: str
    description: str  # Natural language strategy
    timeframe: str = "15m"
    pairs: list[str] = ["BTC/USDT"]


class StrategyResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    parsed_rules: Optional[dict] = None
    timeframe: str
    pairs: list[str]
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/", response_model=StrategyResponse)
async def create_strategy(data: StrategyCreate, db: DbSession):
    engine = StrategyEngine()
    parsed_rules = await engine.parse_strategy(data.description)

    strategy = Strategy(
        user_id=data.user_id,
        name=data.name,
        description=data.description,
        parsed_rules=parsed_rules,
        timeframe=data.timeframe,
        pairs=data.pairs,
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


@router.get("/user/{user_id}", response_model=list[StrategyResponse])
async def get_user_strategies(user_id: UUID, db: DbSession):
    result = await db.execute(
        select(Strategy).where(Strategy.user_id == user_id, Strategy.is_active.is_(True))
    )
    return result.scalars().all()


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: UUID, db: DbSession):
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.delete("/{strategy_id}")
async def deactivate_strategy(strategy_id: UUID, db: DbSession):
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    strategy.is_active = False
    await db.commit()
    return {"message": "Strategy deactivated"}
