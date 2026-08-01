"""Data models for Moscow Hot Water."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class AddressSuggestion:
    """An address returned by mos.ru."""

    key: str
    address: str
    unom: str | None
    start: datetime | None
    end: datetime | None
    porches: str | None


@dataclass(slots=True, frozen=True)
class HotWaterSchedule:
    """Hot-water shutdown schedule."""

    address: str
    start: datetime | None
    end: datetime | None
    source: str
    unom: str | None = None
    raw_status: str | None = None

    @property
    def is_scheduled(self) -> bool:
        return self.start is not None and self.end is not None
