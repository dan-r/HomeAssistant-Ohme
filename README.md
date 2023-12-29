# Ohme EV Charger for Home Assistant

A basic integration for interacting with Ohme EV Chargers.

This is an unofficial integration. I have no affiliation with Ohme besides owning one of their EV chargers.

This integration does not currently support social login or accounts with multiple chargers. It has been tested with the following hardware:
* Ohme Home Pro [UK]
* Ohme Home/Go [UK]
* Ohme ePod [UK]

If you find any bugs or would like to request a feature, please open an issue.

## Entities
This integration exposes the following entities:

* Binary Sensors
    * Car Connected - On when a car is plugged in
    * Car Charging - On when a car is connected and drawing power
    * Pending Approval - On when a car is connected and waiting for approval
* Sensors
    * Power Draw (Watts) - Power draw of connected car
    * Current Draw (Amps) - Current draw of connected car
    * CT Reading (Amps) - Reading from attached CT clamp
    * Accumulative Energy Usage (kWh) - Total energy used by the charger
    * Next Smart Charge Slot - The next time your car will start charging according to the Ohme-generated charge plan
* Switches (Settings) - Only options available to your charger model will show
    * Lock Buttons - Locks buttons on charger
    * Require Approval - Require approval to start a charge
    * Sleep When Inactive - Charger screen & lights will automatically turn off
* Switches (Charge state) - These are only functional when a car is connected
    * Max Charge - Forces the connected car to charge regardless of set schedule
    * Pause Charge - Pauses an ongoing charge
* Buttons
    * Approve Charge - Approves a charge when 'Pending Approval' is on

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
From the Home Assistant Integrations page, search for an add the Ohme integration. If you created your Ohme account through a social login, you will need to 'reset your password' to use this integration.
