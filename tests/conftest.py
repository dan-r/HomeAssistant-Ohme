"""Provide common fixtures."""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.common import MockConfigEntry, load_json_value_fixture
from custom_components.ohme.const import DOMAIN
import json

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield

@pytest.fixture(name="mock_session")
def mock_session():
    """Mock aiohttp.ClientSession."""
    mocker = AiohttpClientMocker()

    mocker.post(
        "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword",
        json={"idToken":"", "refreshToken":""}
    )

    mocker.get(
        "/v1/users/me/account",
        json=load_json_value_fixture("account.json", DOMAIN)
    )

    mocker.get(
        "/v1/chargeSessions",
        json=load_json_value_fixture("charge_sessions.json", DOMAIN)
    )

    mocker.get(
        "/v1/chargeRules",
        json=load_json_value_fixture("charge_rules.json", DOMAIN)
    )

    mocker.get(
        "/v1/chargeDevices/chargerid/advancedSettings",
        json=load_json_value_fixture("advanced_settings.json", DOMAIN)
    )

    with patch(
        "aiohttp.ClientSession",
        side_effect=lambda *args, **kwargs: mocker.create_session(
            asyncio.get_event_loop()
        ),
    ):
        yield mocker
