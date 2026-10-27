"""Sources package for Job Opportunity Bot."""
from sources.base import JobItem, BaseSource
from sources.rss import RSSSource
from sources.reddit import RedditSource
from sources.hn import HackerNewsSource
from sources.threads_stub import ThreadsStubSource, TelegramChannelStubSource

__all__ = [
    "JobItem",
    "BaseSource",
    "RSSSource",
    "RedditSource",
    "HackerNewsSource",
    "ThreadsStubSource",
    "TelegramChannelStubSource",
]
