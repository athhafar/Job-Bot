"""Base interfaces and data structures for job opportunity sources."""
from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class JobItem:
    """Standardized job opportunity item from Threads."""

    id: str
    title: str
    text: str
    url: str
    source: str
    published: datetime
    username: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for serialization or logging."""
        data = asdict(self)
        data["published"] = self.published.isoformat()
        return data


def clean_html_text(raw_html: Optional[str]) -> str:
    """Strips HTML tags, unescapes HTML entities, and normalizes whitespaces."""
    if not raw_html:
        return ""
    clean = re.sub(r"<(script|style).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = html.unescape(clean)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in clean.splitlines()]
    clean = "\n".join([line for line in lines if line])
    return clean.strip()


def parse_iso_timestamp_to_utc(iso_str: Optional[str]) -> datetime:
    """Converts ISO 8601 timestamp string (e.g., 2024-05-01T12:00:00+0000) to UTC datetime."""
    if not iso_str:
        return datetime.now(timezone.utc)
    try:
        # Standardize format
        iso_clean = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


class BaseSource:
    """Abstract base class that data sources must implement."""

    def __init__(self, name: str, timeout: int = 15) -> None:
        self.name = name
        self.timeout = timeout

    def fetch(self) -> List[JobItem]:
        """Fetch items from the data source. Returns a list of JobItem."""
        raise NotImplementedError("Subclasses must implement fetch()")
