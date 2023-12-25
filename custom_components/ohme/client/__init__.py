import aiohttp
import asyncio
import logging
import json
from homeassistant.helpers.entity import DeviceInfo
from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class OhmeApiClient:
  def __init__(self, email, password):
    if email is None or password is None:
      raise Exception("Credentials not provided")
    
    self._email = email
    self._password = password

    self._device_info = None
    self._token = None

  async def async_refresh_session(self):
    async with aiohttp.ClientSession() as session:
      async with session.post(
            'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyC8ZeZngm33tpOXLpbXeKfwtyZ1WrkbdBY',
            data={"email": self._email, "password": self._password, "returnSecureToken": True}
            ) as resp:

        if resp.status != 200:
          return None

        resp_json = await resp.json()
        self._token = resp_json['idToken']
        return True

  async def async_get_charge_sessions(self, is_retry=False):
    """Try to fetch charge sessions endpoint.
       If we get a non 200 response, refresh auth token and try again"""
    async with aiohttp.ClientSession() as session:
      async with session.get(
            'https://api.ohme.io/v1/chargeSessions',
            headers={"Authorization": "Firebase %s" % self._token}
            ) as resp:

        if resp.status != 200 and not is_retry:
          await self.async_refresh_session()
          return self.async_get_charge_sessions(True)
        elif resp.status != 200:
          return False

        resp_json = await resp.json()
        return resp_json[0]

  async def async_update_device_info(self, is_retry=False):
    async with aiohttp.ClientSession() as session:
      async with session.get(
            'https://api.ohme.io/v1/users/me/account',
            headers={"Authorization": "Firebase %s" % self._token}
            ) as resp:

        if resp.status != 200 and not is_retry:
          await self.async_refresh_session()
          return self.async_get_device_info(True)
        elif resp.status != 200:
          return False

        resp_json = await resp.json()
        device = resp_json['chargeDevices'][0]

        info = DeviceInfo(
            identifiers={(DOMAIN, "ohme_charger")},
            name=device['modelTypeDisplayName'],
            connections=set(),
            manufacturer="Ohme",
            model=device['modelTypeDisplayName'].replace("Ohme ", "")
          )

        self._device_info = info

  def get_device_info(self):
      return self._device_info


