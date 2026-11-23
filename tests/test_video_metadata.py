import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from processor import ROOT, video_info


class VideoTests(unittest.TestCase):
    def test_packaged_video_files(self):
        for video in ('244024_medium.mp4','12937233_3840_2160_30fps.mp4'):
            f = ROOT/'videos'/video
            self.assertTrue(f.is_file(), f'Missing source video {video}')
            info = video_info(f)
            self.assertGreater(info['frames'],0)
            self.assertGreater(info['fps'],0)
            self.assertGreater(info['width'],0)


if __name__ == '__main__':
    unittest.main()
