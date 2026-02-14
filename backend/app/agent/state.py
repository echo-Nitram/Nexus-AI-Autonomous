"""Agent State — Typed state for the LangGraph trading agent."""

from typing import Annotated, TypedDict
from operator import add


class AgentState(TypedDict):
    """The state that flows through the LangGraph trading agent."""

    # User context
    user_id: str
    strategy_id: str
    risk_level: str
    shadow_mode: bool

    # Perception
    market_data: dict         # Technical indicators + price data
    sentiment_data: dict      # News + Fear/Greed + social sentiment
    pairs: list[str]          # Trading pairs to monitor

    # Reasoning
    strategy_rules: dict      # Parsed strategy rules
    evaluation: dict          # LLM evaluation result
    past_lessons: list[dict]  # Recalled memory from similar situations

    # Decision
    should_trade: bool
    trade_direction: str      # "long", "short", "none"
    confidence: float
    reasoning: str

    # Action
    trade_params: dict        # pair, side, size, stop_loss, take_profit
    trade_result: dict        # Result from execution
    risk_check: dict          # Result from risk guardrail

    # Agent log
    thoughts: Annotated[list[dict], add]  # Accumulated thought log
    current_step: str
    error: str
