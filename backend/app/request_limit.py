"""Small single-process abuse guard for public authentication endpoints.

This deployment runs one Uvicorn worker. A multi-worker deployment needs a
shared limiter (for example Redis or an edge service) instead of this module.
"""

from collections import deque
from ipaddress import ip_address
from threading import Lock
from time import monotonic


AUTH_LIMITS = {
    "/api/auth/register": (10, 3600),
    "/api/auth/login": (60, 900),
    "/api/auth/verify-email": (30, 900),
    "/api/auth/verify-email/resend": (20, 3600),
    "/api/auth/password-reset/request": (20, 3600),
    "/api/auth/password-reset/confirm": (20, 900),
    "/api/admin/mfa/enroll": (10, 900),
    "/api/admin/mfa/confirm": (10, 900),
}


class RequestLimiter:
    def __init__(self):
        self._events: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    def check(self, address: str, path: str, instant: float | None = None) -> int:
        """Return seconds to retry, or zero when the request is allowed."""
        maximum, window = AUTH_LIMITS[path]
        current = monotonic() if instant is None else instant
        key = (address, path)
        with self._lock:
            # Bound memory even under a flood of distinct source addresses.
            if len(self._events) >= 5000 and key not in self._events:
                self._events = {item: times for item, times in self._events.items()
                                if times and times[-1] > current - AUTH_LIMITS[item[1]][1]}
                if len(self._events) >= 5000:
                    self._events.pop(next(iter(self._events)))
            times = self._events.setdefault(key, deque())
            while times and times[0] <= current - window:
                times.popleft()
            if len(times) >= maximum:
                return max(1, int(times[0] + window - current) + 1)
            times.append(current)
            return 0


def source_address(peer: str, forwarded: str | None) -> str:
    """Only honor Caddy's forwarded address when the immediate peer is loopback."""
    try:
        remote = ip_address(peer)
        if remote.is_loopback and forwarded:
            return str(ip_address(forwarded.split(",", 1)[0].strip()))
        return str(remote)
    except ValueError:
        return peer


limiter = RequestLimiter()
