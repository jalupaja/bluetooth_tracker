# Bluetooth tracker
> This is a WIP project with the goal of tracking Bluetooth devices

## Current Capabilities
- list BLE devices and their properties
- save devices to a local database

## Installation
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`

## create Systemd Service
`./create_service.sh`
`sudo systemctl status bluetooth_tracker`

## Usage
`python scanner.py`

# signal strength
> A TUI + GUI program to show the signal strength to a device in a live Graph

## Usage
`python signal_strength.py`

# stats
> stats is a separate project, supporting the first one by providing functions to analyse the Bluetooth tracker's database

- This is mostly a dump of tools I needed

## BT\_stats.py
> A script to correlate Bluetooth devices

## BLE\_stats.py
> A script to correlate Bluetooth Low Energy devices with or without a random Address

## split\_db.py
> A script to split a too large database for faster

## update\_geolocation.python
> A script to update the geolocation manually per timespan

## helper classes
- Similarity.py
- BT_device.py
- BLE_device.py
- db.py
