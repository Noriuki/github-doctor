"""In-memory TTL cache for repository health reports."""

import time
from typing import Any, Optional

from back.domain.models import RepositoryHealthReport


class ReportCache:
    """Simple TTL cache. Thread-safe for single-threaded async (no locks)."""

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 500):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._store: dict[str, tuple[RepositoryHealthReport, float]] = {}

    def _key(self, owner: str, repo: str, raw: bool) -> str:
        return f"{owner}:{repo}:{raw}"

    def get(self, owner: str, repo: str, raw: bool = False) -> Optional[RepositoryHealthReport]:
        key = self._key(owner, repo, raw)
        entry = self._store.get(key)
        if not entry:
            return None
        report, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return report

    def set(self, owner: str, repo: str, report: RepositoryHealthReport, raw: bool = False) -> None:
        if len(self._store) >= self._max:
            self._evict_expired()
            if len(self._store) >= self._max:
                # Remove oldest (first key)
                first = next(iter(self._store))
                del self._store[first]
        key = self._key(owner, repo, raw)
        self._store[key] = (report, time.monotonic() + self._ttl)

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


# Singleton for app use
_report_cache: Optional[ReportCache] = None


def get_report_cache(ttl_seconds: Optional[int] = None) -> ReportCache:
    global _report_cache
    if _report_cache is None:
        if ttl_seconds is None:
            try:
                from back.config import get_settings
                ttl_seconds = get_settings().cache_ttl_seconds
            except Exception:
                ttl_seconds = 300
        _report_cache = ReportCache(ttl_seconds=ttl_seconds)
    return _report_cache
