from time import time
from datetime import datetime, timedelta
from .const import DOMAIN, DATA_OPTIONS
import pytz
# import logging
# _LOGGER = logging.getLogger(__name__)

def _format_charge_graph(charge_start, points):
    """Convert relative time in points array to real timestamp (s)."""

    charge_start = round(charge_start / 1000)

    # _LOGGER.debug("Charge slot graph points: " + str([{"t": datetime.fromtimestamp(x["x"] + charge_start).strftime('%H:%M:%S'), "y": x["y"]} for x in points]))

    return [{"t": x["x"] + charge_start, "y": x["y"]} for x in points]


def _sanitise_points(points):
    """Discard any points that aren't on a quarter-hour boundary."""
    output = []
    seen = []
    high = max([x['y'] for x in points])

    points.reverse()

    for point in points:
        # Round up the timestamp and get the minute
        ts = point['t'] + 30
        dt = datetime.fromtimestamp(ts)
        hm = dt.strftime('%H:%M')
        m = int(dt.strftime('%M'))

        # If this point is on a 15m boundary and we haven't seen this time before
        # OR y == yMax - so we don't miss the end of the last slot
        if (m % 15 == 0 and hm not in seen) or point['y'] == high:
            output.append(point)
            seen.append(hm)

    output.reverse()
    # _LOGGER.warning("Charge slot graph points: " + str([{"t": datetime.fromtimestamp(x["t"] + 30).strftime('%H:%M:%S'), "y": x["y"]} for x in output]))

    return output


def _next_slot(data, live=False, in_progress=False):
    """Get the next slot. live is whether or not we may start mid charge. Eg: For the next slot end sensor, we dont have the
       start but still want the end of the in progress session, but for the slot list sensor we only want slots that have
       a start AND an end."""
    start_ts = None
    start_ts_y = 0
    end_ts = None
    end_ts_y = 0

    # Loop through every remaining value, skipping the last
    for idx in range(0, len(data) - 1):
        # Calculate the delta between this element and the next
        delta = data[idx + 1]["y"] - data[idx]["y"]
        delta = 0 if delta < 0 else delta # Zero floor deltas

        # If the next point has a Y delta of 10+, consider this the start of a slot
        # This should be 0+ but I had some strange results in testing... revisit
        if delta > 10 and not start_ts:
            # 1s added here as it otherwise often rounds down to xx:59:59
            start_ts = data[idx]["t"] + 1
            start_ts_y = data[idx]["y"]
        
        # If we are working live, in a time slot and haven't seen an end yet,
        # disregard.
        if start_ts and live and in_progress and not end_ts:
            start_ts = None

        # Take the first delta of 0 as the end
        if delta == 0 and data[idx]["y"] != 0 and (start_ts or live) and not end_ts:
            end_ts = data[idx]["t"] + 1
            end_ts_y = data[idx]["y"]

        if start_ts and end_ts:
            break
    
    return [start_ts, end_ts, idx, end_ts_y - start_ts_y]


def charge_graph_next_slot(charge_start, points, skip_format=False):
    """Get the next charge slot start/end times from a list of graph points."""
    now = int(time())
    data = points if skip_format else _format_charge_graph(charge_start, points)
    in_progress = charge_graph_in_slot(charge_start, data, skip_format=True)

    # Filter to points from now onwards
    data = [x for x in data if x["t"] > now]

    # Give up if we have less than 2 points
    if len(data) < 2:
        return {"start": None, "end": None}

    start_ts, end_ts, _, _ = _next_slot(data, live=True, in_progress=in_progress)

    # These need to be presented with tzinfo or Home Assistant will reject them
    return {
        "start": datetime.utcfromtimestamp(start_ts).replace(tzinfo=pytz.utc) if start_ts else None,
        "end": datetime.utcfromtimestamp(end_ts).replace(tzinfo=pytz.utc) if end_ts else None,
    }


def charge_graph_slot_list(charge_start, points, skip_format=False):
    """Get list of charge slots from graph points."""
    data = points if skip_format else _format_charge_graph(charge_start, points)

    # Don't return any slots if charge is over
    if charge_graph_next_slot(charge_start, points)['end'] is None:
        return []

    data = _sanitise_points(data)

    # Give up if we have less than 2 points
    if len(data) < 2:
        return []

    slots = []

    # While we still have data, keep looping
    while len(data) > 1:
        # Get the next slot
        result = _next_slot(data)

        # Break if we fail
        if result[0] is None or result[1] is None:
            break
        
        # Append a dict to the slots list with the start and end time
        slots.append(
            {
                "start": datetime.utcfromtimestamp(result[0]).replace(tzinfo=pytz.utc).astimezone(),
                "end": datetime.utcfromtimestamp(result[1]).replace(tzinfo=pytz.utc).astimezone(),
                "charge_in_kwh": -(result[3] / 1000),
                "source": "smart-charge",
                "location": None
            }
        )

        # Cut off where we got to in this iteration for next time
        data = data[result[2]:]

    return slots


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
