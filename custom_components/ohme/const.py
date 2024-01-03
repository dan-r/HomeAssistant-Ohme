"""Component constants"""
import voluptuous as vol

DOMAIN = "ohme"
USER_AGENT = "dan-r-homeassistant-ohme"
INTEGRATION_VERSION = "0.2.8"
CONFIG_SCHEMA = vol.Schema({
    vol.Required("email"): str,
    vol.Required("password"): str
})

DATA_CLIENT = "client"
DATA_COORDINATORS = "coordinators"
COORDINATOR_CHARGESESSIONS = 0
COORDINATOR_ACCOUNTINFO = 1
COORDINATOR_STATISTICS = 2
COORDINATOR_ADVANCED = 3
COORDINATOR_SCHEDULES = 4
