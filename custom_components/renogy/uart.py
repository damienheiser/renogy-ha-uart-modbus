import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    COMMANDS,
    DEFAULT_DEVICE_ID,
    DEFAULT_DEVICE_TYPE,
    LOGGER,
    UNAVAILABLE_RETRY_INTERVAL,
)

try:
    from renogy_ble import RenogyParser

    PARSER_AVAILABLE = True
except Exception:  # pragma: no cover - library import guard
    PARSER_AVAILABLE = False
    RenogyParser = None  # type: ignore
    LOGGER.error("renogy-ble library not found! Please install the requirements.")


class RenogyUARTDevice:
    """Representation of a Renogy device connected over USB UART."""

    def __init__(self, port: str, device_type: str = DEFAULT_DEVICE_TYPE) -> None:
        self.port = port
        self.address = port  # For compatibility with sensor unique IDs
        self.name = port
        self.device_type = device_type
        self.failure_count = 0
        self.max_failures = 3
        self.available = True
        self.parsed_data: Dict[str, Any] = {}
        self.last_unavailable_time: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Return True if device communication is healthy."""
        return self.available and self.failure_count < self.max_failures

    @property
    def should_retry_connection(self) -> bool:
        """Determine if we should attempt to reconnect to an unavailable device."""
        if self.is_available:
            return True
        if self.last_unavailable_time is None:
            self.last_unavailable_time = datetime.now()
            return False
        retry_time = self.last_unavailable_time + timedelta(
            minutes=UNAVAILABLE_RETRY_INTERVAL
        )
        if datetime.now() >= retry_time:
            self.last_unavailable_time = datetime.now()
            return True
        return False

    def update_availability(
        self, success: bool, error: Optional[Exception] = None
    ) -> None:
        """Update availability based on communication success."""
        if success:
            if self.failure_count > 0:
                LOGGER.info(
                    "Device %s communication restored after %s consecutive failures",
                    self.name,
                    self.failure_count,
                )
            self.failure_count = 0
            if not self.available:
                LOGGER.info("Device %s is now available", self.name)
                self.available = True
                self.last_unavailable_time = None
        else:
            self.failure_count += 1
            if self.failure_count >= self.max_failures and self.available:
                LOGGER.error(
                    "Renogy device %s marked unavailable after %s consecutive polling failures",
                    self.name,
                    self.max_failures,
                )
                self.available = False
                self.last_unavailable_time = datetime.now()


class RenogyActiveUARTCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator to actively poll Renogy devices over UART."""

    def __init__(
        self,
        hass: HomeAssistant,
        port: str,
        device_type: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="Renogy UART",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.address = port
        self.device = RenogyUARTDevice(port, device_type)
        self._client = AsyncModbusSerialClient(port, baudrate=9600, timeout=3)
        self._parser = RenogyParser() if PARSER_AVAILABLE else None

    async def async_close(self) -> None:
        """Close the modbus client."""
        try:
            await self._client.close()
        except Exception:  # pragma: no cover - best effort
            pass

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from the Renogy device."""
        if not PARSER_AVAILABLE:
            raise UpdateFailed("renogy-ble parser library not available")

        if not self.device.should_retry_connection:
            raise UpdateFailed("Device marked unavailable")

        try:
            await self._client.connect()
            parsed: Dict[str, Any] = {}
            for _, (function, register, word_count) in COMMANDS[self.device.device_type].items():
                response = await self._client.read_holding_registers(
                    register,
                    count=word_count,
                    device_id=DEFAULT_DEVICE_ID,
                )
                if hasattr(response, "isError") and response.isError():
                    raise ModbusException(str(response))
                byte_count = word_count * 2
                payload = (
                    bytes([DEFAULT_DEVICE_ID, function, byte_count])
                    + b"".join(reg.to_bytes(2, "big") for reg in response.registers)
                )
                parsed.update(
                    self._parser.parse(payload, self.device.device_type, register)
                )
            self.device.update_availability(True, None)
            self.device.parsed_data = parsed
            return parsed
        except Exception as err:  # pylint: disable=broad-except
            self.device.update_availability(False, err)
            raise UpdateFailed(f"Error communicating with device: {err}") from err
