"""The aurora component."""

import logging

from auroranoaa import AuroraForecast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (
    ATTRIBUTION,
    AURORA_API,
    CONF_THRESHOLD,
    COORDINATOR,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_THRESHOLD,
    DOMAIN,
)
from .coordinator import AuroraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aurora from a config entry."""

    conf = entry.data
    options = entry.options

    session = aiohttp_client.async_get_clientsession(hass)
    api = AuroraForecast(session)

    longitude = conf[CONF_LONGITUDE]
    latitude = conf[CONF_LATITUDE]
    polling_interval = DEFAULT_POLLING_INTERVAL
    threshold = options.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)
    name = conf[CONF_NAME]

    coordinator = AuroraDataUpdateCoordinator(
        hass=hass,
        name=name,
        polling_interval=polling_interval,
        api=api,
        latitude=latitude,
        longitude=longitude,
        threshold=threshold,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        AURORA_API: api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AuroraEntity(CoordinatorEntity[AuroraDataUpdateCoordinator]):
    """Implementation of the base Aurora Entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: AuroraDataUpdateCoordinator,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the Aurora Entity."""

        super().__init__(coordinator=coordinator)

        self._attr_name = name
        self._attr_unique_id = f"{coordinator.latitude}_{coordinator.longitude}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        """Define the device based on name."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, str(self.unique_id))},
            manufacturer="NOAA",
            model="Aurora Visibility Sensor",
            name=self.coordinator.name,
        )
