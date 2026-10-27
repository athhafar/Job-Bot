"""Meta Threads official Keyword Search API source (No scraping)."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import requests

from sources.base import BaseSource, JobItem, clean_html_text, parse_iso_timestamp_to_utc

logger = logging.getLogger(__name__)


def mask_secret(secret: Optional[str]) -> str:
    """Masks a token or secret to prevent leaking in logs (e.g. 'THQW...789x')."""
    if not secret:
        return "(empty)"
    s = secret.strip()
    if len(s) <= 8:
        return "********"
    return f"{s[:4]}...{s[-4:]}"


class ThreadsAPIError(Exception):
    """Custom exception for Threads API errors with status code information."""

    def __init__(self, status_code: int, message: str, error_type: str = "") -> None:
        super().__init__(f"Threads API Error ({status_code}): {message}")
        self.status_code = status_code
        self.message = message
        self.error_type = error_type


class ThreadsSource(BaseSource):
    """Fetches public posts from Meta Threads official keyword search API."""

    ENDPOINT = "https://graph.threads.net/v1.0/keyword_search"

    def __init__(
        self,
        access_token: str,
        keywords: List[str],
        own_username: str = "",
        delay_seconds: float = 1.5,
        max_requests_per_run: int = 10,
        max_pages_per_keyword: int = 2,
        timeout: int = 15,
    ) -> None:
        super().__init__(name="ThreadsSource", timeout=timeout)
        self.access_token = access_token.strip()
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.own_username = own_username.strip().lstrip("@").lower()
        self.delay_seconds = delay_seconds
        self.max_requests_per_run = max_requests_per_run
        self.max_pages_per_keyword = max(1, min(max_pages_per_keyword, 5))

        # Status tracking for specific errors
        self.token_expired_error: bool = False
        self.permission_error: bool = False
        self.last_error_message: str = ""

    def fetch(self) -> List[JobItem]:
        """Fetches posts across configured keywords up to max_requests_per_run."""
        if not self.access_token or self.access_token.startswith("ISI_"):
            raise ValueError("Isi THREADS_ACCESS_TOKEN di .env dulu.")

        logger.info(
            "Memulai pemindaian Meta Threads API resmi (Token: %s).",
            mask_secret(self.access_token),
        )
        logger.warning(
            "PERINGATAN PERMISSION: Jika permission 'threads_keyword_search' belum disetujui Meta "
            "melalui App Review, API hanya akan mengembalikan postingan milik akun tester sendiri."
        )

        all_items: List[JobItem] = []
        seen_post_ids: set[str] = set()
        request_count = 0

        for keyword in self.keywords:
            if request_count >= self.max_requests_per_run:
                logger.info(
                    "Mencapai batas maksimal request Threads per run (%d). Menghentikan fetch.",
                    self.max_requests_per_run,
                )
                break

            logger.info("Mencari keyword Threads: '%s'...", keyword)

            # Pagination per keyword
            next_url: Optional[str] = None
            for page in range(1, self.max_pages_per_keyword + 1):
                if request_count >= self.max_requests_per_run:
                    break

                try:
                    request_count += 1
                    items, next_url = self._search_page(
                        keyword=keyword,
                        page_url=next_url,
                    )

                    for item in items:
                        if item.id not in seen_post_ids:
                            seen_post_ids.add(item.id)
                            all_items.append(item)

                    # If no next page, stop pagination for this keyword
                    if not next_url:
                        break

                    # Pause between requests
                    if self.delay_seconds > 0:
                        time.sleep(self.delay_seconds)

                except ThreadsAPIError as e:
                    self._handle_api_error(e)
                    return all_items
                except Exception as e:
                    logger.error("Gagal mengambil data Threads untuk keyword '%s': %s", keyword, e)
                    break

            # Pause between keywords
            if self.delay_seconds > 0:
                time.sleep(self.delay_seconds)

        logger.info(
            "ThreadsSource berhasil mengumpulkan total %d postingan unik dari %d request.",
            len(all_items),
            request_count,
        )
        return all_items

    def test_search(self, keyword: str = "flutter developer") -> Tuple[int, List[JobItem]]:
        """Executes a single test keyword search without modifying state or calling other services."""
        if not self.access_token or self.access_token.startswith("ISI_"):
            raise ValueError("Isi THREADS_ACCESS_TOKEN di .env dulu.")

        logger.info("Menguji koneksi Threads API dengan keyword: '%s'...", keyword)
        items, _ = self._search_page(keyword=keyword, page_url=None)
        return len(items), items[:3]

    def _search_page(
        self,
        keyword: str,
        page_url: Optional[str] = None,
    ) -> Tuple[List[JobItem], Optional[str]]:
        """Makes a single GET request to Threads keyword search or paging URL."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "JobOpportunityBot-Threads/1.0",
        }

        if page_url:
            req_url = page_url
            params = None
        else:
            req_url = self.ENDPOINT
            params = {
                "q": keyword,
                "search_type": "RECENT",
                "fields": "id,text,permalink,timestamp,username",
                "access_token": self.access_token,
            }

        resp = requests.get(req_url, params=params, headers=headers, timeout=self.timeout)

        if resp.status_code == 401:
            self.token_expired_error = True
            msg = "Token Threads kedaluwarsa atau tidak valid (HTTP 401). Buat ulang di User Token Generator."
            self.last_error_message = msg
            raise ThreadsAPIError(401, msg, "OAuthException")

        if resp.status_code == 403:
            self.permission_error = True
            msg = "Akses Threads ditolak (HTTP 403). Pastikan permission 'threads_keyword_search' aktif."
            self.last_error_message = msg
            raise ThreadsAPIError(403, msg, "PermissionException")

        if resp.status_code != 200:
            err_data = {}
            try:
                err_data = resp.json().get("error", {})
            except Exception:
                pass
            msg = err_data.get("message", f"HTTP {resp.status_code}")
            err_type = err_data.get("type", "")
            self.last_error_message = msg
            raise ThreadsAPIError(resp.status_code, msg, err_type)

        data = resp.json()
        raw_posts = data.get("data", [])
        paging = data.get("paging", {})
        next_page_url = paging.get("next")

        parsed_items: List[JobItem] = []
        for post in raw_posts:
            post_id = str(post.get("id", "")).strip()
            if not post_id:
                continue

            username = str(post.get("username", "")).strip().lstrip("@")
            if self.own_username and username.lower() == self.own_username:
                logger.debug("Melewati postingan dari akun sendiri (@%s).", username)
                continue

            text = clean_html_text(post.get("text", ""))
            permalink = post.get("permalink", "")
            if not permalink:
                permalink = f"https://www.threads.net/t/{post_id}"

            timestamp_str = post.get("timestamp")
            pub_dt = parse_iso_timestamp_to_utc(timestamp_str)

            # Generate title from first 80 characters of text
            first_line = text.split("\n")[0] if text else "Threads Post"
            title = first_line[:80].strip()
            if len(first_line) > 80:
                title += "..."

            parsed_items.append(
                JobItem(
                    id=f"threads_{post_id}",
                    title=title,
                    text=text,
                    url=permalink,
                    source=f"Threads (@{username})" if username else "Threads",
                    published=pub_dt,
                    username=username,
                )
            )

        return parsed_items, next_page_url

    def _handle_api_error(self, err: ThreadsAPIError) -> None:
        """Logs appropriate warning or critical error for Threads API failures."""
        if err.status_code == 401:
            logger.critical("AUTH ERROR: %s", err.message)
        elif err.status_code == 403:
            logger.error("PERMISSION ERROR: %s", err.message)
        else:
            logger.error("THREADS API ERROR: %s", err.message)
