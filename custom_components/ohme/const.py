"""Component constants"""
DOMAIN = "ohme"
USER_AGENT = "dan-r-homeassistant-ohme"
INTEGRATION_VERSION = "0.5.3"
CONFIG_VERSION = 1
ENTITY_TYPES = ["sensor", "binary_sensor", "switch", "button", "number", "time"]

DATA_CLIENT = "client"
DATA_COORDINATORS = "coordinators"
DATA_OPTIONS = "options"

COORDINATOR_CHARGESESSIONS = 0
COORDINATOR_ACCOUNTINFO = 1
COORDINATOR_STATISTICS = 2
COORDINATOR_ADVANCED = 3
COORDINATOR_SCHEDULES = 4