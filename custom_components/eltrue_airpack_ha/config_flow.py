"""Config flow for AirPack."""

from __future__ import annotations

import voluptuous as vol
from pymodbus.client import ModbusTcpClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN, CONF_DEVICE_ID, DEFAULT_PORT, DEFAULT_DEVICE_ID

STEP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.3.29"): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): int,
    }
)


class AirPackConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle AirPack config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            device_id = user_input[CONF_DEVICE_ID]

            ok = await self.hass.async_add_executor_job(
                self._test_connection, host, port, device_id
            )
            if ok:
                await self.async_set_unique_id(f"airpack_{host}_{port}_{device_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"AirPack ({host})",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def _test_connection(host: str, port: int, device_id: int) -> bool:
        client = ModbusTcpClient(host, port=port)
        if not client.connect():
            return False
        r = client.read_holding_registers(4208, count=1, device_id=device_id)
        client.close()
        return not r.isError()
