"""Optional command-line entry point for analyzing either packaged video."""
from __future__ import annotations
import argparse
from pathlib import Path
from processor import ROOT, process_video, video_info
from storage import initialize_database, add_run


def main():
    p = argparse.ArgumentParser(description='YOLO11s + ByteTrack video analysis')
    p.add_argument('--video', default='244024_medium.mp4',
                   help='Video filename inside videos/ or a local path')
    p.add_argument('--seconds', type=int, default=10,
                   help='Seconds to process; use a short run first')
    p.add_argument('--confidence', type=float, default=0.30)
    p.add_argument('--cpu', action='store_true', help='Use CPU if PyTorch imports correctly')
    a = p.parse_args()
    video = Path(a.video)
    if not video.is_file():
        video = ROOT/'videos'/a.video
    if not video.is_file():
        p.error(f'Video not found: {a.video}')
    if not 0.1 <= a.confidence <= 0.95:
        p.error('Confidence must be between 0.10 and 0.95')
    if a.seconds < 1:
        p.error('Seconds must be positive')
    initialize_database()
    info = video_info(video)
    print(f"Video: {video.name} | {info['width']}x{info['height']} | {info['fps']:.2f} FPS")
    def progress(n,total):
        if n == 1 or n % max(1, int(info['fps'] * 2)) == 0 or n == total:
            print(f'Processed {n}/{total} frames', flush=True)
    result = process_video(video, a.seconds, a.confidence, progress, prefer_gpu=not a.cpu)
    add_run(result['video'], result['processed_seconds'], result['processed_frames'],
            result['unique_track_ids'], Path(result['output_dir']))
    print(f"Completed: {result['unique_track_ids']} unique track IDs")
    print(f"Video: {result['output_video']}")
    print(f"Counts: {result['counts_csv']}")
    print(result['methodology_note'])


if __name__ == '__main__':
    main()
