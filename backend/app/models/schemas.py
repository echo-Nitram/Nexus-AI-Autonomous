import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    Integer,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.models.database import Base


class TradeSide(str, Enum):
    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    SCALPER = "scalper"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    risk_level = Column(String(20), default=RiskLevel.MODERATE.value)
    max_capital = Column(Float, default=1000.0)
    max_daily_loss_pct = Column(Float, default=0.02)
    max_position_size_pct = Column(Float, default=0.05)
    exchange = Column(String(50), default="binance")
    encrypted_api_key = Column(Text, nullable=True)
    encrypted_api_secret = Column(Text, nullable=True)
    shadow_mode = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)  # Natural language strategy
    parsed_rules = Column(JSON, nullable=True)  # LLM-parsed structured rules
    timeframe = Column(String(10), default="15m")
    pairs = Column(JSON, default=list)  # ["BTC/USDT", "ETH/USDT"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    max_drawdown_pct = Column(Float, default=0.10)
    max_position_size_pct = Column(Float, default=0.05)
    max_daily_trades = Column(Integer, default=20)
    max_open_positions = Column(Integer, default=5)
    stop_loss_pct = Column(Float, default=0.02)
    take_profit_pct = Column(Float, default=0.04)
    trailing_stop = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TradeOrder(Base):
    __tablename__ = "trade_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True)
    exchange = Column(String(50), nullable=False)
    pair = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String(20), default=TradeStatus.PENDING.value)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    is_shadow = Column(Boolean, default=True)
    exchange_order_id = Column(String(100), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)


class TradeLog(Base):
    __tablename__ = "trade_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trade_orders.id"), nullable=False)
    event = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AgentThought(Base):
    __tablename__ = "agent_thoughts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    session_id = Column(String(100), nullable=False)
    step = Column(String(50), nullable=False)  # perception, reasoning, action
    content = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    embedding = Column(Vector(1536), nullable=True)  # For long-term memory search
