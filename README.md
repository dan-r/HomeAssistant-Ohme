
## Important Note
As of Home Assistant 2025.1, there is now an [Ohme integration](https://www.home-assistant.io/integrations/ohme/) built into the Home Assistant Core. This means you no longer need to install this integration and can simply add your Ohme account through the Home Assistant UI. As a result, this integration is no longer being actively maintained.

The core version of the integration is effectively a ground-up rewrite to follow all the Home Assistant conventions and generally try to maintain a better quality user experience. Because of the amount of work this involves, there is currently a feature gap between custom and core versions, but I'm working to shrink this and am contributing new features to the core gradually. Some things are done differently in the core version (such as different sensor names and having a few of the binary sensors collapsed into an enum sensor), so moving to it may be disruptive if you have working automations.

For the core version of the integration, please raise any issues and pull requests in the [Home Assistant Core](https://github.com/home-assistant/core) repository. The API library is seperate from Home Assistant and can be found in the [ohmepy](https://github.com/dan-r/ohmepy) repository.

Thank you to the community that has formed around this integration, and I hope you can appreciate this important and necessary evolution of the integration.

### Migrating
To migrate from the custom component to the core integration:
1. Ensure you are running an up to date version of Home Assistant
2. Delete your Ohme account from the Home Assistant Devices & services page
3. Uninstall the custom component. If you installed through HACS, you can do this through the UI
4. Restart Home Assistant
5. Configure the core Ohme integration

<br></br>

# Ohme EV Charger for Home Assistant

An unofficial integration for interacting with Ohme EV Chargers. I have no affiliation with Ohme besides owning one of their EV chargers.

This integration does not currently support accounts with multiple chargers.

If you find any bugs or would like to request a feature, please open an issue.

## Tested Hardware
This integration has been tested with the following hardware:
* Ohme Home Pro
* Ohme Home
* Ohme Go
* Ohme ePod

## External Software
The 'Charge Slot Active' binary sensor mimics the `planned_dispatches` and `completed_dispatches` attributes from the [Octopus Energy](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy) integration, so should support external software which reads this such as [predbat](https://springfall2008.github.io/batpred/devices/#ohme).


## Installation

### HACS
This is the recommended installation method.
1. Search for and install the Ohme addon from HACS
2. Restart Home Assistant

### Manual
1. Download the [latest release](https://github.com/dan-r/HomeAssistant-Ohme/releases)
2. Copy the contents of `custom_components` into the `<config directory>/custom_components` directory of your Home Assistant installation
3. Restart Home Assistant


## Setup
From the Home Assistant Integrations page, search for and add the Ohme integration.

### Social Logins
If you created your Ohme account through an Apple, Facebook or Google account, you will need to set a password to use this integration.

Visit the [password reset](https://api.ohme.io/fleet/index.html#/authentication/forgotten-password) page and enter the email address associated with your social account. You can then use this new password to log into the integration.

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
    * Energy Usage (kWh) - Energy used in the current/last session. *This is supported by the energy dashboard.*
    * Battery State of Charge (%) - If your car is API connected this is read from the car, if not it is how much charge Ohme thinks it has added
* Switches (Settings) - **Only options available to your charger model will show**
    * Lock Buttons - Locks buttons on charger
    * Require Approval - Require approval to start a charge
    * Sleep When Inactive - Charger screen & lights will automatically turn off
    * Solar Boost
* Switches (Charge state) - **These are only functional when a car is connected**
    * Max Charge - Forces the connected car to charge regardless of set schedule
    * Pause Charge - Pauses an ongoing charge
    * Enable Price Cap - Whether price cap is applied. _Due to changes by Ohme, this will not show for Intelligent Octopus users._
* Inputs - **If in a charge session, these change the active charge. If disconnected, they change your first schedule.**
    * Number
        * Target Percentage - Change the target battery percentage
        * Preconditioning - Change pre-conditioning time. 0 is off
        * Price Cap - Maximum charge price. _Due to changes by Ohme, this will not show for Intelligent Octopus users._
    * Time
        * Target Time - Change the target time
* Buttons
    * Approve Charge - Approves a charge when 'Pending Approval' is on

## Options
Some options can be set from the 'Configure' menu in Home Assistant:
* Never update an ongoing session - Override the default behaviour of the target time, percentage and preconditioning inputs and only ever update the schedule, not the current session. This was added as changing the current session can cause issues for customers on Intelligent Octopus Go.
* Don't collapse charge slots - By default, adjacent slots are merged into one. This option shows every slot, as shown in the Ohme app.
* Refresh Intervals - The refresh interval for the four coordinators listed below can be configured manually. The default times also serve as minimums, as to be respectful to Ohme, but you can choose to fetch data less frequently.


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
* OhmeChargeSchedulesCoordinator (10m refresh)
    * Inputs: Target time, target percentage and preconditioning (If car disconnected)
