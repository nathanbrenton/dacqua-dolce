import hashlib
import threading
import time
from dataclasses import dataclass


@dataclass
class RateLimitBucket:
    window_started_at: float
    attempts: int


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class AuthenticationRateLimiter:
    """Process-local authentication abuse limiter.

    Production must pair this with reverse-proxy or shared-store
    rate limiting when multiple application processes/nodes exist.
    """

    def __init__(
        self,
        *,
        window_seconds: int,
        max_attempts: int,
        max_buckets: int = 10_000,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_attempts = max_attempts
        self.max_buckets = max_buckets
        self._buckets: dict[str, RateLimitBucket] = {}
        self._lock = threading.Lock()

    @staticmethod
    def email_key(email: str) -> str:
        normalized = email.strip().lower().encode()

        return hashlib.sha256(normalized).hexdigest()

    def check_and_record(
        self,
        key: str,
    ) -> RateLimitDecision:
        now = time.monotonic()

        with self._lock:
            bucket = self._buckets.get(key)

            if bucket is None or now - bucket.window_started_at >= self.window_seconds:
                self._buckets[key] = RateLimitBucket(
                    window_started_at=now,
                    attempts=1,
                )
                self._trim_if_needed()

                return RateLimitDecision(True, 0)

            if bucket.attempts >= self.max_attempts:
                retry_after = max(
                    1,
                    int(self.window_seconds - (now - bucket.window_started_at)),
                )

                return RateLimitDecision(
                    False,
                    retry_after,
                )

            bucket.attempts += 1

            return RateLimitDecision(True, 0)

    def clear(self, key: str) -> None:
        with self._lock:
            self._buckets.pop(key, None)

    def _trim_if_needed(self) -> None:
        if len(self._buckets) <= self.max_buckets:
            return

        oldest = sorted(
            self._buckets.items(),
            key=lambda item: item[1].window_started_at,
        )

        remove_count = len(self._buckets) - self.max_buckets

        for key, _bucket in oldest[:remove_count]:
            self._buckets.pop(key, None)
