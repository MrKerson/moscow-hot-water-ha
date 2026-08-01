"""Sensors for Moscow Hot Water."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import UnitOfTime
from homeassistant.util import dt as dt_util

from .entity import MoscowHotWaterEntity


@dataclass(frozen=True, kw_only=True)
class MoscowSensorDescription(SensorEntityDescription):
    value_fn: Callable = lambda data: None


DESCRIPTIONS = (
    MoscowSensorDescription(key="start", translation_key="start", device_class=SensorDeviceClass.TIMESTAMP),
    MoscowSensorDescription(key="end", translation_key="end", device_class=SensorDeviceClass.TIMESTAMP),
    MoscowSensorDescription(key="days_until", translation_key="days_until", native_unit_of_measurement=UnitOfTime.DAYS),
    MoscowSensorDescription(key="days_remaining", translation_key="days_remaining", native_unit_of_measurement=UnitOfTime.DAYS),
    MoscowSensorDescription(key="status", translation_key="status", icon="mdi:water-alert"),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([MoscowHotWaterSensor(entry.runtime_data, description) for description in DESCRIPTIONS])


class MoscowHotWaterSensor(MoscowHotWaterEntity, SensorEntity):
    entity_description: MoscowSensorDescription

    def __init__(self, coordinator, description: MoscowSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        data = self.coordinator.data
        key = self.entity_description.key
        if key == "start":
            return data.start
        if key == "end":
            return data.end
        now = dt_util.now()
        start = data.start
        end = data.end
        if key == "days_until":
            return max(0, (start.date() - now.date()).days) if start and now < start else 0
        if key == "days_remaining":
            return max(0, (end.date() - now.date()).days + 1) if end and start and start <= now <= end else 0
        if key == "status":
            if not start or not end:
                return "not_scheduled"
            if now < start:
                return "scheduled"
            if start <= now <= end:
                return "disabled"
            return "completed"
        return None
