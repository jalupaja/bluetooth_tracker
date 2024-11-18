#!/usr/bin/env bash


service_template="[Unit]
Description=bluetooth_tracker_service
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=\"PATH=$(pwd)/.venv/bin\"
ExecStart=python $(pwd)/main.py
Restart=always

[Install]
WantedBy=multi-user.target"


echo -e "$service_template" | sudo tee /etc/systemd/system/bluetooth_tracker.service > /dev/null

sudo systemctl enable bluetooth_tracker
sudo systemctl restart bluetooth_tracker
