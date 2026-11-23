"""Read-only verification of the model and the two source videos and frame catalog."""
from pathlib import Path
import csv
from processor import MODEL_PATH, video_info, ROOT


def main():
    files = [MODEL_PATH, ROOT/'videos'/'244024_medium.mp4',
             ROOT/'videos'/'12937233_3840_2160_30fps.mp4']
    for file in files:
        print(('PASS' if file.is_file() else 'MISSING'), file.relative_to(ROOT),
              (f'{file.stat().st_size / 2**20:.1f} MiB' if file.is_file() else ''))
        if file.suffix == '.mp4' and file.exists():
            print('   metadata:', video_info(file))
    catalog = ROOT/'reference_frames'/'catalog.csv'
    if catalog.is_file():
        rows = list(csv.DictReader(catalog.open(encoding='utf-8')))
        present=sum((ROOT/r['image_path']).is_file() for r in rows)
        print('Reference review frames:',present,'/',len(rows))
    else:
        print('Optional frame library not present')
    print('Optional YOLO inference test: python check_setup.py --model')

if __name__ == '__main__':
    main()
