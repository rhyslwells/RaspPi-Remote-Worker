"""GET with timeout and retry, shared by the fetchers."""

import logging
import time

import requests

from grid.collector import config

logger = logging.getLogger(__name__)

_RETRY_STATUS = {429, 500, 502, 503, 504}


def get_text(url: str, timeout: int = 10) -> str:
    """One plain GET with no retry (used for the optional heartbeat ping)."""
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "raspi-grid-collector"})
    resp.raise_for_status()
    return resp.text


def get_json(url: str, params: dict = None):
    """
    GET a URL and return the decoded JSON. Retries on timeouts, connection errors
    and 429/5xx with a short backoff; raises the last error if every attempt fails.
    """
    last_exc = None
    for attempt in range(1, config.HTTP_ATTEMPTS + 1):
        try:
            resp = requests.get(
                url,
                params=params,
                timeout=config.HTTP_TIMEOUT_S,
                headers={"User-Agent": "raspi-grid-collector"},
            )
            if resp.status_code in _RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
            resp.raise_for_status()
            return resp.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_exc = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            # A 4xx other than 429 will not get better by retrying.
            if status is not None and status not in _RETRY_STATUS:
                raise
            if attempt < config.HTTP_ATTEMPTS:
                wait = config.HTTP_BACKOFF_S[min(attempt - 1, len(config.HTTP_BACKOFF_S) - 1)]
                logger.warning(
                    "GET %s failed (%s), retry %d/%d in %ss",
                    url, exc, attempt, config.HTTP_ATTEMPTS - 1, wait,
                )
                time.sleep(wait)
    raise last_exc
