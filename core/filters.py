"""Multi-stage pre-filtering with strict whole-word regex matching to conserve Gemini quota."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.storage import Storage
from sources.base import JobItem

logger = logging.getLogger(__name__)


def build_keyword_regex(keyword: str) -> re.Pattern:
    """Builds a case-insensitive whole-word regex pattern.

    Handles multi-word phrases and symbols cleanly with \\b boundaries.
    For example: 'expo' matches 'expo' but NOT 'exposure'.
    'react native' matches 'react native' with flexible whitespace.
    """
    cleaned = keyword.strip()
    words = re.split(r"\s+", cleaned)
    escaped_words = [re.escape(w) for w in words]
    pattern_str = r"\b" + r"\s+".join(escaped_words) + r"\b"
    return re.compile(pattern_str, flags=re.IGNORECASE)


class JobFilter:
    """Pre-filters raw job items prior to invoking Gemini LLM."""

    def __init__(self, config: Dict[str, Any], storage: Storage) -> None:
        self.config = config
        self.storage = storage

        keywords_cfg = config.get("keywords", {})

        # 1. Mobile Keywords (Whole-word regex)
        raw_includes = keywords_cfg.get(
            "include",
            [
                "flutter",
                "kotlin",
                "android developer",
                "react native",
                "mobile developer",
                "mobile engineer",
                "dart",
                "expo",
            ],
        )
        self.include_patterns: List[Tuple[str, re.Pattern]] = [
            (kw, build_keyword_regex(kw)) for kw in raw_includes if kw.strip()
        ]

        # 2. Specific Opportunity Signals (Must have at least one specific signal)
        # Note: 'remote' and 'opportunity' are explicitly excluded from standalone qualification
        raw_hiring = keywords_cfg.get(
            "hiring",
            [
                "hiring",
                "dicari",
                "lowongan",
                "butuh",
                "need",
                "looking for",
                "freelance",
                "kontrak",
                "open position",
                "kirim cv",
                "dm",
            ],
        )
        self.hiring_patterns: List[Tuple[str, re.Pattern]] = [
            (kw, build_keyword_regex(kw)) for kw in raw_hiring if kw.strip()
        ]

        # 3. Exclude Keywords (Job seekers, unpaid, internship)
        raw_excludes = keywords_cfg.get(
            "exclude",
            [
                "open to work",
                "available for hire",
                "cari kerja",
                "looking for a job",
                "for hire",
                "[for hire]",
                "unpaid",
                "magang",
                "internship",
                "volunteer",
                "portfolio review",
            ],
        )
        self.exclude_patterns: List[Tuple[str, re.Pattern]] = [
            (kw, build_keyword_regex(kw)) for kw in raw_excludes if kw.strip()
        ]

        settings_cfg = config.get("settings", {})
        self.max_age_hours = int(settings_cfg.get("max_post_age_hours", 24))

    def evaluate(self, item: JobItem) -> Tuple[bool, str]:
        """Evaluates whether an item passes all filter criteria.

        Returns:
            Tuple[bool, str]: (is_passed, reason)
        """
        # 1. Deduplication check
        if self.storage.is_seen(item.id, item.url):
            return False, "Already processed (seen)"

        # 2. Age limit check (max 24 hours by default)
        now_utc = datetime.now(timezone.utc)
        age = now_utc - item.published
        if age > timedelta(hours=self.max_age_hours):
            return False, f"Post is too old ({age.total_seconds() / 3600:.1f}h > {self.max_age_hours}h)"

        # Prepare normalized search corpus
        title_text = item.title or ""
        body_text = item.text or ""
        full_corpus = f"{title_text}\n{body_text}"

        # 3. Exclude keywords check (job seekers, unpaid, internship)
        for kw_name, pattern in self.exclude_patterns:
            if pattern.search(full_corpus):
                return False, f"Matched exclude keyword: '{kw_name}'"

        # 4. Mandatory Mobile include keywords check (Must match at least one whole word)
        matched_include: Optional[str] = None
        for kw_name, pattern in self.include_patterns:
            if pattern.search(full_corpus):
                matched_include = kw_name
                break

        if not matched_include:
            return False, "Missing required mobile developer keyword (whole word)"

        # 5. Mandatory Specific Opportunity signal (Must match at least one specific signal)
        matched_hiring: Optional[str] = None
        for kw_name, pattern in self.hiring_patterns:
            if pattern.search(full_corpus):
                matched_hiring = kw_name
                break

        if not matched_hiring:
            return False, "Missing specific hiring/opportunity signal (e.g. hiring, dicari, butuh, freelance)"

        return True, f"Passed filters (Mobile: '{matched_include}', Opportunity: '{matched_hiring}')"

    def filter_batch(self, items: List[JobItem]) -> List[JobItem]:
        """Filters a list of JobItem, logging rejection reasons."""
        passed: List[JobItem] = []
        for item in items:
            ok, reason = self.evaluate(item)
            if ok:
                logger.info("[FILTER PASSED] %s... (%s)", item.title[:60], reason)
                passed.append(item)
            else:
                logger.debug("[FILTER REJECTED] %s... Alasan: %s", item.title[:60], reason)

        logger.info(
            "Filtering selesai: %d dari %d postingan Threads memenuhi syarat untuk evaluasi AI.",
            len(passed),
            len(items),
        )
        return passed
