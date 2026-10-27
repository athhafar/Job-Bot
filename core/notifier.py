"""Telegram notification module for Meta Threads Job Opportunity Bot."""
from __future__ import annotations

import html
import json
import logging
import os
from typing import Any, Dict, List, Optional
import requests

from sources.base import JobItem

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Delivers formatted job opportunity alerts and throttled system warnings to Telegram."""

    TELEGRAM_API_BASE = "https://api.telegram.org/bot"

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        timeout: int = 15,
    ) -> None:
        self.token = (token or os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = (chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        if not self.token or self.token.startswith("ISI_"):
            return False
        if not self.chat_id or self.chat_id.startswith("ISI_"):
            return False
        return True

    def send_opportunity(self, item: JobItem, analysis: Dict[str, Any]) -> bool:
        """Formats and delivers an opportunity alert to Telegram."""
        if not self.is_configured:
            logger.error("Tidak dapat mengirim ke Telegram: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diisi.")
            return False

        relevance = analysis.get("relevance")
        summary = analysis.get("summary", "")
        comment_draft = analysis.get("comment_draft", "")
        dm_draft = analysis.get("dm_draft", "")
        failed_ai = analysis.get("failed_ai", False)

        # Header badge
        if failed_ai or relevance is None:
            score_header = "🔔 <b>[⚠️ Tanpa penilaian AI]</b>"
        else:
            score_header = f"🔔 <b>[{relevance}/10]</b>"

        username_display = f"@{item.username}" if item.username else "Threads User"
        published_str = item.published.strftime("%d %b %Y, %H:%M UTC")

        escaped_title = html.escape(item.title)
        escaped_username = html.escape(username_display)
        escaped_summary = html.escape(summary)
        escaped_url = html.escape(item.url)
        escaped_comment = html.escape(comment_draft)
        escaped_dm = html.escape(dm_draft)

        message_parts = [
            f"{score_header} <b>{escaped_title}</b>",
            f"📌 <b>Threads:</b> {escaped_username} • {published_str}",
            "",
            f"📝 <b>Ringkasan:</b> {escaped_summary}",
            "",
            f"🔗 <b>Link:</b> {escaped_url}",
        ]

        if escaped_comment:
            message_parts.extend([
                "",
                "💬 <b>Draft Komentar:</b> <i>(Tap teks untuk copy)</i>",
                f"<code>{escaped_comment}</code>",
            ])

        if escaped_dm:
            message_parts.extend([
                "",
                "✉️ <b>Draft DM:</b> <i>(Tap teks untuk copy)</i>",
                f"<code>{escaped_dm}</code>",
            ])

        message_html = "\n".join(message_parts)

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🧵 Buka di Threads", "url": item.url}
                ]
            ]
        }

        return self._send_telegram_message(message_html, reply_markup=inline_keyboard)

    def send_token_expired_alert(self) -> bool:
        """Sends alert when Threads access token has expired (HTTP 401)."""
        if not self.is_configured:
            return False
        text = (
            "🚨 <b>Peringatan: Token Threads Kedaluwarsa</b>\n\n"
            "Token Threads Anda sudah tidak valid atau kedaluwarsa (HTTP 401).\n"
            "Silakan buat ulang token di <b>Meta User Token Generator</b> lalu perbarui "
            "Secrets repositori Anda.\n\n"
            "<i>(Notifikasi ini dibatasi maksimal 1 kali per hari)</i>"
        )
        return self._send_telegram_message(text)

    def send_permission_alert(self) -> bool:
        """Sends alert when Threads keyword search permission is not approved or restricted (HTTP 403)."""
        if not self.is_configured:
            return False
        text = (
            "⚠️ <b>Peringatan: Permission Threads Ditolak (HTTP 403)</b>\n\n"
            "API Threads mengembalikan error 403 Forbidden. Pastikan permission "
            "<code>threads_keyword_search</code> sudah aktif di App Dashboard Anda.\n\n"
            "<i>(Notifikasi ini dibatasi maksimal 1 kali per hari)</i>"
        )
        return self._send_telegram_message(text)

    def send_gemini_quota_alert(self) -> bool:
        """Sends alert when Gemini 429 rate limit triggered consecutively."""
        if not self.is_configured:
            return False
        text = (
            "⚠️ <b>Peringatan: Kuota Gemini Habis</b>\n\n"
            "Terjadi 2x rate-limit (HTTP 429) berturut-turut dari Gemini API. "
            "Pemanggilan AI dihentikan sementara untuk run ini. Postingan lolos filter "
            "akan dikirim dengan template tanpa skor AI dan tidak ditandai seen agar dicoba lagi.\n\n"
            "<i>(Notifikasi ini dibatasi maksimal 1 kali per hari)</i>"
        )
        return self._send_telegram_message(text)

    def send_token_expiry_warning(self, remaining_days: int) -> bool:
        """Sends reminder when token is nearing expiration (< 10 days)."""
        if not self.is_configured:
            return False
        text = (
            f"⏳ <b>Peringatan: Masa Berlaku Token Threads Tersisa {remaining_days} Hari</b>\n\n"
            "Segera jalankan skrip perpanjangan token:\n"
            "<code>python scripts/refresh_token.py</code>\n\n"
            "Lalu perbarui GitHub Secrets <code>THREADS_ACCESS_TOKEN</code> Anda.\n"
            "<i>(Notifikasi ini dibatasi maksimal 1 kali per hari)</i>"
        )
        return self._send_telegram_message(text)

    def send_error_alert(self, error_message: str) -> bool:
        """Sends general system failure notification (throttled to 1/hour)."""
        if not self.is_configured:
            return False
        escaped_err = html.escape(error_message[:1000])
        text = (
            "🚨 <b>Job Opportunity Bot - System Alert</b>\n\n"
            f"<code>{escaped_err}</code>\n\n"
            "<i>(Notifikasi ini dibatasi maksimal 1 kali per jam)</i>"
        )
        return self._send_telegram_message(text)

    def send_test_message(self) -> bool:
        """Validates token and chat ID with test message."""
        if not self.is_configured:
            print("ERROR: TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID belum diatur di .env!")
            return False

        text = (
            "✅ <b>Job Opportunity Bot (Threads) - Koneksi Berhasil!</b>\n\n"
            "Bot Telegram Anda terhubung dengan sempurna.\n"
            "• Sumber Aktif: <b>Meta Threads API</b>\n"
            f"• Chat ID: <code>{html.escape(self.chat_id)}</code>\n\n"
            "Bot siap memantau peluang lowongan mobile development di Threads!"
        )
        success = self._send_telegram_message(text)
        if success:
            print("SUKSES: Pesan verifikasi berhasil dikirim ke akun Telegram Anda!")
        else:
            print("GAGAL: Pengiriman pesan Telegram gagal. Periksa token dan Chat ID.")
        return success

    def _send_telegram_message(
        self,
        text_html: str,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        url = f"{self.TELEGRAM_API_BASE}{self.token}/sendMessage"
        chunks = self._split_message(text_html, max_length=4000)

        for i, chunk in enumerate(chunks):
            payload: Dict[str, Any] = {
                "chat_id": self.chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            if i == len(chunks) - 1 and reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)

            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                if resp.status_code != 200:
                    logger.error("Gagal mengirim Telegram (HTTP %d): %s", resp.status_code, resp.text)
                    if "can't parse entities" in resp.text:
                        payload.pop("parse_mode", None)
                        fallback = requests.post(url, json=payload, timeout=self.timeout)
                        return fallback.status_code == 200
                    return False
            except Exception as e:
                logger.error("Exception saat kirim ke Telegram: %s", e)
                return False

        return True

    def _split_message(self, text: str, max_length: int = 4000) -> List[str]:
        if len(text) <= max_length:
            return [text]

        chunks: List[str] = []
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
