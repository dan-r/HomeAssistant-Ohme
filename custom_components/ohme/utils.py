from time import time
from datetime import datetime, timedelta
from .const import DOMAIN, DATA_OPTIONS
import pytz


def _format_charge_graph(charge_start, points):
    """Convert relative time in points array to real timestamp (s)."""

    charge_start = round(charge_start / 1000)
    return [{"t": x["x"] + charge_start, "y": x["y"]} for x in points]


def charge_graph_next_slot(charge_start, points, skip_format=False):
    """Get the next charge slot start/end times from a list of graph points."""
    now = int(time())
    data = points if skip_format else _format_charge_graph(charge_start, points)

    # Filter to points from now onwards
    data = [x for x in data if x["t"] > now]

    # Give up if we have less than 2 points
    if len(data) < 2:
        return {"start": None, "end": None}

    start_ts = None
    end_ts = None

    # Loop through every remaining value, skipping the last
    for idx in range(0, len(data) - 1):
        # Calculate the delta between this element and the next
        delta = data[idx + 1]["y"] - data[idx]["y"]

        # If the next point has a Y delta of 10+, consider this the start of a slot
        # This should be 0+ but I had some strange results in testing... revisit
        if delta > 10 and not start_ts:
            # 1s added here as it otherwise often rounds down to xx:59:59
            start_ts = data[idx]["t"] + 1

        # Take the first delta of 0 as the end
        if delta == 0 and not end_ts:
            end_ts = data[idx]["t"] + 1

    # These need to be presented with tzinfo or Home Assistant will reject them
    return {
        "start": datetime.utcfromtimestamp(start_ts).replace(tzinfo=pytz.utc) if start_ts else None,
        "end": datetime.utcfromtimestamp(end_ts).replace(tzinfo=pytz.utc) if end_ts else None,
    }


def charge_graph_in_slot(charge_start, points, skip_format=False):
    """Are we currently in a charge slot?"""
    now = int(time())
    data = points if skip_format else _format_charge_graph(charge_start, points)

    # Loop through every value, skipping the last
    for idx in range(0, len(data) - 1):
        # This is our current point
        if data[idx]["t"] < now and data[idx + 1]["t"] > now:
            # If the delta line we are on is steeper than 10,
            # we are in a charge slot.
            if data[idx + 1]["y"] - data[idx]["y"] > 10:
                return True
            break

    return False


def time_next_occurs(hour, minute):
    """Find when this time next occurs."""
    current = datetime.now()
    target = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    while target <= current:
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

def get_option(hass, option):
    """Return option value, default to False."""
    return hass.data[DOMAIN][DATA_OPTIONS].get(option, None)
