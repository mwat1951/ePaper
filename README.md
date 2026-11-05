# ePaper: Raspberry Pi slideshow

Raspberry Pi 4B + Waveshare 1.54-inch **200x200 black/white SPI module**.
Python controls the existing display controller; no firmware flashing is required.

## Status and scope

Starter implementation: five generated monochrome icons inspired by the supplied
happy/listening/thinking/phone/alert reference images; custom PNG/JPEG/BMP input;
full-refresh slideshow; sleep between frames; timing logs; 30-second BUSY timeout;
rotation/dithering; hardware-free preview and tests. The supplied PDFs are reference
material and are not redistributed. Generated icons are available after setup.
Hardware bring-up is pending. Partial refresh comparison is a follow-up after full
refresh works; no partial-refresh behavior is claimed by this version.

## 1. Identify the display and wire with power disconnected

Check the panel label for **V2**. Panel revision is distinct from driver PCB Rev2.1.
Default is V2; old V1 requires `--driver v1`. Do not use this project for B/C/E/G
color variants or a bare panel without the Waveshare driver board.
Run `sudo poweroff`, wait for shutdown, then disconnect Pi power before wiring.
Use signal labels, not wire colors. Physical pin numbers below refer to the Pi's
40-pin header, counted from pin 1 (3.3V); verify board orientation first.

| Display label | Pi physical pin | BCM GPIO / signal |
|---|---:|---|
| VCC | 1 | 3.3V |
| GND | 6 | Ground |
| DIN | 19 | GPIO10 / SPI0 MOSI |
| CLK | 23 | GPIO11 / SPI0 SCLK |
| CS | 24 | GPIO8 / SPI0 CE0 |
| DC | 22 | GPIO25 |
| RST | 11 | GPIO17 |
| BUSY | 18 | GPIO24 |

No MISO wire. Do not confuse physical pin 18 (BUSY/GPIO24) with GPIO18
(physical pin 12, unused here). Power from 3.3V keeps compatibility with older boards.
The vendor backend reserves GPIO18 internally; do not attach another load there.

## 2. Install on Raspberry Pi OS

Connect from Windows PowerShell using your usual SSH command, then run on the Pi:

```bash
git clone https://github.com/mwat1951/ePaper.git
cd ePaper
bash scripts/setup_pi.sh
sudo reboot
```

Reconnect, then:

```bash
cd ~/ePaper
cat /etc/os-release
ls -l /dev/spidev0.0
groups
.venv/bin/python slideshow.py --preview
```

Setup uses apt-provided GPIO/SPI/Pillow in a virtual environment with system packages.
It pins Waveshare's upstream source to commit
`d28b3c4cfc78eef1c6cd6e6e3013654e449d2864` rather than copying driver code.
If device access is denied, check membership in `spi` and `gpio`;
`sudo usermod -aG spi,gpio "$USER"`, then log out and reconnect.
If SPI is missing, enable it in `sudo raspi-config` and reboot.

## 3. First display, then slideshow

Confirm the V2 label before using the default driver. For an old V1 panel append
`--driver v1` to hardware commands. First show a single image:

```bash
mkdir -p /tmp/epaper-one
cp images/01_happy.png /tmp/epaper-one/
.venv/bin/python slideshow.py --images /tmp/epaper-one --interval 10
```

Then demonstrate five images once:

```bash
.venv/bin/python slideshow.py --interval 10 --cycles 1
```

Each completed image remains for 10 seconds before the next initialization begins.
Time between completed frames is longer than 10 seconds because refresh/init take time.
Logs report initialization and combined SPI transfer/BUSY-wait time, not optical
pixel response; use a stopwatch/video to measure visual behavior. Full refresh
normally flashes, which is part of this demonstration. The final image remains
visible after sleep and script exit. Ctrl+C attempts sleep; SIGKILL/power loss
cannot run cleanup. BUSY timeout is bounded, but cannot guarantee correct wiring.

**Cadence:** the supplied guide and vendor manual recommend at least 180 seconds
between refreshes. Ten-second runs are finite demonstrations outside that
recommendation, not a validated continuous operating mode. Default interval is
180 seconds. No autostart or infinite loop is installed. Sleep does not remove
VCC from this wired module; it sends the controller's deep-sleep command.

## 4. Custom images and previews

Copy image files into a separate folder and pass `--images /path/to/folder`.
Files sort by filename; use numbered names. Images are padded to 200x200,
transparent pixels become white, and output is one-bit monochrome.
Use `--dither` for photos or `--rotate 90` for orientation.

On any computer with Python and Pillow (no GPIO imports for previews):

```bash
python -m pip install -r requirements-preview.txt
python slideshow.py --generate
python slideshow.py --preview
python -m unittest discover -s tests
```

Inspect `preview/` before sending images to hardware.

## Troubleshooting and next experiments

Blank display: check module revision, power, common ground, SPI device, and all
signal labels. A frozen BUSY line often means wrong driver or wiring. Shut down
and disconnect power before changing connections. Do not repeatedly rerun a
failing test. Ghosting and flashing should be assessed under steady room lighting.

After full-refresh bring-up, add a separately tested V2 partial-refresh mode with
an initial base image and regular full refreshes. Compare refresh time, flashing,
and ghosting. Confirm the vendor's sleep/base-image requirements before mixing
partial updates and deep sleep.

## Working environment

PowerShell SSH is sufficient for first bring-up. For ongoing edits, use VS Code
Remote-SSH to the Pi: open `~/ePaper` and select `~/ePaper/.venv/bin/python`.
The Pi remains the execution target; git is the shared project history.
An external chat session cannot reach a private LAN address directly, so run Pi
commands in SSH and paste relevant output while we work here.

## References

- [Waveshare manual](https://www.waveshare.com/wiki/1.54inch_e-Paper_Module_Manual)
- [Official driver repository](https://github.com/waveshareteam/e-Paper)
- User-supplied `epaper1.pdf` and `display_images.pdf`, reviewed for this framework.
