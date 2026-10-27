"""Storage module for managing deduplication and state persistence via seen.json."""
import json
import logging
import os
import time
from typing import Set, List, Dict, Any

logger = logging.getLogger(__name__)


class Storage:
    """Manages seen IDs and error throttling state in seen.json."""

    def __init__(self, filepath: str = "seen.json", max_items: int = 5000):
        self.filepath = filepath
        self.max_items = max_items
        self.seen_ids_list: List[str] = []
        self.seen_ids_set: Set[str] = set()
        self.last_error_notification_timestamp: float = 0.0
        self._modified = False
        self.load()

    def load(self) -> None:
        """Loads state from seen.json if it exists."""
        if not os.path.exists(self.filepath):
            logger.info(f"{self.filepath} belum ada. Membuat penyimpanan baru.")
            self.seen_ids_list = []
            self.seen_ids_set = set()
            self.last_error_notification_timestamp = 0.0
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                # Backwards compatibility if seen.json was a raw list
                raw_ids = data
                self.last_error_notification_timestamp = 0.0
            elif isinstance(data, dict):
                raw_ids = data.get("seen_ids", [])
                self.last_error_notification_timestamp = float(
                    data.get("last_error_notification_timestamp", 0.0)
                )
            else:
                raw_ids = []

            # Keep only the newest max_items
            self.seen_ids_list = raw_ids[-self.max_items :]
            self.seen_ids_set = set(self.seen_ids_list)
            logger.info(f"Loaded {len(self.seen_ids_set)} seen IDs from {self.filepath}")
        except Exception as e:
            logger.error(f"Gagal membaca {self.filepath}: {e}. Memulai dengan cache kosong.")
            self.seen_ids_list = []
            self.seen_ids_set = set()
            self.last_error_notification_timestamp = 0.0

    def is_seen(self, item_id: str, url: str = "") -> bool:
        """Checks whether an item ID or its URL has already been processed."""
        if item_id in self.seen_ids_set:
            return True
        if url and url in self.seen_ids_set:
            return True
        return False

    def mark_seen(self, item_id: str, url: str = "") -> None:
        """Marks an item ID and optional URL as seen, enforcing the max_items bound."""
        if not self.is_seen(item_id, url):
            self.seen_ids_list.append(item_id)
            self.seen_ids_set.add(item_id)
            if url and url != item_id:
                self.seen_ids_list.append(url)
                self.seen_ids_set.add(url)

            # Trim old items if exceeding max_items
            if len(self.seen_ids_list) > self.max_items:
                overflow = len(self.seen_ids_list) - self.max_items
                self.seen_ids_list = self.seen_ids_list[overflow:]
                self.seen_ids_set = set(self.seen_ids_list)

            self._modified = True

    def can_send_error_notification(self, cooldown_minutes: int = 60) -> bool:
        """Determines if enough time has passed to send another error notification."""
        now = time.time()
        cooldown_seconds = cooldown_minutes * 60
        return (now - self.last_error_notification_timestamp) >= cooldown_seconds

    def record_error_notification_sent(self) -> None:
        """Records the timestamp of an error notification sent to Telegram."""
        self.last_error_notification_timestamp = time.time()
        self._modified = True

    def save(self) -> bool:
        """Saves current state to seen.json atomically."""
        if not self._modified and os.path.exists(self.filepath):
            return True

        data: Dict[str, Any] = {
            "seen_ids": self.seen_ids_list,
            "last_error_notification_timestamp": self.last_error_notification_timestamp,
        }
        temp_path = f"{self.filepath}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.filepath)
            self._modified = False
            logger.info(f"Successfully saved {len(self.seen_ids_list)} items to {self.filepath}")
            return True
        except Exception as e:
            logger.error(f"Gagal menyimpan ke {self.filepath}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
