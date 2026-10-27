"""Storage module for managing deduplication and state persistence via seen.json."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class Storage:
    """Manages seen IDs and alert rate-limiting timestamps in seen.json."""

    def __init__(self, filepath: str = "seen.json", max_items: int = 5000) -> None:
        self.filepath = filepath
        self.max_items = max_items
        self.seen_ids_list: List[str] = []
        self.seen_ids_set: Set[str] = set()

        # Alert timestamps to enforce daily limits
        self.last_error_notification_timestamp: float = 0.0
        self.last_permission_alert_timestamp: float = 0.0
        self.last_token_expired_alert_timestamp: float = 0.0
        self.last_token_expiry_warning_timestamp: float = 0.0
        self.last_gemini_quota_alert_timestamp: float = 0.0

        self._modified: bool = False
        self.load()

    def load(self) -> None:
        """Loads state from seen.json if it exists."""
        if not os.path.exists(self.filepath):
            logger.info("%s belum ada. Menginisialisasi penyimpanan baru.", self.filepath)
            self._reset_state()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                raw_ids = data
                self._reset_timestamps()
            elif isinstance(data, dict):
                raw_ids = data.get("seen_ids", [])
                self.last_error_notification_timestamp = float(data.get("last_error_notification_timestamp", 0.0))
                self.last_permission_alert_timestamp = float(data.get("last_permission_alert_timestamp", 0.0))
                self.last_token_expired_alert_timestamp = float(data.get("last_token_expired_alert_timestamp", 0.0))
                self.last_token_expiry_warning_timestamp = float(data.get("last_token_expiry_warning_timestamp", 0.0))
                self.last_gemini_quota_alert_timestamp = float(data.get("last_gemini_quota_alert_timestamp", 0.0))
            else:
                raw_ids = []
                self._reset_timestamps()

            # Bound strictly to the newest max_items
            self.seen_ids_list = [str(i) for i in raw_ids[-self.max_items :]]
            self.seen_ids_set = set(self.seen_ids_list)
            logger.info("Loaded %d seen IDs from %s", len(self.seen_ids_set), self.filepath)
        except Exception as e:
            logger.error("Gagal membaca %s: %s. Menggunakan memori bersih.", self.filepath, e)
            self._reset_state()

    def _reset_state(self) -> None:
        self.seen_ids_list = []
        self.seen_ids_set = set()
        self._reset_timestamps()

    def _reset_timestamps(self) -> None:
        self.last_error_notification_timestamp = 0.0
        self.last_permission_alert_timestamp = 0.0
        self.last_token_expired_alert_timestamp = 0.0
        self.last_token_expiry_warning_timestamp = 0.0
        self.last_gemini_quota_alert_timestamp = 0.0

    def is_seen(self, item_id: str, url: str = "") -> bool:
        """Checks whether an item ID or its permalink has already been processed."""
        if item_id in self.seen_ids_set:
            return True
        if url and url in self.seen_ids_set:
            return True
        return False

    def mark_seen(self, item_id: str, url: str = "") -> None:
        """Marks an item ID and URL as seen, bounding size to max_items."""
        if not self.is_seen(item_id, url):
            self.seen_ids_list.append(item_id)
            self.seen_ids_set.add(item_id)
            if url and url != item_id:
                self.seen_ids_list.append(url)
                self.seen_ids_set.add(url)

            if len(self.seen_ids_list) > self.max_items:
                overflow = len(self.seen_ids_list) - self.max_items
                self.seen_ids_list = self.seen_ids_list[overflow:]
                self.seen_ids_set = set(self.seen_ids_list)

            self._modified = True

    # Throttling helpers (Max 1 per day = 86400 seconds)
    def can_send_permission_alert(self) -> bool:
        return (time.time() - self.last_permission_alert_timestamp) >= 86400

    def record_permission_alert_sent(self) -> None:
        self.last_permission_alert_timestamp = time.time()
        self._modified = True

    def can_send_token_expired_alert(self) -> bool:
        return (time.time() - self.last_token_expired_alert_timestamp) >= 86400

    def record_token_expired_alert_sent(self) -> None:
        self.last_token_expired_alert_timestamp = time.time()
        self._modified = True

    def can_send_token_expiry_warning(self) -> bool:
        return (time.time() - self.last_token_expiry_warning_timestamp) >= 86400

    def record_token_expiry_warning_sent(self) -> None:
        self.last_token_expiry_warning_timestamp = time.time()
        self._modified = True

    def can_send_gemini_quota_alert(self) -> bool:
        return (time.time() - self.last_gemini_quota_alert_timestamp) >= 86400

    def record_gemini_quota_alert_sent(self) -> None:
        self.last_gemini_quota_alert_timestamp = time.time()
        self._modified = True

    def can_send_error_notification(self, cooldown_minutes: int = 60) -> bool:
        return (time.time() - self.last_error_notification_timestamp) >= (cooldown_minutes * 60)

    def record_error_notification_sent(self) -> None:
        self.last_error_notification_timestamp = time.time()
        self._modified = True

    def save(self) -> bool:
        """Saves current state to seen.json atomically."""
        if not self._modified and os.path.exists(self.filepath):
            return True

        data: Dict[str, Any] = {
            "seen_ids": self.seen_ids_list,
            "last_error_notification_timestamp": self.last_error_notification_timestamp,
            "last_permission_alert_timestamp": self.last_permission_alert_timestamp,
            "last_token_expired_alert_timestamp": self.last_token_expired_alert_timestamp,
            "last_token_expiry_warning_timestamp": self.last_token_expiry_warning_timestamp,
            "last_gemini_quota_alert_timestamp": self.last_gemini_quota_alert_timestamp,
        }
        temp_path = f"{self.filepath}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.filepath)
            self._modified = False
            logger.info("Successfully persisted state to %s (%d items)", self.filepath, len(self.seen_ids_list))
            return True
        except Exception as e:
            logger.error("Gagal menyimpan ke %s: %s", self.filepath, e)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
