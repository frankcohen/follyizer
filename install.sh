#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/follyizer"
SERVICE_FILE="/etc/systemd/system/follyizer.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run this installer with sudo."
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip

mkdir -p "$INSTALL_DIR"
cp -R "$SOURCE_DIR"/. "$INSTALL_DIR"/

python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

if [[ ! -f "$INSTALL_DIR/config.yaml" ]]; then
  cp "$INSTALL_DIR/config.example.yaml" "$INSTALL_DIR/config.yaml"
fi

cp "$INSTALL_DIR/follyizer.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable follyizer.service

echo "Installed Follyizer."
echo "Edit $INSTALL_DIR/config.yaml, then run:"
echo "  sudo systemctl start follyizer"
echo "Logs:"
echo "  journalctl -u follyizer -f"
