# Changelog

All notable changes to this project. Versions follow [semantic versioning](https://semver.org/); each entry links to its full release notes on GitHub, which also say how each change was tested.

## [0.3.4] — 2026-11-17

Mode shows the new mode at once; regression tests.

- **Mode** now shows the mode you picked straight away. Before, it kept showing the old mode until the next poll (up to 30 s), because only the job that was switched on was updated locally.
- **Tested hardware** table at the top of the README, and the one-controller warning before install.
- **Mode table:** what each choice sends and what the unit does.
- **Regression tests** with a fake unit that behaves like a real DDSX, run on every change: mode switches (asserting the writes sent), tank alarm set/clear, connection loss and recovery, characteristics found by UUID.
- **On-device checklist** in CONTRIBUTING.md.

## [0.3.3] — 2026-11-09

Icon in dark mode.

- The icon now also shows in dark mode: Home Assistant asks for `dark_icon.png` and doesn't fall back to `icon.png`, so the integration ships both.

## [0.3.2] — 2026-11-09

The integration's own icon.

- The integration now ships its own icon (`brand/`), so it shows under *Settings → Devices & services* on Home Assistant **2026.3** or newer. Older versions keep the generic placeholder.
- README: icon at the top.

## [0.3.1] — 2026-11-09

First public release.

- **Mode** select: Dehumidify / Purify only / Off, switched the safe way (the unit does one job at a time, and switching the purifier off turns it all off).
- **Eco mode**, **Laundry mode**, **Real Feel** and **Louver swing** switches.
- **Water tank** binary sensor: on when the tank is full or missing (alarm code 3), plus **Alarm** and **Alarm code**.
- **Current mode** (dehumidify, clothes drying or purify), Real Feel colour, mould prediction and resources.
- Entities join the unit's existing device, with ids named after it (`select.dehumidifier_mode`).

[0.3.4]: https://github.com/davidteles/ha-delonghi-ddsx/releases/tag/v0.3.4
[0.3.3]: https://github.com/davidteles/ha-delonghi-ddsx/releases/tag/v0.3.3
[0.3.2]: https://github.com/davidteles/ha-delonghi-ddsx/releases/tag/v0.3.2
[0.3.1]: https://github.com/davidteles/ha-delonghi-ddsx/releases/tag/v0.3.1
