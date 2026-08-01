"""Base entities for Moscow Hot Water."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE_URL
from .coordinator import MoscowHotWaterCoordinator


class MoscowHotWaterEntity(CoordinatorEntity[MoscowHotWaterCoordinator]):
    """Base coordinator entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MoscowHotWaterCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="Правительство Москвы",
            model="График отключения горячей воды",
            configuration_url=SOURCE_URL,
        )

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "address": data.address,
            "source": data.source,
            "raw_status": data.raw_status,
            "last_update_success": self.coordinator.last_update_success,
        }
