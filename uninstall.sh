#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run this uninstaller with sudo."
  exit 1
fi

systemctl disable --now follyizer.service 2>/dev/null || true
rm -f /etc/systemd/system/follyizer.service
systemctl daemon-reload

echo "Service removed. Project files remain in /opt/follyizer."
