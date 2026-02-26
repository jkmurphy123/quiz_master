class OllamaError(Exception):
    """Base class for Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Network-level errors such as timeouts or connection failures."""


class OllamaHTTPError(OllamaError):
    """Non-2xx HTTP errors."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class OllamaResponseError(OllamaError):
    """Errors parsing or validating response payloads."""
