"""AI Traffic Management System - local Streamlit dashboard.

Video analysis is run only when requested. Signal decisions are explicitly
illustrative: no live junction actuation or inferred approach queues.
"""
from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
import time

import pandas as pd
import streamlit as st

from processor import MODEL_PATH, OUTPUTS, ROOT, load_summary, video_info, process_video
from signal_controller import DIRECTIONS, SignalController, choose_green
from simulation_compare import compare, save_report
from track_diagnostics import analyze_observations, export_diagnostics
import storage

VIDEOS = ROOT / "videos"
ASSETS = ROOT / "assets"
TRAINED_CLASSES = (
    "Hatchback", "Sedan", "SUV", "MUV", "Bus", "Truck", "Three-wheeler",
    "Two-wheeler", "LCV", "Mini-bus", "Tempo-traveller", "Bicycle", "Van",
)
VIOLATIONS = (
    "Helmet violation", "Triple riding", "Wrong-way driving",
    "Red-light violation", "Stop-line violation", "Other / demo event",
)

st.set_page_config(page_title="TrafficIQ • Intelligent Traffic Management",
                   page_icon="🚦", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background: #0d1421; color: #e9f0fb;}
[data-testid="stSidebar"] {background: #101c2c; border-right: 1px solid #26344b;}
.block-container {padding-top: 1.5rem; max-width: 1440px;}
h1,h2,h3 {letter-spacing: -.03em;}
div[data-testid="stMetric"] {background: #172438; padding: 1.0rem 1.25rem; border: 1px solid #293a51; border-radius: 14px;}
div[data-testid="stMetricLabel"] {color: #9fb2c7;}
.hero {padding: 24px 26px; background: linear-gradient(115deg,#172b43,#102b37); border: 1px solid #2f4d62; border-radius: 18px; margin-bottom: 20px;}
.hero small {letter-spacing: .16em; text-transform: uppercase; color: #62dcc8; font-weight: 700;}
.hero h1 {margin: 8px 0; font-size: 2.1rem; color: #f5faff;}
.hero p {margin-bottom: 0; color: #b7c7d6;}
.note {padding: 12px 16px; background: #1b2b3d; border-left: 3px solid #59cbb6; border-radius: 5px; color: #bdcfdd;}
.t-light {padding: 13px; margin: 3px 0; border-radius: 9px; background: #152235; text-align: center; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

storage.initialize_database()
OUTPUTS.mkdir(exist_ok=True, parents=True)


def available_videos() -> list[Path]:
    if not VIDEOS.is_dir():
        return []
    return sorted((p for p in VIDEOS.iterdir() if p.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv")), key=lambda x: x.name)


def hero(title: str, subtitle: str):
    st.markdown(f'<div class="hero"><small>TRAFFICIQ / LOCAL DEMONSTRATION</small><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def summary_table(summary: dict):
    data = summary.get("class_counts", {})
    df = pd.DataFrame([{"Vehicle class": name, "Tracked IDs": int(value)} for name,value in data.items()])
    return df


video_list = available_videos()
with st.sidebar:
    st.markdown("## 🚦 TrafficIQ")
    st.caption("Intelligent Traffic Management")
    page = st.radio("Navigate", ["Overview", "Video Analysis", "Signal Control", "Performance Lab", "Frame Review", "Tracking Diagnostics", "Violation Records", "Reports", "System Check"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Select traffic video**")
    if video_list:
        selected_video = st.selectbox("Source video", video_list,
                                      format_func=lambda p: p.name,
                                      help="Each video gets its own analysis folder. Switching videos never overwrites the other clip's result.")
    else:
        selected_video = None
        st.warning("No videos found in the videos/ folder.")
    st.caption("Local processing • your existing YOLO11s checkpoint")
    st.divider()
    st.caption("13 classes • ByteTrack • SQLite")
    st.caption("Prototype only — no physical traffic-light actuation")

meta = None
summary = None
if selected_video is not None:
    try:
        meta = video_info(selected_video)
        summary = load_summary(selected_video)
    except Exception as exc:
        st.error(f"Cannot inspect selected video: {exc}")

if page == "Overview":
    hero("AI-Powered Traffic Management", "Choose either supplied video, process vehicles with YOLO11s + ByteTrack, and explore a safe four-direction signal simulation.")
    a,b,c,d = st.columns(4)
    a.metric("Video sources", len(video_list))
    b.metric("Trained vehicle classes", 13)
    c.metric("Selected clip", selected_video.stem[:17] if selected_video else "Missing")
    d.metric("Analysis", "Ready" if summary else "Not processed")
    st.markdown("### Selected video")
    if selected_video and meta:
        left,right = st.columns([1.4,1])
        with left:
            preview = ASSETS / (selected_video.stem + ".jpg")
            if preview.is_file():
                st.image(str(preview), use_container_width=True)
            else:
                st.video(str(selected_video))
        with right:
            st.markdown(f"**File:** `{selected_video.name}`")
            st.write(f"**Resolution:** {meta['width']} × {meta['height']}")
            st.write(f"**Frame rate:** {meta['fps']:.1f} FPS")
            st.write(f"**Duration:** {meta['duration']:.1f} seconds")
            st.write(f"**Size:** {selected_video.stat().st_size/(1024**2):.1f} MB")
            st.info("Use **Video Analysis** to run or view vehicle detection on this selected clip.")
    st.markdown("### What the system demonstrates")
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown("**01 · Vision**")
        st.write("YOLO11s detection and confidence-weighted class voting for each ByteTrack ID.")
    with col2:
        st.markdown("**02 · Signals**")
        st.write("Sequential North, East, South, West GREEN phases with bounded timings and clearance states.")
    with col3:
        st.markdown("**03 · Records**")
        st.write("Per-video counts, tracking observations, manual incident records and exportable reports.")
    st.markdown('<div class="note">Video-visible counts are <b>not</b> reliable per-approach waiting queues. The signal simulator takes explicitly entered demand and does not claim control of the pictured junction.</div>', unsafe_allow_html=True)

elif page == "Video Analysis":
    hero("Video Analysis", "Select a video in the sidebar. Each source is processed and saved separately.")
    if selected_video and meta:
        c1,c2,c3 = st.columns(3)
        c1.metric("Duration", f"{meta['duration']:.1f}s")
        c2.metric("FPS", f"{meta['fps']:.1f}")
        c3.metric("Resolution", f"{meta['width']} × {meta['height']}")
        with st.expander("Preview original recording", expanded=summary is None):
            st.video(str(selected_video))
        st.markdown("### Inference settings")
        upper = max(1, int(math.ceil(meta['duration'])))
        seconds = st.slider("Process first N seconds", min_value=1, max_value=upper,
                            value=min(15,upper), step=1,
                            help="Start with 5–15 seconds to test your model and GPU before processing everything.")
        confidence = st.slider("Detection confidence", min_value=0.10, max_value=0.80,
                                value=0.30, step=0.05)
        prefer_gpu = st.checkbox("Use CUDA when available (RTX 3050)", value=True)
        st.caption("4K inputs are resized to max 1280px wide before inference. This changes processing resolution only.")
        if st.button("▶ Process selected video", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Starting model…")
            def progress(i,total):
                progress_bar.progress(min(1.0,i/max(1,total)), text=f"Processing frame {i}/{total}")
            try:
                with st.spinner("Running YOLO11s + ByteTrack. Keep this browser tab open…"):
                    result = process_video(selected_video, seconds, conf=confidence,
                                           progress=progress, prefer_gpu=prefer_gpu)
                    storage.add_run(result['video'], result['processed_seconds'],
                                    result['processed_frames'], result['unique_track_ids'],
                                    Path(result['output_dir']))
                st.success(f"Completed {result['processed_frames']} frames on {result['device']}.")
                st.rerun()
            except (OSError, ImportError) as exc:
                st.error(f"Model runtime could not load: {exc}")
                st.info("If WinError 4551 mentions c10_cuda.dll, Windows Application Control is blocking PyTorch. See WINDOWS_TROUBLESHOOTING.md; this is not caused by the dashboard.")
            except Exception as exc:
                st.exception(exc)
        summary = load_summary(selected_video)
        if summary:
            st.divider()
            st.markdown("### Saved analysis for this video")
            x,y,z = st.columns(3)
            x.metric("Processed frames", summary['processed_frames'])
            y.metric("Unique tracker IDs", summary['unique_track_ids'])
            z.metric("Processing device", summary['device'])
            if summary.get('warning'):
                st.warning(summary['warning'])
            st.video(summary['output_video'])
            df = summary_table(summary)
            st.bar_chart(df.set_index('Vehicle class')['Tracked IDs'])
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.caption(summary['methodology_note'])
            c1,c2,c3 = st.columns(3)
            with c1:
                with open(summary['counts_csv'], 'rb') as f:
                    st.download_button('Download vehicle counts', f, file_name=f"{selected_video.stem}_counts.csv", mime='text/csv', use_container_width=True)
            with c2:
                with open(summary['tracks_csv'], 'rb') as f:
                    st.download_button('Download track observations', f, file_name=f"{selected_video.stem}_observations.csv", mime='text/csv', use_container_width=True)
            with c3:
                with open(summary['output_video'], 'rb') as f:
                    st.download_button('Download annotated video', f, file_name=f"{selected_video.stem}_tracked.mp4", mime='video/mp4', use_container_width=True)
        else:
            st.info("This video has not been processed in this project copy yet. Click Process selected video above.")

elif page == "Signal Control":
    hero("Four-Way Signal Controller", "One GREEN direction at a time. GREEN duration is locked until countdown reaches zero.")
    st.markdown('<div class="note"><b>Simulation only:</b> Waiting counts below are manually provided or come from future trusted simulation inputs. Video detections are not assumed to be actual queues.</div>', unsafe_allow_html=True)
    st.markdown("### Waiting vehicles by approach")
    cols = st.columns(4)
    demand = {}
    defaults = {"North":15,"East":8,"South":3,"West":6}
    for idx,direction in enumerate(DIRECTIONS):
        with cols[idx]:
            demand[direction] = st.number_input(direction, 0, 1000, defaults[direction], 1, key=f"count_{direction}")
            st.caption(f"Next GREEN: {choose_green(int(demand[direction]))}s")
    demand = {k:int(v) for k,v in demand.items()}

    if 'controller' not in st.session_state:
        st.session_state.controller = SignalController.start(demand)
        st.session_state.controller_running = False
        st.session_state.controller_last_time = time.monotonic()
        st.session_state.controller_seconds = 0
    c1,c2,c3,c4 = st.columns([1,1,1,1])
    with c1:
        if st.button("▶ Start / Resume", use_container_width=True):
            st.session_state.controller_running = True
            st.session_state.controller_last_time = time.monotonic()
    with c2:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.controller_running = False
    with c3:
        if st.button("+1 second", use_container_width=True):
            st.session_state.controller.tick(demand, seconds=1)
            st.session_state.controller_seconds += 1
            st.session_state.controller_last_time = time.monotonic()
    with c4:
        if st.button("↺ Reset cycle", use_container_width=True):
            st.session_state.controller = SignalController.start(demand)
            st.session_state.controller_running = False
            st.session_state.controller_last_time = time.monotonic()
            st.session_state.controller_seconds = 0

    @st.fragment(run_every="1s")
    def live_signals():
        now = time.monotonic()
        if st.session_state.controller_running:
            elapsed = max(0, int(now - st.session_state.controller_last_time))
            if elapsed:
                st.session_state.controller.tick(demand, seconds=min(elapsed,600))
                st.session_state.controller_seconds += min(elapsed,600)
                st.session_state.controller_last_time += elapsed
        else:
            st.session_state.controller_last_time = now
        controller = st.session_state.controller
        lights = controller.lights()
        row = st.columns(4)
        for idx,d in enumerate(DIRECTIONS):
            with row[idx]:
                state = lights[d]
                bg = '#147d62' if state == 'GREEN' else '#9b7520' if state == 'YELLOW' else '#853e4d'
                st.markdown(f'<div class="t-light" style="border:1px solid {bg};"><span style="color:{"#70e3be" if state=="GREEN" else "#ffd886" if state=="YELLOW" else "#ff9a9a"};">● {d.upper()}<br>{state}</span></div>', unsafe_allow_html=True)
        a,b,c = st.columns(3)
        a.metric("Active direction", controller.active)
        b.metric("Current phase", controller.state)
        c.metric("Countdown", f"{controller.remaining}s")
        st.caption(f"Simulation time: {st.session_state.controller_seconds}s • Completed GREEN phases: {controller.completed_greens}")
        assert sum(v == 'GREEN' for v in lights.values()) <= 1
    live_signals()
    st.caption("Transitions: GREEN → YELLOW (3s) → ALL RED (2s) → next direction GREEN. Yellow/all-red values are illustrative, not certified road-safety timings.")

elif page == "Performance Lab":
    hero("Simulation Performance Lab", "Reproducible synthetic queues: compare fixed-time and adaptive control without using real-world claims.")
    st.warning("This comparison uses synthetic traffic arrivals, not vehicle counts from the uploaded videos. It does not measure real intersection performance.")
    x, y = st.columns(2)
    with x:
        duration = st.slider('Simulated duration (minutes)', 2, 30, 10, step=1)
    with y:
        random_seed = st.number_input('Random seed', min_value=0, max_value=100000, value=42)
    st.markdown('#### Synthetic arrival rates (vehicles per second)')
    rows = st.columns(4)
    rates = {}
    for idx,d in enumerate(DIRECTIONS):
        with rows[idx]:
            rates[d] = st.slider(d, min_value=0.0, max_value=1.5,
                                 value={'North':.32,'East':.22,'South':.18,'West':.25}[d], step=.02,
                                 key=f'lab_arrival_{d}')
    if st.button('Run reproducible comparison', type='primary'):
        report = compare(duration*60, rates, seed=int(random_seed))
        save_report(report, OUTPUTS / 'simulation')
        st.session_state.performance_lab_report = report
    report = st.session_state.get('performance_lab_report')
    if report:
        comparison = []
        records = []
        for policy, details in report['policies'].items():
            comparison.append({
                'Policy':policy, 'Arrived':details['arrived'],
                'Served':details['served'], 'Remaining queue':details['end_queue'],
                'Avg wait, served only (s)': details['avg_wait_served_seconds'],
                'Mean queue size':details['avg_queue_vehicles'],
                'Peak queue':details['peak_queue_vehicles'],
            })
            records.extend(details['timeline'])
        st.markdown('### Comparative metrics')
        st.dataframe(pd.DataFrame(comparison), hide_index=True, use_container_width=True)
        st.markdown('### Queue size over simulated time')
        timeline = pd.DataFrame(records)
        st.line_chart(timeline, x='second', y='queued', color='policy')
        st.caption('Both policies see the same Poisson arrivals, and serve at most 1 vehicle per GREEN second. GREEN/YELLOW/ALL RED are time-limited. Average wait excludes vehicles still queued at the end; comparisons are illustrative only.')
        report_path = OUTPUTS/'simulation'/'simulation_comparison.json'
        timeline_path = OUTPUTS/'simulation'/'simulation_timeline.csv'
        if report_path.is_file() and timeline_path.is_file():
            c1,c2 = st.columns(2)
            with c1:
                st.download_button('Download simulation report', report_path.read_bytes(),
                                   file_name='simulation_comparison.json', mime='application/json')
            with c2:
                st.download_button('Download synthetic timeline', timeline_path.read_bytes(),
                                   file_name='simulation_timeline.csv', mime='text/csv')
    else:
        st.info('Choose synthetic demand and run the simulation comparison.')

elif page == "Frame Review":
    hero("Full-Resolution Frame Review", "Inspect reference frames extracted losslessly from both uploaded videos.")
    st.info('These are original, unannotated video frames. Use them to review camera perspective and potential ROI placements, not as ground-truth detection results.')
    catalog_path = ROOT / 'reference_frames' / 'catalog.csv'
    if not catalog_path.is_file():
        st.warning('Optional frame library not installed. The videos can still be processed normally.')
    elif selected_video is None:
        st.warning('Choose a source video in the sidebar first.')
    else:
        catalog = pd.read_csv(catalog_path)
        catalog = catalog[catalog['source_video'] == selected_video.name].reset_index(drop=True)
        if catalog.empty:
            st.warning('No reference frames available for this source.')
        else:
            st.metric('Full-resolution reference frames', len(catalog))
            idx = st.slider('Select extracted frame', 1, len(catalog), 1)-1
            record = catalog.iloc[idx]
            thumb = ROOT / str(record['thumbnail_path'])
            image = ROOT / str(record['image_path'])
            st.image(str(thumb if thumb.is_file() else image),
                     caption=f"Source {selected_video.name} · approximately {record['timestamp_seconds']:.2f}s · native resolution {record['width']}×{record['height']}",
                     use_container_width=True)
            st.caption('Use the downloaded native-resolution PNG for zooming and detailed ROI review. The display image is a smaller preview.')
            with image.open('rb') as img:
                st.download_button('Download native-resolution frame (PNG)', img.read(),
                                   file_name=image.name, mime='image/png')
            with catalog_path.open('rb') as f:
                st.download_button('Download frame catalog CSV', f.read(),
                                   file_name='frame_catalog.csv', mime='text/csv')

elif page == "Tracking Diagnostics":
    hero("Tracking Diagnostics", "Investigate class changes under one tracking ID; compare your historical tracking clips.")
    st.markdown('### Current selection')
    if selected_video and summary and Path(summary.get('tracks_csv','')).is_file():
        info = analyze_observations(Path(summary['tracks_csv']))
        a,b = st.columns(2)
        a.metric('Unique observed track IDs', info['unique_track_ids'])
        b.metric('IDs with class label changes', info['ids_with_class_changes'])
        table = pd.DataFrame(info['tracks'])
        st.dataframe(table, hide_index=True, use_container_width=True)
        st.caption(info['disclaimer'])
        if not table.empty:
            st.download_button('Download track diagnostics CSV', table.to_csv(index=False),
                               file_name=f'{selected_video.stem}_diagnostics.csv', mime='text/csv')
    else:
        st.info('Run Video Analysis on the selected video to generate its track observations and consistency report.')
    st.markdown('### Historical ByteTrack configuration test')
    st.caption('The following uploaded 30-second clips come from your earlier camera test, not the two currently selected traffic videos. They are provided for manual comparison only.')
    reference_video = ROOT / 'reference_videos'
    original = reference_video/'tracked_video_original_30s.mp4'
    stable = reference_video/'tracked_video_stable_test_h264.mp4'
    if original.is_file() and stable.is_file():
        tab_original,tab_stable = st.tabs(['Original ByteTrack: 30-frame buffer', 'Experimental ByteTrack: 60-frame buffer'])
        with tab_original:
            st.video(str(original))
        with tab_stable:
            st.video(str(stable))
        st.caption('Increasing the tracker buffer from 30 to 60 was not shown to improve identity consistency; treat class flips and fragmented IDs as known limitations.')
    else:
        st.caption('Optional historical tracking clips are not bundled in this copy.')

elif page == "Violation Records":
    hero("Violation Event Register", "Manually document observed traffic events with optional image evidence.")
    st.warning("No helmet, triple-riding, wrong-way or red-light violation is automatically verified using this vehicle-only model.")
    with st.form('record_event', clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            vehicle_id = st.text_input('Vehicle / tracker ID (optional)')
            vehicle_class = st.selectbox('Vehicle class', TRAINED_CLASSES)
            kind = st.selectbox('Event type', VIOLATIONS)
        with c2:
            location = st.text_input('Camera / location', value='Demo camera')
            notes = st.text_area('Notes / observations')
            evidence = st.file_uploader('Evidence image (optional)', type=['jpg','jpeg','png'])
        if st.form_submit_button('Save manual event', type='primary'):
            try:
                storage.add_event(vehicle_id, vehicle_class, kind, location, notes, evidence)
                st.success('Manual event saved locally.')
                st.rerun()
            except Exception as exc:
                st.error(f'Could not save event: {exc}')
    records = storage.get_events()
    st.markdown(f'### Stored records: {len(records)}')
    if records.empty:
        st.info('No records have been entered. Submit the form above to test SQLite persistence.')
    else:
        kinds = sorted(records['violation_type'].dropna().unique().tolist())
        filter_kind = st.selectbox('Filter event type', ['All'] + kinds)
        displayed = records if filter_kind == 'All' else records[records['violation_type'] == filter_kind]
        st.dataframe(displayed.drop(columns=['evidence_path'], errors='ignore'), hide_index=True, use_container_width=True)
        st.download_button('Export displayed events CSV', displayed.to_csv(index=False).encode('utf-8'), file_name='violations.csv', mime='text/csv')
        for _,rec in displayed.iterrows():
            evidence_path = Path(rec.get('evidence_path') or '')
            if evidence_path.is_file():
                with st.expander(f"Evidence for record #{rec['id']}"):
                    st.image(str(evidence_path), use_container_width=True)

elif page == "Reports":
    hero("Reports & Exports", "Per-video analytics, completion logs and manually recorded traffic events.")
    if selected_video:
        st.markdown(f"### Selected source: `{selected_video.name}`")
    if summary:
        df = summary_table(summary)
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.metric('Unique track IDs (not guaranteed distinct vehicles)', summary['unique_track_ids'])
        st.caption(summary['methodology_note'])
        with open(summary['counts_csv'],'rb') as f:
            st.download_button('Download selected source counts',f,file_name=f'{selected_video.stem}_counts.csv',mime='text/csv')
    else:
        st.info('Run an analysis on the selected video to populate its count report.')
    st.markdown('### Saved processing runs')
    runs = storage.get_runs()
    if runs.empty:
        st.caption('No completed inference runs recorded yet.')
    else:
        st.dataframe(runs, use_container_width=True, hide_index=True)
        st.download_button('Export processing history',runs.to_csv(index=False).encode('utf-8'),file_name='processing_runs.csv',mime='text/csv')
    st.markdown('### Manual event export')
    events = storage.get_events()
    st.caption(f'{len(events)} stored manual event records')
    if not events.empty:
        st.download_button('Download manual event CSV',events.to_csv(index=False).encode('utf-8'),file_name='events.csv',mime='text/csv')

elif page == "System Check":
    hero("System Check", "Verify available files and diagnose Windows or CUDA installation problems.")
    statuses = [
        ("Trained model",MODEL_PATH, MODEL_PATH.is_file()),
        ("Tracker configuration",ROOT/'tracker.yaml',(ROOT/'tracker.yaml').is_file()),
        ("Video A", VIDEOS/'244024_medium.mp4',(VIDEOS/'244024_medium.mp4').is_file()),
        ("Video B", VIDEOS/'12937233_3840_2160_30fps.mp4',(VIDEOS/'12937233_3840_2160_30fps.mp4').is_file()),
        ("SQLite database",storage.DB_PATH,storage.DB_PATH.is_file()),
    ]
    st.dataframe(pd.DataFrame([{"Item":title,"Status":"Present" if ok else "Missing","Path":str(path)} for title,path,ok in statuses]), use_container_width=True,hide_index=True)
    if st.button('Check PyTorch / CUDA imports'):
        try:
            import torch
            from ultralytics import YOLO
            st.success(f"PyTorch {torch.__version__}; CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                st.write(f"GPU: {torch.cuda.get_device_name(0)}")
            model = YOLO(str(MODEL_PATH))
            st.write('Checkpoint loaded; class labels:',model.names)
        except Exception as exc:
            st.error(f'Runtime check failed: {exc}')
            st.info('Windows WinError 4551 may mean Application Control blocks c10_cuda.dll. See WINDOWS_TROUBLESHOOTING.md and use an approved Python environment.')
    st.markdown('### Mode boundaries')
    st.markdown('- Detection and tracking use the supplied pretrained YOLO11s checkpoint.\n- Class accuracy and identity continuity are not guaranteed.\n- The four-way signal animation uses **simulated approach queues**, not automatically inferred waiting zones.\n- SQLite violation records are **manual**.\n- Unreal Engine is **not bundled**; a JSON bridge example is included for a future integration.')
    st.caption('Historic checkpoint evaluation reported: P 72.89%, R 70.50%, mAP50 75.59%, mAP50-95 64.78% at epoch 94; these numbers have not been reproduced in this packaged application.')
