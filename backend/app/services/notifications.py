"""Notification System — Telegram & webhook alerts."""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Send trade alerts and reports via Telegram."""

    def __init__(self):
        self.settings = get_settings()
        self._client = httpx.AsyncClient(timeout=15)

    async def close(self):
        await self._client.aclose()

    async def send_trade_alert(self, message: str):
        """Send a trade notification to Telegram."""
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            logger.debug(f"Telegram not configured. Alert: {message}")
            return

        await self._send_telegram(f"🤖 *Nexus AI Trader*\n\n{message}")

    async def send_daily_report(self, report: dict):
        """Send a daily P&L summary."""
        text = (
            f"📊 *Daily Report*\n\n"
            f"Trades: {report.get('total_trades', 0)}\n"
            f"Win Rate: {report.get('win_rate', 0):.1f}%\n"
            f"P&L: ${report.get('pnl', 0):,.2f}\n"
            f"Open Positions: {report.get('open_positions', 0)}\n"
        )
        await self._send_telegram(text)

    async def send_risk_alert(self, message: str):
        """Send urgent risk/security alert."""
        await self._send_telegram(f"⚠️ *RISK ALERT*\n\n{message}")

    async def _send_telegram(self, text: str):
        """Send a message via the Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.settings.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }
            response = await self._client.post(url, json=payload)
            if response.status_code != 200:
                logger.warning(f"Telegram API error: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
