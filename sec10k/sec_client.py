from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import requests

import logging
log = logging.getLogger(__name__)

class SecRateLimitError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecClientConfig:
    user_agent: str
    timeout_seconds: int = 30
    max_retries: int = 3
    backoff_base_seconds: float = 0.8 
    backoff_max_seconds: float = 10.0


class SecClient:
    def __init__(self, config: SecClientConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )


    def get_json(self, url: str, *, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        resp = self._get(url, params=params)
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeError(f"Expected JSON but got non-JSON response from {url}") from e

    def get_text(self, url: str, *, params: Optional[dict[str, Any]] = None) -> str:
        resp = self._get(url, params=params)
        # requests will decode based on headers; enforce utf-8 fallback if missing
        resp.encoding = resp.encoding or "utf-8"
        return resp.text

    def _get(self, url: str, *, params: Optional[dict[str, Any]] = None) -> requests.Response:
        last_exc: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.config.timeout_seconds)

                if resp.status_code == 429:
                    log.warning("SEC rate limited (429). attempt=%s url=%s", attempt, url)
                    self._sleep_backoff(attempt, resp)
                    last_exc = SecRateLimitError(f"SEC rate-limited: 429 | url={url}")
                    continue

                resp.raise_for_status()
                return resp

            except requests.HTTPError as e:
                last_exc = e

                if e.response is not None and e.response.status_code in (500, 502, 503, 504):
                    self._sleep_backoff(attempt, e.response)
                    continue

                body_snippet = ""
                if e.response is not None:
                    body_snippet = (e.response.text or "")[:200]

                raise RuntimeError(
                    f"SEC request failed: "
                    f"{e.response.status_code if e.response else 'unknown'} "
                    f"{e.response.reason if e.response else ''} | "
                    f"url={url} | body_snippet={body_snippet!r}"
                ) from e

            except requests.RequestException as e:
                last_exc = e
                log.warning("SEC request exception. attempt=%s url=%s err=%s", 
                            attempt, 
                            url, 
                            type(e).__name__,)
                self._sleep_backoff(attempt, None)
                continue

        if isinstance(last_exc, SecRateLimitError):
            raise SecRateLimitError(f"SEC request rate-limited after retries: url={url}") from last_exc

        raise RuntimeError(f"SEC request failed after retries: url={url}") from last_exc


    def _sleep_backoff(self, attempt: int, resp: Optional[requests.Response]) -> None:
        retry_after = None
        if resp is not None:
            ra = resp.headers.get("Retry-After")
            if ra and ra.isdigit():
                retry_after = int(ra)

        if retry_after is not None:
            sleep_s = min(float(retry_after), self.config.backoff_max_seconds)
        else:
            sleep_s = min(self.config.backoff_base_seconds * (2 ** attempt), self.config.backoff_max_seconds)

        time.sleep(sleep_s)
