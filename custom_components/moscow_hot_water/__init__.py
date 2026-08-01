"""Moscow Hot Water integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MoscowHotWaterApi
from .const import DOMAIN
from .coordinator import MoscowHotWaterCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON]

type MoscowHotWaterConfigEntry = ConfigEntry[MoscowHotWaterCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MoscowHotWaterConfigEntry) -> bool:
    """Set up from a config entry."""
    api = MoscowHotWaterApi(async_get_clientsession(hass))
    coordinator = MoscowHotWaterCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        entry.runtime_data = None

    return unload_ok

async def _async_reload_entry(hass: HomeAssistant, entry: MoscowHotWaterConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
