import threading
import time
import json
from typing import Any, Dict, List, Optional

# Optionally import python-chargepoint if available
try:
    from python_chargepoint import ChargePoint
except ImportError:
    ChargePoint = None

class RateLimiter:
    """
    Simple token bucket rate limiter.
    Allows up to 'rate' requests per 'per' seconds.
    """
    def __init__(self, rate: int, per: float):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            current = time.monotonic()
            elapsed = current - self.last_check
            self.last_check = current
            self.allowance += elapsed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                time.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= 1.0

class ChargePointDAL:
    """
    Caching, rate-limited data access layer for ChargePoint API.
    """
    def get_session_activity(self, session_id: str, include_samples: bool = True) -> Optional[Dict[str, Any]]:
        """
        Retrieve detailed activity for a specific session, with caching.
        Args:
            session_id: The session ID to fetch details for
            include_samples: Whether to include power samples (default: True)
        Returns:
            Session activity dict, or None if not found
        """
        cache_key = f"session_activity_{session_id}_{'samples' if include_samples else 'nosamples'}"
        with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
        payload = {"session_id": session_id, "include_samples": include_samples}
        response = self.client.session.post(
            self.client.global_config.endpoints.mapcache + "v2",
            json=payload
        )
        self.ratelimiter.acquire()
        data = response.json()
        with self.lock:
            self.cache[cache_key] = data
            self._save_cache()
        return data

    def __init__(self, username: str, password: str, cache_path: Optional[str] = None,
                 rate_limit: int = 6, rate_period: float = 60.0,
                 session_token_path: Optional[str] = None):
        """
        Args:
            username: ChargePoint account username
            password: ChargePoint account password
            cache_path: Path to cache file (optional, defaults to data/cache/chargepoint_dal_cache.json)
            rate_limit: Max requests per rate_period (default: 6/min)
            rate_period: Time window for rate limiting in seconds
                session_token_path: Path to session token cache file (optional, defaults to data/cache/cp_session_token.txt)
        """

        if ChargePoint is None:
            raise ImportError("python-chargepoint is required for ChargePointDAL")

        if session_token_path is None:
            session_token_path = "data/cache/cp_session_token.txt"
        self.session_token_path = session_token_path

        session_token = self._load_session_token()
        try:
            if session_token:
                self.client = ChargePoint(username=username, password=password, session_token=session_token)
            else:
                self.client = ChargePoint(username=username, password=password)
        except Exception:
            # If session token is expired or invalid, fallback to login
            self.client = ChargePoint(username=username, password=password)
        # Always cache the latest session token after login
        self._save_session_token(self.client.session_token)

        if cache_path is None:
            cache_path = "data/cache/chargepoint_dal_cache.json"

        self.cache_path = cache_path
        self.cache: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.ratelimiter = RateLimiter(rate_limit, rate_period)
        self._load_cache()

    def _load_session_token(self) -> Optional[str]:
        try:
            with open(self.session_token_path, "r") as f:
                token = f.read().strip()
                return token if token else None
        except Exception:
            return None

    def _save_session_token(self, token: Optional[str]):
        if not token:
            return
        try:
            with open(self.session_token_path, "w") as f:
                f.write(token)
        except Exception:
            pass

    def _load_cache(self):
        try:
            with open(self.cache_path, "r") as f:
                self.cache = json.load(f)
        except Exception:
            self.cache = {}

    def _save_cache(self):
        if not self.cache_path:
            return
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f)

    def get_sessions(self, max_batches: int = 10, batch_size: int = 10, year: int = None, month: int = None) -> List[Dict[str, Any]]:
        """
        Fetches charging sessions, using cache if available.
        Args:
            max_batches: Maximum number of batches to fetch
            batch_size: Number of sessions per batch
            year: Optional year for monthly paging (e.g., 2025)
            month: Optional month for monthly paging (1-12)
        Returns:
            List of session dicts
        """
        page_offset = None
        if year is not None and month is not None:
            page_offset = f"p_{year}_{month:02d}"
        cache_key = f"sessions_{max_batches}_{batch_size}_{page_offset or 'all'}"
        with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
        sessions = []
        # Initial request payload
        payload = {"charging_activity_monthly": {"page_size": batch_size, "show_address_for_home_sessions": True}}
        if page_offset:
            payload["charging_activity_monthly"]["page_offset"] = page_offset
            response = self.client.session.post(
                self.client.global_config.endpoints.mapcache + "v2",
            json=payload
        )
        self.ratelimiter.acquire()
        data = response.json()
        activity = data.get("charging_activity")
        if activity:
            sessions.extend(activity.get("sessions", []))
            page_offset = activity.get("page_offset")
        else:
            # Try alternate format: charging_activity_monthly → month_info → [0] → sessions
            monthly = data.get("charging_activity_monthly")
            if monthly and "month_info" in monthly and monthly["month_info"]:
                month_info = monthly["month_info"][0]
                if "sessions" in month_info:
                    sessions.extend(month_info["sessions"])
                    page_offset = data.get("page_offset") or monthly.get("page_offset")
            else:
                print("No 'charging_activity' or 'charging_activity_monthly' in response:", data)
                return sessions
        for i in range(max_batches - 1):
            if page_offset == "last_page":
                break
            payload["charging_activity_monthly"]["page_offset"] = page_offset
            response = self.client.session.post(
                    self.client.global_config.endpoints.mapcache + "v2",
                json=payload
            )
            self.ratelimiter.acquire()
            data = response.json()
            activity = data.get("charging_activity")
            if not activity:
                print("No 'charging_activity' in response:", data)
                break
            sessions.extend(activity.get("sessions", []))
            page_offset = activity.get("page_offset")
        with self.lock:
            self.cache[cache_key] = sessions
            # Cache each session individually by session_id
            for session in sessions:
                sid = session.get("session_id") or session.get("sessionId")
                if sid is not None:
                    self.cache[f"session_{sid}"] = session
            self._save_cache()
        return sessions

    # Additional methods for fetching session details, status, etc. can be added here
