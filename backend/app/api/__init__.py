from fastapi import APIRouter

from app.api.routes import trading, strategies, dashboard, users, agent
from app.api.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
router.include_router(trading.router, prefix="/trading", tags=["Trading"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(agent.router, prefix="/agent", tags=["Agent"])
