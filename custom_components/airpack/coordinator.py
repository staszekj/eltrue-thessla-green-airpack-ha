"""DataUpdateCoordinator for AirPack."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    REG_TEMPS_ADDR,
    REG_FLOWS_ADDR,
    REG_FW_ADDR,
    REG_SN_ADDR,
    REG_FPX_FLAGA,
    REG_FPX_TRYB,
    REG_TRYB,
    REG_SEZON,
    REG_INTENSYWNOSC,
    REG_FUNKCJE_SPECJALNE,
    REG_BYPASS_WYLACZONY,
    REG_BYPASS_MIN_TEMP,
    REG_BYPASS_TEMP_GRZANIE,
    REG_BYPASS_TEMP_CHLODZENIE,
    REG_BYPASS_STATUS,
    REG_BYPASS_TRYB,
    REG_NOMINAL_NAWIEW,
    REG_NOMINAL_WYWIEW,
    REG_ONOFF,
    COIL_BYPASS_SILOWNIK,
)

_LOGGER = logging.getLogger(__name__)

_UNAVAILABLE_TEMP = 32768


def _signed(val: int) -> int:
    return val if val < 32768 else val - 65536


class AirPackCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all AirPack data in a single polling cycle."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, device_id: int) -> None:
        self._host = host
        self._port = port
        self._device_id = device_id
        self._client = ModbusTcpClient(host, port=port)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ── public write helpers ─────────────────────────────────────

    def write_register(self, address: int, value: int) -> None:
        """Write a single holding register (blocking, call via executor)."""
        if not self._client.connected:
            self._client.connect()
        result = self._client.write_register(address, value, device_id=self._device_id)
        if result.isError():
            raise ModbusException(f"Write to register {address} failed: {result}")

    def write_coil(self, address: int, value: bool) -> None:
        """Write a single coil (blocking)."""
        if not self._client.connected:
            self._client.connect()
        result = self._client.write_coil(address, value, device_id=self._device_id)
        if result.isError():
            raise ModbusException(f"Write to coil {address} failed: {result}")

    # ── internal poll ────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._fetch_all)
        except ModbusException as err:
            raise UpdateFailed(f"Modbus error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _fetch_all(self) -> dict[str, Any]:
        if not self._client.connected:
            if not self._client.connect():
                raise ModbusException("Cannot connect to AirPack gateway")

        data: dict[str, Any] = {}
        slave = self._device_id

        # ── Input registers ──────────────────────────────────────

        r = self._client.read_input_registers(REG_TEMPS_ADDR, count=7, device_id=slave)
        if not r.isError():
            keys = ["tz1", "tn1", "tp", "tz2", "tn2", "tz3", "to"]
            for key, raw in zip(keys, r.registers):
                data[key] = None if raw == _UNAVAILABLE_TEMP else round(_signed(raw) * 0.1, 1)

        r = self._client.read_input_registers(REG_FLOWS_ADDR, count=4, device_id=slave)
        if not r.isError():
            data["nawiew_pct"] = r.registers[0]
            data["wywiew_pct"] = r.registers[1]
            data["nawiew_m3h"] = r.registers[2]
            data["wywiew_m3h"] = r.registers[3]

        r = self._client.read_input_registers(REG_FW_ADDR, count=2, device_id=slave)
        if not r.isError():
            data["fw_major"] = r.registers[0]
            data["fw_minor"] = r.registers[1]

        r = self._client.read_input_registers(REG_SN_ADDR, count=4, device_id=slave)
        if not r.isError():
            data["sn"] = r.registers  # list of 4

        # ── Holding registers ────────────────────────────────────

        for addr, key in [
            (REG_FPX_FLAGA, "fpx_flaga"),
            (REG_FPX_TRYB, "fpx_tryb"),
        ]:
            r = self._client.read_holding_registers(addr, count=1, device_id=slave)
            if not r.isError():
                data[key] = r.registers[0]

        r = self._client.read_holding_registers(REG_TRYB, count=3, device_id=slave)
        if not r.isError():
            data["tryb"] = r.registers[0]
            data["sezon"] = r.registers[1]
            data["intensywnosc"] = r.registers[2]

        r = self._client.read_holding_registers(REG_FUNKCJE_SPECJALNE, count=1, device_id=slave)
        if not r.isError():
            data["funkcje_specjalne"] = r.registers[0]

        r = self._client.read_holding_registers(REG_BYPASS_WYLACZONY, count=4, device_id=slave)
        if not r.isError():
            data["bypass_wylaczony"] = r.registers[0]
            data["bypass_min_temp"] = round(r.registers[1] * 0.5, 1)
            data["bypass_temp_grzanie"] = round(r.registers[2] * 0.5, 1)
            data["bypass_temp_chlodzenie"] = round(r.registers[3] * 0.5, 1)

        r = self._client.read_holding_registers(REG_BYPASS_STATUS, count=2, device_id=slave)
        if not r.isError():
            data["bypass_status"] = r.registers[0]
            data["bypass_tryb"] = r.registers[1]

        r = self._client.read_holding_registers(REG_NOMINAL_NAWIEW, count=2, device_id=slave)
        if not r.isError():
            data["nominal_nawiew"] = r.registers[0]
            data["nominal_wywiew"] = r.registers[1]

        r = self._client.read_holding_registers(REG_ONOFF, count=1, device_id=slave)
        if not r.isError():
            data["onoff"] = r.registers[0]

        # ── Coils ────────────────────────────────────────────────

        r = self._client.read_coils(COIL_BYPASS_SILOWNIK, count=1, device_id=slave)
        if not r.isError():
            data["bypass_silownik"] = bool(r.bits[0])

        return data
