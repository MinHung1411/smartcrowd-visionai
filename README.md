<p align="center">
  <img src="docs/images/banner.png" alt="VisionAI Banner" width="100%"/>
</p>

<p align="center">
  <strong>🔍 AI-Powered Real-time Object Detection Platform with Data Lakehouse Architecture</strong>
</p>

<p align="center">
  <a href="https://github.com/dovanminh1001/visionai-databricks/actions"><img src="https://github.com/dovanminh1001/visionai-databricks/actions/workflows/ci.yml/badge.svg" alt="CI/CD"></a>
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3-green?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-purple?logo=yolo&logoColor=white" alt="YOLOv8">
  <img src="https://img.shields.io/badge/Databricks-Unity_Catalog-red?logo=databricks&logoColor=white" alt="Databricks">
  <img src="https://img.shields.io/badge/Docker-Containerized-blue?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-contributors">Contributors</a>
</p>

---

## 📋 Overview

**VisionAI** is a full-stack, production-ready AI platform that combines **real-time computer vision** with a **cloud-native Data Lakehouse** architecture. The system enables users to detect objects, recognize faces, analyze colors, and classify images through an intuitive web interface — while all analytical data flows through a **Medallion (Bronze → Silver → Gold)** pipeline on **Databricks Unity Catalog** for advanced business intelligence.

