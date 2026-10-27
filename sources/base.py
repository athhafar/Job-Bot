"""Base interfaces and data structures for job opportunity sources."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import re
import html


@dataclass
class JobItem:
    """Standardized job opportunity item."""
    id: str
    title: str
    text: str
    url: str
    source: str
    published: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary for serialization or logging."""
        data = asdict(self)
        data["published"] = self.published.isoformat()
        return data


def clean_html_text(raw_html: Optional[str]) -> str:
    """Strips HTML tags, unescapes HTML entities, and normalizes whitespaces."""
    if not raw_html:
        return ""
    # Remove script and style elements
    clean = re.sub(r"<(script|style).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Replace breaks and paragraphs with newlines
    clean = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", clean, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    clean = re.sub(r"<[^>]+>", " ", clean)
    # Decode HTML entities like &amp;, &nbsp;, &#39;
    clean = html.unescape(clean)
    # Clean multiple spaces while preserving single newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in clean.splitlines()]
    clean = "\n".join([line for line in lines if line])
    return clean.strip()


def parse_timestamp_to_utc(ts: Optional[float]) -> datetime:
    """Convert unix timestamp float/int to timezone-aware UTC datetime."""
    if not ts:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


class BaseSource:
    """Abstract base class that all data sources must implement."""

    def __init__(self, name: str, timeout: int = 15):
        self.name = name
        self.timeout = timeout

    def fetch(self) -> List[JobItem]:
        """Fetch items from the data source. Returns a list of JobItem."""
        raise NotImplementedError("Subclasses must implement fetch()")
