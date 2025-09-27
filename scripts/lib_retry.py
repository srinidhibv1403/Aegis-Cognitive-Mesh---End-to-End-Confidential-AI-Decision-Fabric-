#!/usr/bin/env python3
import time, random
from typing import Callable, Tuple

class RetryError(Exception):
    pass

def retry(
    func: Callable[[], Tuple[bool, str]],
    attempts: int = 5,
    base_delay: float = 0.4,
    max_delay: float = 3.0,
    jitter: float = 0.25,
) -> Tuple[bool, str]:
    """
    Calls func() which must return (ok: bool, msg: str).
    Retries on ok=False with exponential backoff + jitter.
    """
    delay = base_delay
    last_msg = ""
    for i in range(1, attempts + 1):
        ok, msg = func()
        if ok:
            return True, msg
        last_msg = msg
        if i == attempts:
            break
        sleep_for = min(max_delay, delay * (1.5 ** (i - 1)))
        sleep_for += random.uniform(-jitter, jitter) * base_delay
        time.sleep(max(0.05, sleep_for))
    return False, f"retry_exhausted: {last_msg}"
