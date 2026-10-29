"""Google Gemini API client with flash-lite model, pacing, backoff, and strict no-fake-score policy."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional, Tuple
import requests

from sources.base import JobItem

logger = logging.getLogger(__name__)


def validate_profile_content(profile_text: str) -> None:
    """Checks whether config/profile.md still contains unfilled template placeholders."""
    if not profile_text or not profile_text.strip():
        raise ValueError("Isi config/profile.md dulu (file profil kosong).")

    placeholders = [
        "yourusername",
        "[Nama Lengkap Anda]",
        "[Contoh:",
        "your.email@example.com",
        "yourportfolio.dev",
    ]
    for ph in placeholders:
        if ph in profile_text:
            raise ValueError(f"Isi config/profile.md dulu (ditemukan placeholder belum diisi: '{ph}').")


class GeminiClient:
    """Evaluates Threads job opportunities and drafts responses using Google Gemini API."""

    DEFAULT_MODEL = "gemini-3.1-flash-lite"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        prompt_path: str = "prompts/draft.txt",
        profile_path: str = "config/profile.md",
        fallback_templates: Optional[Dict[str, str]] = None,
        read_timeout: int = 45,
        inter_call_delay: float = 6.0,
    ) -> None:
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        self.model = (model or os.environ.get("GEMINI_MODEL", "")).strip() or self.DEFAULT_MODEL
        self.prompt_template = self._load_file(prompt_path, default="")
        self.profile_path = profile_path
        self.profile_content = self._load_file(profile_path, default="")
        self.fallback_templates = fallback_templates or {}
        self.read_timeout = read_timeout
        self.inter_call_delay = inter_call_delay

        # Consecutive 429 rate limit tracking
        self.consecutive_429_count: int = 0
        self.quota_exhausted: bool = False

    def _load_file(self, path: str, default: str = "") -> str:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            logger.error("Gagal membaca file %s: %s", path, e)
        return default

    def evaluate_and_draft(self, item: JobItem) -> Optional[Dict[str, Any]]:
        """Evaluates a candidate post using Gemini.

        Returns:
            Dict containing:
            {
                "is_opportunity": bool,
                "relevance": Optional[int],  # None if AI failed
                "summary": str,
                "comment_draft": str,
                "dm_draft": str,
                "failed_ai": bool
            }
        """
        # Validate profile before proceeding
        validate_profile_content(self.profile_content)

        if self.quota_exhausted:
            logger.warning("Kuota Gemini habis pada run ini. Mengembalikan status AI gagal.")
            return self._create_failed_ai_response(item)

        if not self.api_key or self.api_key.startswith("ISI_"):
            raise ValueError("Isi GEMINI_API_KEY di .env dulu.")

        # Truncate post text to 1500 chars for token conservation
        truncated_text = item.text[:1500] if item.text else item.title
        username_str = f"@{item.username}" if item.username else "Threads User"

        prompt = self.prompt_template.replace("{PROFILE}", self.profile_content)
        prompt = prompt.replace("{POST_TITLE}", item.title)
        prompt = prompt.replace("{POST_SOURCE}", f"Threads ({username_str})")
        prompt = prompt.replace("{POST_URL}", item.url)
        prompt = prompt.replace("{POST_TEXT}", truncated_text)

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 450,
                "responseMimeType": "application/json",
            },
        }

        max_retries = 3
        backoff_delays = [3, 6, 12]

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "Mengirim evaluasi ke Gemini (%s) untuk '%s...' (Percobaan %d)",
                    self.model,
                    item.title[:40],
                    attempt + 1,
                )
                resp = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=(10, self.read_timeout),
                )

                if resp.status_code == 200:
                    self.consecutive_429_count = 0  # Reset counter
                    data = resp.json()
                    raw_text = self._extract_text(data)
                    parsed = self._parse_json_safely(raw_text)
                    if parsed:
                        parsed["failed_ai"] = False
                        return parsed
                    logger.warning("Gagal parse JSON dari respons Gemini. Mengalihkan ke fallback tanpa AI.")
                    return self._create_failed_ai_response(item)

                if resp.status_code == 429:
                    self.consecutive_429_count += 1
                    logger.warning("Gemini 429 Rate Limit (Beruntun: %d)", self.consecutive_429_count)

                    if self.consecutive_429_count >= 2:
                        logger.critical("Terdeteksi 2x error 429 beruntun! Menghentikan panggilan Gemini pada run ini.")
                        self.quota_exhausted = True
                        return self._create_failed_ai_response(item)

                    # Respect Retry-After header if returned
                    retry_after = resp.headers.get("Retry-After")
                    sleep_time = int(retry_after) if retry_after and retry_after.isdigit() else backoff_delays[attempt]
                    if attempt < max_retries:
                        time.sleep(sleep_time)
                        continue
                    return self._create_failed_ai_response(item)

                if resp.status_code in [500, 502, 503, 504]:
                    self.consecutive_429_count = 0
                    logger.warning("Gemini server error (HTTP %d). Percobaan ulang...", resp.status_code)
                    if attempt < max_retries:
                        time.sleep(backoff_delays[attempt])
                        continue
                    return self._create_failed_ai_response(item)

                logger.error("Gemini API error (HTTP %d): %s", resp.status_code, resp.text[:200])
                return self._create_failed_ai_response(item)

            except Exception as e:
                logger.error("Exception saat menghubungi Gemini API: %s", e)
                if attempt < max_retries:
                    time.sleep(backoff_delays[attempt])
                    continue
                return self._create_failed_ai_response(item)

        return self._create_failed_ai_response(item)

    def _extract_text(self, data: Dict[str, Any]) -> str:
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception:
            pass
        return ""

    def _parse_json_safely(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

        try:
            res = json.loads(cleaned)
            return self._normalize_result(res)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                res = json.loads(match.group(0))
                return self._normalize_result(res)
            except Exception:
                pass
        return None

    def _normalize_result(self, res: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "is_opportunity": bool(res.get("is_opportunity", True)),
            "relevance": int(res.get("relevance", 7)),
            "summary": str(res.get("summary", "")).strip(),
            "comment_draft": str(res.get("comment_draft", "")).strip(),
            "dm_draft": str(res.get("dm_draft", "")).strip(),
        }

    def _create_failed_ai_response(self, item: JobItem) -> Dict[str, Any]:
        """Provides un-scored fallback without faking relevance score.

        Relevance is None so callers know AI was not involved.
        """
        fallback_comment = self.fallback_templates.get(
            "comment_draft",
            "Halo! Saya Mobile Developer (Flutter/Kotlin/React Native). Tertarik berdiskusi terkait project ini, boleh saya kontak via DM?",
        )
        fallback_dm = self.fallback_templates.get(
            "dm_draft",
            "Halo! Saya membaca postingan lowongan Anda di Threads. Saya berpengalaman membangun aplikasi mobile multiplatform & native. Senang jika bisa berdiskusi lebih lanjut!",
        )
        return {
            "is_opportunity": True,  # Already pre-passed strict filters
            "relevance": None,       # NO FAKE SCORE! Explicitly None.
            "summary": f"Postingan Threads lolos filter ketat: {item.title}",
            "comment_draft": fallback_comment.strip(),
            "dm_draft": fallback_dm.strip(),
            "failed_ai": True,
        }
