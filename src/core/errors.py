from __future__ import annotations

from typing import Any


class SeedanceError(Exception):
    """Base exception for Seedance Studio."""


class SeedanceConfigError(SeedanceError):
    """Raised when required local configuration is missing or invalid."""


class SeedanceAPIError(SeedanceError):
    """Raised when the Seedance API returns an unsuccessful response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.response = response
