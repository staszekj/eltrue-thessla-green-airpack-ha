"""
Tests for the AirPack integration.

Uses importlib.util to load modules directly — no full HA environment required.
"""
import importlib.util
import sys
import types
import os
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load(relative_path):
    """Load a module from a file path without triggering package __init__."""
    full_path = os.path.join(ROOT, relative_path)
    spec = importlib.util.spec_from_file_location("_test_module", full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── const.py tests (no HA dependencies) ─────────────────────────────────────

const = _load("custom_components/airpack/const.py")


def test_domain():
    assert const.DOMAIN == "airpack"


def test_platforms_complete():
    assert set(const.PLATFORMS) == {"sensor", "binary_sensor", "switch", "select", "number"}


def test_tryb_options():
    opts = const.TRYB_OPTIONS
    assert len(opts) == 3
    assert opts[0] == "Automatyczny"
    assert opts[1] == "Manualny"
    assert opts[2] == "Chwilowy"


def test_sezon_options():
    opts = const.SEZON_OPTIONS
    assert len(opts) == 2
    assert opts[0] == "Lato"
    assert opts[1] == "Zima"


def test_funkcje_options():
    opts = const.FUNKCJE_OPTIONS
    assert len(opts) == 12
    assert opts[0] == "Brak"
    assert opts[10] == "Otwarte okna"
    assert opts[11] == "Pusty dom"


def test_defaults():
    assert const.DEFAULT_PORT == 4196
    assert const.DEFAULT_DEVICE_ID == 10
    assert const.DEFAULT_SCAN_INTERVAL == 30


def test_key_register_addresses():
    assert const.REG_ONOFF == 4387
    assert const.REG_TRYB == 4208
    assert const.REG_SEZON == 4209
    assert const.REG_INTENSYWNOSC == 4210
    assert const.REG_FUNKCJE_SPECJALNE == 4224
    assert const.COIL_BYPASS_SILOWNIK == 9


# ── sensor.py pure function tests ────────────────────────────────────────────

def _load_sensor():
    """Load sensor.py with minimal HA stubs."""
    import dataclasses
    from typing import Any as _Any

    class _Subscriptable:
        """Stub base class that supports Generic[T] subscript syntax and keyword init."""
        def __class_getitem__(cls, item):
            return cls
        def __init__(self, *args, **kwargs):
            pass
        def __init_subclass__(cls, **kwargs):
            pass

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class _SensorEntityDescription:
        """Minimal stub for SensorEntityDescription (must be a real dataclass for inheritance)."""
        key: str = ""
        name: _Any = None
        device_class: _Any = None
        native_unit_of_measurement: _Any = None
        state_class: _Any = None
        icon: _Any = None
        entity_registry_enabled_default: bool = True
        entity_registry_visible_default: bool = True
        has_entity_name: bool = False
        translation_key: _Any = None
        translation_placeholders: _Any = None
        unit_of_measurement: _Any = None

        def __class_getitem__(cls, item):
            return cls

    stubs = {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.components": types.ModuleType("homeassistant.components"),
        "homeassistant.components.sensor": types.SimpleNamespace(
            SensorDeviceClass=types.SimpleNamespace(TEMPERATURE="temperature", ENERGY="energy", POWER="power"),
            SensorEntity=type("SensorEntity", (), {"__class_getitem__": classmethod(lambda c, i: c), "__init__": lambda s, *a, **k: None}),
            SensorEntityDescription=_SensorEntityDescription,
            SensorStateClass=types.SimpleNamespace(MEASUREMENT="measurement", TOTAL_INCREASING="total_increasing"),
        ),
        "homeassistant.config_entries": types.SimpleNamespace(ConfigEntry=_Subscriptable),
        "homeassistant.const": types.SimpleNamespace(
            UnitOfTemperature=types.SimpleNamespace(CELSIUS="°C"),
            UnitOfVolumeFlowRate=types.SimpleNamespace(CUBIC_METERS_PER_HOUR="m³/h"),
            PERCENTAGE="%",
            CONF_HOST="host",
            CONF_PORT="port",
        ),
        "homeassistant.core": types.SimpleNamespace(HomeAssistant=object),
        "homeassistant.exceptions": types.SimpleNamespace(ConfigEntryNotReady=Exception),
        "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
        "homeassistant.helpers.entity_platform": types.SimpleNamespace(AddEntitiesCallback=None),
        "homeassistant.helpers.update_coordinator": types.SimpleNamespace(
            CoordinatorEntity=type("CoordinatorEntity", (), {"__class_getitem__": classmethod(lambda c, i: c), "__init__": lambda s, *a, **k: None, "__init_subclass__": classmethod(lambda c, **k: None)}),
            DataUpdateCoordinator=_Subscriptable,
            UpdateFailed=Exception,
        ),
        "homeassistant.helpers.device_registry": types.SimpleNamespace(DeviceInfo=dict),
        "pymodbus": types.ModuleType("pymodbus"),
        "pymodbus.client": types.SimpleNamespace(ModbusTcpClient=object),
        "pymodbus.exceptions": types.SimpleNamespace(ModbusException=Exception),
    }
    for name, stub in stubs.items():
        sys.modules[name] = stub

    const_spec = importlib.util.spec_from_file_location(
        "_airpack_const", os.path.join(ROOT, "custom_components/airpack/const.py")
    )
    const_mod = importlib.util.module_from_spec(const_spec)
    sys.modules["custom_components"] = types.ModuleType("custom_components")
    sys.modules["custom_components.airpack"] = types.ModuleType("custom_components.airpack")
    sys.modules["custom_components.airpack.const"] = const_mod
    sys.modules["custom_components.airpack.coordinator"] = types.SimpleNamespace(
        AirPackCoordinator=_Subscriptable
    )
    # Also stub pymodbus so coordinator.py doesn't fail if ever imported
    sys.modules["pymodbus"] = types.ModuleType("pymodbus")
    sys.modules["pymodbus.client"] = types.SimpleNamespace(ModbusTcpClient=object)
    sys.modules["pymodbus.exceptions"] = types.SimpleNamespace(ModbusException=Exception)
    const_spec.loader.exec_module(const_mod)

    sensor_spec = importlib.util.spec_from_file_location(
        "custom_components.airpack.sensor",
        os.path.join(ROOT, "custom_components/airpack/sensor.py"),
        submodule_search_locations=[],
    )
    sensor_mod = importlib.util.module_from_spec(sensor_spec)
    sys.modules["custom_components.airpack.sensor"] = sensor_mod
    sensor_spec.loader.exec_module(sensor_mod)
    return sensor_mod


sensor = _load_sensor()


def test_sprawnosc_typical():
    result = sensor._sprawnosc({"tz1": 0.0, "tn1": 17.4, "tp": 20.0})
    assert result == pytest.approx(87.0, abs=1.0)


def test_sprawnosc_none_input():
    assert sensor._sprawnosc({"tz1": None, "tn1": 17.4, "tp": 20.0}) is None


def test_sprawnosc_no_gradient():
    assert sensor._sprawnosc({"tz1": 20.0, "tn1": 17.4, "tp": 20.0}) is None


def test_roznica():
    assert sensor._roznica({"tn1": 19.4, "tp": 20.8}) == pytest.approx(-1.4, abs=0.05)


def test_roznica_missing():
    assert sensor._roznica({"tn1": None, "tp": 20.8}) is None


def test_firmware():
    assert sensor._firmware({"fw_major": 4, "fw_minor": 85}) == "4.85"
    assert sensor._firmware({"fw_major": None, "fw_minor": 85}) is None


def test_serial():
    assert sensor._serial({"sn": [0xFE, 0xBD, 0x41, 0x1C]}) == "FEBD 411C"
    assert sensor._serial({"sn": None}) is None


def test_model():
    assert sensor._model({"nominal_nawiew": 450}) == "AirPack 450"
    assert sensor._model({"nominal_nawiew": 0}) == "AirPack"


def test_fpx_status():
    assert sensor._fpx_status_text({"fpx_flaga": 0, "fpx_tryb": 0}) == "Wyłączony"
    assert sensor._fpx_status_text({"fpx_flaga": 1, "fpx_tryb": 1}) == "FPX1 ochrona przed zamrożeniem"
    assert sensor._fpx_status_text({"fpx_flaga": 1, "fpx_tryb": 2}) == "FPX2 dogrzewanie nawiewu"


def test_bypass_status():
    assert sensor._bypass_status_text(0) == "Nieaktywny"
    assert sensor._bypass_status_text(1) == "Dogrzewanie"
    assert sensor._bypass_status_text(2) == "Chłodzenie"


def test_bypass_tryb():
    assert "przepustnica" in sensor._bypass_tryb_text(1)
    assert "różnicowanie" in sensor._bypass_tryb_text(2)
    assert "wywiew" in sensor._bypass_tryb_text(3)
