"""Meta Threads access token management (inspection, refresh, exchange)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import requests

from sources.threads import mask_secret

logger = logging.getLogger(__name__)


class ThreadsTokenManager:
    """Manages Meta Threads long-lived user access tokens."""

    REFRESH_ENDPOINT = "https://graph.threads.net/refresh_access_token"
    EXCHANGE_ENDPOINT = "https://graph.threads.net/access_token"
    ME_ENDPOINT = "https://graph.threads.net/v1.0/me"

    def __init__(
        self,
        access_token: str,
        app_id: str = "",
        app_secret: str = "",
        timeout: int = 15,
    ) -> None:
        self.access_token = access_token.strip()
        self.app_id = app_id.strip()
        self.app_secret = app_secret.strip()
        self.timeout = timeout

    def inspect_token(self) -> Dict[str, Any]:
        """Validates token by querying authenticated user profile (/me)."""
        if not self.access_token or self.access_token.startswith("ISI_"):
            return {"valid": False, "error": "Token belum diisi"}

        try:
            resp = requests.get(
                self.ME_ENDPOINT,
                params={"fields": "id,username,threads_profile_picture_url", "access_token": self.access_token},
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "valid": True,
                    "user_id": data.get("id"),
                    "username": data.get("username"),
                    "masked_token": mask_secret(self.access_token),
                }
            else:
                err = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                return {"valid": False, "error": err}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def refresh_long_lived_token(self) -> Tuple[bool, Optional[str], int, str]:
        """Refreshes an unexpired long-lived access token.

        Returns:
            Tuple[success, new_access_token, expires_in_seconds, error_or_expiry_message]
        """
        if not self.access_token or self.access_token.startswith("ISI_"):
            return False, None, 0, "Token belum diisi di environment variable."

        params = {
            "grant_type": "th_refresh_token",
            "access_token": self.access_token,
        }

        try:
            logger.info("Memanggil endpoint refresh token Threads (grant_type=th_refresh_token)...")
            resp = requests.get(self.REFRESH_ENDPOINT, params=params, timeout=self.timeout)

            if resp.status_code == 200:
                data = resp.json()
                new_token = data.get("access_token")
                expires_in = int(data.get("expires_in", 5184000))  # approx 60 days
                expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                expiry_str = expiry_dt.strftime("%Y-%m-%d %H:%M:%S UTC")

                logger.info(
                    "Token Threads berhasil diperbarui! Masa berlaku hingga: %s (expires_in: %d detik).",
                    expiry_str,
                    expires_in,
                )
                return True, new_token, expires_in, expiry_str
            else:
                err_msg = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                logger.error("Gagal memperbarui token Threads: %s", err_msg)
                return False, None, 0, err_msg
        except Exception as e:
            logger.error("Exception saat memperbarui token Threads: %s", e)
            return False, None, 0, str(e)

    def exchange_short_lived_token(self) -> Tuple[bool, Optional[str], int, str]:
        """Exchanges a short-lived user token for a long-lived 60-day token using THREADS_APP_SECRET."""
        if not self.app_secret or self.app_secret.startswith("ISI_"):
            return False, None, 0, "THREADS_APP_SECRET diperlukan untuk menukar token jangka pendek."

        params = {
            "grant_type": "th_exchange_token",
            "client_secret": self.app_secret,
            "access_token": self.access_token,
        }

        try:
            logger.info("Menukar token jangka pendek dengan jangka panjang (th_exchange_token)...")
            resp = requests.get(self.EXCHANGE_ENDPOINT, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                new_token = data.get("access_token")
                expires_in = int(data.get("expires_in", 5184000))
                expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                return True, new_token, expires_in, expiry_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                err_msg = resp.json().get("error", {}).get("message", f"HTTP {resp.status_code}")
                return False, None, 0, err_msg
        except Exception as e:
            return False, None, 0, str(e)
