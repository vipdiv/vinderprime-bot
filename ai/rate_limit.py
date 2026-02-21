import time

class RateLimiter:
    """Simple RPM limiter: guarantees we don't exceed requests/minute."""
    def __init__(self, rpm: int):
        self.rpm = max(int(rpm), 1)
        self.min_seconds = 60.0 / self.rpm
        self.last_ts = 0.0

    def wait(self):
        now = time.time()
        sleep_for = (self.last_ts + self.min_seconds) - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        self.last_ts = time.time()
