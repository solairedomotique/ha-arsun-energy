## 0.3.2
- Added instantaneous power sensors for ARSUN outputs 1 and 2 (W).
- Preserved all existing sensor names and entity unique IDs.
- Kept cumulative energy sensors in kWh with `device_class: energy` and `state_class: total_increasing` for Home Assistant Energy compatibility.
- Kept the forced-mode binary sensors and the existing heater energy allocation.

## 0.3.1
- Added binary sensors for forced mode on ARSUN channels 1 and 2 (ON when the corresponding LED state is `H`).
- Kept the existing energy and power sensors and the heater energy split calculation.

# Changelog

## 0.3.0
- Corrected the gauge sign: positive means export to EDF; negative means consumption from EDF.
- Renamed grid energy sensors to clarify energy consumed from EDF and energy returned to EDF.
- Added four restored cumulative energy counters for heater outputs 1 and 2: solar and EDF shares.
- Heater split uses the global forced state: LED S1 is `H` OR LED S2 is `H`.
- During forced mode, EDF import is allocated proportionally to the instantaneous wattage measured on outputs 1 and 2. Remaining heater power is attributed to solar.
- When neither LED is `H`, measured heater output power is attributed to solar, as specified.

## 0.2.1
- Previous gauge sign correction release.

## 0.2.0
- Bidirectional signed gauge and default source selection.

## 0.1.3
- Initial public release with original power, split grid power, and cumulative energy counters.
