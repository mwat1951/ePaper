#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo apt update
sudo apt install -y git python3-venv python3-pil python3-spidev python3-gpiozero python3-lgpio
python3 -m venv --system-site-packages .venv
mkdir -p vendor
if [ ! -d vendor/e-Paper/.git ]; then
    git clone --no-checkout https://github.com/waveshareteam/e-Paper.git vendor/e-Paper
fi
git -C vendor/e-Paper checkout --detach d28b3c4cfc78eef1c6cd6e6e3013654e449d2864
sudo raspi-config nonint do_spi 0
.venv/bin/python slideshow.py --generate
printf '%s\n' 'Setup complete. Reboot, verify /dev/spidev0.0, then follow README.'
