import json
import os
import time
from typing import Dict, Iterable, Iterator, List, Optional

import requests

from .errors import (
    OllamaConnectionError,
    OllamaHTTPError,
    OllamaResponseError,
)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 60.0,
        max_retries: int = 2,
        backoff_s: float = 0.5,
    ) -> None:
        self.base_url = base_url or os.getenv("QUIZMASTER_OLLAMA_HOST", "http://localhost:11434")
        self.model = model
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self._session = requests.Session()

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict] = None,
        keep_alive: Optional[str] = None,
    ) -> Dict | Iterator[Dict]:
        resolved_model = model or self.model
        if not resolved_model:
            raise ValueError("model is required for Ollama chat requests")
        payload: Dict = {
            "model": resolved_model,
            "messages": messages,
            "stream": stream,
        }
        if options is not None:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        return self._request("POST", "/api/chat", payload, stream=stream)

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict] = None,
        keep_alive: Optional[str] = None,
        system: Optional[str] = None,
    ) -> Dict | Iterator[Dict]:
        resolved_model = model or self.model
        if not resolved_model:
            raise ValueError("model is required for Ollama generate requests")
        payload: Dict = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": stream,
        }
        if system is not None:
            payload["system"] = system
        if options is not None:
            payload["options"] = options
        if keep_alive is not None:
            payload["keep_alive"] = keep_alive
        return self._request("POST", "/api/generate", payload, stream=stream)

    def health_check(self) -> bool:
        try:
            self._request("GET", "/api/version", payload=None, stream=False, expect_json=False)
            return True
        except Exception:
            try:
                self._request("GET", "/api/tags", payload=None, stream=False, expect_json=False)
                return True
            except Exception:
                return False

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict],
        stream: bool,
        expect_json: bool = True,
    ) -> Dict | Iterator[Dict]:
        url = self.base_url.rstrip("/") + path
        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.request(
                    method,
                    url,
                    json=payload if payload is not None else None,
                    timeout=self.timeout_s,
                    stream=stream,
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exception = exc
                if attempt >= self.max_retries:
                    raise OllamaConnectionError(str(exc)) from exc
                self._sleep(attempt)
                continue

            if response.status_code in RETRY_STATUS_CODES:
                if attempt >= self.max_retries:
                    raise OllamaHTTPError(response.status_code, self._safe_text(response))
                self._sleep(attempt)
                continue

            if not 200 <= response.status_code < 300:
                raise OllamaHTTPError(response.status_code, self._safe_text(response))

            if stream:
                return self._stream_json_lines(response)

            if not expect_json:
                return {"status_code": response.status_code}

            try:
                return response.json()
            except ValueError as exc:
                raise OllamaResponseError("Invalid JSON response") from exc

        if last_exception:
            raise OllamaConnectionError(str(last_exception)) from last_exception
        raise OllamaResponseError("Request failed without a response")

    def _stream_json_lines(self, response: requests.Response) -> Iterator[Dict]:
        def generator() -> Iterator[Dict]:
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except ValueError as exc:
                        raise OllamaResponseError("Invalid JSON in stream") from exc
            finally:
                response.close()

        return generator()

    def _sleep(self, attempt: int) -> None:
        time.sleep(self.backoff_s * (2**attempt))

    @staticmethod
    def _safe_text(response: requests.Response) -> str:
        try:
            return response.text
        except Exception:
            return "<unavailable>"
