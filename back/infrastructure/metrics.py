"""Simple in-memory metrics for observability (request counts, cache, errors)."""

import time
from typing import Any


class Metrics:
    """Lightweight metrics store. Increment from middleware and routes."""

    def __init__(self) -> None:
        self.requests_total = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.reports_generated = 0
        self.errors_total = 0
        self._start: float = 0.0
        self._duration_samples: list[float] = []

    def record_request_start(self) -> None:
        self._start = time.perf_counter()
        self.requests_total += 1

    def record_request_end(self) -> float:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        if len(self._duration_samples) < 1000:
            self._duration_samples.append(elapsed_ms)
        return elapsed_ms

    def _requests_duration_list(self) -> list[float]:
        return self._duration_samples

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def record_report_generated(self) -> None:
        self.reports_generated += 1

    def record_error(self) -> None:
        self.errors_total += 1

    def snapshot(self) -> dict[str, Any]:
        samples = self._requests_duration_list()
        avg_ms = sum(samples) / len(samples) if samples else 0
        return {
            "requests_total": self.requests_total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0 else 0
            ),
            "reports_generated": self.reports_generated,
            "errors_total": self.errors_total,
            "avg_request_duration_ms": round(avg_ms, 2),
        }

    def prometheus(self) -> str:
        """Prometheus exposition format for /metrics scraping."""
        s = self.snapshot()
        lines = [
            "# HELP github_doctor_requests_total Total HTTP requests",
            "# TYPE github_doctor_requests_total counter",
            f"github_doctor_requests_total {s['requests_total']}",
            "# HELP github_doctor_cache_hits Cache hits",
            "# TYPE github_doctor_cache_hits counter",
            f"github_doctor_cache_hits {s['cache_hits']}",
            "# HELP github_doctor_cache_misses Cache misses",
            "# TYPE github_doctor_cache_misses counter",
            f"github_doctor_cache_misses {s['cache_misses']}",
            "# HELP github_doctor_reports_generated Reports generated (cache misses that computed)",
            "# TYPE github_doctor_reports_generated counter",
            f"github_doctor_reports_generated {s['reports_generated']}",
            "# HELP github_doctor_errors_total Total errors",
            "# TYPE github_doctor_errors_total counter",
            f"github_doctor_errors_total {s['errors_total']}",
        ]
        return "\n".join(lines)


_metrics: Metrics | None = None


def get_metrics() -> Metrics:
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics
