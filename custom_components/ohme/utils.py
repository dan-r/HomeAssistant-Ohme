from functools import reduce
from datetime import datetime, timedelta
from .const import DOMAIN, DATA_OPTIONS
import pytz
# import logging
# _LOGGER = logging.getLogger(__name__)


def next_slot(hass, account_id, data):
    """Get the next charge slot start/end times."""
    slots = slot_list(data)
    collapse_slots = not get_option(hass, account_id, "never_collapse_slots", False)

    start = None
    end = None

    # Loop through slots
    for slot in slots:
        # Only take the first slot start/end that matches. These are in order.
        if end is None and slot['end'] > datetime.now().astimezone():
            end = slot['end']

        if start is None and slot['start'] > datetime.now().astimezone():
            start = slot['start']
        elif collapse_slots and slot['start'] == end:
            end = slot['end']
        elif start is not None and end is not None:
            break

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
    
    if 'batterySocBefore' in data and data['batterySocBefore'] is not None and data['batterySocBefore']['wh'] is not None:
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


def slot_list_str(hass, account_id, slots):
        """Convert slot list to string."""

        # Convert list to tuples of times
        t_slots = []
        for slot in slots:
            t_slots.append((slot['start'].strftime('%H:%M'), slot['end'].strftime('%H:%M')))

        state = []

        if not get_option(hass, account_id, "never_collapse_slots", False):
            # Collapse slots so consecutive slots become one
            for i in range(len(t_slots)):
                if not state or state[-1][1] != t_slots[i][0]:
                    state.append(t_slots[i])
                else:
                    state[-1] = (state[-1][0], t_slots[i][1])
        else:
            state = t_slots
            
        # Convert list of tuples to string
        state = reduce(lambda acc, slot: acc + f"{slot[0]}-{slot[1]}, ", state, "")[:-2]

        # Make sure we return None/Unknown if the list is empty
        return None if state == "" else state


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


def session_in_progress(hass, account_id, data):
    """Is there a session in progress?
       Used to check if we should update the current session rather than the first schedule."""
    # If config option set, never update session specific schedule
    if get_option(hass, account_id, "never_session_specific"):
        return False
    
    # Default to False with no data
    if not data:
        return False
    
    # Car disconnected or pending approval, we should update the schedule
    if data['mode'] == "DISCONNECTED" or data['mode'] == "PENDING_APPROVAL":
        return False
    
    return True


def get_option(hass, account_id, option, default=False):
    """Return option value, with settable default."""
    return hass.data[DOMAIN][account_id][DATA_OPTIONS].get(option, default)
