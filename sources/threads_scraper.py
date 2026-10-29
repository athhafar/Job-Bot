"""Threads scraper data source using threads-parser CLI via subprocess."""
from __future__ import annotations

import json
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sources.base import BaseSource, JobItem, clean_html_text, parse_iso_timestamp_to_utc

logger = logging.getLogger(__name__)


class ThreadsScraperError(Exception):
    """Custom exception raised when threads-parser CLI execution fails."""

    def __init__(self, message: str, returncode: Optional[int] = None, output: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.output = output


class ThreadsScraperSource(BaseSource):
    """Fetches public posts from Threads using the external threads-parser CLI."""

    def __init__(
        self,
        keywords: List[str],
        own_username: str = "",
        delay_range: Tuple[float, float] = (5.0, 15.0),
        max_posts_per_keyword: int = 20,
        cli_timeout: int = 120,
        timeout: int = 15,
    ) -> None:
        super().__init__(name="ThreadsScraperSource", timeout=timeout)
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.own_username = own_username.strip().lstrip("@").lower()
        self.delay_range = delay_range
        self.max_posts_per_keyword = max(1, min(max_posts_per_keyword, 50))
        self.cli_timeout = cli_timeout

        # Tracking consecutive failures or empty runs
        self.consecutive_errors: int = 0
        self.last_error_message: str = ""

    def fetch(self) -> List[JobItem]:
        """Runs threads-parser CLI across configured keywords with polite delays."""
        if not self.keywords:
            logger.warning("Tidak ada keyword Threads yang dikonfigurasi.")
            return []

        all_items: List[JobItem] = []
        seen_ids: set[str] = set()

        for idx, keyword in enumerate(self.keywords):
            logger.info("Memindai Threads via scraper untuk keyword: '%s'...", keyword)
            try:
                keyword_items = self._fetch_keyword(keyword)
                for item in keyword_items:
                    if item.id not in seen_ids:
                        seen_ids.add(item.id)
                        all_items.append(item)
                self.consecutive_errors = 0
            except Exception as exc:
                self.consecutive_errors += 1
                self.last_error_message = str(exc)
                logger.error("Gagal mengambil data untuk keyword '%s': %s", keyword, exc)

            # Jeda acak antar keyword (kecuali pada keyword terakhir)
            if idx < len(self.keywords) - 1:
                sleep_time = random.uniform(self.delay_range[0], self.delay_range[1])
                logger.debug("Jeda acak %.2f detik sebelum keyword berikutnya...", sleep_time)
                time.sleep(sleep_time)

        logger.info(
            "Selesai pemindaian Threads scraper. Total postingan unik didapat: %d",
            len(all_items),
        )
        return all_items

    def _fetch_keyword(self, keyword: str) -> List[JobItem]:
        """Executes CLI inside an isolated temporary directory to prevent repo pollution."""
        temp_dir = tempfile.mkdtemp(prefix="threads_scrape_")
        try:
            cmd = self._build_cli_command(keyword)
            logger.debug("Menjalankan CLI: %s (cwd=%s)", " ".join(cmd), temp_dir)

            res = subprocess.run(
                cmd,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.cli_timeout,
            )

            if res.returncode != 0:
                err_output = (res.stderr or res.stdout or "").strip()
                raise ThreadsScraperError(
                    f"CLI threads-parser keluar dengan kode {res.returncode}: {err_output[:300]}",
                    returncode=res.returncode,
                    output=err_output,
                )

            posts_file = self._find_posts_json(temp_dir)
            if not posts_file or not os.path.exists(posts_file):
                logger.warning("File posts.json tidak ditemukan di direktori output untuk '%s'.", keyword)
                return []

            return self._parse_posts_json(posts_file)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _build_cli_command(self, keyword: str) -> List[str]:
        """Builds command args for threads-parser CLI."""
        venv_bin = os.path.join(os.path.dirname(sys.executable), "threads-parser")
        cli_bin = venv_bin if os.path.isfile(venv_bin) and os.access(venv_bin, os.X_OK) else shutil.which("threads-parser")

        if cli_bin:
            cmd = [cli_bin]
        else:
            cmd = [sys.executable, "-m", "threads_parser"]

        cmd.extend([
            "--search", keyword,
            "--search-mode", "keyword",
            "--search-type", "recent",
            "--max-posts", str(self.max_posts_per_keyword),
        ])
        return cmd

    def _find_posts_json(self, temp_dir: str) -> Optional[str]:
        """Finds posts.json generated in output tree under temp_dir."""
        temp_path = Path(temp_dir)
        posts_paths = list(temp_path.glob("**/posts.json"))
        if posts_paths:
            return str(posts_paths[0])
        return None

    def _parse_posts_json(self, filepath: str) -> List[JobItem]:
        """Parses output posts.json into JobItem list."""
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            logger.warning("Format posts.json tidak valid (bukan JSON array).")
            return []

        items: List[JobItem] = []
        for post in raw_data:
            if not isinstance(post, dict):
                continue

            raw_id = str(post.get("id") or "").strip()
            if not raw_id:
                continue

            username = str(post.get("username") or "").strip().lstrip("@")
            if self.own_username and username.lower() == self.own_username:
                logger.debug("Mengabaikan postingan milik sendiri (@%s).", username)
                continue

            raw_text = str(post.get("text") or "").strip()
            cleaned_text = clean_html_text(raw_text)
            if not cleaned_text:
                continue

            # First line as title
            title_line = cleaned_text.splitlines()[0].strip()
            title = title_line[:120]

            permalink = str(post.get("permalink") or "").strip()
            published = parse_iso_timestamp_to_utc(post.get("timestamp"))

            item_id = f"threads_{raw_id}"

            items.append(
                JobItem(
                    id=item_id,
                    title=title,
                    text=cleaned_text,
                    url=permalink,
                    source="threads",
                    published=published,
                    username=username,
                )
            )

        return items

