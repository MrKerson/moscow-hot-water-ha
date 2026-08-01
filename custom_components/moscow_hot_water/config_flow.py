"""Config flow for Moscow Hot Water."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AddressNotFoundError, InvalidResponseError, MoscowHotWaterApi
from .const import CONF_ADDRESS, CONF_ADDRESS_QUERY, CONF_UNOM, DOMAIN
from .models import AddressSuggestion

_LOGGER = logging.getLogger(__name__)


ADDRESS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS_QUERY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        )
    }
)


class MoscowHotWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self) -> None:
        self._query = ""
        self._suggestions: dict[str, AddressSuggestion] = {}
        self._reconfigure_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Accept a free-form address in one line."""
        return await self._async_address_step("user", user_input)

    async def _async_address_step(
        self, step_id: str, user_input: dict[str, Any] | None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._query = " ".join(user_input[CONF_ADDRESS_QUERY].strip().split())
            try:
                suggestions = await MoscowHotWaterApi(
                    async_get_clientsession(self.hass)
                ).async_suggest(self._query)
            except AddressNotFoundError:
                errors["base"] = "address_not_found"
            except InvalidResponseError:
                errors["base"] = "cannot_connect"
            except Exception:  # Keep frontend errors human-readable.
                _LOGGER.exception("Unexpected error while looking up address %r", self._query)
                errors["base"] = "unknown"
            else:
                self._suggestions = {item.key: item for item in suggestions}
                try:
                    return await self.async_step_select_address()
                except Exception:
                    _LOGGER.exception("Unexpected error while building address suggestions")
                    errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ADDRESS_QUERY,
                    default=(user_input or {}).get(CONF_ADDRESS_QUERY, self._query),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                )
            }
        )
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user select one suggestion returned by mos.ru."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = self._suggestions.get(user_input[CONF_ADDRESS])
            if selected is None:
                errors["base"] = "address_not_found"
            else:
                unique_id = selected.unom or selected.address.lower()
                await self.async_set_unique_id(unique_id)
                if self._reconfigure_entry is None:
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=selected.address,
                        data={
                            CONF_ADDRESS_QUERY: self._query,
                            CONF_ADDRESS: selected.address,
                            CONF_UNOM: selected.unom or "",
                        },
                    )

                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    unique_id=unique_id,
                    title=selected.address,
                    data_updates={
                        CONF_ADDRESS_QUERY: self._query,
                        CONF_ADDRESS: selected.address,
                        CONF_UNOM: selected.unom or "",
                    },
                )

        # ``vol.In`` is supported by older Home Assistant releases too.  Using
        # SelectOptionDict here made the flow crash after a successful lookup on
        # releases where that newer selector API is not available.
        options = {item.key: item.address for item in self._suggestions.values()}
        schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(options)
            }
        )
        return self.async_show_form(
            step_id="select_address",
            data_schema=schema,
            errors=errors,
            description_placeholders={"query": self._query},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the configured address."""
        self._reconfigure_entry = self._get_reconfigure_entry()
        if user_input is None:
            current_query = self._reconfigure_entry.data.get(
                CONF_ADDRESS_QUERY, self._reconfigure_entry.data.get(CONF_ADDRESS, "")
            )
            user_input = None
            self._query = current_query
        return await self._async_address_step("reconfigure", user_input)
