# Project guidance
Target: Raspberry Pi 4B, Waveshare 1.54-inch 200x200 monochrome SPI module.
Confirm panel V1/V2 label before hardware tests. Do not assume a color model is compatible.
Keep GPIO imports lazy so preview/test operations work without a Pi.
Use the vendor driver, pin its upstream commit, preserve upstream licensing.
Run `python -m unittest discover -s tests` and the generate/preview commands after changes.
Keep demos finite; 10-second operation is a short demonstration. Vendor recommendation is >=180s.
Sleep the panel between full updates and on exit. Never drive partial updates indefinitely.
Hardware tests require the user's Pi; do not claim software-only tests validate hardware.
Do not commit credentials, machine addresses, generated files, or vendor checkouts.
