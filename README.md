# Ohme EV Charger for Home Assistant

An unofficial integration for interacting with Ohme EV Chargers. I have no affiliation with Ohme besides owning one of their EV chargers.

This integration does not currently support accounts with multiple chargers.

If you find any bugs or would like to request a feature, please open an issue.

## Tested Hardware
This integration has been tested with the following hardware:
* Ohme Home Pro [v1.32]
* Ohme Home [v1.32]
* Ohme Go [v1.32]
* Ohme ePod [v2.12]

## External Software
The 'Charge Slot Active' binary sensor mimics the `planned_dispatches` and `completed_dispatches` attributes from the [Octopus Energy](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy) integration, so should support external software which reads this such as [predbat](https://github.com/springfall2008/batpred).


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

### Social Logins
If you created your Ohme account through an Apple, Facebook or Google account, you will need to set a password in the Ohme app.

Open the menu in the Ohme app (☰) and note the email address shown under your name. This is your login email address and may differ from what you expect.

To set a password, open **Settings** from this menu and click **Account Details > Change Password**. Thanks to [EV Nick](https://www.youtube.com/c/NicolasRaimo) for these instructions.


## Entities
This integration exposes the following entities:

* Binary Sensors
    * Car Connected - On when a car is plugged in
    * Car Charging - On when a car is connected and drawing power
    * Pending Approval - On when a car is connected and waiting for approval
    * Charge Slot Active - On when a charge slot is in progress according to the Ohme-generated charge plan
    * Charger Online - On if charger is online and connected to the internet
* Sensors (Session specific) - **Only available during a charge session**
    * Power Draw (Watts) - Power draw of connected car
    * Current Draw (Amps) - Current draw of connected car
    * Voltage (Volts) - Voltage reading
    * Charge Slots - A comma separated list of assigned charge slots 
    * Next Charge Slot Start - The next time your car will start charging according to the Ohme-generated charge plan
    * Next Charge Slot End - The next time your car will stop charging according to the Ohme-generated charge plan
* Sensors (Other)
    * CT Reading (Amps) - Reading from attached CT clamp
    * Session Energy Usage (kWh) - Energy used in the current session
    * Accumulative Energy Usage (kWh) - Total energy used by the charger (If enabled in options)
    * Battery State of Charge (%) - If your car is API connected this is read from the car, if not it is how much charge Ohme thinks it has added
* Switches (Settings) - **Only options available to your charger model will show**
    * Lock Buttons - Locks buttons on charger
    * Require Approval - Require approval to start a charge
    * Sleep When Inactive - Charger screen & lights will automatically turn off
* Switches (Charge state) - **These are only functional when a car is connected**
    * Max Charge - Forces the connected car to charge regardless of set schedule
    * Pause Charge - Pauses an ongoing charge
    * Enable Price Cap - Whether price cap is applied
* Inputs - **If in a charge session, these change the active charge. If disconnected, they change your first schedule.**
    * Number
        * Target Percentage - Change the target battery percentage
        * Preconditioning - Change pre-conditioning time. 0 is off
        * Price Cap - Maximum charge price
    * Time
        * Target Time - Change the target time
* Buttons
    * Approve Charge - Approves a charge when 'Pending Approval' is on

## Options
Some options can be set from the 'Configure' menu in Home Assistant:
* Never update an ongoing session - Override the default behaviour of the target time, percentage and preconditioning inputs and only ever update the schedule, not the current session. This was added as changing the current session can cause issues for customers on Intelligent Octopus Go.
* Enable accumulative energy usage sensor - Enable the sensor showing an all-time incrementing energy usage counter. This causes issues with some accounts. 


## Coordinators
Updates are made to entity states by polling the Ohme API. This is handled by 'coordinators' defined to Home Assistant, which refresh at a set interval or when externally triggered.

The coordinators are listed with their refresh intervals below. Relevant coordinators are also refreshed when using switches and buttons.

* OhmeChargeSessionsCoordinator (30s refresh)
    * Binary Sensors: Car connected, car charging, pending approval and charge slot active
    * Buttons: Approve Charge
    * Sensors: Power, current, voltage, session energy usage, charge slots, and next slot (start & end)
    * Switches: Max charge, pause charge
    * Inputs: Target time, target percentage and preconditioning (If car connected)
* OhmeAccountInfoCoordinator (1m refresh)
    * Switches: Lock buttons, require approval,  sleep when inactive and enable price cap
    * Inputs: Price cap
* OhmeAdvancedSettingsCoordinator (1m refresh)
    * Sensors: CT reading sensor
    * Binary Sensors: Charger online
* OhmeStatisticsCoordinator (30m refresh)
    * Sensors: Accumulative energy usage
* OhmeChargeSchedulesCoordinator (10m refresh)
    * Inputs: Target time, target percentage and preconditioning (If car disconnected)
