"""LangGraph Trading Agent — The orchestration brain.

This is the core of Nexus AI. It defines a stateful graph where each node
represents a step in the agent's reasoning cycle:

  Perceive → Recall Memory → Reason → Decide → Check Risk → Execute → Reflect

The agent "thinks" before it acts, and learns from outcomes.
"""

import logging
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def create_trading_agent() -> StateGraph:
    """Build the LangGraph trading agent."""

    graph = StateGraph(AgentState)

    # ─── Node Definitions ───────────────────────────────────────────

    async def perceive(state: AgentState) -> dict:
        """Step 1: Gather market data and sentiment."""
        from app.services.market_data import MarketDataService
        from app.services.sentiment import SentimentService

        market_service = MarketDataService()
        sentiment_service = SentimentService()

        thoughts = []
        all_market_data = {}
        all_sentiment = {}

        try:
            await market_service.initialize()

            for pair in state["pairs"]:
                snapshot = await market_service.get_market_snapshot(pair)
                all_market_data[pair] = snapshot

                sentiment = await sentiment_service.analyze_sentiment(pair)
                all_sentiment[pair] = sentiment

                thoughts.append({
                    "step": "perception",
                    "content": (
                        f"Analyzed {pair}: price=${snapshot['indicators']['current_price']:,.2f}, "
                        f"RSI={snapshot['indicators']['rsi']}, "
                        f"trend={snapshot['indicators']['trend']}, "
                        f"sentiment={sentiment['overall_sentiment']}"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            logger.error(f"Perception error: {e}")
            thoughts.append({
                "step": "perception",
                "content": f"Error gathering market data: {e}",
                "timestamp": datetime.utcnow().isoformat(),
            })
        finally:
            await market_service.close()
            await sentiment_service.close()

        return {
            "market_data": all_market_data,
            "sentiment_data": all_sentiment,
            "thoughts": thoughts,
            "current_step": "perceive",
        }

    async def recall_memory(state: AgentState) -> dict:
        """Step 2: Recall similar past situations from long-term memory."""
        from app.models.database import async_session
        from app.services.memory import MemoryService

        thoughts = []
        lessons = []

        try:
            async with async_session() as db:
                memory = MemoryService(db)
                lessons = await memory.get_trade_lessons(state["user_id"])

                if lessons:
                    thoughts.append({
                        "step": "memory",
                        "content": f"Recalled {len(lessons)} past trade outcomes for learning.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                else:
                    thoughts.append({
                        "step": "memory",
                        "content": "No past trade history to learn from yet.",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            logger.error(f"Memory recall error: {e}")
            thoughts.append({
                "step": "memory",
                "content": f"Memory recall skipped: {e}",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {
            "past_lessons": lessons,
            "thoughts": thoughts,
            "current_step": "recall",
        }

    async def reason(state: AgentState) -> dict:
        """Step 3: Evaluate strategy conditions against current market state."""
        from app.services.strategy_engine import StrategyEngine

        engine = StrategyEngine()
        thoughts = []
        best_eval = {
            "should_trade": False,
            "direction": "none",
            "confidence": 0.0,
            "reasoning": "No opportunity found",
        }
        best_pair = None

        for pair in state["pairs"]:
            market = state["market_data"].get(pair, {})
            sentiment = state["sentiment_data"].get(pair, {})

            if not market:
                continue

            evaluation = await engine.evaluate_conditions(
                parsed_rules=state["strategy_rules"],
                market_state=market,
                sentiment=sentiment,
            )

            thoughts.append({
                "step": "reasoning",
                "content": (
                    f"Evaluated {pair}: should_trade={evaluation.get('should_trade')}, "
                    f"direction={evaluation.get('direction')}, "
                    f"confidence={evaluation.get('confidence', 0):.2f}\n"
                    f"Reasoning: {evaluation.get('reasoning', 'N/A')}"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            })

            if (
                evaluation.get("should_trade")
                and evaluation.get("confidence", 0) > best_eval.get("confidence", 0)
            ):
                best_eval = evaluation
                best_pair = pair

        return {
            "evaluation": best_eval,
            "should_trade": best_eval.get("should_trade", False),
            "trade_direction": best_eval.get("direction", "none"),
            "confidence": best_eval.get("confidence", 0.0),
            "reasoning": best_eval.get("reasoning", ""),
            "trade_params": {
                "pair": best_pair,
                "side": best_eval.get("direction", "none"),
                "size_pct": best_eval.get("suggested_size_pct", 0.02),
                "stop_loss_pct": best_eval.get("suggested_stop_loss_pct", 0.02),
                "take_profit_pct": best_eval.get("suggested_take_profit_pct", 0.04),
            } if best_pair else {},
            "thoughts": thoughts,
            "current_step": "reason",
        }

    async def check_risk(state: AgentState) -> dict:
        """Step 4: Pass the proposed trade through the hard-coded risk guardrail."""
        from app.models.database import async_session
        from app.services.risk_guardrail import RiskGuardrail

        thoughts = []
        risk_result = {"approved": False, "reason": "No trade proposed"}

        if state["should_trade"] and state["trade_params"]:
            try:
                async with async_session() as db:
                    guardrail = RiskGuardrail(db)
                    params = state["trade_params"]
                    approved, reason = await guardrail.check_trade(
                        user_id=state["user_id"],
                        pair=params["pair"],
                        side=params["side"],
                        size=params.get("size", 0),
                    )
                    risk_result = {"approved": approved, "reason": reason}

                    thoughts.append({
                        "step": "risk_check",
                        "content": f"Risk guardrail: {'APPROVED' if approved else 'BLOCKED'} — {reason}",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                risk_result = {"approved": False, "reason": f"Risk check error: {e}"}
                thoughts.append({
                    "step": "risk_check",
                    "content": f"Risk check failed: {e}",
                    "timestamp": datetime.utcnow().isoformat(),
                })
        else:
            thoughts.append({
                "step": "risk_check",
                "content": "No trade to evaluate — skipping risk check.",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {
            "risk_check": risk_result,
            "thoughts": thoughts,
            "current_step": "risk_check",
        }

    async def execute(state: AgentState) -> dict:
        """Step 5: Execute the trade if approved by risk guardrail."""
        from app.models.database import async_session
        from app.services.executor import TradeExecutor

        thoughts = []
        trade_result = {}

        risk = state.get("risk_check", {})
        if state["should_trade"] and risk.get("approved"):
            try:
                async with async_session() as db:
                    executor = TradeExecutor(db)
                    params = state["trade_params"]
                    order = await executor.execute(
                        user_id=state["user_id"],
                        pair=params["pair"],
                        side=params["side"],
                        size=params.get("size", 0),
                        stop_loss=params.get("stop_loss"),
                        take_profit=params.get("take_profit"),
                        strategy_id=state.get("strategy_id"),
                        reasoning=state["reasoning"],
                    )
                    trade_result = {
                        "trade_id": str(order.id),
                        "pair": order.pair,
                        "side": order.side,
                        "entry_price": order.entry_price,
                        "status": order.status,
                        "is_shadow": order.is_shadow,
                    }
                    mode = "SHADOW" if order.is_shadow else "LIVE"
                    thoughts.append({
                        "step": "execution",
                        "content": (
                            f"[{mode}] Executed {order.side.upper()} {order.pair} "
                            f"@ ${order.entry_price:,.2f}"
                        ),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                trade_result = {"error": str(e)}
                thoughts.append({
                    "step": "execution",
                    "content": f"Execution failed: {e}",
                    "timestamp": datetime.utcnow().isoformat(),
                })
        else:
            reason = risk.get("reason", "No trade signal")
            thoughts.append({
                "step": "execution",
                "content": f"No execution — {reason}",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {
            "trade_result": trade_result,
            "thoughts": thoughts,
            "current_step": "execute",
        }

    async def reflect(state: AgentState) -> dict:
        """Step 6: Store thoughts and learn from this cycle."""
        from app.models.database import async_session
        from app.services.memory import MemoryService

        thoughts = []
        session_id = str(uuid.uuid4())

        try:
            async with async_session() as db:
                memory = MemoryService(db)
                for thought in state["thoughts"]:
                    await memory.store_thought(
                        user_id=state["user_id"],
                        session_id=session_id,
                        step=thought["step"],
                        content=thought["content"],
                        context={
                            "market_data": state.get("market_data", {}),
                            "trade_result": state.get("trade_result", {}),
                        },
                    )

                summary = (
                    f"Cycle complete. Analyzed {len(state['pairs'])} pairs. "
                    f"Decision: {'TRADE' if state['should_trade'] else 'HOLD'}. "
                    f"Confidence: {state['confidence']:.2f}. "
                    f"Result: {state.get('trade_result', {})}"
                )
                thoughts.append({
                    "step": "reflection",
                    "content": summary,
                    "timestamp": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            thoughts.append({
                "step": "reflection",
                "content": f"Reflection storage failed: {e}",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {
            "thoughts": thoughts,
            "current_step": "reflect",
        }

    # ─── Graph Construction ─────────────────────────────────────────

    graph.add_node("perceive", perceive)
    graph.add_node("recall_memory", recall_memory)
    graph.add_node("reason", reason)
    graph.add_node("check_risk", check_risk)
    graph.add_node("execute", execute)
    graph.add_node("reflect", reflect)

    # Linear flow: Perceive → Recall → Reason → Risk → Execute → Reflect
    graph.set_entry_point("perceive")
    graph.add_edge("perceive", "recall_memory")
    graph.add_edge("recall_memory", "reason")
    graph.add_edge("reason", "check_risk")
    graph.add_edge("check_risk", "execute")
    graph.add_edge("execute", "reflect")
    graph.add_edge("reflect", END)

    return graph.compile()
