"""Hacker News source using Algolia HN Search API (Free, no API key needed)."""
import logging
from datetime import datetime, timezone, timedelta
from typing import List
import requests

from sources.base import BaseSource, JobItem, clean_html_text, parse_timestamp_to_utc

logger = logging.getLogger(__name__)


class HackerNewsSource(BaseSource):
    """Fetches job opportunities and hiring comments from Hacker News via Algolia API."""

    ALGOLIA_API_URL = "https://hn.algolia.com/api/v1/search_by_date"

    def __init__(self, queries: List[str], limit_per_query: int = 20, timeout: int = 15):
        super().__init__(name="HackerNewsSource", timeout=timeout)
        self.queries = queries
        self.limit = limit_per_query

    def fetch(self) -> List[JobItem]:
        items: List[JobItem] = []
        # Look back 48 hours to ensure we don't miss comments
        time_cutoff = int((datetime.now(timezone.utc) - timedelta(hours=48)).timestamp())

        for query in self.queries:
            query = query.strip()
            if not query:
                continue

            try:
                logger.info(f"Searching Hacker News comments for query: '{query}'")
                params = {
                    "query": query,
                    "tags": "comment",
                    "numericFilters": f"created_at_i>{time_cutoff}",
                    "hitsPerPage": self.limit,
                }
                resp = requests.get(
                    self.ALGOLIA_API_URL,
                    params=params,
                    headers={"User-Agent": "JobOpportunityBot/1.0"},
                    timeout=self.timeout,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", [])
                    for hit in hits:
                        obj_id = hit.get("objectID")
                        if not obj_id:
                            continue

                        comment_text = hit.get("comment_text", "")
                        story_title = hit.get("story_title", "HN Comment")
                        story_id = hit.get("story_id")
                        created_at_i = hit.get("created_at_i")

                        # Link directly to HN comment
                        item_url = f"https://news.ycombinator.com/item?id={obj_id}"
                        title = f"{story_title} (Comment #{obj_id})"
                        clean_text = clean_html_text(comment_text)

                        items.append(
                            JobItem(
                                id=f"hn_comment_{obj_id}",
                                title=title,
                                text=clean_text,
                                url=item_url,
                                source="Hacker News (Who is hiring)",
                                published=parse_timestamp_to_utc(created_at_i),
                            )
                        )
                else:
                    logger.warning(f"HN Algolia search returned HTTP {resp.status_code} for query '{query}'")

            except Exception as e:
                logger.warning(f"Error fetching HN query '{query}': {e}")

        logger.info(f"HackerNewsSource fetched {len(items)} items")
        return items