> 🌐 **Live Demo**: [visionai-databricks.onrender.com](https://visionai-databricks.onrender.com)

---

## ✨ Features

| Feature | Description | Model/Algorithm |
|---------|-------------|-----------------|
| 🎯 **Object Detection** | Real-time detection of 80+ object classes via camera or image upload | YOLOv8 Nano |
| 👤 **Face Recognition** | Detect & identify registered faces with template matching | Haar Cascade + OpenCV |
| 🎨 **Color Analysis** | Extract 5 dominant colors from any image with HEX/RGB values | K-Means Clustering |
| 📊 **Object Classification** | Classify objects with bilingual labels (English/Vietnamese) | YOLOv8 + Custom Labels |
| 😀 **Emotion Detection** | Detect facial emotions from camera or uploaded images | OpenCV Cascade |
| 📈 **Analytics Dashboard** | Real-time statistics, charts, and detection history | Databricks SQL + Gold Tables |
| 👥 **User Management** | Role-based access control (Admin/User), profile management | Flask-Login + bcrypt |
| 📤 **Data Export** | Export detection history as CSV with full details | Flask Response |

---

## 🏗 Architecture

<p align="center">
  <img src="docs/images/architecture.png" alt="System Architecture" width="90%"/>
</p>

### Data Flow & Medallion Architecture

```mermaid
graph LR
    A[📷 Camera / Image Upload] -->|Base64 / File| B[🌐 Flask Web App]
    B -->|YOLOv8 Inference| C[🤖 AI Engine]
    C -->|Detection Results| D[(🗄️ Databricks Unity Catalog)]
    B -->|Upload Image| E[🤗 Hugging Face Dataset]

    D --> F[🥉 Bronze Layer<br/>Raw Detections]
    F --> G[🥈 Silver Layer<br/>Feature Engineering]
    G --> H[🥇 Gold Layer<br/>Aggregated Analytics]
    H --> I[📊 Databricks Dashboard]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#9C27B0,color:#fff
    style D fill:#FF5722,color:#fff
    style E fill:#FFD700,color:#000
    style I fill:#00BCD4,color:#fff
```

### Medallion Layers Detail

| Layer | Table | Purpose | Update Frequency |
|-------|-------|---------|-----------------|
| 🥉 **Bronze** | `bronze.raw_detections` | Raw data VIEW joining detections + users | Real-time (on write) |
| 🥈 **Silver** | `silver.detections_enriched` | +6 engineered features (time_shift, speed_grade, etc.) | Every 15 minutes |
| 🥇 **Gold** | `gold.detection_by_feature` | Aggregated stats by AI feature | Every hour |
| 🥇 **Gold** | `gold.detection_by_shift` | Activity breakdown by work shift | Every hour |
| 🥇 **Gold** | `gold.hourly_activity` | Hourly usage patterns | Every hour |
| 🥇 **Gold** | `gold.speed_analysis` | AI processing speed analytics | Every hour |
| 🥇 **Gold** | `gold.ml_experiment_log` | MLflow-style model training history | Daily at 2 AM |

---

## 📸 Screen Demos & Platform Integration

Here are some screenshots demonstrating the frontend web application and the Databricks Lakehouse data engineering backend:

### 1. Web Application - Dashboard Overview
The main dashboard provides real-time statistics of total detections, quick shortcuts to all 5 AI features, recent activity stream, and connection status.
<p align="center">
  <img src="docs/images/dashboard_overview.png" alt="Dashboard Overview" width="90%"/>
</p>

### 2. Web Application - Activity Log & Admin Panel
The admin area provides user management and a comprehensive detection log. Admins can view detailed parameters of each detection, download CSV records, and manage account details.
<p align="center">
  <img src="docs/images/activity_log.png" alt="Activity Log & Admin Panel" width="90%"/>
</p>

### 3. Databricks - Unity Catalog (Bronze Layer)
Detection events and metadata are sent directly to the Databricks Unity Catalog (`bronze.raw_detections`), providing a centralized, secure, and governed audit trail.
<p align="center">
  <img src="docs/images/databricks_catalog.png" alt="Databricks Unity Catalog" width="90%"/>
</p>

### 4. Databricks - Workflow Jobs & Pipelines
Automated jobs manage the pipeline lifecycle on Databricks: scheduling ingestion (every 15 min), system monitoring analytics updates (every hour), and daily machine learning model evaluation runs.
<p align="center">
  <img src="docs/images/databricks_jobs.png" alt="Databricks Workflow Jobs" width="90%"/>
</p>

---

## 🛠 Tech Stack

<table>
<tr>
<td valign="top" width="33%">

### 🖥️ Backend
- Python 3.11
- Flask + SQLAlchemy
- Flask-Login (Auth)
- Gunicorn (WSGI)
- bcrypt (Password Hashing)

</td>
<td valign="top" width="33%">

### 🤖 AI / ML
- YOLOv8 (Ultralytics)
- OpenCV (Computer Vision)
- Haar Cascade (Face Detection)
- K-Means (Color Analysis)
- PyTorch (CPU-optimized)

</td>
<td valign="top" width="33%">

### ☁️ Cloud & Data
- Databricks Unity Catalog
- Delta Lake (Medallion)
- Hugging Face Datasets
- Docker + Nginx
- GitHub Actions CI/CD

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ and pip
- Docker & Docker Compose (optional, for containerized deployment)
- Databricks workspace with Unity Catalog (for data pipeline)

### 1. Clone the Repository

```bash
git clone https://github.com/dovanminh1001/visionai-databricks.git
cd visionai-databricks
```

### 2. Web Application Setup (branch `web-app-deploy`)

```bash
git checkout web-app-deploy
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env           # Edit with your Databricks credentials
python run.py                  # Visit http://localhost:5000
```

### 3. Data Pipeline Setup (branch `main`)

```bash
git checkout main
pip install -r requirements.txt

# Deploy Medallion SQL jobs to Databricks
python deploy_separate_jobs.py
```

### 4. Docker Deployment

```bash
# Development
docker-compose -f docker/docker-compose.yml up -d

# Production (with Nginx + SSL + 2 replicas)
docker-compose -f docker/docker-compose.production.yml up -d
```

---

## 📁 Project Structure

```
visionai-databricks/
│
├── 🌐 Web Application (branch: web-app-deploy)
│   ├── app/
│   │   ├── models/              # SQLAlchemy ORM (User, Detection)
│   │   ├── views/               # Flask Blueprints
│   │   │   ├── auth.py          # Authentication (login/register/logout)
│   │   │   ├── main.py          # Dashboard, History, Admin, CSV Export
│   │   │   ├── detection.py     # YOLOv8 Object Detection (camera + upload)
│   │   │   ├── face_detection.py # Haar Cascade Face Recognition
│   │   │   ├── color_detection.py # K-Means Color Analysis
│   │   │   └── classification.py # Object Classification
│   │   ├── services/
│   │   │   ├── db_service.py    # Centralized DB + HF upload + Pipeline sync
│   │   │   └── classification_service.py
│   │   ├── templates/           # Jinja2 HTML (Tailwind CSS)
│   │   └── static/              # CSS, JS, Images
│   ├── config/config.py         # App configuration + bilingual labels
│   ├── docker/                  # Dockerfile, docker-compose, nginx.conf
│   ├── scripts/                 # Deploy scripts (AWS, GCP, Azure, Local)
│   ├── Dockerfile               # Production Docker image (CPU-optimized)
│   ├── requirements.txt
│   └── run.py                   # Application entrypoint
│
├── 📊 Data Pipeline (branch: main)
│   ├── sql/
│   │   ├── 01_create_schemas.sql    # Create bronze/silver/gold schemas
│   │   ├── 02_bronze_from_app.sql   # Bronze VIEW from raw app data
│   │   ├── 03_silver_enriched.sql   # Silver TABLE with 6 new features
│   │   ├── 04_gold_tables.sql       # 4 Gold aggregation tables
│   │   └── 05_mlflow_experiment.sql # ML experiment tracking table
│   ├── src/
│   │   ├── ingestion/              # Bronze layer ingestion scripts
│   │   ├── processing/             # Silver layer processing
│   │   └── training/               # YOLOv8 training simulation + MLflow
│   ├── tests/                      # PyTest unit tests
│   ├── .github/workflows/ci.yml    # GitHub Actions CI/CD pipeline
│   ├── databricks.yml              # Databricks Asset Bundle config
│   ├── deploy_separate_jobs.py     # Auto-deploy 3 Workflow Jobs via REST API
│   └── requirements.txt
│
└── 📄 docs/                        # Documentation & architecture diagrams
```

---

## 🔄 CI/CD Pipeline

The project uses **GitHub Actions** for continuous integration:

```mermaid
graph LR
    A[📝 Git Push / PR] --> B[🧪 PyTest]
    B --> C[✅ Databricks Bundle Validate]
    C --> D[🚀 Deploy Ready]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style D fill:#9C27B0,color:#fff
```

| Step | Tool | Purpose |
|------|------|---------|
| 1 | `pytest` | Run unit tests for ingestion & processing modules |
| 2 | `databricks bundle validate` | Verify Databricks deployment configuration |
| 3 | Auto-deploy | Push to `main` triggers pipeline sync |

---

## 🐳 Docker Services

| Environment | Services | Config File |
|-------------|----------|-------------|
| **Development** | Flask App + PostgreSQL | `docker/docker-compose.yml` |
| **Production** | Flask (2 replicas) + PostgreSQL + Nginx (SSL) | `docker/docker-compose.production.yml` |

**Key optimizations for production:**
- CPU-only PyTorch (`--index-url https://download.pytorch.org/whl/cpu`)
- Single worker + single thread Gunicorn to minimize RAM usage
- `torch.set_num_threads(1)` for constrained environments
- Auto-restart policy (`unless-stopped`)
- Health checks every 30 seconds

---

## 📊 Databricks Workflow Jobs

Three automated jobs manage the data pipeline:

| Job Name | Tasks | Schedule | Purpose |
|----------|-------|----------|---------|
| **VisionAI Model Deployment** | Create Schemas → Bronze → Silver | Every 15 min | Data ingestion & enrichment |
| **VisionAI Model Training** | MLflow Experiment Log | Daily at 2 AM | Track model training metrics |
| **VisionAI System Monitoring** | Gold Tables (4 tables) | Every hour | Dashboard analytics refresh |

---

## 🔐 Environment Variables

```env
# Required
DATABASE_URL=databricks://token:YOUR_TOKEN@YOUR_HOST...
SECRET_KEY=your-secret-key

# Optional
HF_TOKEN=your-huggingface-token
YOLO_MODEL_PATH=yolov8n.pt
FLASK_ENV=production
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/dovanminh1001">
        <sub><b>Đỗ Văn Minh</b></sub>
        <sub><b>- Võ Trần Gia Huy</b></sub>
      </a>
    </td>
  </tr>
</table>

---

<p align="center">
  <sub>Built with ❤️ using Python, YOLOv8, Databricks & Docker</sub>
</p>
