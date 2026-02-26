import json

import pytest
import requests

from quizmaster.clients.ollama_client import OllamaClient
from quizmaster.clients.errors import (
    OllamaHTTPError,
    OllamaResponseError,
)


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text="", lines=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self._lines = lines or []
        self.closed = False

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data

    def iter_lines(self, decode_unicode=False):
        for line in self._lines:
            yield line

    def close(self):
        self.closed = True


def test_chat_payload_construction(monkeypatch):
    calls = []

    def fake_request(method, url, json=None, timeout=None, stream=None):
        calls.append((method, url, json, timeout, stream))
        return DummyResponse(json_data={"message": {"content": "ok"}})

    client = OllamaClient(base_url="http://host", model="m1", timeout_s=12)
    monkeypatch.setattr(client._session, "request", fake_request)

    response = client.chat([{"role": "user", "content": "hi"}], stream=False)
    assert response["message"]["content"] == "ok"
    method, url, payload, timeout, stream = calls[0]
    assert method == "POST"
    assert url == "http://host/api/chat"
    assert payload["model"] == "m1"
    assert payload["messages"][0]["content"] == "hi"
    assert payload["stream"] is False
    assert timeout == 12
    assert stream is False


def test_generate_payload_construction(monkeypatch):
    calls = []

    def fake_request(method, url, json=None, timeout=None, stream=None):
        calls.append((method, url, json, timeout, stream))
        return DummyResponse(json_data={"response": "ok"})

    client = OllamaClient(base_url="http://host", model="m2")
    monkeypatch.setattr(client._session, "request", fake_request)

    response = client.generate("hello", stream=False, system="sys")
    assert response["response"] == "ok"
    method, url, payload, _, _ = calls[0]
    assert method == "POST"
    assert url == "http://host/api/generate"
    assert payload["model"] == "m2"
    assert payload["prompt"] == "hello"
    assert payload["system"] == "sys"
    assert payload["stream"] is False


def test_streaming_parsing(monkeypatch):
    lines = [
        json.dumps({"message": {"content": "first"}}),
        json.dumps({"message": {"content": "second"}}),
    ]

    def fake_request(method, url, json=None, timeout=None, stream=None):
        return DummyResponse(json_data=None, lines=lines)

    client = OllamaClient(base_url="http://host", model="m3")
    monkeypatch.setattr(client._session, "request", fake_request)

    iterator = client.chat([{"role": "user", "content": "hi"}], stream=True)
    results = list(iterator)
    assert results[0]["message"]["content"] == "first"
    assert results[1]["message"]["content"] == "second"


def test_retry_on_connection_error(monkeypatch):
    attempts = {"count": 0}

    def fake_request(method, url, json=None, timeout=None, stream=None):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise requests.ConnectionError("boom")
        return DummyResponse(json_data={"message": {"content": "ok"}})

    client = OllamaClient(base_url="http://host", model="m4", max_retries=2, backoff_s=0)
    monkeypatch.setattr(client._session, "request", fake_request)
    monkeypatch.setattr("time.sleep", lambda _: None)

    response = client.chat([{"role": "user", "content": "hi"}], stream=False)
    assert response["message"]["content"] == "ok"
    assert attempts["count"] == 3


def test_retry_on_http_503(monkeypatch):
    attempts = {"count": 0}

    def fake_request(method, url, json=None, timeout=None, stream=None):
        attempts["count"] += 1
        if attempts["count"] == 1:
            return DummyResponse(status_code=503, text="down")
        return DummyResponse(json_data={"message": {"content": "ok"}})

    client = OllamaClient(base_url="http://host", model="m5", max_retries=1, backoff_s=0)
    monkeypatch.setattr(client._session, "request", fake_request)
    monkeypatch.setattr("time.sleep", lambda _: None)

    response = client.chat([{"role": "user", "content": "hi"}], stream=False)
    assert response["message"]["content"] == "ok"
    assert attempts["count"] == 2


def test_non_retryable_http_error(monkeypatch):
    def fake_request(method, url, json=None, timeout=None, stream=None):
        return DummyResponse(status_code=400, text="bad request")

    client = OllamaClient(base_url="http://host", model="m6", max_retries=0)
    monkeypatch.setattr(client._session, "request", fake_request)

    with pytest.raises(OllamaHTTPError):
        client.chat([{"role": "user", "content": "hi"}], stream=False)


def test_invalid_json_response(monkeypatch):
    def fake_request(method, url, json=None, timeout=None, stream=None):
        return DummyResponse(json_data=ValueError("nope"))

    client = OllamaClient(base_url="http://host", model="m7", max_retries=0)
    monkeypatch.setattr(client._session, "request", fake_request)

    with pytest.raises(OllamaResponseError):
        client.chat([{"role": "user", "content": "hi"}], stream=False)
