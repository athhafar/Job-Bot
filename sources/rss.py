"""RSS Feed source for job opportunities (RemoteOK, We Work Remotely, etc.)."""
import logging
from datetime import datetime, timezone
import time
from typing import List, Dict, Any
import requests
import feedparser

from sources.base import BaseSource, JobItem, clean_html_text

logger = logging.getLogger(__name__)


class RSSSource(BaseSource):
    """Fetches job opportunities from configured public RSS feeds."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36 (JobOpportunityBot)"
    )

    def __init__(self, feeds: List[Dict[str, str]], timeout: int = 15):
        super().__init__(name="RSSSource", timeout=timeout)
        self.feeds = feeds

    def fetch(self) -> List[JobItem]:
        items: List[JobItem] = []

        for feed_cfg in self.feeds:
            feed_name = feed_cfg.get("name", "Unknown RSS")
            feed_url = feed_cfg.get("url", "")
            if not feed_url:
                continue

            try:
                logger.info(f"Fetching RSS feed: {feed_name} ({feed_url})")
                resp = requests.get(
                    feed_url,
                    headers={"User-Agent": self.DEFAULT_USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"},
                    timeout=self.timeout,
                )
                if resp.status_code != 200:
                    logger.warning(f"RSS {feed_name} returned status code {resp.status_code}")
                    continue

                parsed = feedparser.parse(resp.content)
                if parsed.bozo and not parsed.entries:
                    logger.warning(f"Error parsing RSS {feed_name}: {parsed.bozo_exception}")
                    continue

                for entry in parsed.entries:
                    # Extract Unique ID
                    item_id = entry.get("id") or entry.get("guid") or entry.get("link") or ""
                    if not item_id:
                        continue

                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    if not url:
                        url = item_id

                    # Extract Content / Summary
                    summary_html = entry.get("summary", "") or entry.get("description", "")
                    content_list = entry.get("content", [])
                    if content_list and isinstance(content_list, list):
                        summary_html = content_list[0].get("value", summary_html)

                    text = clean_html_text(summary_html)

                    # Extract Published Time
                    pub_datetime = self._parse_published(entry)

                    items.append(
                        JobItem(
                            id=f"rss_{item_id}",
                            title=title,
                            text=text,
                            url=url,
                            source=f"RSS: {feed_name}",
                            published=pub_datetime,
                        )
                    )

            except Exception as e:
                logger.error(f"Failed to fetch RSS {feed_name}: {e}", exc_info=False)

        logger.info(f"RSSSource fetched {len(items)} raw items across {len(self.feeds)} feeds")
        return items

    def _parse_published(self, entry: Any) -> datetime:
        """Parses entry publication date into a timezone-aware UTC datetime."""
        # Try struct_time from published_parsed or updated_parsed
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            try:
                return datetime.fromtimestamp(time.mktime(time_struct), tz=timezone.utc)
            except Exception:
                pass

        return datetime.now(timezone.utc)
