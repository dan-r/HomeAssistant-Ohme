import aiohttp
import asyncio
import logging
import json
from datetime import datetime, timedelta
from homeassistant.helpers.entity import DeviceInfo
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OhmeApiClient:
    """API client for Ohme EV chargers."""

    def __init__(self, email, password):
        if email is None or password is None:
            raise Exception("Credentials not provided")

        self._email = email
        self._password = password

        self._device_info = None
        self._token = None
        self._user_id = ""
        self._serial = ""
        self._session = aiohttp.ClientSession()

    async def async_refresh_session(self):
        """Refresh the user auth token from the stored credentials."""
        async with self._session.post(
            'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyC8ZeZngm33tpOXLpbXeKfwtyZ1WrkbdBY',
            data={"email": self._email, "password": self._password,
                  "returnSecureToken": True}
        ) as resp:

            if resp.status != 200:
                return None

            resp_json = await resp.json()
            self._token = resp_json['idToken']
            return True

    async def _post_request(self, url, skip_json=False, data=None, is_retry=False):
        """Try to make a POST request
           If we get a non 200 response, refresh auth token and try again"""
        async with self._session.post(
            url,
            data=data,
            headers={"Authorization": "Firebase %s" % self._token}
        ) as resp:
            if resp.status != 200 and not is_retry:
                await self.async_refresh_session()
                return await self._post_request(url, skip_json=skip_json, data=data, is_retry=True)
            elif resp.status != 200:
                return False

            if skip_json:
                return await resp.text()

            resp_json = await resp.json()
            return resp_json

    async def _put_request(self, url, data=None, is_retry=False):
        """Try to make a PUT request
           If we get a non 200 response, refresh auth token and try again"""
        async with self._session.put(
            url,
            data=data,
            headers={"Authorization": "Firebase %s" % self._token}
        ) as resp:
            if resp.status != 200 and not is_retry:
                await self.async_refresh_session()
                return await self._put_request(url, data=data, is_retry=True)
            elif resp.status != 200:
                return False

            return True

    async def _get_request(self, url, is_retry=False):
        """Try to make a GET request
           If we get a non 200 response, refresh auth token and try again"""
        async with self._session.get(
            url,
            headers={"Authorization": "Firebase %s" % self._token}
        ) as resp:
            if resp.status != 200 and not is_retry:
                await self.async_refresh_session()
                return await self._get_request(url, is_retry=True)
            elif resp.status != 200:
                return False

            return await resp.json()

    async def async_pause_charge(self):
        """Pause an ongoing charge"""
        result = await self._post_request(f"https://api.ohme.io/v1/chargeSessions/{self._serial}/stop", skip_json=True)
        return bool(result)

    async def async_resume_charge(self):
        """Resume a paused charge"""
        result = await self._post_request(f"https://api.ohme.io/v1/chargeSessions/{self._serial}/resume", skip_json=True)
        return bool(result)

    async def async_max_charge(self):
        """Enable max charge"""
        result = await self._put_request(f"https://api.ohme.io/v1/chargeSessions/{self._serial}/rule?maxCharge=true")
        return bool(result)

    async def async_stop_max_charge(self):
        """Stop max charge.
           This is more complicated than starting one as we need to give more parameters."""
        result = await self._put_request(f"https://api.ohme.io/v1/chargeSessions/{self._serial}/rule?enableMaxPrice=false&toPercent=80.0&inSeconds=43200")
        return bool(result)

    async def async_get_charge_sessions(self, is_retry=False):
        """Try to fetch charge sessions endpoint.
           If we get a non 200 response, refresh auth token and try again"""
        resp = await self._get_request('https://api.ohme.io/v1/chargeSessions')

        if not resp:
            return False

        return resp[0]

    async def async_update_device_info(self, is_retry=False):
        """Update _device_info with our charger model."""
        resp = await self._get_request('https://api.ohme.io/v1/users/me/account')

        if not resp:
            return False

        device = resp['chargeDevices'][0]

        info = DeviceInfo(
            identifiers={(DOMAIN, "ohme_charger")},
            name=device['modelTypeDisplayName'],
            manufacturer="Ohme",
            model=device['modelTypeDisplayName'].replace("Ohme ", ""),
            sw_version=device['firmwareVersionLabel'],
            serial_number=device['id']
        )

        self._user_id = resp['user']['id']
        self._serial = device['id']
        self._device_info = info

        return True

    def _last_second_of_month_timestamp(self):
        """Get the last second of this month."""
        dt = datetime.today()
        dt = dt.replace(day=1) + timedelta(days=32)
        dt = dt.replace(day=1, hour=0, minute=0, second=0,
                        microsecond=0) - timedelta(seconds=1)
        return int(dt.timestamp()*1e3)

    async def async_get_charge_statistics(self):
        """Get charge statistics. Currently this is just for all time (well, Jan 2019)."""
        end_ts = self._last_second_of_month_timestamp()
        resp = await self._get_request(f"https://api.ohme.io/v1/chargeSessions/summary/users/{self._user_id}?&startTs=1546300800000&endTs={end_ts}&granularity=MONTH")

        if not resp:
            return False

        return resp['totalStats']

    def get_device_info(self):
        return self._device_info

    def get_unique_id(self, name):
        return f"ohme_{self._serial}_{name}"
