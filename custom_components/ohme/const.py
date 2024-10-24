"""Component constants"""
DOMAIN = "ohme"
USER_AGENT = "dan-r-homeassistant-ohme"
INTEGRATION_VERSION = "1.0.0"
CONFIG_VERSION = 1
ENTITY_TYPES = ["sensor", "binary_sensor", "switch", "button", "number", "time"]

DATA_CLIENT = "client"
DATA_COORDINATORS = "coordinators"
DATA_OPTIONS = "options"
DATA_SLOTS = "slots"

COORDINATOR_CHARGESESSIONS = 0
COORDINATOR_ACCOUNTINFO = 1
COORDINATOR_ADVANCED = 2
COORDINATOR_SCHEDULES = 3
