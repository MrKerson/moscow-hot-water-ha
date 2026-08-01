"""Coordinator for Moscow Hot Water."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MoscowHotWaterApi, MoscowHotWaterError
from .const import CONF_ADDRESS, CONF_ADDRESS_QUERY, CONF_UNOM, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import HotWaterSchedule

_LOGGER = logging.getLogger(__name__)


class MoscowHotWaterCoordinator(DataUpdateCoordinator[HotWaterSchedule]):
    """Coordinate schedule updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: MoscowHotWaterApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.entry = entry
        self.api = api

    async def _async_update_data(self) -> HotWaterSchedule:
        data = {**self.entry.data, **self.entry.options}
        try:
            return await self.api.async_get_schedule(
                data[CONF_ADDRESS_QUERY],
                unom=data.get(CONF_UNOM) or None,
                expected_address=data.get(CONF_ADDRESS) or None,
            )
        except MoscowHotWaterError as err:
            raise UpdateFailed(str(err)) from err
