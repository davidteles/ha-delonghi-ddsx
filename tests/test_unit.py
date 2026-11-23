"""Regression tests against a fake unit (see conftest.py).

What a fake can't prove (the real 20-second shutdown, the real HomeKit
session) is on the on-device checklist in CONTRIBUTING.md.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from custom_components.delonghi_ddsx import map_characteristics
from custom_components.delonghi_ddsx.const import ALARMS, DEHUM_ACTIVE, ECO, PURIFIER_ACTIVE, REAL_FEEL_ON

from .conftest import (
    AID, ALARMS_IID, DEHUM_ACTIVE_IID, IID, LAYOUT, PRIVATE_UUID, PURIFIER_ACTIVE_IID, make_connection,
)

MODE = "select.dehumidifier_mode"
TANK = "binary_sensor.dehumidifier_water_tank"
ALARM = "binary_sensor.dehumidifier_alarm"
CURRENT = "sensor.dehumidifier_current_mode"


async def _select(hass: HomeAssistant, option: str) -> None:
    await hass.services.async_call("select", "select_option", {"entity_id": MODE, "option": option}, blocking=True)
    await hass.async_block_till_done()


async def _refresh(hass: HomeAssistant, entry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


def test_characteristics_are_found_by_uuid_not_position(connection) -> None:
    chars = map_characteristics(connection)
    assert chars[DEHUM_ACTIVE] == (AID, DEHUM_ACTIVE_IID)
    assert chars[PURIFIER_ACTIVE] == (AID, PURIFIER_ACTIVE_IID)
    assert chars[ALARMS] == (AID, ALARMS_IID)
    # Same unit, other iids (as on another firmware): still found.
    shifted = make_connection([(s, c, iid + 500) for s, c, iid in LAYOUT])
    assert map_characteristics(shifted)[ALARMS] == (AID, ALARMS_IID + 500)


async def test_setup_waits_without_the_private_service(hass: HomeAssistant, connection, setup_unit) -> None:
    connection.entity_map.accessories[0].services = [
        s for s in connection.entity_map.accessories[0].services if not s.type.startswith(PRIVATE_UUID[:8])
    ]
    entry = await setup_unit()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_dehumidify_to_purify_never_switches_the_purifier_off(hass, connection, setup_unit) -> None:
    await setup_unit()
    assert hass.states.get(MODE).state == "dehumidify"
    await _select(hass, "purify")
    # Only "purifier on" is sent; the unit stops dehumidifying by itself.
    assert connection.pairing.writes == [(AID, PURIFIER_ACTIVE_IID, 1)]
    # Shown straight away, not only after the next 30-second poll.
    assert hass.states.get(MODE).state == "purify"


async def test_purify_to_dehumidify_never_switches_the_purifier_off(hass, connection, setup_unit) -> None:
    connection.pairing.values.update({DEHUM_ACTIVE_IID: 0, PURIFIER_ACTIVE_IID: 1})
    entry = await setup_unit()
    assert hass.states.get(MODE).state == "purify"
    await _select(hass, "dehumidify")
    # Writing "purifier off" here would shut the whole unit down ~20 s later.
    assert connection.pairing.writes == [(AID, DEHUM_ACTIVE_IID, 1)]
    assert hass.states.get(MODE).state == "dehumidify"  # straight away
    await _refresh(hass, entry)  # what the unit really reports afterwards
    assert hass.states.get(MODE).state == "dehumidify"
    assert hass.states.get(CURRENT).state == "dehumidify"


async def test_off_switches_both_jobs_off(hass, connection, setup_unit) -> None:
    entry = await setup_unit()
    await _select(hass, "off")
    assert sorted(connection.pairing.writes) == sorted([(AID, DEHUM_ACTIVE_IID, 0), (AID, PURIFIER_ACTIVE_IID, 0)])
    await _refresh(hass, entry)
    assert hass.states.get(MODE).state == "off"


async def test_tank_alarm_sets_and_clears(hass, connection, setup_unit) -> None:
    entry = await setup_unit()
    assert hass.states.get(TANK).state == STATE_OFF
    assert hass.states.get(ALARM).state == STATE_OFF

    connection.pairing.values[ALARMS_IID] = 3  # tank full or missing
    await _refresh(hass, entry)
    assert hass.states.get(TANK).state == STATE_ON
    assert hass.states.get(ALARM).state == STATE_ON

    connection.pairing.values[ALARMS_IID] = 0  # emptied and back in place
    await _refresh(hass, entry)
    assert hass.states.get(TANK).state == STATE_OFF
    assert hass.states.get(ALARM).state == STATE_OFF


async def test_other_alarms_are_not_the_tank(hass, connection, setup_unit) -> None:
    connection.pairing.values[ALARMS_IID] = 5
    await setup_unit()
    assert hass.states.get(TANK).state == STATE_OFF
    assert hass.states.get(ALARM).state == STATE_ON


async def test_connection_loss_and_recovery(hass, connection, setup_unit) -> None:
    entry = await setup_unit()
    connection.pairing.connected = False
    await _refresh(hass, entry)
    assert hass.states.get(MODE).state == STATE_UNAVAILABLE
    assert hass.states.get(TANK).state == STATE_UNAVAILABLE

    connection.pairing.connected = True
    connection.pairing.values[ALARMS_IID] = 3
    await _refresh(hass, entry)
    assert hass.states.get(MODE).state == "dehumidify"
    assert hass.states.get(TANK).state == STATE_ON


async def test_switches_write_the_type_the_unit_expects(hass, connection, setup_unit) -> None:
    await setup_unit()
    for entity_id in ("switch.dehumidifier_eco_mode", "switch.dehumidifier_real_feel"):
        await hass.services.async_call("switch", "turn_on", {"entity_id": entity_id}, blocking=True)
    await hass.async_block_till_done()
    # Eco is a boolean characteristic, Real Feel a 0/1 number.
    assert (AID, IID[(PRIVATE_UUID, ECO)], True) in connection.pairing.writes
    assert (AID, IID[(PRIVATE_UUID, REAL_FEEL_ON)], 1) in connection.pairing.writes
    assert hass.states.get("switch.dehumidifier_eco_mode").state == STATE_ON


async def test_older_home_assistant_without_runtime_data_is_found_too(hass, connection) -> None:
    """Before HomeKit Controller used entry.runtime_data (e.g. 2025.1), its connections lived in
    hass.data["homekit_controller-devices"]. The fallback lookup must find the unit there."""
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.delonghi_ddsx.const import CONF_HK_ENTRY, DOMAIN

    hass.config.components.add("homekit_controller")
    hk_entry = MockConfigEntry(domain="homekit_controller", title="Dehumidifier")
    hk_entry.add_to_hass(hass)
    connection.config_entry = hk_entry          # how the old KNOWN_DEVICES entries point back to their entry
    hass.data["homekit_controller-devices"] = {"00:00:00:00:00:00": connection}
    dr.async_get(hass).async_get_or_create(
        config_entry_id=hk_entry.entry_id,
        identifiers={("homekit_controller", "00:00:00:00:00:00:aid:1")},
        manufacturer="DeLonghi", model="DDSX 1.2.1", name="Dehumidifier",
    )
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HK_ENTRY: hk_entry.entry_id}, unique_id=hk_entry.entry_id)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get(MODE).state == "dehumidify"
    assert await hass.config_entries.async_unload(entry.entry_id)
