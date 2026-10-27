"""Gemini API client with structured JSON output, exponential backoff, and static fallback."""
import json
import logging
import os
import re
import time
from typing import Dict, Any, Optional
import requests

from sources.base import JobItem

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for generating AI evaluation and drafts via Google Gemini API."""

    DEFAULT_MODEL = "gemini-3.8-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        prompt_path: str = "prompts/draft.txt",
        profile_path: str = "config/profile.md",
        fallback_templates: Optional[Dict[str, str]] = None,
        timeout: int = 20,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = model or os.environ.get("GEMINI_MODEL", "").strip() or self.DEFAULT_MODEL
        self.prompt_template = self._load_file(prompt_path, default="Analisis postingan ini: {POST_TITLE} {POST_TEXT}")
        self.profile_content = self._load_file(profile_path, default="Mobile Developer (Flutter, Android Kotlin, React Native)")
        self.fallback_templates = fallback_templates or {}
        self.timeout = timeout

        if not self.api_key:
            logger.warning("GEMINI_API_KEY belum diatur di environment variable!")

    def _load_file(self, path: str, default: str = "") -> str:
        """Helper to read text file contents safely."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Gagal membaca file {path}: {e}")
        return default

    def evaluate_and_draft(self, item: JobItem) -> Optional[Dict[str, Any]]:
        """Evaluates a job post and generates comment/DM drafts.

        Returns a dictionary:
        {
            "is_opportunity": bool,
            "relevance": int,
            "summary": str,
            "comment_draft": str,
            "dm_draft": str,
            "used_fallback": bool
        }
        """
        # Format the user prompt
        # Truncate post text to ~1500 chars to conserve input tokens
        truncated_text = item.text[:1500] if item.text else "(Konten kosong, mengacu pada judul)"
        prompt = self.prompt_template.replace("{PROFILE}", self.profile_content)
        prompt = prompt.replace("{POST_TITLE}", item.title)
        prompt = prompt.replace("{POST_SOURCE}", item.source)
        prompt = prompt.replace("{POST_URL}", item.url)
        prompt = prompt.replace("{POST_TEXT}", truncated_text)

        # Call Gemini with exponential backoff on HTTP 429
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 450,
                "responseMimeType": "application/json",
            },
        }

        max_retries = 3
        backoff_delays = [2, 4, 8]

        for attempt in range(max_retries + 1):
            if not self.api_key:
                logger.warning("Tanpa API Key: Menggunakan fallback template statis.")
                return self._create_fallback_response(item)

            try:
                logger.info(f"Mengirim permintaan ke Gemini ({self.model}) untuk '{item.title[:40]}...' (Percobaan {attempt + 1})")
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)

                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = self._extract_text_from_response(data)
                    parsed = self._parse_json_safely(raw_text)
                    if parsed:
                        parsed["used_fallback"] = False
                        return parsed
                    else:
                        logger.warning("Gagal mem-parsing output JSON dari Gemini. Menggunakan fallback.")
                        return self._create_fallback_response(item)

                elif resp.status_code == 429:
                    logger.warning(f"Gemini API Rate Limit (HTTP 429) pada percobaan {attempt + 1}.")
                    if attempt < max_retries:
                        sleep_time = backoff_delays[attempt]
                        logger.info(f"Menunggu {sleep_time} detik sebelum retry...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        logger.error("Rate limit Gemini tetap terjadi setelah 3x retry. Mengalihkan ke template statis.")
                        return self._create_fallback_response(item)
                else:
                    logger.error(f"Gemini API error (HTTP {resp.status_code}): {resp.text[:200]}")
                    if attempt < max_retries and resp.status_code in [500, 502, 503, 504]:
                        time.sleep(backoff_delays[attempt])
                        continue
                    return self._create_fallback_response(item)

            except Exception as e:
                logger.error(f"Exception saat memanggil Gemini API: {e}")
                if attempt < max_retries:
                    time.sleep(backoff_delays[attempt])
                    continue
                return self._create_fallback_response(item)

        return self._create_fallback_response(item)

    def _extract_text_from_response(self, data: Dict[str, Any]) -> str:
        """Extracts generated text candidate from Gemini response payload."""
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        except Exception as e:
            logger.warning(f"Error extracting text from response: {e}")
        return ""

    def _parse_json_safely(self, text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from raw response string."""
        if not text:
            return None

        # Strip markdown code blocks like ```json ... ```
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

        # Attempt direct parse
        try:
            result = json.loads(cleaned)
            return self._normalize_result(result)
        except Exception:
            pass

        # Try regex search for first { ... } block
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                result = json.loads(match.group(0))
                return self._normalize_result(result)
            except Exception as e:
                logger.warning(f"Regex JSON parse failed: {e}")

        return None

    def _normalize_result(self, res: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all expected keys and types exist."""
        return {
            "is_opportunity": bool(res.get("is_opportunity", True)),
            "relevance": int(res.get("relevance", 7)),
            "summary": str(res.get("summary", "Lowongan mobile developer.")).strip(),
            "comment_draft": str(res.get("comment_draft", "")).strip(),
            "dm_draft": str(res.get("dm_draft", "")).strip(),
        }

    def _create_fallback_response(self, item: JobItem) -> Dict[str, Any]:
        """Provides static fallback draft templates so opportunity notification is never lost."""
        comment_tpl = self.fallback_templates.get(
            "comment_draft",
            "Halo! Saya Mobile Developer (Flutter/Kotlin/React Native). Tertarik berdiskusi terkait project ini, boleh saya kirimkan portofolio via DM?",
        )
        dm_tpl = self.fallback_templates.get(
            "dm_draft",
            "Halo! Saya tertarik dengan lowongan Mobile Developer ini. Berpengalaman di Flutter, Kotlin, & React Native. Portofolio: https://github.com/yourusername. Siap berdiskusi!",
        )
        return {
            "is_opportunity": True,
            "relevance": 7,  # Default above threshold so user gets notified
            "summary": f"Peluang lowongan terdeteksi dari {item.source}: {item.title[:100]}",
            "comment_draft": comment_tpl.strip(),
            "dm_draft": dm_tpl.strip(),
            "used_fallback": True,
        }
