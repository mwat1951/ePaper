import argparse
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
import slideshow


class Tests(unittest.TestCase):
    def test_generated_and_custom_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slideshow.generate(root)
            self.assertEqual(len(list(root.glob('*.png'))), 5)
            for path in root.glob('*.png'):
                frame = slideshow.prepare(path, 90)
                self.assertEqual(frame.mode, '1')
                self.assertEqual(frame.size, (200, 200))
            Image.new('RGBA', (50, 100), (0, 0, 0, 0)).save(root/'alpha.png')
            self.assertEqual(slideshow.prepare(root/'alpha.png').getextrema(), (255, 255))

    def test_sleep_attempted_on_failure(self):
        class FailedDisplay:
            slept = False
            def init(self, mode):
                raise RuntimeError('fake SPI failure')
            def sleep(self):
                self.slept = True
        epd = FailedDisplay()
        args = argparse.Namespace(cycles=1, interval=10)
        with self.assertRaises(RuntimeError):
            slideshow.run(args, epd, [(Path('test.png'), None)])
        self.assertTrue(epd.slept)

    def test_ten_second_dwell_excludes_refresh(self):
        from unittest.mock import Mock
        epd = Mock()
        args = argparse.Namespace(cycles=1, interval=10)
        with patch('slideshow.time.monotonic', side_effect=[0, 1, 3, 5]), patch('slideshow.time.sleep') as sleep:
            slideshow.run(args, epd, [(Path('test.png'), None)])
        sleep.assert_called_once_with(8)
        epd.display.assert_called_once()


if __name__ == '__main__':
    unittest.main()
