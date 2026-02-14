from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.schemas import UserProfile, RiskProfile, RiskLevel
from app.services.security import hash_password, encrypt_api_key

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    risk_level: RiskLevel = RiskLevel.MODERATE
    max_capital: float = 1000.0
    exchange: str = "binance"


class ExchangeKeysUpdate(BaseModel):
    api_key: str
    api_secret: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    risk_level: str
    max_capital: float
    exchange: str
    shadow_mode: bool
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/", response_model=UserResponse)
async def create_user(data: UserCreate, db: DbSession):
    existing = await db.execute(
        select(UserProfile).where(UserProfile.username == data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = UserProfile(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        risk_level=data.risk_level.value,
        max_capital=data.max_capital,
        exchange=data.exchange,
    )
    db.add(user)

    risk_profile = RiskProfile(user_id=user.id)
    db.add(risk_profile)

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: DbSession):
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}/exchange-keys")
async def update_exchange_keys(user_id: UUID, data: ExchangeKeysUpdate, db: DbSession):
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.encrypted_api_key = encrypt_api_key(data.api_key)
    user.encrypted_api_secret = encrypt_api_key(data.api_secret)
    await db.commit()
    return {"message": "Exchange keys updated and encrypted"}


@router.put("/{user_id}/toggle-shadow")
async def toggle_shadow_mode(user_id: UUID, db: DbSession):
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.shadow_mode = not user.shadow_mode
    await db.commit()
    return {"shadow_mode": user.shadow_mode}
