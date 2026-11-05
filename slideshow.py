#!/usr/bin/env python3
"""200x200 monochrome demo. Hardware imports happen only on a real run."""
import argparse
import importlib
import logging
from pathlib import Path
import signal
import sys
import time
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
NAMES = ('happy', 'listening', 'thinking', 'phone', 'alert')


def icon(name):
    image = Image.new('1', (200, 200), 255)
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((10, 10, 189, 189), radius=35, fill=0)
    d.rounded_rectangle((17, 17, 182, 182), radius=29, outline=255, width=2)
    if name == 'happy':
        for x in (53, 119):
            d.arc((x, 77, x+28, 111), 180, 360, fill=255, width=6)
    elif name in ('listening', 'thinking'):
        for x in (66, 132):
            d.ellipse((x-13, 82, x+13, 108), fill=255)
            if name == 'thinking':
                d.ellipse((x-2, 77, x+18, 99), fill=0)
        if name == 'listening':
            for x, height in ((32, 12), (40, 30), (48, 20), (152, 20), (160, 30), (168, 12)):
                d.line((x, 95-height//2, x, 95+height//2), fill=255, width=3)
        else:
            for x in (82, 100, 118):
                d.ellipse((x-4, 142, x+4, 150), fill=255)
    elif name == 'phone':
        d.arc((57, 45, 145, 139), 50, 210, fill=255, width=17)
        d.rounded_rectangle((51, 65, 75, 91), radius=6, fill=255)
        d.rounded_rectangle((109, 127, 136, 151), radius=6, fill=255)
    elif name == 'alert':
        d.ellipse((76, 56, 124, 111), fill=255)
        d.polygon(((77, 83), (123, 83), (133, 132), (67, 132)), fill=255)
        d.rectangle((65, 129, 135, 136), fill=255)
        d.ellipse((93, 140, 107, 152), fill=255)
        for x in (45, 145):
            d.line((x, 87, x+10, 87), fill=255, width=3)
    else:
        raise ValueError(name)
    return image


def prepare(path, rotate=0, dither=False):
    with Image.open(path) as source:
        rgba = source.convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        gray = Image.alpha_composite(background, rgba).convert('L')
        gray = ImageOps.pad(gray, (200, 200), color=255)
        return gray.rotate(rotate).convert('1', dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)


def generate(directory):
    directory.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(NAMES, 1):
        icon(name).save(directory / f'{index:02d}_{name}.png')


def run(args, epd, frames):
    # Driver sleep closes SPI; init reopens it before every full refresh.
    # Finally also attempts sleep after failed init/display or Ctrl+C.
    awake = False
    try:
        for cycle in range(args.cycles):
            for path, frame in frames:
                started = time.monotonic()
                awake = True
                result = epd.init(0)
                if result == -1:
                    raise RuntimeError('Display initialization failed')
                init_done = time.monotonic()
                epd.display(epd.getbuffer(frame))
                refreshed = time.monotonic()
                logging.info('%s cycle=%d init=%.3fs transfer_and_refresh=%.3fs',
                             path.name, cycle+1, init_done-started, refreshed-init_done)
                epd.sleep()
                awake = False
                # Ten seconds of completed-image dwell, including the driver's sleep delay.
                time.sleep(max(0, args.interval - (time.monotonic()-refreshed)))
    finally:
        try:
            if awake:
                epd.sleep()
        except Exception:
            logging.exception('Sleep failed; shut down and disconnect power before inspecting wiring')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--images', type=Path, default=ROOT/'images')
    p.add_argument('--generate', action='store_true', help='Generate five sample icons and exit')
    p.add_argument('--preview', action='store_true', help='Write prepared frames without GPIO access')
    p.add_argument('--interval', type=float, default=180, help='Completed-image dwell seconds, default 180')
    p.add_argument('--cycles', type=int, default=1, help='Finite playlist repetitions')
    p.add_argument('--driver', choices=('v1', 'v2'), default='v2')
    p.add_argument('--rotate', type=int, choices=(0, 90, 180, 270), default=0)
    p.add_argument('--dither', action='store_true')
    args = p.parse_args()
    if args.interval < 0 or args.cycles < 1:
        p.error('interval must be nonnegative and cycles must be at least 1')
    if args.generate:
        generate(args.images)
        return
    files = sorted(path for path in args.images.iterdir() if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp'))
    if not files:
        p.error('No images found; first run with --generate')
    frames = [(path, prepare(path, args.rotate, args.dither)) for path in files]
    if args.preview:
        out = ROOT/'preview'
        out.mkdir(exist_ok=True)
        for path, frame in frames:
            frame.save(out/(path.stem+'.png'))
        print(f'Prepared {len(frames)} frames in {out}')
        return
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    if args.interval < 180:
        logging.warning('Short demo cadence: vendor recommends refresh intervals of at least 180 seconds')
    lib = ROOT/'vendor/e-Paper/RaspberryPi_JetsonNano/python/lib'
    if not lib.exists():
        p.error('Vendor library missing; run bash scripts/setup_pi.sh')
    sys.path.insert(0, str(lib))
    module = importlib.import_module('waveshare_epd.epd1in54_V2' if args.driver == 'v2' else 'waveshare_epd.epd1in54')
    epd = module.EPD()
    # Bound the vendor's otherwise unbounded BUSY polling loop.
    def bounded_busy():
        deadline = time.monotonic()+30
        while module.epdconfig.digital_read(epd.busy_pin) == 1:
            if time.monotonic() >= deadline:
                raise TimeoutError('BUSY stuck for 30 seconds: check wiring and panel revision')
            time.sleep(.02)
    epd.ReadBusy = bounded_busy
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        if args.driver == 'v1':
            # V1 uses waveform constants instead of the V2 boolean init argument.
            original_init = epd.init
            epd.init = lambda _: original_init(epd.lut_full_update)
        run(args, epd, frames)
    except KeyboardInterrupt:
        logging.info('Stopped')


if __name__ == '__main__':
    main()
