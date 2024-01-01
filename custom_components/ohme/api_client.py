import aiohttp
import logging
import json
from time import time
from datetime import datetime, timedelta
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN
from .utils import time_next_occurs

_LOGGER = logging.getLogger(__name__)

GOOGLE_API_KEY = "AIzaSyC8ZeZngm33tpOXLpbXeKfwtyZ1WrkbdBY"


class OhmeApiClient:
    """API client for Ohme EV chargers."""

    def __init__(self, email, password):
        if email is None or password is None:
            raise Exception("Credentials not provided")

        # Credentials from configuration
        self._email = email
        self._password = password

        # Charger and its capabilities
        self._device_info = None
        self._capabilities = {}
        self._ct_connected = False

        # Authentication
        self._token_birth = 0
        self._token = None
        self._refresh_token = None

        # User info
        self._user_id = ""
        self._serial = ""

        # Cache the last rule to use when we disable max charge or change schedule
        self._last_rule = {}

        # Sessions
        self._session = aiohttp.ClientSession(
            base_url="https://api.ohme.io")
        self._auth_session = aiohttp.ClientSession()

    # Auth methods

    async def async_create_session(self):
        """Refresh the user auth token from the stored credentials."""
        async with self._auth_session.post(
            f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={GOOGLE_API_KEY}",
            data={"email": self._email, "password": self._password,
                  "returnSecureToken": True}
        ) as resp:
            if resp.status != 200:
                return None

            resp_json = await resp.json()
            self._token_birth = time()
            self._token = resp_json['idToken']
            self._refresh_token = resp_json['refreshToken']
            return True

    async def async_refresh_session(self):
        """Refresh auth token if needed."""
        if self._token is None:
            return await self.async_create_session()

        # Don't refresh token unless its over 45 mins old
        if time() - self._token_birth < 2700:
            return

        async with self._auth_session.post(
            f"https://securetoken.googleapis.com/v1/token?key={GOOGLE_API_KEY}",
            data={"grantType": "refresh_token",
                  "refreshToken": self._refresh_token}
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                msg = f"Ohme auth refresh error: {text}"
                _LOGGER.error(msg)
                raise AuthException(msg)

            resp_json = await resp.json()
            self._token_birth = time()
            self._token = resp_json['id_token']
            self._refresh_token = resp_json['refresh_token']
            return True

    # Internal methods

    def _last_second_of_month_timestamp(self):
        """Get the last second of this month."""
        dt = datetime.today()
        dt = dt.replace(day=1) + timedelta(days=32)
        dt = dt.replace(day=1, hour=0, minute=0, second=0,
                        microsecond=0) - timedelta(seconds=1)
        return int(dt.timestamp()*1e3)

    async def _handle_api_error(self, url, resp):
        """Raise an exception if API response failed."""
        if resp.status != 200:
            text = await resp.text()
            msg = f"Ohme API response error: {url}, {resp.status}; {text}"
            _LOGGER.error(msg)
            raise ApiException(msg)

    def _get_headers(self):
        """Get auth and content-type headers"""
        return {
            "Authorization": "Firebase %s" % self._token,
            "Content-Type": "application/json"
        }

    async def _post_request(self, url, skip_json=False, data=None):
        """Make a POST request."""
        await self.async_refresh_session()
        async with self._session.post(
            url,
            data=data,
            headers=self._get_headers()
        ) as resp:
            _LOGGER.debug(f"POST request to {url}, status code {resp.status}")
            await self._handle_api_error(url, resp)

            if skip_json:
                return await resp.text()

            return await resp.json()

    async def _put_request(self, url, data=None):
        """Make a PUT request."""
        await self.async_refresh_session()
        async with self._session.put(
            url,
            data=json.dumps(data),
            headers=self._get_headers()
        ) as resp:
            _LOGGER.debug(f"PUT request to {url}, status code {resp.status}")
            await self._handle_api_error(url, resp)

            return True

    async def _get_request(self, url):
        """Make a GET request."""
        await self.async_refresh_session()
        async with self._session.get(
            url,
            headers=self._get_headers()
        ) as resp:
            _LOGGER.debug(f"GET request to {url}, status code {resp.status}")
            await self._handle_api_error(url, resp)

            return await resp.json()

    # Simple getters

    def ct_connected(self):
        """Is CT clamp connected."""
        return self._ct_connected

    def is_capable(self, capability):
        """Return whether or not this model has a given capability."""
        return bool(self._capabilities[capability])

    def get_device_info(self):
        return self._device_info

    def get_unique_id(self, name):
        return f"ohme_{self._serial}_{name}"

    # Push methods

    async def async_pause_charge(self):
        """Pause an ongoing charge"""
        result = await self._post_request(f"/v1/chargeSessions/{self._serial}/stop", skip_json=True)
        return bool(result)

    async def async_resume_charge(self):
        """Resume a paused charge"""
        result = await self._post_request(f"/v1/chargeSessions/{self._serial}/resume", skip_json=True)
        return bool(result)

    async def async_approve_charge(self):
        """Approve a charge"""
        result = await self._put_request(f"/v1/chargeSessions/{self._serial}/approve?approve=true")
        return bool(result)

    async def async_max_charge(self):
        """Enable max charge"""
        result = await self._put_request(f"/v1/chargeSessions/{self._serial}/rule?maxCharge=true")
        return bool(result)

    async def async_apply_charge_rule(self, max_price=None, target_time=None, target_percent=None, pre_condition=None, pre_condition_length=None):
        """Apply charge rule/stop max charge."""
        # Check every property. If we've provided it, use that. If not, use the existing.
        if max_price is None:
            max_price = self._last_rule['settings'][0]['enabled'] if 'settings' in self._last_rule and len(
                self._last_rule['settings']) > 1 else False

        if target_percent is None:
            target_percent = self._last_rule['targetPercent'] if 'targetPercent' in self._last_rule else 80

        if pre_condition is None:
            pre_condition = self._last_rule['preconditioningEnabled'] if 'preconditioningEnabled' in self._last_rule else False

        if pre_condition_length is None:
            pre_condition_length = self._last_rule[
                'preconditionLengthMins'] if 'preconditionLengthMins' in self._last_rule else 30

        if target_time is None:
            # Default to 9am
            target_time = self._last_rule['targetTime'] if 'targetTime' in self._last_rule else 32400
            target_time = (target_time // 3600,
                           (target_time % 3600) // 60)

        target_ts = int(time_next_occurs(
            target_time[0], target_time[1]).timestamp() * 1000)

        # Convert these to string form
        max_price = 'true' if max_price else 'false'
        pre_condition = 'true' if pre_condition else 'false'

        result = await self._put_request(f"/v1/chargeSessions/{self._serial}/rule?enableMaxPrice={max_price}&targetTs={target_ts}&enablePreconditioning={pre_condition}&toPercent={target_percent}&preconditionLengthMins={pre_condition_length}")
        return bool(result)

    async def async_set_configuration_value(self, values):
        """Set a configuration value or values."""
        result = await self._put_request(f"/v1/chargeDevices/{self._serial}/appSettings", data=values)
        return bool(result)

    # Pull methods

    async def async_get_charge_sessions(self, is_retry=False):
        """Try to fetch charge sessions endpoint.
           If we get a non 200 response, refresh auth token and try again"""
        resp = await self._get_request('/v1/chargeSessions')
        resp = resp[0]

        # Cache the current rule if we are given it
        if resp["mode"] == "SMART_CHARGE" and 'appliedRule' in resp:
            self._last_rule = resp["appliedRule"]

        return resp

    async def async_get_account_info(self):
        resp = await self._get_request('/v1/users/me/account')

        return resp

    async def async_update_device_info(self, is_retry=False):
        """Update _device_info with our charger model."""
        resp = await self.async_get_account_info()

        device = resp['chargeDevices'][0]

        info = DeviceInfo(
            identifiers={(DOMAIN, "ohme_charger")},
            name=device['modelTypeDisplayName'],
            manufacturer="Ohme",
            model=device['modelTypeDisplayName'].replace("Ohme ", ""),
            sw_version=device['firmwareVersionLabel'],
            serial_number=device['id']
        )

        self._capabilities = device['modelCapabilities']
        self._user_id = resp['user']['id']
        self._serial = device['id']
        self._device_info = info

        return True

    async def async_get_charge_statistics(self):
        """Get charge statistics. Currently this is just for all time (well, Jan 2019)."""
        end_ts = self._last_second_of_month_timestamp()
        resp = await self._get_request(f"/v1/chargeSessions/summary/users/{self._user_id}?&startTs=1546300800000&endTs={end_ts}&granularity=MONTH")

        return resp['totalStats']

    async def async_get_ct_reading(self):
        """Get CT clamp reading."""
        resp = await self._get_request(f"/v1/chargeDevices/{self._serial}/advancedSettings")

        # If we ever get a reading above 0, assume CT connected
        if resp['clampAmps'] and resp['clampAmps'] > 0:
            self._ct_connected = True

        return resp['clampAmps']


# Exceptions
class ApiException(Exception):
    ...


class AuthException(ApiException):
    ...
