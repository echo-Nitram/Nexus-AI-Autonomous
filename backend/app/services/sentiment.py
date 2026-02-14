"""Perception Layer — News & Sentiment Analysis via LLM."""

import logging
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class SentimentService:
    """Retrieves and analyzes market sentiment from news and social media."""

    def __init__(self):
        self.settings = get_settings()
        self._client = httpx.AsyncClient(timeout=30)

    async def close(self):
        await self._client.aclose()

    async def fetch_crypto_news(self, query: str = "bitcoin") -> list[dict]:
        """Fetch recent crypto news headlines.

        In production, connect to Bloomberg, CoinDesk, or CryptoPanic APIs.
        This implementation uses CryptoPanic's free API as a starting point.
        """
        try:
            url = "https://cryptopanic.com/api/free/v1/posts/"
            params = {
                "auth_token": "free",
                "currencies": query.upper(),
                "filter": "important",
                "public": "true",
            }
            response = await self._client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "title": post.get("title", ""),
                        "source": post.get("source", {}).get("title", "unknown"),
                        "url": post.get("url", ""),
                        "published_at": post.get("published_at", ""),
                        "kind": post.get("kind", "news"),
                    }
                    for post in data.get("results", [])[:10]
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch news: {e}")

        return []

    async def fetch_fear_greed_index(self) -> dict:
        """Fetch the crypto Fear & Greed Index."""
        try:
            response = await self._client.get("https://api.alternative.me/fng/?limit=1")
            if response.status_code == 200:
                data = response.json()["data"][0]
                return {
                    "value": int(data["value"]),
                    "classification": data["value_classification"],
                    "timestamp": data["timestamp"],
                }
        except Exception as e:
            logger.warning(f"Failed to fetch Fear & Greed index: {e}")

        return {"value": 50, "classification": "Neutral", "timestamp": ""}

    async def analyze_sentiment(self, symbol: str) -> dict:
        """Build a comprehensive sentiment analysis for the agent.

        Combines news headlines and market fear/greed into a structured
        sentiment report that the LLM agent can reason about.
        """
        news = await self.fetch_crypto_news(symbol.split("/")[0])
        fng = await self.fetch_fear_greed_index()

        # Build a text summary for the LLM to interpret
        news_summary = "\n".join(
            [f"- [{n['source']}] {n['title']}" for n in news[:5]]
        ) if news else "No recent news available."

        return {
            "symbol": symbol,
            "fear_greed_index": fng,
            "news_headlines": news[:5],
            "news_summary": news_summary,
            "overall_sentiment": self._classify_fng(fng["value"]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _classify_fng(value: int) -> str:
        if value <= 25:
            return "extreme_fear"
        elif value <= 40:
            return "fear"
        elif value <= 60:
            return "neutral"
        elif value <= 75:
            return "greed"
        else:
            return "extreme_greed"
