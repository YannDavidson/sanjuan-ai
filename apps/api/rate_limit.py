"""Small in-memory rate limiter for the SanJuan AI MVP API.

This limiter is intentionally simple and dependency-free. It is useful for local
MVP demos and a single-process deployment, but it is not a complete production
abuse protection system. For multi-process or scaled production deployments, use
an edge proxy, API gateway, Redis-backed limiter, or managed platform control.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import DefaultDict, Deque


@dataclass
class RateLimitDecision:
    """Result of a rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


@dataclass
class InMemoryRateLimiter:
    """Sliding-window request limiter keyed by client identifier."""

    max_requests: int
    window_seconds: int = 60
    _requests: DefaultDict[str, Deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def check(self, key: str, now: float | None = None) -> RateLimitDecision:
        """Record one request attempt and return whether it is allowed."""
        current_time = time.time() if now is None else now
        window_start = current_time - self.window_seconds
        request_times = self._requests[key]

        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        if len(request_times) >= self.max_requests:
            oldest = request_times[0]
            retry_after = max(1, int(round((oldest + self.window_seconds) - current_time)))
            return RateLimitDecision(
                allowed=False,
                limit=self.max_requests,
                remaining=0,
                retry_after_seconds=retry_after,
            )

        request_times.append(current_time)
        return RateLimitDecision(
            allowed=True,
            limit=self.max_requests,
            remaining=max(0, self.max_requests - len(request_times)),
            retry_after_seconds=0,
        )

    def reset(self) -> None:
        """Clear all in-memory counters. Primarily useful for tests."""
        self._requests.clear()
