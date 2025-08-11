from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_TYPE,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)
from .uart import RenogyActiveUARTCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renogy UART integration from a config entry."""
    port = entry.data[CONF_PORT]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE)

    LOGGER.info(
        "Setting up Renogy UART device on %s with scan interval %ss", port, scan_interval
        )

    coordinator = RenogyActiveUARTCoordinator(
        hass, port, device_type, scan_interval
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Renogy UART config entry."""
    coordinator: RenogyActiveUARTCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_close()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
