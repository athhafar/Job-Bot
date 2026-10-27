"""Reddit source using public RSS / JSON endpoints with clear User-Agent."""
import logging
from datetime import datetime, timezone
from typing import List, Optional
import requests
import feedparser

from sources.base import BaseSource, JobItem, clean_html_text, parse_timestamp_to_utc

logger = logging.getLogger(__name__)


class RedditSource(BaseSource):
    """Fetches job posts from public Reddit subreddits."""

    def __init__(
        self,
        subreddits: List[str],
        user_agent: str = "JobOpportunityBot/1.0 (mobile-dev-hunter by github-action)",
        limit_per_sub: int = 25,
        timeout: int = 15,
    ):
        super().__init__(name="RedditSource", timeout=timeout)
        self.subreddits = subreddits
        self.user_agent = user_agent
        self.limit = limit_per_sub

    def fetch(self) -> List[JobItem]:
        items: List[JobItem] = []
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, application/rss+xml, text/html",
        }

        for sub in self.subreddits:
            sub = sub.strip().replace("r/", "")
            if not sub:
                continue

            sub_items = self._fetch_subreddit_json(sub, headers)
            if not sub_items:
                # Fallback to RSS if JSON is blocked or throttled
                sub_items = self._fetch_subreddit_rss(sub, headers)

            items.extend(sub_items)

        logger.info(f"RedditSource fetched total {len(items)} items across {len(self.subreddits)} subreddits")
        return items

    def _fetch_subreddit_json(self, sub: str, headers: dict) -> List[JobItem]:
        """Fetch using Reddit JSON endpoint."""
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={self.limit}"
        items: List[JobItem] = []
        try:
            logger.info(f"Fetching Reddit r/{sub} (JSON)")
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    post_id = post.get("id")
                    if not post_id:
                        continue

                    title = post.get("title", "").strip()
                    selftext = post.get("selftext", "").strip()
                    permalink = post.get("permalink", "")
                    post_url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
                    created_utc = post.get("created_utc")
                    pub_dt = parse_timestamp_to_utc(created_utc)

                    full_text = f"{title}\n\n{selftext}" if selftext else title

                    items.append(
                        JobItem(
                            id=f"reddit_{post_id}",
                            title=title,
                            text=clean_html_text(full_text),
                            url=post_url,
                            source=f"Reddit: r/{sub}",
                            published=pub_dt,
                        )
                    )
                return items
            else:
                logger.warning(f"Reddit r/{sub} JSON returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error fetching Reddit r/{sub} JSON: {e}")

        return items

    def _fetch_subreddit_rss(self, sub: str, headers: dict) -> List[JobItem]:
        """Fallback to Reddit RSS endpoint."""
        url = f"https://www.reddit.com/r/{sub}/new.rss"
        items: List[JobItem] = []
        try:
            logger.info(f"Fetching Reddit r/{sub} via RSS fallback")
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[: self.limit]:
                    item_id = entry.get("id", "") or entry.get("link", "")
                    title = entry.get("title", "").strip()
                    post_url = entry.get("link", "")
                    raw_content = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")

                    # Fallback pub date
                    pub_dt = datetime.now(timezone.utc)
                    if entry.get("published_parsed"):
                        import time
                        pub_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)

                    items.append(
                        JobItem(
                            id=f"reddit_rss_{item_id}",
                            title=title,
                            text=clean_html_text(raw_content),
                            url=post_url,
                            source=f"Reddit: r/{sub}",
                            published=pub_dt,
                        )
                    )
        except Exception as e:
            logger.warning(f"Error fetching Reddit r/{sub} RSS: {e}")

        return items
