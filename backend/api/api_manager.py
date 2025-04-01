import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

# File to track API usage
USAGE_TRACKER_FILE = 'api_usage.json'
# MarketAux free tier limit
DAILY_REQUEST_LIMIT = 100


class APIUsageTracker:
    """
    Tracks and manages API usage to stay within free tier limits.
    MarketAux free tier: 100 requests/day, 3 articles/request

    Thread-safe implementation for concurrent API calls.
    """

    def __init__(self, data_dir):
        self.tracker_path = Path(data_dir) / USAGE_TRACKER_FILE
        self.lock = threading.Lock()  # Add thread safety
        self.usage_data = self._load_usage_data()

    def _load_usage_data(self):
        """
        Load the usage tracking data from file, or create default if not exists.

        Returns:
            dict: The usage data
        """
        if self.tracker_path.exists():
            try:
                with open(self.tracker_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Log the error
                print(f"Error loading API usage data: {e}")

        # Default data structure if file doesn't exist or is corrupted
        return {
            "last_reset": datetime.now().isoformat(),
            "requests_today": 0,
            "total_requests": 0
        }

    def _save_usage_data(self):
        """Save the current usage data to file."""
        try:
            # Ensure the parent directory exists
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.tracker_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except IOError as e:
            print(f"Error saving API usage data: {e}")

    def _check_reset_day(self):
        """Check if we need to reset the daily counter."""
        try:
            last_reset = datetime.fromisoformat(self.usage_data["last_reset"])
            now = datetime.now()

            # If it's a new day, reset the counter
            if now.date() > last_reset.date():
                self.usage_data["last_reset"] = now.isoformat()
                self.usage_data["requests_today"] = 0
                self._save_usage_data()
        except (ValueError, KeyError) as e:
            # Handle malformed date or missing keys
            print(f"Error checking reset day: {e}")
            # Reset the usage data to defaults
            self.usage_data = {
                "last_reset": datetime.now().isoformat(),
                "requests_today": 0,
                "total_requests": 0
            }
            self._save_usage_data()

    def can_make_request(self):
        """
        Check if we can make another API request within our daily limit.

        Returns:
            bool: True if we can make a request, False otherwise
        """
        with self.lock:
            self._check_reset_day()
            return self.usage_data["requests_today"] < DAILY_REQUEST_LIMIT

    def record_request(self):
        """
        Record that we made an API request.
        Thread-safe implementation.
        """
        with self.lock:
            self._check_reset_day()
            self.usage_data["requests_today"] += 1
            self.usage_data["total_requests"] += 1
            self._save_usage_data()

    def get_remaining_requests(self):
        """
        Get number of remaining requests for today.

        Returns:
            int: Number of remaining requests
        """
        with self.lock:
            self._check_reset_day()
            return DAILY_REQUEST_LIMIT - self.usage_data["requests_today"]

    def get_usage_stats(self):
        """
        Get current usage statistics.

        Returns:
            dict: Dictionary with usage statistics
        """
        with self.lock:
            self._check_reset_day()

            # Calculate next reset time (midnight tonight)
            now = datetime.now()
            next_reset = datetime.combine(now.date() + timedelta(days=1),
                                          datetime.min.time())

            # Calculate hours until reset
            hours_until_reset = (next_reset - now).total_seconds() / 3600

            return {
                "requests_today": self.usage_data["requests_today"],
                "requests_remaining": DAILY_REQUEST_LIMIT - self.usage_data["requests_today"],
                "total_requests": self.usage_data["total_requests"],
                "last_reset": self.usage_data["last_reset"],
                "next_reset": next_reset.isoformat(),
                "reset_in_hours": round(hours_until_reset, 1)
            }