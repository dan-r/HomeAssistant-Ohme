from time import time
from datetime import datetime
import pytz

def charge_graph_next_slot(charge_start, points):
    """Get the next charge slot from a list of graph points."""
    # Get start and current timestamp in seconds
    charge_start = round(charge_start / 1000)
    now = int(time())
    
    # Replace relative timestamp (seconds) with real timestamp
    data = [{"t": x["x"] + charge_start, "y": x["y"]} for x in points]
    
    # Filter to points from now onwards
    data = [x for x in data if x["t"] > now]
    
    # Give up if we have less than 3 points
    if len(data) < 3:
        return None

    next_ts = None

    # Loop through every remaining value, skipping the last
    for idx in range(0, len(data) - 1):
        # Calculate the delta between this element and the next
        delta = data[idx + 1]["y"] - data[idx]["y"]

        # If the next point has a Y delta of 10+, consider this the start of a slot
        # This should be 0+ but I had some strange results in testing... revisit
        if delta > 10:
            next_ts = data[idx]["t"]
            break

    # This needs to be presented with tzinfo or Home Assistant will reject it
    return None if next_ts is None else datetime.utcfromtimestamp(next_ts).replace(tzinfo=pytz.utc)

