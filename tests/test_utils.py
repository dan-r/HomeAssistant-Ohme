"""Tests for the utils."""
from unittest import mock
import random
from time import time

from custom_components.ohme import utils


async def test_format_charge_graph(hass):
    """Test that the _test_format_charge_graph function adds given timestamp / 1000 to each x coordinate."""
    TEST_DATA = [{"x": 10, "y": 0}, {"x": 20, "y": 0},
                 {"x": 30, "y": 0}, {"x": 40, "y": 0}]

    start_time = random.randint(1577836800, 1764547200)  # 2020-2025
    start_time_ms = start_time * 1000

    result = utils._format_charge_graph(start_time_ms, TEST_DATA)
    expected = [{"t": TEST_DATA[0]['x'] + start_time, "y": mock.ANY},
                {"t": TEST_DATA[1]['x'] + start_time, "y": mock.ANY},
                {"t": TEST_DATA[2]['x'] + start_time, "y": mock.ANY},
                {"t": TEST_DATA[3]['x'] + start_time, "y": mock.ANY}]

    assert expected == result


async def test_charge_graph_next_slot(hass):
    """Test that we correctly work out when the next slot starts and ends."""
    start_time = int(time())
    TEST_DATA = [{"t": start_time - 100, "y": 0},
                 {"t": start_time + 1000, "y": 0},
                 {"t": start_time + 1600, "y": 1000},
                 {"t": start_time + 1800, "y": 1000}]

    result = utils.charge_graph_next_slot(0, TEST_DATA, skip_format=True)
    result = {
        "start": result['start'].timestamp(),
        "end": result['end'].timestamp(),
    }

    expected = {
        "start": start_time + 1001,
        "end": start_time + 1601,
    }

    assert expected == result


async def test_charge_graph_in_slot(hass):
    """Test that we correctly intepret outselves as in a slot."""
    start_time = int(time())
    TEST_DATA = [{"t": start_time - 100, "y": 0},
                 {"t": start_time - 10, "y": 0},
                 {"t": start_time + 200, "y": 1000},
                 {"t": start_time + 300, "y": 1000}]

    result = utils.charge_graph_in_slot(0, TEST_DATA, skip_format=True)
    expected = True

    assert expected == result


async def test_next_slot_no_live_no_in_progress():
    """Test that the _next_slot function returns the correct result when live and in_progress are False."""
    TEST_DATA = [{"t": 10, "y": 0}, {"t": 20, "y": 0},
            {"t": 30, "y": 10}, {"t": 40, "y": 20},
            {"t": 50, "y": 20}, {"t": 60, "y": 0}]

    result = utils._next_slot(TEST_DATA, live=False, in_progress=False)
    expected = [30, 50, 3, 10]

    assert expected == result


async def test_next_slot_live_no_in_progress():
    """Test that the _next_slot function returns the correct result when live is True and in_progress is False."""
    TEST_DATA = [{"t": 10, "y": 0}, {"t": 20, "y": 0},
            {"t": 30, "y": 10}, {"t": 40, "y": 20},
            {"t": 50, "y": 20}, {"t": 60, "y": 0}]

    result = utils._next_slot(TEST_DATA, live=True, in_progress=False)
    expected = [30, 50, 3, 10]

    assert expected == result


async def test_next_slot_no_live_in_progress():
    """Test that the _next_slot function returns the correct result when live is False and in_progress is True."""
    TEST_DATA = [{"t": 10, "y": 0}, {"t": 20, "y": 0},
            {"t": 30, "y": 10}, {"t": 40, "y": 20},
            {"t": 50, "y": 20}, {"t": 60, "y": 0}]

    result = utils._next_slot(TEST_DATA, live=False, in_progress=True)
    expected = [None, None, None, 0]

    assert expected == result


async def test_next_slot_live_in_progress():
    """Test that the _next_slot function returns the correct result when live and in_progress are True."""
    TEST_DATA = [{"t": 10, "y": 0}, {"t": 20, "y": 0},
            {"t": 30, "y": 10}, {"t": 40, "y": 20},
            {"t": 50, "y": 20}, {"t": 60, "y": 0}]

    result = utils._next_slot(TEST_DATA, live=True, in_progress=True)
    expected = [None, None, None, 0]

    assert expected == result
