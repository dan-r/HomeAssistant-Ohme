# Ohme EV Charger for Home Assistant

A basic integration for interacting with Ohme EV Chargers.

This is an unofficial integration. I have no affiliation with Ohme besides owning one of their EV chargers.

This integration does not currently support social login or accounts with multiple chargers. It has been tested with the following hardware:
* Ohme Home Pro [v1.32]
* Ohme Home [v1.32]
* Ohme Go [v1.32]
* Ohme ePod [v2.12]

If you find any bugs or would like to request a feature, please open an issue.


## Installation

### HACS
This is the recommended installation method.
1. Add this repository to HACS as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories)
2. Search for and install the Ohme addon from HACS
3. Restart Home Assistant

### Manual
1. Download the [latest release](https://github.com/dan-r/HomeAssistant-Ohme/releases)
2. Copy the contents of `custom_components` into the `<config directory>/custom_components` directory of your Home Assistant installation
3. Restart Home Assistant


## Setup
From the Home Assistant Integrations page, search for and add the Ohme integration.

If you created your Ohme account through a social login (Apple/Facebook/Google), you will need to set a password in the Ohme app or 'reset your password' to use this integration.


## Entities
This integration exposes the following entities:

* Binary Sensors
    * Car Connected - On when a car is plugged in
    * Car Charging - On when a car is connected and drawing power
    * Pending Approval - On when a car is connected and waiting for approval
    * Charge Slot Active - On when a charge slot is in progress according to the Ohme-generated charge plan
    * Charger Online - On if charger is online and connected to the internet
* Sensors (Charge power) - **Only available during a charge session**
    * Power Draw (Watts) - Power draw of connected car
    * Current Draw (Amps) - Current draw of connected car
    * Voltage (Volts) - Voltage reading
* Sensors (Other)
    * CT Reading (Amps) - Reading from attached CT clamp
    * Accumulative Energy Usage (kWh) - Total energy used by the charger
    * Next Charge Slot Start - The next time your car will start charging according to the Ohme-generated charge plan
    * Next Charge Slot End - The next time your car will stop charging according to the Ohme-generated charge plan
* Switches (Settings) - **Only options available to your charger model will show**
    * Lock Buttons - Locks buttons on charger
    * Require Approval - Require approval to start a charge
    * Sleep When Inactive - Charger screen & lights will automatically turn off
* Switches (Charge state) - **These are only functional when a car is connected**
    * Max Charge - Forces the connected car to charge regardless of set schedule
    * Pause Charge - Pauses an ongoing charge
* Inputs - **If in a charge session, these change the active charge. If disconnected, they change your first schedule.**
    * Number: Target Percentage - Change the target battery percentage
    * Time: Target Time - Change the target time
* Buttons
    * Approve Charge - Approves a charge when 'Pending Approval' is on

## Coordinators
Updates are made to entity states by polling the Ohme API. This is handled by 'coordinators' defined to Home Assistant, which refresh at a set interval or when externally triggered.

The coordinators are listed with their refresh intervals below. Relevant coordinators are also refreshed when using switches and buttons.

* OhmeChargeSessionsCoordinator (30s refresh)
    * Binary Sensors: Car connected, car charging, pending approval and charge slot active
    * Buttons: Approve Charge
    * Sensors: Power, current, voltage and next slot (start & end)
    * Switches: Max charge, pause charge
    * Inputs: Target time and target percentage (If car connected)
* OhmeAccountInfoCoordinator (1m refresh)
    * Switches: Lock buttons, require approval and sleep when inactive
* OhmeAdvancedSettingsCoordinator (1m refresh)
    * Sensors: CT reading sensor
    * Binary Sensors: Charger online
* OhmeStatisticsCoordinator (30m refresh)
    * Sensors: Accumulative energy usage
* OhmeChargeSchedulesCoordinator (10m refresh)
    * Inputs: Target time and target percentage (If car disconnected)
