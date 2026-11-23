# 🚦 AI-Powered Intelligent Traffic Management System (TrafficIQ)

An intelligent traffic management prototype developed using **Deep Learning, Computer Vision, and Python** to detect and track vehicles, analyze traffic patterns, and simulate adaptive traffic signal control.

## Project Overview

TrafficIQ aims to demonstrate how artificial intelligence can support traffic monitoring and signal management.

The system uses a trained **YOLO11s** model for vehicle detection, **ByteTrack** for vehicle tracking, and **Streamlit** for an interactive dashboard.

It also includes a four-way adaptive traffic signal simulation, SQLite-based manual violation records, and downloadable analytics reports.

## Key Features

- Vehicle detection using YOLO11s
- Vehicle tracking using ByteTrack
- Classification of 13 vehicle classes
- Traffic video processing and annotated playback
- Four-way adaptive traffic signal simulation
- Dynamic green-light durations based on simulated traffic demand
- Safe yellow and all-red signal transitions
- Vehicle analytics and CSV reports
- Manual traffic violation record management
- SQLite database integration
- Streamlit monitoring dashboard
- Unreal Engine 5 simulation prototype (under development)

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend and processing |
| YOLO11s | Vehicle detection |
| Ultralytics | Deep learning framework |
| ByteTrack | Multi-object tracking |
| OpenCV | Video processing |
| Streamlit | Web dashboard |
| PyTorch | Model inference |
| SQLite | Violation record storage |
| Pandas | Data analysis |
| FFmpeg | Browser-compatible video conversion |
| Unreal Engine 5 | 3D traffic simulation development |

## System Architecture

```text
Traffic Video
     |
     v
YOLO11s Vehicle Detection
     |
     v
ByteTrack Vehicle Tracking
     |
     v
Vehicle Statistics & Analytics
     |
     v
Streamlit Dashboard
     |
     +---- Reports & CSV Export
     |
     +---- SQLite Violation Records
     |
     +---- Adaptive Signal Simulation
                 |
                 v
          Four-Way Traffic Control
```

The current signal simulation uses manually entered or simulated vehicle queues rather than automatically measured four-way intersection queues.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Powered-Intelligent-Traffic-Management-System.git
```

### 2. Open the project directory

```bash
cd AI-Powered-Intelligent-Traffic-Management-System
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the dashboard

```bash
python -m streamlit run dashboard.py
```

Open:

`http://localhost:8501`

**Note:** The sample traffic videos are excluded from GitHub because of their size. Add compatible input videos to the `videos/` folder before running video analysis.

## Traffic Signal Simulation

The system simulates traffic control for four directions:

- North
- East
- South
- West

Green-light duration is selected based on simulated traffic demand.

| Signal Phase | Duration |
|---|---|
| Green | 20, 30, or 45 seconds |
| Yellow | 3 seconds |
| All Red | 2 seconds |

**Safety rule:** Only one direction can have a green signal at any time.

## Model Information

- **Model:** YOLO11s
- **Dataset:** BMD-45
- **Vehicle classes:** 13
- **Inference:** CPU supported
- **Tracking algorithm:** ByteTrack

### Reported Model Evaluation

| Metric | Score |
|---|---:|
| Precision | 72.89% |
| Recall | 70.50% |
| mAP@50 | 75.59% |
| mAP@50:95 | 64.78% |

These are previously reported validation results for the trained model.

## Dashboard Modules

1. Overview
2. Video Analysis
3. Signal Control
4. Performance Lab
5. Frame Review
6. Tracking Diagnostics
7. Violation Records
8. Reports
9. System Check

## Testing

Run the automated tests using:

```bash
python -m unittest discover -s tests -v
```

The project has previously passed 10 automated tests.

## Current Limitations

- Vehicle tracking IDs may change, so ID totals are not guaranteed to equal distinct vehicle counts.
- The adaptive signal controller operates on simulated or manually entered traffic demand.
- Helmet and red-light violations are not automatically detected by the vehicle-only model.
- The Unreal Engine integration is under development and has not yet been verified in Unreal Editor.

## Future Scope

- Real-time traffic camera integration
- Automatic lane-wise vehicle counting
- Improved tracking accuracy
- Emergency vehicle prioritization
- Automated traffic violation detection
- Unreal Engine 5 traffic visualization
- GPU-accelerated inference

## Project Type

**B.Tech Major Project / Project-Based Learning**

**Project Title:** AI-Powered Intelligent Traffic Management System

**Application:** Intelligent Transportation Systems, Deep Learning, Computer Vision, and Traffic Analytics
