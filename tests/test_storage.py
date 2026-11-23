import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
import tempfile
import storage


class SQLiteTests(unittest.TestCase):
    def test_initialize_and_manual_record(self):
        old_db,old_out,old_evidence = storage.DB_PATH,storage.OUT,storage.EVIDENCE
        try:
            with tempfile.TemporaryDirectory() as d:
                folder = Path(d)
                storage.OUT = folder
                storage.DB_PATH = folder/'demo.db'
                storage.EVIDENCE = folder/'evidence'
                storage.initialize_database()
                storage.add_event('ID-5','SUV','Other / demo event','Camera 1','Test record')
                events = storage.get_events()
                self.assertEqual(len(events), 1)
                self.assertIn('Manually recorded', events.iloc[0]['status'])
                storage.add_run('test.mp4',5.0,100,7,folder)
                self.assertEqual(len(storage.get_runs()),1)
        finally:
            storage.DB_PATH,storage.OUT,storage.EVIDENCE = old_db,old_out,old_evidence


if __name__ == '__main__':
    unittest.main()
