#!/usr/bin/env python3
"""Mobile Job Opportunity Bot - Main Orchestrator.

Monitors mobile development job opportunities (Flutter, Android Kotlin, React Native),
filters noise, evaluates with Gemini AI, and delivers actionable alerts with ready-to-use
comment & DM drafts to Telegram.
"""

import argparse
import logging
import os
import sys
from typing import List, Dict, Any
import yaml
from dotenv import load_dotenv

from sources.base import JobItem, BaseSource
from sources.rss import RSSSource
from sources.reddit import RedditSource
from sources.hn import HackerNewsSource
from sources.threads_stub import ThreadsStubSource, TelegramChannelStubSource
from core.storage import Storage
from core.filters import JobFilter
from core.gemini_client import GeminiClient
from core.notifier import TelegramNotifier

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("JobBot")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Loads YAML configuration file."""
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def init_sources(config: Dict[str, Any]) -> List[BaseSource]:
    """Instantiates enabled sources based on config.yaml."""
    sources_cfg = config.get("sources", {})
    timeout = config.get("settings", {}).get("request_timeout_seconds", 15)
    active_sources: List[BaseSource] = []

    # 1. RSS Feeds
    rss_cfg = sources_cfg.get("rss", {})
    if rss_cfg.get("enabled", True):
        feeds = rss_cfg.get("feeds", [])
        if feeds:
            active_sources.append(RSSSource(feeds=feeds, timeout=timeout))

    # 2. Reddit
    reddit_cfg = sources_cfg.get("reddit", {})
    if reddit_cfg.get("enabled", True):
        subs = reddit_cfg.get("subreddits", [])
        ua = reddit_cfg.get("user_agent", "JobOpportunityBot/1.0")
        limit = reddit_cfg.get("limit_per_sub", 25)
        if subs:
            active_sources.append(RedditSource(subreddits=subs, user_agent=ua, limit_per_sub=limit, timeout=timeout))

    # 3. Hacker News
    hn_cfg = sources_cfg.get("hacker_news", {})
    if hn_cfg.get("enabled", True):
        queries = hn_cfg.get("queries", ["mobile", "flutter", "react native", "android"])
        limit_q = hn_cfg.get("limit_per_query", 20)
        active_sources.append(HackerNewsSource(queries=queries, limit_per_query=limit_q, timeout=timeout))

    # 4. Threads (Stub)
    threads_cfg = sources_cfg.get("threads", {})
    if threads_cfg.get("enabled", False):
        active_sources.append(ThreadsStubSource(keywords=threads_cfg.get("keywords", []), timeout=timeout))

    # 5. Telegram Channels (Stub)
    tg_chan_cfg = sources_cfg.get("telegram_channels", {})
    if tg_chan_cfg.get("enabled", False):
        active_sources.append(TelegramChannelStubSource(channels=tg_chan_cfg.get("channels", []), timeout=timeout))

    return active_sources


def run_pipeline(dry_run: bool = False, config_path: str = "config.yaml") -> int:
    """Executes the full pipeline: Fetch -> Filter -> Gemini Draft -> Telegram Notify."""
    config = load_config(config_path)
    settings = config.get("settings", {})
    max_gemini_calls = int(settings.get("max_gemini_calls_per_run", 10))
    relevance_threshold = int(settings.get("relevance_threshold", 6))
    max_seen = int(settings.get("max_seen_items", 5000))
    cooldown_error_min = int(settings.get("error_notify_cooldown_minutes", 60))

    storage = Storage(filepath="seen.json", max_items=max_seen)
    notifier = TelegramNotifier()
    job_filter = JobFilter(config=config, storage=storage)
    gemini = GeminiClient(
        fallback_templates=config.get("fallback_templates", {}),
        prompt_path="prompts/draft.txt",
        profile_path="config/profile.md",
    )

    logger.info("=" * 60)
    logger.info(f"Starting Job Opportunity Bot (Dry Run: {dry_run})")
    logger.info("=" * 60)

    try:
        # Step 1: Collect from all sources with isolated fault-tolerance
        sources = init_sources(config)
        all_raw_items: List[JobItem] = []

        for src in sources:
            try:
                items = src.fetch()
                all_raw_items.extend(items)
            except Exception as src_err:
                logger.error(f"Error executing source {src.name}: {src_err}", exc_info=True)

        logger.info(f"Total raw items collected from all sources: {len(all_raw_items)}")

        # Step 2: Multi-stage pre-filtering
        candidates = job_filter.filter_batch(all_raw_items)
        logger.info(f"Items passing pre-filter criteria: {len(candidates)}")

        if not candidates:
            logger.info("Tidak ada lowongan baru yang memenuhi kriteria filter pada run ini.")
            return 0

        # Step 3: Rate limiter - process up to max_gemini_calls
        if len(candidates) > max_gemini_calls:
            logger.info(f"Membatasi analisis ke {max_gemini_calls} postingan teratas untuk hemat kuota Gemini.")
            candidates = candidates[:max_gemini_calls]

        notified_count = 0

        # Step 4: AI Analysis & Drafting + Notification
        for index, item in enumerate(candidates, start=1):
            logger.info(f"[{index}/{len(candidates)}] Menilai dengan Gemini: '{item.title[:60]}...'")
            analysis = gemini.evaluate_and_draft(item)

            if not analysis:
                logger.warning(f"Tidak ada respons dari evaluator untuk item: {item.id}")
                continue

            is_opp = analysis.get("is_opportunity", False)
            score = analysis.get("relevance", 0)

            logger.info(f"Hasil AI -> Is Opportunity: {is_opp}, Skor Relevansi: {score}/10")

            if not is_opp:
                logger.info(f"Dilewati: AI menilai postingan BUKAN lowongan/proyek mobile dev valid.")
                if not dry_run:
                    storage.mark_seen(item.id, item.url)
                continue

            if score < relevance_threshold:
                logger.info(f"Dilewati: Skor ({score}) di bawah ambang batas ({relevance_threshold}).")
                if not dry_run:
                    storage.mark_seen(item.id, item.url)
                continue

            # Qualified Opportunity!
            if dry_run:
                print("\n" + "=" * 65)
                print(f"🎯 [DRY-RUN MATCH] [{score}/10] {item.title}")
                print(f"📌 Sumber: {item.source} | URL: {item.url}")
                print(f"📝 Ringkasan: {analysis.get('summary')}")
                print(f"💬 Draft Komentar:\n{analysis.get('comment_draft')}")
                print(f"✉️ Draft DM:\n{analysis.get('dm_draft')}")
                print("=" * 65 + "\n")
                notified_count += 1
            else:
                sent = notifier.send_opportunity(item, analysis)
                if sent:
                    notified_count += 1
                    logger.info(f"Notifikasi berhasil terkirim ke Telegram untuk '{item.title[:40]}'")
                else:
                    logger.error(f"Gagal mengirim notifikasi Telegram untuk '{item.title[:40]}'")

                storage.mark_seen(item.id, item.url)

        logger.info(f"Pipeline selesai. Total notifikasi terkirim: {notified_count}")

        # Step 5: Persist updated state
        if not dry_run:
            storage.save()

        return 0

    except Exception as e:
        logger.critical(f"FATAL ERROR dalam pipeline bot: {e}", exc_info=True)
        if not dry_run and storage.can_send_error_notification(cooldown_minutes=cooldown_error_min):
            notifier.send_error_alert(f"Critical error: {str(e)}")
            storage.record_error_notification_sent()
            storage.save()
        return 1


def main():
    parser = argparse.ArgumentParser(description="Mobile Job Opportunity Bot")
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

    code = run_pipeline(dry_run=args.dry_run, config_path=args.config)
    sys.exit(code)


if __name__ == "__main__":
    main()
