# Technical design — TrafficIQ Expanded

## Architecture

1. `videos/` — two user-provided traffic video recordings. Dropdown selection in Streamlit.
2. `processor.py` — loads the supplied 13-class YOLO11s checkpoint on demand, processes video frames (4K resized to <=1280 px for inference), performs ByteTrack with `tracker.yaml`, writes annotated H.264 video, per-frame observation CSV and per-class unique-track CSV. Video A and Video B use separate output directories.
3. `track_diagnostics.py` — identifies **class label changes for a given tracking ID** and track visibility gaps. It does **not** prove if a vehicle was assigned multiple new IDs.
4. `signal_controller.py` — reusable one-green-at-a-time controller for North, East, South, West with one GREEN (20/30/45 s), YELLOW (3 s) and ALL-RED (2 s). Signal decisions are made only at phase boundaries. Directions are rotated fairly.
5. `simulation_compare.py` — deterministic comparison of *synthetic* Poisson arrivals under the adaptive controller versus a fixed 30-second controller. This is a teaching/demonstration model, not a calibrated city traffic model.
6. `storage.py` — local SQLite manual violation/evidence records and processing-run metadata.
7. `dashboard.py` — Overview, Video Analysis, Signal Control, Performance Lab, Frame Review, Tracking Diagnostics, Violation Records, Reports and System Check. The dashboard remains accessible when torch is blocked by Windows Application Control; processing requires an approved, functioning PyTorch environment.
8. `reference_frames/` — 40 large full-resolution stills from the two source videos, lossless PNG plus small JPEG thumbnails. Useful for inspecting visually small vehicles and planning camera-specific ROIs, but not annotated data.
9. `reference_videos/` — two historical annotated tracking test clips in H.264, allowing visual comparison of the original and experimental ByteTrack configurations.

## Non-claims and limitations

- The unique tracking-ID count is **not** a verified number of physical vehicles or line crossings. ByteTrack IDs can fragment. Confidence-weighted voting does not fix misclassification reliably.
- Visible detections are **not** waiting vehicle queues. The signal controller currently uses manually entered or simulated queues; there is no automated video-to-per-approach waiting queue integration.
- Automatic helmet, triple-riding, wrong-way and red-light enforcement are **not implemented** by a 13-class vehicle detector. Event records are manual.
- No certified signal timing, real-world road-safety validation, or physical light controller is provided. The one-GREEN invariant and clearance stages are exercised in tests, but this does not establish deployment safety.
- Unreal Engine is **not implemented**; `signal_demo.py` outputs a JSON state example for later integration.
- Recorded model metrics were supplied in historical handover notes and have **not** been reproduced in the packaged test environment.
- The `reference_frames` directory increases the archive size for meaningful full-resolution visual assets, not fake binary padding. It can be deleted to reduce the installed size.

## Outputs

`outputs/<selected-video-stem>/`: `tracked_web.mp4`, `vehicle_counts.csv`, `track_observations.csv`, `summary.json`.

`outputs/simulation/`: `simulation_comparison.json` and `simulation_timeline.csv` — synthetic scenario only.

`outputs/traffic_violations.db`: manual SQLite incident log.

## Reproducibility

Run `python -m unittest discover -s tests -v`, `python verify_package.py`, `python simulation_compare.py --seconds 600`, `python check_setup.py --model`, and finally process five seconds of each video in Video Analysis. A successful model runtime is **not** assured on the user device until WinError 4551 signing restrictions are resolved.
