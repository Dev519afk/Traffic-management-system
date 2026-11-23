# Expanded package test report — 22 November 2026

## Verified in this build environment

- `python -m unittest discover -s tests -v`: **10/10 passed**.
- `python -m py_compile`: Python source modules compile without syntax errors.
- `python verify_package.py`: checkpoint and both source videos present; correct source video metadata; 40/40 PNG reference frames present.
- `python simulation_compare.py --seconds 600`: generated deterministic *synthetic* comparison JSON and timeline CSV.
- 30-second H.264 tracking comparison clips and 40 original full-resolution PNGs included.
- Final archive integrity is checked after ZIP packaging.

## Not verified in this build environment

- Fresh YOLO11s + ByteTrack inference with the checkpoint (Ultralytics/Streamlit aren't available here).
- Streamlit browser rendering on the user's Windows system.
- Any tracking accuracy percentage, queue-detection accuracy, or real-world traffic benefit.
- Unreal Engine integration or automatic traffic-violation detection.

**Windows risk:** Earlier Windows Application Control blocked `torch/lib/c10_cuda.dll` with WinError 4551; resolve via an approved environment/administrator before rerunning inference. Never disable security to work around it.

## Expected app outputs when tested locally

- Selected Video A and B each write separate `outputs/<video_stem>/` folders.
- `Signal Control`: only one GREEN direction; 20/30/45s GREEN, 3s YELLOW, 2s ALL RED.
- `Performance Lab`: synthetic result visualization and exports (not actual video measurements).
- `Tracking Diagnostics`: class-change report if the user runs video processing.
- `Violation Records`: manual records in SQLite.
