"""Diagnostics for Moscow Hot Water."""
from dataclasses import asdict

async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "entry": {"title": entry.title, "data": dict(entry.data), "options": dict(entry.options)},
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "data": asdict(coordinator.data),
        },
    }
