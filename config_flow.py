"""Config flow for PUK Rumia trash pickup integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, HANDLERS

try:
    from .const import CONF_UNIT_ID, DOMAIN
except ImportError:  # pragma: no cover - local test fallback
    from const import CONF_UNIT_ID, DOMAIN


@HANDLERS.register(DOMAIN)
class PukRumiaConfigFlow(ConfigFlow):
    """Handle config flow for the integration."""

    VERSION = 1

    # pylint: disable=unused-argument
    def is_matching(self, other_flow: ConfigFlow) -> bool:
        """Return whether this flow matches another in-progress flow."""
        return False

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unit_id = str(user_input[CONF_UNIT_ID]).strip()
            if not unit_id:
                errors[CONF_UNIT_ID] = "required"
            else:
                await self.async_set_unique_id(unit_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"PUK Rumia ({unit_id})",
                    data={CONF_UNIT_ID: unit_id},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_UNIT_ID): str}),
            errors=errors,
        )
