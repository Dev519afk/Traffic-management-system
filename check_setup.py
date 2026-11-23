"""Read-only checks. Use --model to attempt PyTorch + YOLO checkpoint loading."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from processor import ROOT, MODEL_PATH, video_info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', action='store_true', help='Also test torch and Ultralytics imports')
    args = ap.parse_args()
    print('Python:', sys.version.split()[0])
    print('Interpreter:', sys.executable)
    print('Project:', ROOT)
    print('Model:', MODEL_PATH, 'PRESENT' if MODEL_PATH.is_file() else 'MISSING')
    if MODEL_PATH.is_file():
        print('Model size:', round(MODEL_PATH.stat().st_size / 1024**2,1), 'MiB')
    for path in sorted((ROOT/'videos').glob('*.mp4')):
        try:
            print('Video:', path.name, video_info(path))
        except Exception as exc:
            print('Video failed:', path, exc)
    if args.model:
        try:
            import torch
            from ultralytics import YOLO
            print('Torch:', torch.__version__, 'CUDA:', torch.cuda.is_available())
            if torch.cuda.is_available():
                print('GPU:', torch.cuda.get_device_name(0))
            model = YOLO(str(MODEL_PATH))
            print('Model class names:', model.names)
        except Exception as exc:
            print('Model test failed:', type(exc).__name__, str(exc))
            print('See WINDOWS_TROUBLESHOOTING.md for Windows App Control DLL blocks.')
            sys.exit(2)


if __name__ == '__main__':
    main()
