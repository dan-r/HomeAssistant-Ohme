from time import time
from datetime import datetime, timedelta
from .const import DOMAIN, DATA_OPTIONS
import pytz
# import logging
# _LOGGER = logging.getLogger(__name__)


def next_slot(data):
    """Get the next charge slot start/end times."""
    slots = slot_list(data)
    start = None
    end = None

    # Loop through slots
    for slot in slots:
        # Only take the first slot start/end that matches. These are in order.
        if start is None and slot['start'] > datetime.now().astimezone():
            start = slot['start']
        if end is None and slot['end'] > datetime.now().astimezone():
            end = slot['end']
    
    return {
        "start": start,
        "end": end
    }


def slot_list(data):
    """Get list of charge slots."""
    session_slots = data['allSessionSlots']
    if session_slots is None or len(session_slots) == 0:
        return []
    
    slots = []
    wh_tally = 0
    
    if 'batterySocBefore' in data and data['batterySocBefore'] is not None:
        wh_tally = data['batterySocBefore']['wh'] # Get the wh value we start from

    for slot in session_slots:
        slots.append(
            {
                "start": datetime.utcfromtimestamp(slot['startTimeMs'] / 1000).replace(tzinfo=pytz.utc, microsecond=0).astimezone(),
                "end": datetime.utcfromtimestamp(slot['endTimeMs'] / 1000).replace(tzinfo=pytz.utc, microsecond=0).astimezone(),
                "charge_in_kwh": -((slot['estimatedSoc']['wh'] - wh_tally) / 1000), # Work out how much we add in just this slot
                "source": "smart-charge",
                "location": None
            }
        )
        
        wh_tally = slot['estimatedSoc']['wh']

    return slots


def in_slot(data):
    """Are we currently in a charge slot?"""
    slots = slot_list(data)

    # Loop through slots
    for slot in slots:
        # If we are in one
        if slot['start'] < datetime.now().astimezone() and slot['end'] > datetime.now().astimezone():
            return True
    
    return False


def time_next_occurs(hour, minute):
    """Find when this time next occurs."""
    current = datetime.now()
    target = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= datetime.now():
        target = target + timedelta(days=1)

    return target


def session_in_progress(hass, data):
    """Is there a session in progress?
       Used to check if we should update the current session rather than the first schedule."""
    # If config option set, never update session specific schedule
    if get_option(hass, "never_session_specific"):
        return False
    
    # Default to False with no data
    if not data:
        return False
    
    # Car disconnected or pending approval, we should update the schedule
    if data['mode'] == "DISCONNECTED" or data['mode'] == "PENDING_APPROVAL":
        return False
    
    return True


def get_option(hass, option, default=False):
    """Return option value, with settable default."""
    return hass.data[DOMAIN][DATA_OPTIONS].get(option, default)
