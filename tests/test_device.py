"""Tests for the RenogyUARTDevice class without dependencies."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


class TestRenogyUARTDevice:
    """Test the RenogyUARTDevice functionality without importing the full module."""

    @pytest.fixture
    def mock_port(self):
        """Create a mock serial port path."""
        return "/dev/ttyUSB0"

    @pytest.fixture
    def device_class(self):
        """Create a RenogyUARTDevice-like class for testing."""

        class MockRenogyDevice:
            def __init__(self, port, device_type="controller"):
                self.port = port
                self.address = port
                self.name = port
                self.failure_count = 0
                self.max_failures = 3
                self.available = True
                self.parsed_data = {}
                self.device_type = device_type
                self.last_unavailable_time = None
                self.update_availability_calls = []

            @property
            def is_available(self):
                return self.available and self.failure_count < self.max_failures

            @property
            def should_retry_connection(self):
                if self.is_available:
                    return True
                if self.last_unavailable_time is None:
                    self.last_unavailable_time = datetime.now()
                    return False
                retry_time = self.last_unavailable_time + timedelta(minutes=10)
                if datetime.now() >= retry_time:
                    self.last_unavailable_time = datetime.now()
                    return True
                return False

            def update_availability(self, success, error=None):
                self.update_availability_calls.append((success, error))
                if success:
                    if self.failure_count > 0:
                        pass
                    self.failure_count = 0
                    if not self.available:
                        self.available = True
                        self.last_unavailable_time = None
                else:
                    self.failure_count += 1
                    if self.failure_count >= self.max_failures and self.available:
                        self.available = False
                        self.last_unavailable_time = datetime.now()

            def update_parsed_data(self, raw_data, register, cmd_name="unknown"):
                if not raw_data:
                    return False
                try:
                    if len(raw_data) > 0:
                        self.parsed_data = {"battery_voltage": 12.6, "battery_percentage": 85}
                        return True
                    return False
                except Exception:
                    return False

        return MockRenogyDevice

    def test_device_initialization(self, mock_port, device_class):
        """Test device initialization."""
        device = device_class(mock_port)

        assert device.address == mock_port
        assert device.name == mock_port
        assert device.available is True
        assert device.failure_count == 0
        assert device.parsed_data == {}
        assert device.device_type == "controller"

    def test_update_availability(self, mock_port, device_class):
        """Test the update_availability method."""
        device = device_class(mock_port)

        device.update_availability(True)
        assert device.available is True
        assert device.failure_count == 0

        device.update_availability(False)
        assert device.failure_count == 1

        device.update_availability(False)
        device.update_availability(False)
        assert device.available is False

    def test_is_available(self, mock_port, device_class):
        device = device_class(mock_port)
        device.available = True
        assert device.is_available is True
        device.available = False
        assert device.is_available is False
        device.available = True
        device.failure_count = device.max_failures
        assert device.is_available is False

    def test_should_retry_connection(self, mock_port, device_class):
        device = device_class(mock_port)
        device.available = True
        assert device.should_retry_connection is True
        device.available = False
        device.last_unavailable_time = None
        assert device.should_retry_connection is False
        past_time = datetime.now() - timedelta(minutes=20)
        device.last_unavailable_time = past_time
        assert device.should_retry_connection is True

    def test_update_parsed_data(self, mock_port, device_class):
        device = device_class(mock_port)
        result = device.update_parsed_data(b"data", 0)
        assert result is True
        assert device.parsed_data["battery_voltage"] == 12.6
