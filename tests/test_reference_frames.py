import csv
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ReferenceFrameLibraryTests(unittest.TestCase):
    def test_frame_catalog(self):
        cat=ROOT/'reference_frames'/'catalog.csv'
        self.assertTrue(cat.is_file())
        with cat.open(encoding='utf-8') as handle:
            rows=list(csv.DictReader(handle))
        self.assertEqual(len(rows),40)
        self.assertEqual(sum(row['source_video']=='12937233_3840_2160_30fps.mp4' for row in rows),24)
        self.assertEqual(sum(row['source_video']=='244024_medium.mp4' for row in rows),16)
        for row in rows:
            p=ROOT/row['image_path']
            self.assertTrue(p.is_file())
            self.assertGreater(p.stat().st_size,100_000)
            self.assertTrue((ROOT/row['thumbnail_path']).is_file())

if __name__=='__main__': unittest.main()
