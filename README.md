<div align="center">

# 🚶‍♂️ SmartCrowd: Real-Time Crowd Analytics & People Counting Platform
### AI-Powered Multi-Object Tracking (YOLOv11 + ByteTrack) with Cloud Data Lakehouse Architecture (Databricks Unity Catalog)

[![Live Demo](https://img.shields.io/badge/%F0%9F%A4%97%20LIVE%20DEMO-Try%20Now!-FF6B35?style=for-the-badge)](https://minhunhooo-crowd-people-counter.hf.space/)&nbsp;&nbsp;[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MinHung1411/smartcrowd-visionai)&nbsp;&nbsp;[![Author](https://img.shields.io/badge/Author-Ho%20Minh%20Hung-2ea44f?style=for-the-badge)](https://github.com/MinHung1411)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/YOLOv11m-Ultralytics-FF6B35?logo=yolo&logoColor=white" alt="YOLOv11">
  <img src="https://img.shields.io/badge/Tracking-ByteTrack-00C49F" alt="ByteTrack">
  <img src="https://img.shields.io/badge/mAP@50-95.8%25-brightgreen" alt="mAP">
  <img src="https://img.shields.io/badge/Flask-2.3-green?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Databricks-Unity_Catalog-red?logo=databricks&logoColor=white" alt="Databricks">
  <img src="https://img.shields.io/badge/Docker-Containerized-blue?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

</div>

---

## 📋 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Model Evaluation & Benchmarks](#-model-evaluation--benchmarks)
- [Databricks Medallion Lakehouse](#-databricks-medallion-lakehouse)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Author](#-author)
- [License](#-license)

---

## 🔍 Overview

**SmartCrowd** is an enterprise-grade Computer Vision and Big Data analytics platform engineered to monitor, count, and analyze pedestrian flow and crowd density in public spaces (smart buildings, retail stores, transit stations, and events).

The system seamlessly bridges **Edge Computer Vision** with a **Cloud-Native Data Lakehouse**:
1. **Real-time Edge Vision**: Utilizes a fine-tuned **YOLOv11 Medium** model combined with **ByteTrack** multi-object tracking to detect persons in dense crowds, maintain unique identities, and track bi-directional virtual line crossing (**IN / OUT**).
2. **Cloud Data Lakehouse (Medallion Pipeline)**: Continuously streams traffic events and density metrics into **Databricks Unity Catalog**, running automated **Bronze → Silver → Gold** ETL pipelines for real-time BI reporting, peak hour detection, and safety compliance audits.

> 🌐 **Live Model Demo**: [minhunhooo-crowd-people-counter.hf.space](https://minhunhooo-crowd-people-counter.hf.space/)

---

## ✨ Key Features

| Feature | Description | Technology |
|---|---|---|
| 🚶‍♂️ **Dense Crowd Detection** | Detects people in overlapping, crowded scenes without missing small/occluded bodies | YOLOv11m fine-tuned on CrowdHuman |
| 🔄 **Bi-directional Counting** | Virtual crossing line detects direction: entry (**IN +1**) vs exit (**OUT +1**) | ByteTrack + Line Crossing Vector |
| 🏢 **Occupancy Monitoring** | Live calculation of current persons in the area and net occupancy ($\text{IN} - \text{OUT}$) | Real-time Sliding Window State |
| ⚠️ **Overcrowding Safety Alert** | Immediate visual alarm and database flag when crowd count exceeds safety threshold | Dynamic Threshold Detector |
| 🎨 **Crowd Density Heatmap** | Accumulates movement paths and overlays a thermal density map on CCTV view | Gaussian Blur + OpenCV Colormap JET |
| 📊 **Databricks Analytics** | Hourly traffic distribution, peak shift summary, and safety violation audit logs | Databricks Unity Catalog (SQL) |
| 🔐 **User Management** | Role-based access control (Admin / Operator), audit logging, and CSV export | Flask-Login + bcrypt |

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[📷 CCTV / Webcam Stream] -->|Base64 Frames| B[🌐 Flask Web Application]
    B -->|Inference Frame| C[🤖 YOLOv11m Engine]
    C -->|Bounding Boxes| D[🎯 ByteTrack Multi-Object Tracker]
    D -->|Centroid Trajectories| E[📐 Line Crossing Vector Engine]
    
    E -->|Real-time HUD| F[🖥️ Live Monitoring UI]
    E -->|Thermal Coordinates| G[🎨 Crowd Heatmap Generator]
    
    E -->|Crowd Metrics & Events| H[(🗄️ Databricks Unity Catalog)]
    
    H --> I[🥉 Bronze Layer<br/>Raw Traffic Logs]
    I --> J[🥈 Silver Layer<br/>Feature Engineering & Shift Classification]
    J --> K[🥇 Gold Layer<br/>Hourly Aggregates & Safety Violation Logs]
    K --> L[📊 Executive BI Dashboard]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF6B35,color:#fff
    style D fill:#9C27B0,color:#fff
    style H fill:#E24A4A,color:#fff
    style K fill:#FFD700,color:#000
    style L fill:#00BCD4,color:#fff
```

---

## 📊 Model Evaluation & Benchmarks

The core vision model was fine-tuned from **YOLOv11m** on the challenging **CrowdHuman Benchmark** (15,000 train images, 4,370 validation images) using NVIDIA Tesla T4 GPU acceleration:

| Metric | Value | Comparison vs Baseline |
|---|:---:|:---:|
| **Architecture** | **YOLOv11 Medium (`best.pt`)** | SOTA Ultralytics release |
| **Dataset** | **CrowdHuman (Dense Crowds)** | Benchmark standard |
| **mAP@50** | **95.8%** | +24.8% over COCO default |
| **mAP@50-95** | **84.8%** | +39.8% over COCO default |
| **Precision** | **88.0%** | Minimal false positives |
| **Recall** | **90.1%** | Detects heavily occluded persons |
| **Inference Latency** | **~8ms (GPU) / ~35ms (CPU)** | 60+ FPS Real-time capability |
| **Tracking Algorithm** | **ByteTrack (`bytetrack.yaml`)** | ID-consistent tracking |

---

## ☁️ Databricks Medallion Lakehouse

Traffic metrics and safety alerts flow through 3 structured Delta Lake layers:

### 1. 🥉 Bronze Layer (`bronze.raw_crowd_detections`)
Raw view joining web telemetry and user audit trails: captures timestamp, camera identifier, `people_in_frame`, `total_entered`, `total_exited`, `density_level`, and `is_overcrowded`.

### 2. 🥈 Silver Layer (`silver.crowd_traffic_enriched`)
Cleaned and enriched with **6 engineered analytical features**:
- `hour_of_day`: 0 – 23 hour bucket.
- `time_shift`: `MORNING_PEAK`, `AFTERNOON`, `EVENING_PEAK`, `NIGHT_OFFPEAK`.
- `traffic_intensity`: `LIGHT` (<5), `MODERATE` (5-15), `HEAVY` (16-25), `CRITICAL_CONGESTION` (>25).
- `net_occupancy`: $\max(0, \text{total\_entered} - \text{total\_exited})$.
- `latency_grade`: `REALTIME_FAST` (<50ms) vs `ACCEPTABLE`.
- `is_weekend`: Weekday vs Weekend traffic flag.

### 3. 🥇 Gold Layer (Executive Analytics Tables)
- `gold.hourly_crowd_traffic`: Hourly volume, inflow/outflow, and peak crowd sizes.
- `gold.shift_occupancy_summary`: Density distribution by operational work shifts.
- `gold.overcrowding_safety_alerts`: Audit trail of all safety limit violations for compliance reporting.
- `gold.ai_inference_performance`: Latency percentiles, min/max runtime, and effective processing FPS.
- `gold.ml_experiment_log`: Benchmark history comparing YOLOv8, YOLOv10, and YOLOv11.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Webcam or video file
- (Optional) Databricks workspace credentials

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/MinHung1411/smartcrowd-visionai.git
cd smartcrowd-visionai

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Web Application

```bash
# Navigate to src and run
cd src
python run.py
```

Open your browser at **`http://localhost:5000`**

**Default Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

---

## 📁 Project Structure

```
smartcrowd-visionai/
│
├── src/                               # Web Application Source
│   ├── app/
│   │   ├── models/                    # SQLAlchemy ORM (User, Detection)
│   │   ├── services/
│   │   │   ├── crowd_service.py       # YOLOv11m + ByteTrack + Line Crossing Engine
│   │   │   └── db_service.py          # Database & Databricks synchronization
│   │   ├── templates/                 # Jinja2 HTML (Tailwind CSS Dark HUD)
│   │   │   ├── detection/camera.html  # Live CCTV People Counting interface
│   │   │   ├── detection/upload.html  # Image analysis interface
│   │   │   └── dashboard.html         # Analytics & Charts
│   │   └── views/                     # Flask Blueprints
│   ├── best.pt                        # YOLOv11m fine-tuned model (~40.5 MB)
│   ├── config/config.py               # Application configurations
│   ├── requirements.txt               # Dependencies
│   └── run.py                         # Application entrypoint
│
├── sql/                               # Databricks Lakehouse SQL Pipelines
│   ├── 01_create_schemas.sql          # Bronze, Silver, Gold schemas
│   ├── 02_bronze_from_app.sql         # Raw traffic data view
│   ├── 03_silver_enriched.sql         # Feature engineering table
│   ├── 04_gold_tables.sql             # 4 Business intelligence summary tables
│   └── 05_mlflow_experiment.sql       # MLflow experiment log & benchmark
│
├── docker/                            # Production Docker configurations
├── docs/                              # Architecture diagrams and demo images
└── README.md                          # Project documentation
```

---

## 👨‍💻 Author

**Hồ Minh Hưng**
- GitHub: [@MinHung1411](https://github.com/MinHung1411)
- Hugging Face: [@minhunhooo](https://huggingface.co/minhunhooo)
- Email: `hmhung1411@gmail.com`

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
