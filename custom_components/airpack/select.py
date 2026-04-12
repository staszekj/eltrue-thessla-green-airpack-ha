"""Select platform for AirPack (tryb, sezon, funkcje specjalne)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FUNKCJE_OPTIONS,
    REG_FUNKCJE_SPECJALNE,
    REG_SEZON,
    REG_TRYB,
    SEZON_OPTIONS,
    TRYB_OPTIONS,
)
from .coordinator import AirPackCoordinator
from .sensor import _device_info


@dataclass(frozen=True, kw_only=True)
class AirPackSelectDescription(SelectEntityDescription):
    data_key: str = ""
    register: int = 0
    options_list: list[str] = None


SELECTS: list[AirPackSelectDescription] = [
    AirPackSelectDescription(
        key="rekuperator_tryb",
        name="Rekuperator tryb",
        data_key="tryb",
        register=REG_TRYB,
        options_list=TRYB_OPTIONS,
        options=TRYB_OPTIONS,
    ),
    AirPackSelectDescription(
        key="rekuperator_sezon",
        name="Rekuperator sezon",
        data_key="sezon",
        register=REG_SEZON,
        options_list=SEZON_OPTIONS,
        options=SEZON_OPTIONS,
    ),
    AirPackSelectDescription(
        key="rekuperator_funkcje_specjalne",
        name="Rekuperator funkcje specjalne",
        data_key="funkcje_specjalne",
        register=REG_FUNKCJE_SPECJALNE,
        options_list=FUNKCJE_OPTIONS,
        options=FUNKCJE_OPTIONS,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirPackCoordinator = entry.runtime_data
    async_add_entities([AirPackSelect(coordinator, entry, desc) for desc in SELECTS])


class AirPackSelect(CoordinatorEntity[AirPackCoordinator], SelectEntity):
    def __init__(
        self,
        coordinator: AirPackCoordinator,
        entry: ConfigEntry,
        description: AirPackSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = description.key
        self._attr_name = description.name
        self._attr_options = description.options_list
        self._attr_device_info = _device_info(entry)
        self._description = description

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.data.get(self._description.data_key)
        if val is None:
            return None
        opts = self._description.options_list
        if 0 <= val < len(opts):
            return opts[val]
        return None

    async def async_select_option(self, option: str) -> None:
        value = self._description.options_list.index(option)
        await self.hass.async_add_executor_job(
            self.coordinator.write_register, self._description.register, value
        )
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
