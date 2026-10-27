"""Stub implementations for optional Meta Threads API & Telegram Channel sources.

These are disabled by default in config.yaml.
Follow the TODO comments below whenever you are ready to activate them.
"""
import logging
import os
from typing import List
from sources.base import BaseSource, JobItem

logger = logging.getLogger(__name__)


class ThreadsStubSource(BaseSource):
    """Stub for official Meta Threads API keyword search.

    =============================================================================
    TODO: CARA AKTIVASI SUMBER RESMI META THREADS API
    =============================================================================
    1. Kunjungi Meta for Developers: https://developers.facebook.com/
    2. Buat App baru dengan Use Case: 'Threads' / 'Access the Threads API'.
    3. Hubungkan akun Threads profesional atau uji coba Anda.
    4. Minta izin akses: 'threads_basic' dan 'threads_content_publish'.
    5. Generate Long-Lived User Access Token melalui Graph API Explorer.
    6. Simpan token ke environment variable: THREADS_ACCESS_TOKEN.
    7. Panggil endpoint keyword search Threads API:
       GET https://graph.threads.net/v1.0/search?q={keyword}&access_token={token}
    8. Di config.yaml: ubah `sources.threads.enabled: true`
    =============================================================================
    """

    def __init__(self, keywords: List[str], timeout: int = 15):
        super().__init__(name="ThreadsStubSource", timeout=timeout)
        self.keywords = keywords
        self.access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")

    def fetch(self) -> List[JobItem]:
        if not self.access_token:
            logger.info("ThreadsStubSource: THREADS_ACCESS_TOKEN tidak diatur. Melewati sumber ini.")
            return []

        logger.info("ThreadsStubSource: Siap diimplementasikan menggunakan Meta Graph API resmi.")
        # Contoh panggilan:
        # resp = requests.get(
        #     "https://graph.threads.net/v1.0/search",
        #     params={"q": "flutter", "access_token": self.access_token},
        #     timeout=self.timeout
        # )
        return []


class TelegramChannelStubSource(BaseSource):
    """Stub for fetching job openings from Telegram Channels/Groups where bot is a member.

    =============================================================================
    TODO: CARA AKTIVASI SUMBER TELEGRAM CHANNELS/GROUPS
    =============================================================================
    1. Tambahkan bot Telegram Anda ke Grup atau Channel info lowongan mobile dev.
    2. Berikan bot izin 'Read Messages'.
    3. Jika bot adalah admin channel publik, bot dapat membaca pesan terbaru
       lewat endpoint `getUpdates`:
       GET https://api.telegram.org/bot<TOKEN>/getUpdates
    4. Filter pesan berdasarkan channel_post atau message dari ID grup target.
    5. Di config.yaml: ubah `sources.telegram_channels.enabled: true`
    =============================================================================
    """

    def __init__(self, channels: List[str] = None, timeout: int = 15):
        super().__init__(name="TelegramChannelStubSource", timeout=timeout)
        self.channels = channels or []

    def fetch(self) -> List[JobItem]:
        logger.info("TelegramChannelStubSource: Menggunakan stub. Aktifkan getUpdates jika bot dimasukkan ke channel.")
        return []
