"""YOLO11s + ByteTrack recorded video analysis. Imports Ultralytics only when run."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import csv
import json
import os
import shutil
import subprocess
import tempfile
import cv2

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'
MODEL_PATH = ROOT / 'models' / 'vehicle_detector' / 'yolo11s_bmd45_19k' / 'weights' / 'best.pt'
TRACKER_PATH = ROOT / 'tracker.yaml'


def video_info(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f'Cannot open video: {path}')
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0
        if fps <= 0: fps = 25.0
        frame_count = max(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        return {
            'fps': fps,
            'frames': frame_count,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': frame_count / fps if frame_count else 0.0,
        }
    finally:
        cap.release()


def find_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which('ffmpeg')


def process_video(video_path: Path, seconds: int, conf: float = 0.25,
                  progress=None, prefer_gpu=True) -> dict:
    """Analyze a selected file and create H.264 playback, counts CSV and observation CSV.

    Counts reflect unique track IDs, with confidence-weighted class voting.
    This is NOT verified intersection crossing/queue counting.
    """
    if not video_path.is_file():
        raise FileNotFoundError(video_path)
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f'Model missing: {MODEL_PATH}')

    # Deliberately lazy import: dashboard remains usable if Windows blocks a CUDA DLL.
    import torch
    from ultralytics import YOLO

    meta = video_info(video_path)
    max_frames = min(meta['frames'], max(1, int(seconds * meta['fps'])))
    if max_frames <= 0:
        raise RuntimeError('Input video contains no readable frames')

    device = 0 if (prefer_gpu and torch.cuda.is_available()) else 'cpu'
    model = YOLO(str(MODEL_PATH))
    names = model.names
    folder = OUTPUTS / video_path.stem
    folder.mkdir(parents=True, exist_ok=True)
    raw_video = folder / 'tracked_raw.mp4'
    final_video = folder / 'tracked_web.mp4'
    counts_path = folder / 'vehicle_counts.csv'
    tracks_path = folder / 'track_observations.csv'

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError('Unable to open video for processing')
    # 4K clips are resized for GPU memory safety, preserving aspect ratio.
    width, height = meta['width'], meta['height']
    max_width = 1280
    if width > max_width:
        height = int(round(height * max_width / width))
        width = max_width
    writer = cv2.VideoWriter(str(raw_video), cv2.VideoWriter_fourcc(*'mp4v'),
                             meta['fps'], (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError('Could not open output video writer')

    seen_classes = defaultdict(lambda: defaultdict(float))
    processed = 0
    try:
        with tracks_path.open('w', newline='', encoding='utf-8') as f:
            row_writer = csv.writer(f)
            row_writer.writerow(['frame', 'second', 'track_id', 'class_id', 'class_name',
                                 'confidence', 'x1', 'y1', 'x2', 'y2'])
            while processed < max_frames:
                ok, frame = cap.read()
                if not ok:
                    break
                processed += 1
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
                result = model.track(
                    frame, persist=True, tracker=str(TRACKER_PATH), conf=conf,
                    imgsz=640, device=device, verbose=False,
                )[0]
                boxes = result.boxes
                visible = len(boxes) if boxes is not None else 0
                if boxes is not None and boxes.id is not None and boxes.cls is not None:
                    track_ids = boxes.id.int().cpu().tolist()
                    class_ids = boxes.cls.int().cpu().tolist()
                    confidence_values = boxes.conf.cpu().tolist()
                    coords = boxes.xyxy.cpu().tolist()
                    for tid, cls, confidence, bounds in zip(track_ids, class_ids,
                                                              confidence_values, coords):
                        seen_classes[tid][int(cls)] += float(confidence)
                        row_writer.writerow([processed, round((processed - 1) / meta['fps'], 3),
                                             tid, cls, names[int(cls)], round(confidence, 4),
                                             *[round(v, 1) for v in bounds]])
                # Keep video captions clear and readable on both scenes.
                annotated = result.plot()
                density = 'LOW' if visible < 5 else 'MEDIUM' if visible < 12 else 'HIGH'
                suggested = 20 if visible < 5 else 30 if visible < 12 else 45
                cv2.rectangle(annotated, (10, 10), (430, 112), (25, 29, 40), -1)
                cv2.putText(annotated, f'Frame {processed} | Tracked IDs: {len(seen_classes)}',
                            (22, 37), cv2.FONT_HERSHEY_SIMPLEX, .6, (250, 250, 250), 2)
                cv2.putText(annotated, f'Visible detections: {visible} | Density: {density}',
                            (22, 66), cv2.FONT_HERSHEY_SIMPLEX, .57, (245, 225, 130), 2)
                cv2.putText(annotated, f'Illustrative GREEN suggestion: {suggested}s',
                            (22, 95), cv2.FONT_HERSHEY_SIMPLEX, .57, (120, 230, 190), 2)
                writer.write(annotated)
                if progress and (processed == 1 or processed % 15 == 0 or processed == max_frames):
                    progress(processed, max_frames)
    finally:
        cap.release()
        writer.release()

    if processed == 0:
        raise RuntimeError('No frames could be read from the video')

    # One ID counted once. Use all observations to choose a more stable class,
    # rather than counting an ID again whenever YOLO changes its class.
    counts = {str(name): 0 for name in names.values()}
    for class_weights in seen_classes.values():
        winner = max(class_weights, key=class_weights.get)
        counts[str(names[winner])] += 1
    with counts_path.open('w', newline='', encoding='utf-8') as f:
        cw = csv.writer(f)
        cw.writerow(['Vehicle Class', 'Unique Tracked Count'])
        for name, count in counts.items():
            cw.writerow([name, count])

    conversion_warning = ''
    web_video = raw_video
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        # H.264 avoids Streamlit/browser MP4V playback failures on Windows.
        command = [ffmpeg, '-y', '-v', 'error', '-i', str(raw_video),
                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
                   '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(final_video)]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode == 0 and final_video.is_file() and final_video.stat().st_size > 0:
            web_video = final_video
            raw_video.unlink(missing_ok=True)
        else:
            conversion_warning = 'H.264 conversion failed. Browser playback might not work. ' + completed.stderr[-400:]
    else:
        conversion_warning = 'FFmpeg not found; browser may not play the MP4V file.'

    summary = {
        'video': video_path.name,
        'output_video': str(web_video),
        'counts_csv': str(counts_path),
        'tracks_csv': str(tracks_path),
        'output_dir': str(folder),
        'processed_frames': processed,
        'processed_seconds': round(processed / meta['fps'], 2),
        'unique_track_ids': len(seen_classes),
        'class_counts': counts,
        'device': str(device),
        'conf': conf,
        'warning': conversion_warning,
        'methodology_note': ('Unique tracker IDs, aggregated by confidence-weighted class vote; '
                             'ID fragmentation can overcount physical vehicles; no queue or line-crossing count.'),
    }
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


def load_summary(video_path: Path) -> dict | None:
    path = OUTPUTS / video_path.stem / 'summary.json'
    if not path.is_file():
        return None
    try:
        summary = json.loads(path.read_text(encoding='utf-8'))
        if not Path(summary['output_video']).is_file():
            return None
        return summary
    except (ValueError, KeyError, TypeError):
        return None
