# Ohme EV Charger for Home Assistant

A basic integration for interacting with Ohme EV Chargers.

This is an unofficial integration. I have no affiliation with Ohme besides owning one of their EV chargers.

This has only be tested with an Ohme Home Pro and does not currently support social login or accounts with multiple chargers.

It's still very early in development but I plan to add more sensors and support for pausing/resuming charge.

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