import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from track_diagnostics import analyze_observations

class TrackDiagnosticsTests(unittest.TestCase):
    def test_class_flip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tracks.csv'
            with p.open('w',newline='') as f:
                w=csv.writer(f)
                w.writerow(['frame','track_id','class_name','confidence'])
                w.writerow([1,5,'Hatchback',.7])
                w.writerow([2,5,'SUV',.6])
                w.writerow([3,6,'Sedan',.9])
            info=analyze_observations(p)
            self.assertEqual(info['unique_track_ids'],2)
            self.assertEqual(info['ids_with_class_changes'],1)

if __name__ == '__main__': unittest.main()
