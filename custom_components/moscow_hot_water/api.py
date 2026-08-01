"""Client for the Moscow hot-water shutdown service."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession

from .const import API_URL, SOURCE_URL
from .models import AddressSuggestion, HotWaterSchedule

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


class MoscowHotWaterError(Exception):
    """Base API error."""


class AddressNotFoundError(MoscowHotWaterError):
    """Address was not found."""


class InvalidResponseError(MoscowHotWaterError):
    """Remote service returned an unsupported response."""


class MoscowHotWaterApi:
    """Fetch shutdown information from the official mos.ru address service."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_suggest(self, query: str) -> list[AddressSuggestion]:
        """Return address suggestions for a free-form query."""
        query = " ".join(str(query).strip().split())
        if len(query) < 3:
            raise AddressNotFoundError(query)

        try:
            async with self._session.get(
                API_URL,
                params={"q": query},
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": SOURCE_URL,
                    "User-Agent": "HomeAssistant-MoscowHotWater/0.1.0",
                },
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise InvalidResponseError(str(err)) from err

        raw = payload.get("suggests") if isinstance(payload, dict) else None
        if not isinstance(raw, list):
            raise InvalidResponseError("Response does not contain a suggests list")

        result: list[AddressSuggestion] = []
        used_keys: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            address = str(item.get("Address") or item.get("body") or "").strip()
            if not address:
                continue
            unom = str(item.get("UNOM") or "").strip() or None
            base_key = unom or str(item.get("id") or index)
            key = base_key
            suffix = 2
            while key in used_keys:
                key = f"{base_key}:{suffix}"
                suffix += 1
            used_keys.add(key)
            result.append(
                AddressSuggestion(
                    key=key,
                    address=address,
                    unom=unom,
                    start=self._parse_moscow_datetime(item.get("OutageBegin")),
                    end=self._parse_moscow_datetime(item.get("OutageEnd")),
                    porches=str(item.get("Porches") or "").strip() or None,
                )
            )

        if not result:
            raise AddressNotFoundError(query)
        return result

    async def async_get_schedule(
        self, query: str, *, unom: str | None = None, expected_address: str | None = None
    ) -> HotWaterSchedule:
        """Return the schedule for the selected address."""
        suggestions = await self.async_suggest(expected_address or query)
        selected = self._select(suggestions, unom=unom, expected_address=expected_address)
        if selected is None:
            # Retry using the original user query because address text may have changed.
            if expected_address and expected_address != query:
                suggestions = await self.async_suggest(query)
                selected = self._select(suggestions, unom=unom, expected_address=expected_address)
        if selected is None:
            raise AddressNotFoundError(expected_address or query)

        return HotWaterSchedule(
            address=selected.address,
            start=selected.start,
            end=selected.end,
            source=SOURCE_URL,
            unom=selected.unom,
            raw_status=selected.porches,
        )

    @staticmethod
    def _select(
        suggestions: list[AddressSuggestion],
        *,
        unom: str | None,
        expected_address: str | None,
    ) -> AddressSuggestion | None:
        if unom:
            for suggestion in suggestions:
                if suggestion.unom == unom:
                    return suggestion
        if expected_address:
            expected = " ".join(expected_address.lower().replace("ё", "е").split())
            for suggestion in suggestions:
                candidate = " ".join(suggestion.address.lower().replace("ё", "е").split())
                if candidate == expected:
                    return suggestion
        return suggestions[0] if len(suggestions) == 1 else None

    @staticmethod
    def _parse_moscow_datetime(value: Any) -> datetime | None:
        """Parse API timestamps as Moscow local time.

        The service appends ``Z`` although displayed clock values are already Moscow time.
        The suffix must therefore be ignored instead of converting from UTC.
        """
        if value in (None, ""):
            return None
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1]
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed.replace(tzinfo=MOSCOW_TZ)
