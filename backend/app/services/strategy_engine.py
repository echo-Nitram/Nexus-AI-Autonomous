"""Strategy Engine — Natural Language Strategy Parser.

Converts user-written strategies in plain language into structured
trading rules using an LLM.
"""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings

logger = logging.getLogger(__name__)

STRATEGY_PARSER_PROMPT = """You are a trading strategy parser. Your job is to convert
natural language trading strategies into structured JSON rules.

Given a strategy description, extract:
1. entry_conditions: List of conditions that must be true to enter a trade
2. exit_conditions: List of conditions to exit a trade
3. indicators: Which technical indicators are needed (RSI, MACD, EMA, BB, etc.)
4. timeframe: The preferred candle timeframe
5. sentiment_filter: Whether social/news sentiment should be considered
6. pair_preferences: Which trading pairs to focus on
7. position_sizing: How to size positions (percentage of capital)
8. risk_management: Stop loss, take profit rules

Return a valid JSON object with these fields. Be precise and specific.

Example input: "Busca divergencias en el RSI de 15m pero solo opera si el sentimiento
en Twitter es alcista"

Example output:
{
  "entry_conditions": [
    {"type": "rsi_divergence", "timeframe": "15m", "direction": "bullish"},
    {"type": "sentiment", "source": "social", "required": "bullish"}
  ],
  "exit_conditions": [
    {"type": "rsi", "threshold": 70, "action": "close_long"},
    {"type": "stop_loss", "percentage": 2}
  ],
  "indicators": ["RSI", "price_action"],
  "timeframe": "15m",
  "sentiment_filter": true,
  "pair_preferences": [],
  "position_sizing": {"type": "percentage", "value": 5},
  "risk_management": {"stop_loss_pct": 2, "take_profit_pct": 4}
}"""


class StrategyEngine:
    """Parses natural language strategies into structured trading rules."""

    def __init__(self):
        self.settings = get_settings()
        self.llm = self._create_llm()

    def _create_llm(self):
        if self.settings.llm_provider == "anthropic":
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=self.settings.anthropic_api_key,
                temperature=0,
                max_tokens=2000,
            )
        else:
            return ChatOpenAI(
                model="gpt-4o",
                api_key=self.settings.openai_api_key,
                temperature=0,
                max_tokens=2000,
            )

    async def parse_strategy(self, description: str) -> dict:
        """Convert a natural language strategy into structured rules."""
        try:
            messages = [
                SystemMessage(content=STRATEGY_PARSER_PROMPT),
                HumanMessage(content=f"Parse this trading strategy:\n\n{description}"),
            ]
            response = await self.llm.ainvoke(messages)

            import json
            content = response.content
            # Extract JSON from possible markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"Strategy parsing failed: {e}")
            return {
                "raw_description": description,
                "parse_error": str(e),
                "entry_conditions": [],
                "exit_conditions": [],
                "indicators": [],
                "timeframe": "15m",
                "sentiment_filter": False,
            }

    async def evaluate_conditions(
        self, parsed_rules: dict, market_state: dict, sentiment: dict
    ) -> dict:
        """Ask the LLM to evaluate if current conditions match the strategy."""
        prompt = f"""Given the following trading strategy rules and current market state,
determine if there is a trading opportunity.

STRATEGY RULES:
{parsed_rules}

CURRENT MARKET STATE:
{market_state}

CURRENT SENTIMENT:
{sentiment}

Analyze the data and respond with a JSON object:
{{
  "should_trade": true/false,
  "direction": "long" or "short" or "none",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of why this trade should or should not be taken",
  "suggested_size_pct": 0.01-0.05,
  "suggested_stop_loss_pct": 0.01-0.05,
  "suggested_take_profit_pct": 0.02-0.10
}}"""

        try:
            messages = [
                SystemMessage(content="You are a quantitative trading analyst. Be conservative and data-driven."),
                HumanMessage(content=prompt),
            ]
            response = await self.llm.ainvoke(messages)

            import json
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"Strategy evaluation failed: {e}")
            return {
                "should_trade": False,
                "direction": "none",
                "confidence": 0.0,
                "reasoning": f"Evaluation error: {e}",
            }
