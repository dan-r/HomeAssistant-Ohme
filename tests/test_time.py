"""Tests for time entity."""

from datetime import time as dt_time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ohme.const import (
    COORDINATOR_CHARGESESSIONS,
    COORDINATOR_SCHEDULES,
    DATA_CLIENT,
    DATA_COORDINATORS,
    DOMAIN,
)
from custom_components.ohme.time import TargetTime, async_setup_entry


@pytest.fixture
def mock_hass():
    """Fixture for creating a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "test@example.com": {
                DATA_COORDINATORS: [
                    MagicMock(async_refresh=AsyncMock()),
                    MagicMock(async_refresh=AsyncMock()),
                    MagicMock(async_refresh=AsyncMock()),
                    MagicMock(async_refresh=AsyncMock()),
                ],
                DATA_CLIENT: MagicMock(
                    async_apply_session_rule=AsyncMock(),
                    async_update_schedule=AsyncMock(),
                ),
            }
        }
    }
    return hass


@pytest.fixture
def mock_config_entry():
    """Fixture for creating a mock config entry."""
    return AsyncMock(data={"email": "test@example.com"})


@pytest.fixture
def mock_async_add_entities():
    """Fixture for creating a mock async_add_entities."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_async_setup_entry(
    mock_hass, mock_config_entry, mock_async_add_entities
) -> None:
    """Test async_setup_entry."""
    await async_setup_entry(mock_hass, mock_config_entry, mock_async_add_entities)
    assert mock_async_add_entities.called


@pytest.fixture
def target_time_entity(mock_hass) -> None:
    """Fixture for creating a target time entity."""
    coordinator = mock_hass.data[DOMAIN]["test@example.com"][DATA_COORDINATORS][
        COORDINATOR_CHARGESESSIONS
    ]
    coordinator_schedules = mock_hass.data[DOMAIN]["test@example.com"][
        DATA_COORDINATORS
    ][COORDINATOR_SCHEDULES]
    client = mock_hass.data[DOMAIN]["test@example.com"][DATA_CLIENT]
    return TargetTime(coordinator, coordinator_schedules, mock_hass, client)


@pytest.mark.asyncio
async def test_async_added_to_hass(target_time_entity) -> None:
    """Test async_added_to_hass."""
    with patch.object(
        target_time_entity.coordinator_schedules,
        "async_add_listener",
        return_value=AsyncMock(),
    ) as mock_add_listener:
        await target_time_entity.async_added_to_hass()
        assert mock_add_listener.called


@pytest.mark.asyncio
async def test_async_set_value(target_time_entity) -> None:
    """Test async_set_value."""
    with patch(
        "custom_components.ohme.time.session_in_progress", return_value=True
    ):
        await target_time_entity.async_set_value(dt_time(12, 30))
        assert target_time_entity._client.async_apply_session_rule.called

    with patch(
        "custom_components.ohme.time.session_in_progress", return_value=False
    ):
        await target_time_entity.async_set_value(dt_time(12, 30))
        assert target_time_entity._client.async_update_schedule.called


def test_native_value(target_time_entity) -> None:
    """Test native_value."""
    target_time_entity._state = dt_time(12, 30)
    assert target_time_entity.native_value == dt_time(12, 30)
