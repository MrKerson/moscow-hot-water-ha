"""Binary sensors for Moscow Hot Water."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.util import dt as dt_util

from .entity import MoscowHotWaterEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([HotWaterShutdownBinarySensor(entry.runtime_data)])


class HotWaterShutdownBinarySensor(MoscowHotWaterEntity, BinarySensorEntity):
    """Whether hot water is currently shut down."""

    _attr_translation_key = "shutdown"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:water-off"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "shutdown")

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if not data.start or not data.end:
            return False
        now = dt_util.now()
        start = data.start if data.start.tzinfo else data.start.replace(tzinfo=now.tzinfo)
        end = data.end if data.end.tzinfo else data.end.replace(tzinfo=now.tzinfo)
        return start <= now <= end
