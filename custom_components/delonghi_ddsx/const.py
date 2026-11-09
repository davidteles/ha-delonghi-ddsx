"""Constants for De'Longhi DDSX extras."""

DOMAIN = "delonghi_ddsx"
CONF_HK_ENTRY = "hk_entry_id"
SCAN_SECONDS = 30

# Private De'Longhi service and its characteristics, matched by the first
# 8 hex digits of their UUIDs (stable across units; the iids are not).
PRIVATE_SERVICE = "9B8AA3E7"
LAUNDRY = "50233326"  # bool, read/write
ECO = "CAF353CE"  # bool, read/write
MOLD = "925DE44D"  # data, read
REAL_FEEL_ON = "CE88A1DC"  # uint8 0/1, read/write
CURRENT_MODE = "416FF0AE"  # uint8, read: 1 = dehumidify, 2 = clothes drying, 3 = purify only
REAL_FEEL = "E1672A87"  # data, read
REAL_FEEL_COLOR = "85E82A99"  # uint8 0..2, read
ALARMS = "20CF101A"  # uint8 alarm code, read: 3 = water tank full or missing
RESOURCES = "7FE3D3A4"  # int, read

# Standard HomeKit services/characteristics Home Assistant doesn't expose here.
DEHUMIDIFIER_SERVICE = "000000BD"
PURIFIER_SERVICE = "000000BB"
ACTIVE = "000000B0"
SWING = "000000B6"

# Keys used internally for the standard characteristics.
DEHUM_ACTIVE = "dehumidifier_active"
DEHUM_SWING = "dehumidifier_swing"
PURIFIER_ACTIVE = "purifier_active"

MODE_NAMES = {1: "dehumidify", 2: "laundry", 3: "purify"}
TANK_ALARM_CODE = 3
