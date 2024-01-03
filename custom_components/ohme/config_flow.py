import voluptuous as vol
from homeassistant.config_entries import (ConfigFlow, OptionsFlow)
from .const import DOMAIN
from .api_client import OhmeApiClient


USER_SCHEMA = vol.Schema({
    vol.Required("email"): str,
    vol.Required("password"): str
})

class OhmeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    async def async_step_user(self, info):
        errors = {}

        if info is not None:
            await self.async_set_unique_id("ohme")
            self._abort_if_unique_id_configured()
            instance = OhmeApiClient(info['email'], info['password'])
            if await instance.async_refresh_session() is None:
                errors["base"] = "auth_error"
            else:
                return self.async_create_entry(
                    title="Ohme Charger",
                    data=info
                )

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )
