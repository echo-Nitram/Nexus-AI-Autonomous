"""Agent management endpoints — start, stop, and check status of the trading agent."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.schemas import Strategy, UserProfile

router = APIRouter()


class AgentStartRequest(BaseModel):
    user_id: UUID
    strategy_id: UUID
    interval_seconds: int = 300


class AgentStatusResponse(BaseModel):
    running: bool
    user_id: str | None = None
    strategy_id: str | None = None


# In-memory registry of running agents (single-process; use Redis for multi-process)
_running_agents: dict[str, object] = {}


@router.post("/start")
async def start_agent(req: AgentStartRequest, db: DbSession):
    """Start the trading agent for a user/strategy pair."""
    import asyncio
    from app.agent.runner import AgentRunner

    key = f"{req.user_id}:{req.strategy_id}"
    if key in _running_agents:
        raise HTTPException(status_code=409, detail="Agent already running for this user/strategy")

    # Validate user and strategy exist
    user_result = await db.execute(select(UserProfile).where(UserProfile.id == req.user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    strategy_result = await db.execute(select(Strategy).where(Strategy.id == req.strategy_id))
    if not strategy_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Strategy not found")

    runner = AgentRunner(db, req.user_id, req.strategy_id)
    _running_agents[key] = runner

    asyncio.create_task(runner.run_continuous(req.interval_seconds))

    return {
        "message": "Agent started",
        "user_id": str(req.user_id),
        "strategy_id": str(req.strategy_id),
        "interval_seconds": req.interval_seconds,
    }


@router.post("/stop")
async def stop_agent(req: AgentStartRequest):
    """Stop a running trading agent."""
    key = f"{req.user_id}:{req.strategy_id}"
    runner = _running_agents.pop(key, None)
    if not runner:
        raise HTTPException(status_code=404, detail="No running agent found for this user/strategy")

    runner.stop()
    return {"message": "Agent stopped"}


@router.get("/status/{user_id}", response_model=list[AgentStatusResponse])
async def get_agent_status(user_id: UUID):
    """Check which agents are running for a user."""
    results = []
    for key, runner in _running_agents.items():
        uid, sid = key.split(":")
        if uid == str(user_id):
            results.append(AgentStatusResponse(
                running=True,
                user_id=uid,
                strategy_id=sid,
            ))
    return results
