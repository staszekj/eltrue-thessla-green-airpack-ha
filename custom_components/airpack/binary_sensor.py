"""Binary sensor platform for AirPack."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AirPackCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirPackCoordinator = entry.runtime_data
    async_add_entities([
        AirPackBinarySensor(
            coordinator, entry,
            key="rekuperator_wlaczony",
            name="Rekuperator włączony",
            data_key="onoff",
            device_class=None,
            value_fn=lambda v: v == 1,
        ),
        AirPackBinarySensor(
            coordinator, entry,
            key="rekuperator_zima",
            name="Rekuperator zima",
            data_key="sezon",
            device_class=None,
            value_fn=lambda v: v == 1,
        ),
        AirPackBinarySensor(
            coordinator, entry,
            key="rekuperator_bypass_silownik",
            name="Rekuperator bypass silownik",
            data_key="bypass_silownik",
            device_class=BinarySensorDeviceClass.OPENING,
            value_fn=lambda v: bool(v),
        ),
    ])


class AirPackBinarySensor(CoordinatorEntity[AirPackCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, entry, key, name, data_key, device_class, value_fn):
        super().__init__(coordinator)
        self._data_key = data_key
        self._value_fn = value_fn
        self._attr_unique_id = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get(self._data_key)
        if val is None:
            return None
        return self._value_fn(val)
