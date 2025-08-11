# Renogy UART Integration for Home Assistant
This custom Home Assistant integration provides monitoring capabilities for Renogy devices via a USB to UART Modbus connection.

## Currently Supported Devices
Tested:
- Renogy Rover
- Renogy Wanderer

Should work, but untested:
- Renogy Adventurer
- Renogy DC-DC Charger

## Features
- Poll data from Renogy charge controllers over a USB serial connection
- Monitor battery status (voltage, current, temperature, charge state)
- Monitor solar panel (PV) performance metrics
- Monitor load status and statistics
- Monitor controller information
- All data exposed as Home Assistant sensors
- Energy dashboard compatible sensors
- Configurable polling interval
- Automatic error recovery
- Optional MQTT forwarding for Venus OS (see `venus_mqtt_example.yaml`)

## Prerequisites
- Home Assistant instance (version 2025.3 or newer)
- Renogy device connected via USB to UART (Modbus) adapter
- USB access on the Home Assistant host

## Installation
This integration can be installed via HACS (Home Assistant Community Store).

1. Ensure you have [HACS](https://hacs.xyz/) installed
2. Add this repository to your HACS custom repositories:
   - Click on HACS in the sidebar
   - Click on the three dots in the top right corner
   - Select "Custom repositories"
   - Add this repository URL
   - Select "Integration" as the category
3. Search for "Renogy" in the HACS store and install it
4. Restart Home Assistant

## Configuration
The integration is configurable through the Home Assistant UI after installation:

1. Go to Settings > Devices & Services
2. Click the "+ Add Integration" button
3. Search for "Renogy" and select it
4. Enter the serial port path (e.g. `/dev/ttyUSB0`) and optional polling interval

## Sensors
The integration provides the following sensor groups:

### Battery Sensors
- Voltage
- Current
- Temperature
- State of Charge
- Charging Status

### Solar Panel (PV) Sensors
- Voltage
- Current
- Power
- Daily Generation
- Total Generation

### Load Sensors
- Status
- Current Draw
- Power Consumption
- Daily Usage

### Controller Info
- Temperature
- Device Information
- Operating Status

All sensors are automatically added to Home Assistant's Energy Dashboard where applicable.

## Venus OS MQTT
To publish the collected data to a Victron Venus OS MQTT server for auto-discovery, use the example configuration in `venus_mqtt_example.yaml`.

## Support
- For bugs, please open an issue on GitHub
- Include Home Assistant logs and your device model information

## License
This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
