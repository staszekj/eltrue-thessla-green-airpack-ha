"""Constants for the AirPack integration."""

DOMAIN = "airpack"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICE_ID = "device_id"

DEFAULT_PORT = 4196
DEFAULT_DEVICE_ID = 10
DEFAULT_SCAN_INTERVAL = 30

PLATFORMS = ["sensor", "binary_sensor", "switch", "select", "number"]

# ── Register map ────────────────────────────────────────────────
# Input registers (read_input_registers)
REG_TEMPS_ADDR = 16        # TZ1..TO, count=7, scale ×0.1, signed, 32768=N/A
REG_FLOWS_ADDR = 272       # nawiew_%, wywiew_%, nawiew_m3h, wywiew_m3h, count=4
REG_FW_ADDR = 0            # fw_major, fw_minor, count=2
REG_SN_ADDR = 24           # sn_1..sn_4, count=4

# Holding registers (read_holding_registers)
REG_FPX_FLAGA = 4192
REG_FPX_TRYB = 4198
REG_TRYB = 4208
REG_SEZON = 4209
REG_INTENSYWNOSC = 4210
REG_FUNKCJE_SPECJALNE = 4224
REG_BYPASS_WYLACZONY = 4320
REG_BYPASS_MIN_TEMP = 4321   # scale ×0.5
REG_BYPASS_TEMP_GRZANIE = 4322  # scale ×0.5
REG_BYPASS_TEMP_CHLODZENIE = 4323  # scale ×0.5
REG_BYPASS_STATUS = 4330
REG_BYPASS_TRYB = 4331
REG_NOMINAL_NAWIEW = 4354
REG_NOMINAL_WYWIEW = 4355
REG_ONOFF = 4387

# Coils
COIL_BYPASS_SILOWNIK = 9

# Tryb options
TRYB_OPTIONS = ["Automatyczny", "Manualny", "Chwilowy"]

# Sezon options
SEZON_OPTIONS = ["Lato", "Zima"]

# Funkcje specjalne options
FUNKCJE_OPTIONS = [
    "Brak",
    "Okap",
    "Kominek",
    "Wietrzenie (dzwonek)",
    "Wietrzenie (włącznik)",
    "Wietrzenie (higrostat)",
    "Wietrzenie (jakość pow.)",
    "Wietrzenie (ręczne)",
    "Wietrzenie (auto-harmonogram)",
    "Wietrzenie (man-harmonogram)",
    "Otwarte okna",
    "Pusty dom",
]
