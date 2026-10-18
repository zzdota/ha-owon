# OWON Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant integration for OWON smart meters (PC321, PC341，4713 series) via MQTT.

## Supported Devices

- OWON PC321 (WiFi MQTT)
- OWON PC341 (WiFi MQTT)
- OWON 4713 series (WiFi MQTT)


## Installation via HACS

1. Open HACS in Home Assistant
2. Search for **OWON** and install
3. Restart Home Assistant

## Configuration

Go to **Settings → Devices & Services → Add Integration** and search for **OWON**.

Make sure MQTT is configured before adding this integration.

## Requirements

- Home Assistant with MQTT integration configured
- OWON smart meter connected to the same MQTT broker
