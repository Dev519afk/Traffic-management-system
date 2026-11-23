# Demonstration sequence (8–12 minutes)

1. Launch `python -m streamlit run dashboard.py` and show source dropdown. Switch between the roundabout recording and 4K city-road recording; source folders and reports stay independent.
2. Show `Video Analysis`; process **five seconds** on the selected source **only after the environment passes `python check_setup.py --model`**. If Windows blocks torch, show pre-existing annotated historical clips under Tracking Diagnostics rather than claim successful new inference.
3. Show an actual `vehicle_counts.csv` and `track_observations.csv` produced by the app. Explain that track IDs may fragment, so counts aren't ground truth.
4. Show `Tracking Diagnostics`, with class flip counts and historical H.264 ID comparison videos.
5. Show `Frame Review`, select and download a real full-resolution PNG from each source. Explain these frames are unlabeled reference assets.
6. Show `Signal Control`; manually enter North=15, East=8, South=3, West=6, then demonstrate timing and switch using +1 second / running timer. State that one and only one GREEN is permitted, and that GREEN is locked once started.
7. Show `Performance Lab`, run synthetic comparison and export JSON/CSV. Do not claim these are results from real video.
8. Show `Violation Records`, record one explicitly **manual** sample event and export it.
9. Show `Reports`, `System Check` and automated test results.

## Viva explanation

**Q:** How does detection differ from tracking? **A:** YOLO11s predicts a class and box on each frame, while ByteTrack attempts to associate boxes across frames and maintain an ID. ID consistency is not guaranteed.

**Q:** How is green time chosen? **A:** A separate phase-based controller consumes *per-approach waiting counts* from manual or synthetic inputs, applies 20/30/45-second bounds, and locks time until phase completion. It does not derive actual queues from the provided video footage.

**Q:** Can two directions go GREEN? **A:** The simulation enforces one GREEN at a time and automated tests check that invariant. A real installation would require hardware-level safety validation and certified timing.

**Q:** Where is Unreal? **A:** The current package includes a JSON export interface as a future integration hook, not a finished Unreal scene.
