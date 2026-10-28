# SmartCrowd VisionAI — Production Source Module (`src/`)

Welcome to the core service module of **SmartCrowd VisionAI**, an enterprise Computer Vision & Lakehouse analytics application developed by **Hồ Minh Hưng**.

---

## 🌟 Module Architecture

The application is engineered with a modular, decoupled architecture adhering to production Python best practices:

```
src/
├── app/
│   ├── models/                # SQLAlchemy Models (User, Detection, AuditLog)
│   ├── services/
│   │   ├── crowd_service.py   # YOLOv11m + ByteTrack + ROI Polygon + Video Analytics Engine
│   │   ├── alert_service.py   # Telegram Bot & Webhook Incident Dispatcher
│   │   ├── db_service.py      # Databricks Lakehouse synchronization & SQLite fallback
│   │   └── classification_service.py # Auxiliary Vision Classifiers
│   ├── templates/             # Cyberpunk Dark HUD Jinja2 Templates (Tailwind CSS + FontAwesome)
│   │   ├── auth/login.html    # Recruiter-focused 1-Click Login & Dual Credential Switcher
│   │   ├── dashboard.html     # Real-time KPIs, AI Shift Briefing & Hourly Traffic Curves
│   │   ├── detection/camera.html # CCTV Live Video Tracking, Bi-directional Flux & Virtual Fence
│   │   ├── detection/video.html  # CCTV Video Upload, Trajectory Profiling & Heatmap Export
│   │   ├── detection/upload.html # High-density Crowd Image Analysis
│   │   └── history.html       # Medallion Audit Trails & CSV Incident Export
│   └── views/                 # Flask Blueprints (auth, detection, main)
├── config/
│   └── config.py              # Environment configuration & Lakehouse connection parameters
├── data/
│   └── 01_databricks_seed.sql # Databricks seed schemas & lakehouse tables
├── docker/                    # Multi-stage Dockerfile and Docker Compose configurations
├── best.pt                    # Fine-tuned YOLOv11 Medium model weights (~40.5 MB)
├── requirements.txt           # Core Python dependencies
└── run.py                     # Local standalone development server entrypoint
```

---

## 🤖 Vision Engine Specifications

- **Model**: Fine-tuned **YOLOv11 Medium (`best.pt`)**
- **Pre-trained Benchmark**: CrowdHuman Dataset (15,000+ dense pedestrian images)
- **mAP@50**: 95.8%
- **Multi-Object Tracking**: ByteTrack (`bytetrack.yaml`) with centroid motion smoothing
- **Virtual Line Crossing**: Vector direction dot-product tracking (IN / OUT)
- **Virtual Fence (Polygon ROI)**: Millisecond point-in-polygon verification (`cv2.pointPolygonTest`)
- **Cumulative Spatial Heatmap**: Gaussian 2D density accumulation with OpenCV `COLORMAP_JET`

---

## 🔐 Authentication & Roles

The system seeds two standard accounts at startup:
- **Demo Reviewer** (`demo` / `demo123`, role: `viewer`): Dedicated account for recruiters and evaluators to test all live detection and video analytics features without administrative side effects.
- **Administrator** (`admin` / `admin123`, role: `admin`): Full administrative rights, configuration sliders, and security logs.

---

## 🚀 Running Locally

```bash
cd src
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
python run.py
```
App runs at `http://localhost:5000`.
