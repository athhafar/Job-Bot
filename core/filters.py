"""Multi-stage pre-filtering to conserve Gemini API quota and eliminate noise."""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from sources.base import JobItem
from core.storage import Storage

logger = logging.getLogger(__name__)


class JobFilter:
    """Pre-filters raw job items prior to invoking Gemini LLM."""

    def __init__(self, config: Dict[str, Any], storage: Storage):
        self.config = config
        self.storage = storage

        keywords_cfg = config.get("keywords", {})
        self.include_keywords = [k.lower() for k in keywords_cfg.get("include", [])]
        self.hiring_keywords = [k.lower() for k in keywords_cfg.get("hiring", [])]
        self.exclude_keywords = [k.lower() for k in keywords_cfg.get("exclude", [])]

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
        title_lower = (item.title or "").lower()
        text_lower = (item.text or "").lower()
        full_corpus = f"{title_lower} \n {text_lower}"

        # 3. Exclude keywords check (unpaid, internship, job seekers like [FOR HIRE])
        # Prioritize title check for job seeker flags like [for hire]
        for exc in self.exclude_keywords:
            if exc in title_lower or exc in full_corpus:
                return False, f"Matched exclude keyword: '{exc}'"

        # 4. Mandatory Mobile include keywords check
        matched_include = None
        for inc in self.include_keywords:
            if inc in full_corpus:
                matched_include = inc
                break

        if not matched_include:
            return False, "Missing mobile developer include keyword"

        # 5. Mandatory Hiring / Opportunity keywords check
        matched_hiring = None
        for hir in self.hiring_keywords:
            if hir in full_corpus:
                matched_hiring = hir
                break

        if not matched_hiring:
            return False, "Missing hiring/opportunity intent keyword"

        return True, f"Passed filters (Include: '{matched_include}', Hiring: '{matched_hiring}')"

    def filter_batch(self, items: List[JobItem]) -> List[JobItem]:
        """Filters a list of JobItem, logging rejection reasons."""
        passed: List[JobItem] = []
        for item in items:
            ok, reason = self.evaluate(item)
            if ok:
                logger.info(f"[FILTER PASSED] {item.title[:60]}... ({reason})")
                passed.append(item)
            else:
                logger.debug(f"[FILTER REJECTED] {item.title[:60]}... Reason: {reason}")

        logger.info(f"Filtering complete: {len(passed)} of {len(items)} items qualified for AI review")
        return passed
