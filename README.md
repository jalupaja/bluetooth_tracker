# Bluetooth scanner
> This is a WIP project with the goal of tracking Bluetooth devices

## Current Capabilities
- list BLE devices and their properties
- save devices to a local database

## Installation
`python -m venv .venv`
`source .venv/bin/activate`
`pip install -r requirements.txt`

### Installation using nix-shell
`nix-shell`

## create Systemd Service
`./create_service.sh`
`sudo systemctl status bluetooth_tracker`

## Usage
`python -m scanner`

# signal strength
> A TUI + GUI program to show the signal strength to a device in a live Graph

## Usage
`python -m signal_strength`

# stats
> stats is a separate project, supporting the first one by providing functions to analyse the Bluetooth tracker's database

- This is mostly a dump of tools I needed

## bt\_stats.py
> A script to correlate Bluetooth devices

`python -m bt_stats`

## ble\_stats.py
> A script to correlate Bluetooth Low Energy devices with or without a random Address

`python -m ble_stats`

# tools
> scripts to help me manage my databases
- split\_db.py
- fix\_table.py
- fix update\_geolocation.py

`python -m tools.split_db`

# lib
> Tools, needed for above programs

- bt\_device.py
- bt\_scanner.py
- ble\_device.py
- ble\_scanner.py
- db.py
- manufacturers.py
- device\_classes.py
- similarity.py
- log.py
- UI.py
