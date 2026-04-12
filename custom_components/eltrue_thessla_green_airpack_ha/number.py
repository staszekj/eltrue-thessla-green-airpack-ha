"""Number platform for AirPack (intensywnosc wentylacji)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_INTENSYWNOSC
from .coordinator import AirPackCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirPackCoordinator = entry.runtime_data
    async_add_entities([AirPackIntensywnosc(coordinator, entry)])


class AirPackIntensywnosc(CoordinatorEntity[AirPackCoordinator], NumberEntity):
    _attr_unique_id = "rekuperator_intensywnosc"
    _attr_name = "Rekuperator intensywność"
    _attr_native_min_value = 10
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator: AirPackCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("intensywnosc")

    async def async_set_native_value(self, value: float) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, REG_INTENSYWNOSC, int(value)
        )
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
