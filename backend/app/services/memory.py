"""Memory Layer — Long-term learning with pgvector.

Stores agent thoughts and trade outcomes as vector embeddings
so the agent can recall similar past situations.
"""

import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import get_settings
from app.models.schemas import AgentThought

logger = logging.getLogger(__name__)


class MemoryService:
    """Vector-based long-term memory for the trading agent."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def store_thought(
        self,
        user_id: UUID,
        session_id: str,
        step: str,
        content: str,
        context: dict | None = None,
        embedding: list[float] | None = None,
    ) -> AgentThought:
        """Store an agent thought with optional embedding for similarity search."""
        thought = AgentThought(
            user_id=user_id,
            session_id=session_id,
            step=step,
            content=content,
            context=context,
            embedding=embedding,
        )
        self.db.add(thought)
        await self.db.commit()
        await self.db.refresh(thought)
        return thought

    async def recall_similar(
        self,
        embedding: list[float],
        user_id: UUID,
        limit: int = 5,
    ) -> list[dict]:
        """Find similar past thoughts using cosine similarity search."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT id, step, content, context, timestamp,
                           1 - (embedding <=> :embedding::vector) as similarity
                    FROM agent_thoughts
                    WHERE user_id = :user_id
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """),
                {
                    "embedding": str(embedding),
                    "user_id": str(user_id),
                    "limit": limit,
                },
            )
            rows = result.fetchall()
            return [
                {
                    "id": str(row.id),
                    "step": row.step,
                    "content": row.content,
                    "context": row.context,
                    "timestamp": row.timestamp.isoformat(),
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Memory recall failed: {e}")
            return []

    async def get_recent_thoughts(
        self, user_id: UUID, limit: int = 20
    ) -> list[dict]:
        """Get recent agent thoughts chronologically."""
        result = await self.db.execute(
            select(AgentThought)
            .where(AgentThought.user_id == user_id)
            .order_by(AgentThought.timestamp.desc())
            .limit(limit)
        )
        thoughts = result.scalars().all()
        return [
            {
                "step": t.step,
                "content": t.content,
                "context": t.context,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in thoughts
        ]

    async def get_trade_lessons(self, user_id: UUID) -> list[dict]:
        """Get thoughts specifically tagged as trade outcomes for learning."""
        result = await self.db.execute(
            select(AgentThought)
            .where(
                AgentThought.user_id == user_id,
                AgentThought.step == "trade_outcome",
            )
            .order_by(AgentThought.timestamp.desc())
            .limit(50)
        )
        thoughts = result.scalars().all()
        return [
            {
                "content": t.content,
                "context": t.context,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in thoughts
        ]
