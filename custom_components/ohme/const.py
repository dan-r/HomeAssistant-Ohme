"""Component constants"""
DOMAIN = "ohme"
USER_AGENT = "dan-r-homeassistant-ohme"
INTEGRATION_VERSION = "0.7.1"
CONFIG_VERSION = 1
ENTITY_TYPES = ["sensor", "binary_sensor", "switch", "button", "number", "time"]

DATA_CLIENT = "client"
DATA_COORDINATORS = "coordinators"
DATA_OPTIONS = "options"
DATA_SLOTS = "slots"

COORDINATOR_CHARGESESSIONS = 0
COORDINATOR_ACCOUNTINFO = 1
COORDINATOR_STATISTICS = 2
COORDINATOR_ADVANCED = 3
COORDINATOR_SCHEDULES = 4