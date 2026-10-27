#!/usr/bin/env python3
"""Mobile Job Opportunity Bot (Meta Threads Source Only).

Monitors mobile development job opportunities exclusively via official Meta Threads API,
filters opportunities with strict whole-word regex matching, crafts professional response
drafts using Google Gemini AI, and delivers actionable alerts to Telegram.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

from core.filters import JobFilter
from core.gemini_client import GeminiClient, validate_profile_content
from core.notifier import TelegramNotifier
from core.storage import Storage
from core.threads_token import ThreadsTokenManager
from sources.base import JobItem
from sources.threads import ThreadsAPIError, ThreadsSource, mask_secret

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("JobBot-Threads")


def check_required_env_vars() -> None:
    """Validates that credentials exist and do not contain template placeholders."""
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token or token.startswith("ISI_"):
        logger.error("Isi THREADS_ACCESS_TOKEN di .env dulu.")
        print("\n❌ ERROR: Isi THREADS_ACCESS_TOKEN di .env dulu.")
        print("Dapatkan User Access Token dari Meta for Developers > Threads App > User Token Generator.\n")
        sys.exit(1)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_test_threads(config: Dict[str, Any]) -> None:
    """Executes --test-threads to verify access token and API response."""
    check_required_env_vars()
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    threads_cfg = config.get("sources", {}).get("threads", {})
    keywords = threads_cfg.get("keywords", ["flutter developer"])
    test_kw = keywords[0] if keywords else "flutter developer"

    print("\n" + "=" * 65)
    print("🔍 MENGUJI KONEKSI META THREADS API (--test-threads)")
    print(f"Token Terdeteksi: {mask_secret(token)}")
    print(f"Keyword Uji: '{test_kw}'")
    print("=" * 65)

    source = ThreadsSource(
        access_token=token,
        keywords=[test_kw],
        timeout=int(config.get("settings", {}).get("request_timeout_seconds", 15)),
    )

    try:
        count, sample_items = source.test_search(keyword=test_kw)
        print(f"\n✅ Koneksi Threads API Berhasil!")
        print(f"Total postingan ditemukan untuk '{test_kw}': {count}")
        if sample_items:
            print("\n📋 3 Contoh Postingan Teratas:")
            for idx, it in enumerate(sample_items, start=1):
                print(f"  {idx}. [{it.source}] {it.title}")
                print(f"     URL: {it.url}")
        else:
            print("ℹ️ Tidak ada postingan yang ditemukan untuk keyword ini.")
            print("Catatan: Sebelum permission 'threads_keyword_search' disetujui Meta,")
            print("API hanya mengembalikan postingan yang dibuat oleh akun tester Anda sendiri.")
        print("=" * 65 + "\n")
    except ThreadsAPIError as e:
        print(f"\n❌ Threads API Error ({e.status_code}): {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Gagal menghubungi Threads API: {e}")
        sys.exit(1)


def run_pipeline(dry_run: bool = False, config_path: str = "config.yaml") -> int:
    """Executes the full pipeline: Threads -> filter -> Gemini -> Telegram."""
    check_required_env_vars()

    config = load_config(config_path)
    settings = config.get("settings", {})
    max_gemini_calls = int(settings.get("max_gemini_calls_per_run", 10))
    relevance_threshold = int(settings.get("relevance_threshold", 6))
    max_seen = int(settings.get("max_seen_items", 5000))
    timeout_sec = int(settings.get("request_timeout_seconds", 15))
    error_cooldown_min = int(settings.get("error_notify_cooldown_minutes", 60))

    storage = Storage(filepath="seen.json", max_items=max_seen)
    notifier = TelegramNotifier()
    job_filter = JobFilter(config=config, storage=storage)

    # Validate profile content early
    profile_path = "config/profile.md"
    try:
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as pf:
                validate_profile_content(pf.read())
        else:
            raise ValueError("File config/profile.md tidak ditemukan.")
    except ValueError as ve:
        logger.error("%s", ve)
        print(f"\n❌ ERROR: {ve}\n")
        return 1

    gemini = GeminiClient(
        fallback_templates=config.get("fallback_templates", {}),
        prompt_path="prompts/draft.txt",
        profile_path=profile_path,
        read_timeout=45,
        inter_call_delay=6.0,
    )

    logger.info("=" * 65)
    logger.info("Starting Mobile Job Opportunity Bot (Meta Threads Source)")
    logger.info("Dry Run Mode: %s", dry_run)
    logger.info("=" * 65)

    # Check token health (Inspect token and alert if near expiry < 10 days)
    threads_token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    token_mgr = ThreadsTokenManager(
        access_token=threads_token,
        app_id=os.environ.get("THREADS_APP_ID", "").strip(),
        app_secret=os.environ.get("THREADS_APP_SECRET", "").strip(),
        timeout=timeout_sec,
    )

    # 1. Fetch from Meta Threads API
    threads_cfg = config.get("sources", {}).get("threads", {})
    source = ThreadsSource(
        access_token=threads_token,
        keywords=threads_cfg.get("keywords", []),
        own_username=threads_cfg.get("own_username", ""),
        delay_seconds=float(threads_cfg.get("rate_limit_delay_seconds", 1.5)),
        max_requests_per_run=int(threads_cfg.get("max_requests_per_run", 10)),
        max_pages_per_keyword=int(threads_cfg.get("max_pages_per_keyword", 2)),
        timeout=timeout_sec,
    )

    raw_items: List[JobItem] = []
    try:
        raw_items = source.fetch()
    except Exception as e:
        logger.critical("Gagal mengambil data dari Threads: %s", e)
        if not dry_run:
            if source.token_expired_error and storage.can_send_token_expired_alert():
                notifier.send_token_expired_alert()
                storage.record_token_expired_alert_sent()
                storage.save()
            elif source.permission_error and storage.can_send_permission_alert():
                notifier.send_permission_alert()
                storage.record_permission_alert_sent()
                storage.save()
            elif storage.can_send_error_notification(cooldown_minutes=error_cooldown_min):
                notifier.send_error_alert(f"Threads API Failure: {str(e)}")
                storage.record_error_notification_sent()
                storage.save()
        return 1

    # Check for permission/token status reported by source
    if source.token_expired_error:
        if not dry_run and storage.can_send_token_expired_alert():
            notifier.send_token_expired_alert()
            storage.record_token_expired_alert_sent()
            storage.save()
        return 1

    if source.permission_error:
        if not dry_run and storage.can_send_permission_alert():
            notifier.send_permission_alert()
            storage.record_permission_alert_sent()
            storage.save()
        return 1

    logger.info("Total postingan Threads diambil: %d", len(raw_items))

    # 2. Strict Pre-filtering (Regex whole-word matching)
    candidates = job_filter.filter_batch(raw_items)
    logger.info("Postingan lolos filter bertahap: %d", len(candidates))

    if not candidates:
        logger.info("Tidak ada postingan baru yang memenuhi kriteria filter pada run ini.")
        if dry_run:
            logger.info("Total notifikasi yang AKAN dikirim (dry-run, tidak dikirim): 0")
        return 0

    if len(candidates) > max_gemini_calls:
        logger.info("Membatasi ke %d postingan teratas untuk hemat kuota Gemini.", max_gemini_calls)
        candidates = candidates[:max_gemini_calls]

    will_send_count = 0

    # 3. Gemini Evaluation & Telegram Notification
    for index, item in enumerate(candidates, start=1):
        logger.info("[%d/%d] Evaluasi dengan Gemini: '%s...'", index, len(candidates), item.title[:50])

        # Delay between Gemini calls (minimum 6s)
        if index > 1:
            time.sleep(6.0)

        analysis = gemini.evaluate_and_draft(item)
        if not analysis:
            continue

        # Check if consecutive 429 quota exhausted triggered
        if gemini.quota_exhausted and not dry_run and storage.can_send_gemini_quota_alert():
            notifier.send_gemini_quota_alert()
            storage.record_gemini_quota_alert_sent()
            storage.save()

        failed_ai = analysis.get("failed_ai", False)
        relevance = analysis.get("relevance")
        is_opp = analysis.get("is_opportunity", False)

        if failed_ai:
            # PENTING: Jika Gemini gagal, JANGAN beri skor palsu!
            # Kirim notif berlabel "⚠️ Tanpa penilaian AI" HANYA karena lolos filter ketat di atas.
            # JANGAN masukkan ke seen.json agar dicoba lagi di run berikutnya.
            logger.warning(
                "Gemini gagal menilai. Postingan lolos filter ketat akan dikirim tanpa skor AI (tidak disimpan ke seen.json)."
            )
            will_send_count += 1
            if dry_run:
                print("\n" + "=" * 65)
                print(f"⚠️ [DRY-RUN FALLBACK TANPA SKOR AI] {item.title}")
                print(f"📌 Sumber: {item.source} | URL: {item.url}")
                print(f"📝 Ringkasan: {analysis.get('summary')}")
                print(f"💬 Draft Komentar:\n{analysis.get('comment_draft')}")
                print(f"✉️ Draft DM:\n{analysis.get('dm_draft')}")
                print("=" * 65 + "\n")
            else:
                notifier.send_opportunity(item, analysis)
                # DO NOT mark seen! It will be retried when Gemini quota recovers.
            continue

        if not is_opp:
            logger.info("Dilewati: AI menilai postingan bukan lowongan/proyek mobile dev valid.")
            if not dry_run:
                storage.mark_seen(item.id, item.url)
            continue

        if relevance is not None and relevance < relevance_threshold:
            logger.info("Dilewati: Skor relevansi (%d) di bawah ambang batas (%d).", relevance, relevance_threshold)
            if not dry_run:
                storage.mark_seen(item.id, item.url)
            continue

        # Qualified Opportunity!
        will_send_count += 1
        if dry_run:
            print("\n" + "=" * 65)
            print(f"🎯 [DRY-RUN MATCH] [{relevance}/10] {item.title}")
            print(f"📌 Sumber: {item.source} | URL: {item.url}")
            print(f"📝 Ringkasan: {analysis.get('summary')}")
            print(f"💬 Draft Komentar (Threads):\n{analysis.get('comment_draft')}")
            print(f"✉️ Draft DM:\n{analysis.get('dm_draft')}")
            print("=" * 65 + "\n")
        else:
            sent = notifier.send_opportunity(item, analysis)
            if sent:
                logger.info("Notifikasi berhasil terkirim ke Telegram untuk '%s'", item.title[:40])
            storage.mark_seen(item.id, item.url)

    if dry_run:
        logger.info("Total notifikasi yang AKAN dikirim (dry-run, tidak dikirim): %d", will_send_count)
    else:
        logger.info("Pipeline selesai. Total notifikasi terkirim: %d", will_send_count)
        storage.save()

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Mobile Job Opportunity Bot (Threads Source)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Jalankan seluruh pipeline dan cetak ke konsol tanpa kirim Telegram dan tanpa update seen.json.",
    )
    parser.add_argument(
        "--test-telegram",
        action="store_true",
        help="Kirim pesan tes ke Telegram untuk memvalidasi token dan chat_id.",
    )
    parser.add_argument(
        "--test-threads",
        action="store_true",
        help="Uji panggilan Meta Threads API dengan satu keyword dan cetak hasil tanpa Gemini & Telegram.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Lokasi file konfigurasi YAML (default: config.yaml).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Aktifkan log DEBUG untuk analisis detail.",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test_telegram:
        notifier = TelegramNotifier()
        success = notifier.send_test_message()
        sys.exit(0 if success else 1)

    if args.test_threads:
        config = load_config(args.config)
        run_test_threads(config)
        sys.exit(0)

    code = run_pipeline(dry_run=args.dry_run, config_path=args.config)
    sys.exit(code)


if __name__ == "__main__":
    main()
