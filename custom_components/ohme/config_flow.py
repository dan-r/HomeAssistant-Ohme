import voluptuous as vol
from homeassistant.config_entries import (ConfigFlow, OptionsFlow)
from .const import DOMAIN, CONFIG_VERSION
from .api_client import OhmeApiClient


USER_SCHEMA = vol.Schema({
    vol.Required("email"): str,
    vol.Required("password"): str
})


class OhmeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""
    VERSION = CONFIG_VERSION

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

    def async_get_options_flow(entry):
        return OhmeOptionsFlow(entry)


class OhmeOptionsFlow(OptionsFlow):
    """Options flow."""

    def __init__(self, entry) -> None:
        self._config_entry = entry

    async def async_step_init(self, info):
        errors = {}
        if info is not None:
            instance = OhmeApiClient(info['email'], info['password'])
            if await instance.async_refresh_session() is None:
                errors["base"] = "auth_error"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry, data=info
                )
                return self.async_create_entry(
                    title="",
                    data={}
                )

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(
                    {
                        vol.Required(
                            "email", default=self._config_entry.data['email']
                        ): str,
                        vol.Required(
                            "password"
                        ): str
                    }), errors=errors
        )
