"""Update button for Moscow Hot Water."""
from homeassistant.components.button import ButtonEntity

from .entity import MoscowHotWaterEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([MoscowHotWaterRefreshButton(entry.runtime_data)])


class MoscowHotWaterRefreshButton(MoscowHotWaterEntity, ButtonEntity):
    _attr_translation_key = "refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
