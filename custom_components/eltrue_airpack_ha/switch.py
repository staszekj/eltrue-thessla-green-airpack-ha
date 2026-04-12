"""Switch platform for AirPack (main ON/OFF)."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_ONOFF
from .coordinator import AirPackCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirPackCoordinator = entry.runtime_data
    async_add_entities([AirPackSwitch(coordinator, entry)])


class AirPackSwitch(CoordinatorEntity[AirPackCoordinator], SwitchEntity):
    _attr_unique_id = "rekuperator_onoff"
    _attr_name = "Rekuperator"
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: AirPackCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("onoff", 0) == 1

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, REG_ONOFF, 1
        )
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, REG_ONOFF, 0
        )
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
