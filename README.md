# De'Longhi DDSX extras for Home Assistant

Unlock the hidden features of De'Longhi **DDSX** dehumidifiers (Tasciugo AriaDry Multi, e.g. DDSX220WF) in Home Assistant: **eco mode, laundry mode, a proper Dehumidify / Purify-only / Off mode, louver swing and a real water-tank alarm**. Fully local, through the HomeKit pairing you already have.

[![Validate](https://github.com/davidteles/ha-delonghi-ddsx/actions/workflows/validate.yml/badge.svg)](https://github.com/davidteles/ha-delonghi-ddsx/actions/workflows/validate.yml)
![Version](https://img.shields.io/badge/version-0.3.1-blue)
![IoT class](https://img.shields.io/badge/IoT-local%20polling-brightgreen)

---

## Why this exists

These units speak HomeKit over Wi-Fi. Home Assistant's built-in **HomeKit Controller** integration pairs with them and gives you the basics: on/off, target humidity, current humidity, the purifier fan and temperature.

But the unit also has a **private De'Longhi HomeKit service**, which only De'Longhi's own app uses. Home Assistant ignores it, so you miss:

- eco mode and laundry mode,
- which job the unit is doing (it dehumidifies **or** purifies, never both),
- the dehumidifier's louver swing,
- the **water-tank alarm**. The "water level" some HomeKit apps show never reports anything.

This integration reads and writes that private service **through HomeKit Controller's existing connection**. It never pairs a second time, needs no account, and nothing leaves your network.

## What you get

All entities appear on the dehumidifier's existing device, next to the ones HomeKit Controller already creates.

| Entity | Type | What it does |
|---|---|---|
| **Mode** | select | `Dehumidify` / `Purify only` / `Off`, changed the safe way (see [How the modes behave](#how-the-modes-behave)) |
| **Eco mode** | switch | De'Longhi eco mode |
| **Laundry mode** | switch | Laundry drying mode |
| **Louver swing** | switch | The dehumidifier's swinging louver (the purifier's swing is already on HomeKit Controller's fan entity) |
| **Real Feel** | switch | De'Longhi "Real Feel" comfort mode |
| **Water tank** | binary sensor | **On** when the tank is full or not in place, so the unit has stopped drying |
| **Alarm** | binary sensor | On for any alarm the unit reports |
| **Alarm code** | sensor | The raw alarm code, with the bits set and a `water_tank` attribute |
| **Current mode** | sensor (diagnostic) | `dehumidify` / `laundry` (clothes drying) / `purify`, as reported by the unit |
| **Real Feel colour** | sensor | The Real Feel indicator colour (0–2) and the raw Real Feel data |
| **Mould prediction** | sensor (diagnostic) | Raw mould-prediction data (hex); its meaning isn't decoded yet |
| **Resources** | sensor (diagnostic) | Raw value reported by the unit |

## Requirements

- Home Assistant **2025.1** or newer.
- A De'Longhi **DDSX** dehumidifier with HomeKit (Wi-Fi), **paired with Home Assistant's HomeKit Controller integration**.

> **One controller at a time.** HomeKit Wi-Fi accessories can only be paired with one controller. If your unit is in Apple Home today, you have to remove it there first. You can then share it back to Apple Home through Home Assistant's HomeKit Bridge (see [Apple Home](#apple-home)).

## Installation

### Home Assistant Marketplace / HACS

1. Add this repository as a **custom repository** (category **Integration**): `https://github.com/davidteles/ha-delonghi-ddsx`
2. Install **De'Longhi DDSX extras**.
3. Restart Home Assistant.

### Manual

Copy `custom_components/delonghi_ddsx` into your Home Assistant `config/custom_components/` folder and restart.

## Setup

1. **Pair the unit with HomeKit Controller** (skip this if it's already paired):
   1. If the unit is in Apple Home, remove it there (*accessory settings → Remove Accessory*).
   2. In Home Assistant, go to *Settings → Devices & services*. The unit shows up under **Discovered** as a HomeKit device. Choose **Configure** and type the 8-digit HomeKit code from the label on the unit.
2. **Add this integration:** *Settings → Devices & services → Add integration → De'Longhi DDSX extras*. It finds the paired unit by itself. With more than one unit, pick which one.

That's it. The new entities appear on the dehumidifier's device page.

## How the modes behave

Learned from a real unit. This is why the **Mode** select is the recommended control.

- The unit does **one job at a time**. Switching the purifier on makes the unit stop dehumidifying by itself.
- **Switching the purifier off turns the whole unit off** (after about 20 seconds), even if you just asked it to dehumidify.
- So **Mode** only ever switches the *wanted* job on and lets the unit stop the other one. `Off` switches both off.

## Alarm codes

| Code | Meaning | What the unit does |
|---|---|---|
| `0` | No alarm | |
| `3` | **Water tank full or not in place** | Stops drying; restarts by itself when the emptied tank is back |
| other | Unknown | Please [open an issue](https://github.com/davidteles/ha-delonghi-ddsx/issues) with the code and what the unit's display showed |

## Example automations

**Phone notification when the tank needs emptying.** It waits 2 minutes, so it doesn't fire while you're emptying it, and removes itself when the tank is back:

```yaml
alias: Dehumidifier - empty the tank
triggers:
  - trigger: state
    entity_id: binary_sensor.dehumidifier_water_tank
    to: "on"
    for: "00:02:00"
    id: full
  - trigger: state
    entity_id: binary_sensor.dehumidifier_water_tank
    to: "off"
    id: emptied
actions:
  - choose:
      - conditions: [{ condition: trigger, id: full }]
        sequence:
          - action: notify.mobile_app_your_phone
            data:
              title: "💧 Dehumidifier: empty the tank"
              message: "The water tank is full, so it stopped drying. Empty it and slide it back in."
              data: { tag: dehumidifier-tank }
      - conditions: [{ condition: trigger, id: emptied }]
        sequence:
          - action: notify.mobile_app_your_phone
            data: { message: clear_notification, data: { tag: dehumidifier-tank } }
```

**Eco mode at night:**

```yaml
alias: Dehumidifier - eco at night
triggers:
  - trigger: time
    at: "23:00:00"
    id: night
  - trigger: time
    at: "07:00:00"
    id: day
actions:
  - action: "switch.turn_{{ 'on' if trigger.id == 'night' else 'off' }}"
    target: { entity_id: switch.dehumidifier_eco_mode }
```

Entity IDs depend on your device name. The examples assume a device called *Dehumidifier*.

## Apple Home

After the move to Home Assistant, you can share the unit back to Apple Home with the **HomeKit Bridge** integration. Add only the entities you want, by name, rather than whole domains (that would flood Apple Home with helpers).

| In Apple Home | Native pairing | Through Home Assistant |
|---|---|---|
| Dehumidifier on/off, target humidity, current humidity | ✅ | ✅ |
| Purifier on/off, speed, auto/manual, swing | ✅ | ✅ (shown as a fan) |
| Temperature | ✅ | ✅ |
| Dehumidifier louver swing | ✅ | ❌ (use this integration's switch in Home Assistant) |
| De'Longhi's own app (eco, laundry, history, timers, firmware updates) | ✅ | ❌ |

## Limitations

- **Polling** every 30 seconds. Changes you make in Home Assistant show immediately; changes made on the unit's buttons show within 30 seconds.
- **Not decoded yet:** the humidity history, the timer program and the meaning of the mould-prediction bytes.
- **Timers aren't supported.** If a timer or delayed start is set on the unit (clock or calendar icon on its display), it can stay on but idle. Switching it off and on from Home Assistant doesn't clear that: press the clock button on the unit.
- After switching **Real Feel** off, HomeKit Controller may show the dehumidifier in *auto* mode. Set it back to *normal* on the dehumidifier entity if it doesn't dry.
- **Not available:** firmware updates and the filter reset. Use De'Longhi's app while the unit is paired natively.
- The entities are moved onto HomeKit Controller's device so everything stays together. If you remove HomeKit Controller's entry, remove this one too.

## Troubleshooting

| Problem | Fix |
|---|---|
| "No De'Longhi DDSX found" | Pair the unit with **HomeKit Controller** first. This integration piggybacks on that pairing. |
| Setup keeps retrying | HomeKit Controller hasn't connected to the unit yet. Check the unit is online and the HomeKit Controller entry is loaded. |
| Entities unavailable | The unit is offline, or HomeKit Controller lost it. Reload HomeKit Controller's entry. |
| An alarm code isn't in the table | Open an issue with the code. It helps everyone. |

## Contributing

Tested on a **DDSX220WF** (firmware 1.0.8). Reports from other DDSX models and firmware are very welcome: open an issue with the model, the firmware (shown on HomeKit Controller's device page) and what worked. Pull requests are welcome too.

The long-term goal is to add these features to Home Assistant's own HomeKit Controller integration, as was done for other vendors' HomeKit extras. That would make this integration unnecessary.

## Disclaimer

Not affiliated with or endorsed by De'Longhi. "De'Longhi", "Tasciugo" and "AriaDry" are trademarks of their owners. Use at your own risk.

## Licence

[MIT](LICENSE)
