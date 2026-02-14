from fastapi import APIRouter

from app.api.routes import trading, strategies, dashboard, users

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
router.include_router(trading.router, prefix="/trading", tags=["Trading"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
