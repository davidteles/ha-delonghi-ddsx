"""A fake De'Longhi DDSX behind a fake HomeKit Controller connection.

The fake unit follows the behaviour seen on a real DDSX220WF (firmware 1.0.8):

* it does one job at a time: switching one job on stops the other one;
* switching the *purifier* off turns the whole unit off (on the real unit this
  happens about 20 seconds later, the fake does it at once).

Every write is recorded, so tests can assert exactly what the integration sent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.delonghi_ddsx.const import (
    ACTIVE, ALARMS, CONF_HK_ENTRY, CURRENT_MODE, DOMAIN, ECO, LAUNDRY, MOLD, REAL_FEEL, REAL_FEEL_COLOR, REAL_FEEL_ON,
    RESOURCES, SWING,
)

AID = 1
PRIVATE_UUID = "9B8AA3E7-0000-0000-0000-000000000000"
DEHUM_UUID = "000000BD-0000-1000-8000-0026BB765291"
PURIFIER_UUID = "000000BB-0000-1000-8000-0026BB765291"


def _uuid(short: str) -> str:
    return f"{short}-0000-1000-8000-0026BB765291"


# (service uuid, characteristic short type, iid). The iids are deliberately not
# the ones on a real unit: the integration must find everything by UUID.
LAYOUT = [
    (DEHUM_UUID, ACTIVE, 41),
    (DEHUM_UUID, SWING, 47),
    (PURIFIER_UUID, ACTIVE, 61),
    (PRIVATE_UUID, LAUNDRY, 101),
    (PRIVATE_UUID, ECO, 102),
    (PRIVATE_UUID, MOLD, 103),
    (PRIVATE_UUID, REAL_FEEL_ON, 104),
    (PRIVATE_UUID, CURRENT_MODE, 105),
    (PRIVATE_UUID, REAL_FEEL, 106),
    (PRIVATE_UUID, REAL_FEEL_COLOR, 107),
    (PRIVATE_UUID, ALARMS, 108),
    (PRIVATE_UUID, RESOURCES, 109),
]
IID = {(service, short): iid for service, short, iid in LAYOUT}
DEHUM_ACTIVE_IID = IID[(DEHUM_UUID, ACTIVE)]
PURIFIER_ACTIVE_IID = IID[(PURIFIER_UUID, ACTIVE)]
ALARMS_IID = IID[(PRIVATE_UUID, ALARMS)]
MODE_IID = IID[(PRIVATE_UUID, CURRENT_MODE)]


@dataclass
class FakeChar:
    type: str
    iid: int


@dataclass
class FakeService:
    type: str
    characteristics: list[FakeChar]


@dataclass
class FakeAccessory:
    aid: int
    services: list[FakeService]


@dataclass
class FakeEntityMap:
    accessories: list[FakeAccessory]


@dataclass
class FakePairing:
    """The unit itself: values by iid, plus every write it received."""

    values: dict[int, Any] = field(default_factory=dict)
    writes: list[tuple[int, int, Any]] = field(default_factory=list)
    connected: bool = True

    async def get_characteristics(self, addresses: list[tuple[int, int]]) -> dict[tuple[int, int], dict[str, Any]]:
        if not self.connected:
            raise ConnectionError("unit unreachable")
        return {(aid, iid): {"value": self.values[iid]} for aid, iid in addresses if iid in self.values}

    async def put_characteristics(self, writes: list[tuple[int, int, Any]]) -> None:
        if not self.connected:
            raise ConnectionError("unit unreachable")
        for aid, iid, value in writes:
            self.writes.append((aid, iid, value))
            self.values[iid] = value
            if iid == DEHUM_ACTIVE_IID and value:  # dehumidify on: the unit stops purifying
                self.values[PURIFIER_ACTIVE_IID] = 0
                self.values[MODE_IID] = 1
            elif iid == PURIFIER_ACTIVE_IID and value:  # purify on: the unit stops dehumidifying
                self.values[DEHUM_ACTIVE_IID] = 0
                self.values[MODE_IID] = 3
            elif iid == PURIFIER_ACTIVE_IID and not value:  # the trap: purifier off = whole unit off
                self.values[DEHUM_ACTIVE_IID] = 0


@dataclass
class FakeConnection:
    pairing: FakePairing
    entity_map: FakeEntityMap


def make_connection(layout: list[tuple[str, str, int]] = LAYOUT) -> FakeConnection:
    services: dict[str, list[FakeChar]] = {}
    for service, short, iid in layout:
        services.setdefault(service, []).append(FakeChar(_uuid(short), iid))
    accessory = FakeAccessory(AID, [FakeService(s, chars) for s, chars in services.items()])
    pairing = FakePairing(values={
        DEHUM_ACTIVE_IID: 1, IID[(DEHUM_UUID, SWING)]: 0, PURIFIER_ACTIVE_IID: 0,
        IID[(PRIVATE_UUID, LAUNDRY)]: False, IID[(PRIVATE_UUID, ECO)]: False, IID[(PRIVATE_UUID, MOLD)]: "",
        IID[(PRIVATE_UUID, REAL_FEEL_ON)]: 0, MODE_IID: 1, IID[(PRIVATE_UUID, REAL_FEEL)]: "",
        IID[(PRIVATE_UUID, REAL_FEEL_COLOR)]: 1, ALARMS_IID: 0, IID[(PRIVATE_UUID, RESOURCES)]: 0,
    })
    return FakeConnection(pairing, FakeEntityMap([accessory]))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def connection() -> FakeConnection:
    return make_connection()


@pytest.fixture
async def setup_unit(hass: HomeAssistant, connection: FakeConnection):
    """HomeKit Controller (faked) holding the unit, then our integration on top."""
    hass.config.components.add("homekit_controller")  # its real setup needs a real accessory
    hk_entry = MockConfigEntry(domain="homekit_controller", title="Dehumidifier")
    hk_entry.add_to_hass(hass)
    hk_entry.runtime_data = connection
    dr.async_get(hass).async_get_or_create(
        config_entry_id=hk_entry.entry_id,
        identifiers={("homekit_controller", f"00:00:00:00:00:00:aid:{AID}")},
        manufacturer="DeLonghi",
        model="DDSX 1.2.1",
        name="Dehumidifier",
    )
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HK_ENTRY: hk_entry.entry_id}, unique_id=hk_entry.entry_id)
    entry.add_to_hass(hass)

    async def _setup() -> MockConfigEntry:
        await hass.config_entries.async_setup(entry.entry_id)  # False while it waits to retry
        await hass.async_block_till_done()
        return entry

    return _setup
