"""Sensor platform for AirPack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfVolumeFlowRate, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, TRYB_OPTIONS, SEZON_OPTIONS, FUNKCJE_OPTIONS
from .coordinator import AirPackCoordinator


@dataclass(frozen=True, kw_only=True)
class AirPackSensorDescription(SensorEntityDescription):
    data_key: str
    value_fn: Any = None  # optional transform


def _tryb_text(v):
    return TRYB_OPTIONS[v] if isinstance(v, int) and 0 <= v < len(TRYB_OPTIONS) else None


def _sezon_text(v):
    return SEZON_OPTIONS[v] if isinstance(v, int) and 0 <= v < len(SEZON_OPTIONS) else None


def _funkcje_text(v):
    return FUNKCJE_OPTIONS[v] if isinstance(v, int) and 0 <= v < len(FUNKCJE_OPTIONS) else None


def _bypass_status_text(v):
    mapping = {0: "Nieaktywny", 1: "Dogrzewanie", 2: "Chłodzenie"}
    return mapping.get(v)


def _bypass_tryb_text(v):
    mapping = {
        1: "Tryb 1 – tylko przepustnica",
        2: "Tryb 2 – przepustnica + różnicowanie",
        3: "Tryb 3 – przepustnica + wyłączenie wywiewu",
    }
    return mapping.get(v, f"Tryb {v}")


def _fpx_status_text(data):
    flaga = data.get("fpx_flaga", 0) or 0
    tryb = data.get("fpx_tryb", 0) or 0
    if flaga == 0:
        return "Wyłączony"
    if tryb == 1:
        return "FPX1 ochrona przed zamrożeniem"
    if tryb == 2:
        return "FPX2 dogrzewanie nawiewu"
    return f"FPX aktywny (tryb {tryb})"


def _sprawnosc(data):
    tz1 = data.get("tz1")
    tn1 = data.get("tn1")
    tp = data.get("tp")
    if None in (tz1, tn1, tp):
        return None
    denom = tp - tz1
    if denom == 0:
        return None
    return round((tn1 - tz1) / denom * 100, 1)


def _roznica(data):
    tn1 = data.get("tn1")
    tp = data.get("tp")
    if None in (tn1, tp):
        return None
    return round(tn1 - tp, 1)


def _firmware(data):
    maj = data.get("fw_major")
    minn = data.get("fw_minor")
    if maj is None or minn is None:
        return None
    return f"{maj}.{minn:02d}"


def _serial(data):
    sn = data.get("sn")
    if not sn or len(sn) < 4:
        return None
    return "{:02X}{:02X} {:02X}{:02X}".format(*sn)


def _model(data):
    q = data.get("nominal_nawiew")
    if q:
        return f"AirPack {q}"
    return "AirPack"


# Sensors with a single data_key and optional value_fn
SIMPLE_SENSORS: list[AirPackSensorDescription] = [
    AirPackSensorDescription(
        key="rekuperator_tz1",
        name="Rekuperator TZ1",
        data_key="tz1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_tn1",
        name="Rekuperator TN1",
        data_key="tn1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_tp",
        name="Rekuperator TP",
        data_key="tp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_tz2",
        name="Rekuperator TZ2",
        data_key="tz2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_to",
        name="Rekuperator TO",
        data_key="to",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_nawiew_procent",
        name="Rekuperator nawiew procent",
        data_key="nawiew_pct",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_wywiew_procent",
        name="Rekuperator wywiew procent",
        data_key="wywiew_pct",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_nawiew_m3h",
        name="Rekuperator nawiew m3h",
        data_key="nawiew_m3h",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_wywiew_m3h",
        name="Rekuperator wywiew m3h",
        data_key="wywiew_m3h",
        native_unit_of_measurement="m³/h",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_bypass_min_temp",
        name="Rekuperator bypass min temp",
        data_key="bypass_min_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_bypass_temp_grzanie",
        name="Rekuperator bypass temp grzanie",
        data_key="bypass_temp_grzanie",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_bypass_temp_chlodzenie",
        name="Rekuperator bypass temp chlodzenie",
        data_key="bypass_temp_chlodzenie",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AirPackSensorDescription(
        key="rekuperator_nominal_nawiew",
        name="Rekuperator nominal nawiew",
        data_key="nominal_nawiew",
        native_unit_of_measurement="m³/h",
    ),
    AirPackSensorDescription(
        key="rekuperator_nominal_wywiew",
        name="Rekuperator nominal wywiew",
        data_key="nominal_wywiew",
        native_unit_of_measurement="m³/h",
    ),
    # Text sensors using value_fn
    AirPackSensorDescription(
        key="rekuperator_tryb",
        name="Rekuperator tryb",
        data_key="tryb",
        value_fn=_tryb_text,
    ),
    AirPackSensorDescription(
        key="rekuperator_sezon",
        name="Rekuperator sezon",
        data_key="sezon",
        value_fn=_sezon_text,
    ),
    AirPackSensorDescription(
        key="rekuperator_funkcje_specjalne",
        name="Rekuperator funkcje specjalne",
        data_key="funkcje_specjalne",
        value_fn=_funkcje_text,
    ),
    AirPackSensorDescription(
        key="rekuperator_bypass_status",
        name="Rekuperator bypass status",
        data_key="bypass_status",
        value_fn=_bypass_status_text,
    ),
    AirPackSensorDescription(
        key="rekuperator_bypass_tryb_opis",
        name="Rekuperator bypass tryb opis",
        data_key="bypass_tryb",
        value_fn=_bypass_tryb_text,
    ),
]

# Sensors that need the full data dict (multi-key)
COMPUTED_SENSORS = [
    ("rekuperator_sprawnosc", "Rekuperator sprawnosc", PERCENTAGE, _sprawnosc),
    ("rekuperator_roznica_temperatur", "Rekuperator roznica temperatur", UnitOfTemperature.CELSIUS, _roznica),
    ("rekuperator_firmware", "Rekuperator firmware", None, _firmware),
    ("rekuperator_numer_seryjny", "Rekuperator numer seryjny", None, _serial),
    ("rekuperator_model", "Rekuperator model", None, _model),
    ("rekuperator_fpx_status", "Rekuperator FPX status", None, _fpx_status_text),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirPackCoordinator = entry.runtime_data
    entities = []
    for desc in SIMPLE_SENSORS:
        entities.append(AirPackSimpleSensor(coordinator, entry, desc))
    for key, name, unit, fn in COMPUTED_SENSORS:
        entities.append(AirPackComputedSensor(coordinator, entry, key, name, unit, fn))
    async_add_entities(entities)


class AirPackSimpleSensor(CoordinatorEntity[AirPackCoordinator], SensorEntity):
    entity_description: AirPackSensorDescription

    def __init__(self, coordinator, entry, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = description.key
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self.entity_description.data_key)
        fn = self.entity_description.value_fn
        if fn is not None:
            return fn(raw)
        return raw


class AirPackComputedSensor(CoordinatorEntity[AirPackCoordinator], SensorEntity):
    def __init__(self, coordinator, entry, key, name, unit, fn):
        super().__init__(coordinator)
        self._key = key
        self._fn = fn
        self._attr_unique_id = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self._fn(self.coordinator.data)


def _device_info(entry):
    from homeassistant.helpers.device_registry import DeviceInfo
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="AirPack",
        manufacturer="Thessla Green",
        model="AirPack",
    )
