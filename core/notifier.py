"""Telegram notification module with HTML parse mode, inline keyboard, and message splitting."""
import html
import json
import logging
import os
from typing import Dict, Any, Optional
import requests

from sources.base import JobItem

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends formatted job opportunities and error alerts to Telegram."""

    TELEGRAM_API_BASE = "https://api.telegram.org/bot"

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        timeout: int = 15,
    ):
        self.token = (token or os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = (chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
        self.timeout = timeout

        if not self.token or not self.chat_id:
            logger.warning("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diatur!")

    @property
    def is_configured(self) -> bool:
        """Returns True if bot token and chat ID are both present."""
        return bool(self.token and self.chat_id)

    def send_opportunity(self, item: JobItem, analysis: Dict[str, Any]) -> bool:
        """Formats and sends an opportunity notification with drafts to Telegram."""
        if not self.is_configured:
            logger.error("Tidak dapat mengirim ke Telegram: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID kosong.")
            return False

        relevance = analysis.get("relevance", 7)
        summary = analysis.get("summary", "Peluang lowongan baru terdeteksi.")
        comment_draft = analysis.get("comment_draft", "")
        dm_draft = analysis.get("dm_draft", "")
        used_fallback = analysis.get("used_fallback", False)

        fallback_badge = " ⚠️ <i>(Template Statis - Gemini Rate Limit)</i>" if used_fallback else ""

        # Format publication date
        published_str = item.published.strftime("%d %b %Y, %H:%M UTC")

        # HTML escape all dynamic text to prevent Telegram entity parsing errors
        escaped_title = html.escape(item.title)
        escaped_source = html.escape(item.source)
        escaped_summary = html.escape(summary)
        escaped_url = html.escape(item.url)
        escaped_comment = html.escape(comment_draft)
        escaped_dm = html.escape(dm_draft)

        message_html = (
            f"🔔 <b>[{relevance}/10] {escaped_title}</b>{fallback_badge}\n"
            f"📌 {escaped_source} • {published_str}\n\n"
            f"📝 <b>Ringkasan:</b> {escaped_summary}\n\n"
            f"🔗 <b>Link:</b> {escaped_url}\n\n"
            f"💬 <b>Draft Komentar:</b> <i>(Tap teks untuk copy)</i>\n"
            f"<code>{escaped_comment}</code>\n\n"
            f"✉️ <b>Draft DM:</b> <i>(Tap teks untuk copy)</i>\n"
            f"<code>{escaped_dm}</code>"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🔗 Buka Postingan", "url": item.url}
                ]
            ]
        }

        return self._send_telegram_message(message_html, reply_markup=inline_keyboard)

    def send_error_alert(self, error_message: str) -> bool:
        """Sends a high-priority system alert to Telegram when a run fails critically."""
        if not self.is_configured:
            return False

        escaped_err = html.escape(error_message[:1000])
        text = (
            "🚨 <b>Job Opportunity Bot Alert</b>\n"
            "Terjadi kegagalan pada proses otomatis bot:\n\n"
            f"<code>{escaped_err}</code>\n\n"
            "<i>Notifikasi ini dibatasi maksimal 1 kali per jam. Silakan periksa log GitHub Actions.</i>"
        )
        return self._send_telegram_message(text)

    def send_test_message(self) -> bool:
        """Sends a test verification message to ensure token and chat_id are valid."""
        if not self.is_configured:
            print("ERROR: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diatur!")
            return False

        text = (
            "✅ <b>Job Opportunity Bot - Uji Koneksi Berhasil!</b>\n\n"
            "Bot berhasil terhubung ke chat Anda.\n"
            "• Bot Token: Valid\n"
            f"• Chat ID: <code>{html.escape(self.chat_id)}</code>\n\n"
            "Bot siap memantau lowongan mobile development dan mengirimkan draft balasan AI!"
        )
        success = self._send_telegram_message(text)
        if success:
            print("SUKSES: Pesan tes Telegram berhasil dikirim ke Chat ID Anda!")
        else:
            print("GAGAL: Pengiriman pesan tes Telegram gagal. Periksa token dan Chat ID.")
        return success

    def _send_telegram_message(self, text_html: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """Handles sending, HTML parse mode, and message splitting if >4096 characters."""
        url = f"{self.TELEGRAM_API_BASE}{self.token}/sendMessage"

        # Split message into chunks if exceeding Telegram's 4096 character limit
        chunks = self._split_message(text_html, max_length=4000)

        for i, chunk in enumerate(chunks):
            payload: Dict[str, Any] = {
                "chat_id": self.chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            # Attach inline button to the last chunk
            if i == len(chunks) - 1 and reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)

            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code != 200:
                    logger.error(f"Gagal mengirim pesan Telegram (HTTP {resp.status_code}): {resp.text}")
                    # Try plain text fallback if HTML parse failed
                    if "can't parse entities" in resp.text:
                        logger.warning("Mencoba kirim ulang dengan plain text...")
                        payload.pop("parse_mode", None)
                        fallback_resp = requests.post(url, json=payload, timeout=self.timeout)
                        return fallback_resp.status_code == 200
                    return False
            except Exception as e:
                logger.error(f"Exception saat kirim ke Telegram: {e}")
                return False

        return True

    def _split_message(self, text: str, max_length: int = 4000) -> list[str]:
        """Splits long text by newlines so Telegram messages never exceed limit."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""
        for line in text.split("\n"):
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = f"{current_chunk}\n{line}" if current_chunk else line

        if current_chunk:
            chunks.append(current_chunk)
        return chunks
