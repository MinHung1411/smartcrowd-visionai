# VisionAI Object Detection System

A full-stack web application for real-time object detection using YOLOv8, with bilingual support (English/Vietnamese), user authentication, and mobile-responsive design.

## Features

- **Real-time Camera Detection**: Live object detection using webcam
- **Image Upload Detection**: Upload and analyze images for object detection
- **Bilingual Support**: Detection results in both English and Vietnamese
- **User Authentication**: Secure login system with role-based access control
- **Responsive Design**: Mobile-friendly interface
- **Detection History**: Track and view past detections
- **Admin Dashboard**: Activity monitoring and user management
- **Cloud Deployment**: Docker configuration for easy deployment

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **AI/ML**: YOLOv8 (Ultralytics), OpenCV
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: Flask-Login, bcrypt
- **Deployment**: Docker, Docker Compose, Nginx

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js (for development tools)
- Docker and Docker Compose (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd visionai_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://localhost:5000`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Create admin user**
   ```bash
   docker-compose exec web python -c "
   from app import create_app, db
   from app.models.user import User
   app = create_app()
   app.app_context().push()
   
   admin = User(username='admin', email='admin@example.com', role='admin')
   admin.set_password('admin123')
   db.session.add(admin)
   db.session.commit()
   print('Admin user created successfully')
   "
   ```

## Usage

### First Time Setup

1. **Register a new account** or use the default admin account:
   - Email: `admin@example.com`
   - Password: `admin123`

2. **Start using the detection features**:
   - **Camera Detection**: Click "Camera Detection" to start real-time detection
   - **Image Upload**: Click "AI Image Analysis" to upload and analyze images

### Features

#### Camera Detection
- Click "Start Camera" to begin live detection
- Click "Capture & Detect" to analyze the current frame
- View detected objects with confidence scores

#### Image Upload
- Drag and drop or click to upload images
- Supported formats: PNG, JPG, JPEG, GIF, BMP, WebP
- Maximum file size: 16MB
- View annotated images with bounding boxes

#### Dashboard
- View detection statistics
- See top detected objects
- Access all features from the main dashboard

#### History
- View all past detections
- Filter by detection type (camera/upload)
- View detailed results for each detection

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Detection
- `POST /detection/detect_image` - Detect objects in uploaded image
- `POST /detection/detect_camera` - Detect objects in camera frame
- `GET /detection/uploads/<filename>` - Serve uploaded images

### User Interface
- `GET /` - Redirect to dashboard or login
- `GET /dashboard` - Main dashboard
- `GET /detection/camera` - Camera detection page
- `GET /detection/upload` - Image upload page
- `GET /history` - Detection history
- `GET /activity` - Admin activity log
- `GET /settings` - User settings

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key (required)
- `DATABASE_URL`: Database connection string
- `YOLO_MODEL_PATH`: Path to YOLO model file
- `UPLOAD_FOLDER`: Folder for uploaded images
- `MAX_CONTENT_LENGTH`: Maximum upload file size in bytes

### YOLO Models

The system supports different YOLOv8 models:
- `yolov8n.pt`: Nano model (fast, less accurate)
- `yolov8s.pt`: Small model (balanced)
- `yolov8m.pt`: Medium model (more accurate)
- `yolov8l.pt`: Large model (very accurate, slower)
- `yolov8x.pt`: Extra large model (most accurate, slowest)

Change the model by updating `YOLO_MODEL_PATH` in your environment or config.

## Deployment

### Cloud Deployment

The application is containerized and ready for cloud deployment on:
- AWS (ECS, EKS)
- Google Cloud Platform (Cloud Run, GKE)
- Azure (Container Instances, AKS)
- DigitalOcean (App Platform, Kubernetes)

### Production Considerations

1. **Security**:
   - Change default passwords and secret keys
   - Use HTTPS in production
   - Implement rate limiting
   - Set up proper CORS policies

2. **Performance**:
   - Use Redis for session storage
   - Implement caching for static assets
   - Use CDN for image storage
   - Monitor resource usage

3. **Scaling**:
   - Use load balancers
   - Implement horizontal scaling
   - Consider serverless deployment for detection API

## � Project Structure

```
visionai_app/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   └── detection.py        # Detection model
│   ├── views/                   # Route handlers (Blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   ├── main.py             # Main dashboard routes
│   │   └── detection.py        # Detection routes
│   ├── templates/               # HTML templates
│   │   ├── base.html           # Base template
│   │   ├── dashboard.html      # Dashboard page
│   │   ├── auth/               # Auth templates
│   │   └── detection/          # Detection templates
│   └── static/                  # Static assets (CSS, JS, images)
├── config/                      # Configuration files
│   └── config.py               # App configuration
├── scripts/                     # Utility scripts
│   ├── init_db.py              # Database initialization
│   ├── deploy.sh               # Local deployment script
│   ├── deploy-aws.sh           # AWS deployment script
│   ├── deploy-gcp.sh           # Google Cloud deployment script
│   ├── deploy-azure.sh         # Azure deployment script
│   └── quick-deploy.sh         # Interactive deployment selector
├── docker/                      # Docker configuration
│   ├── Dockerfile              # Development Dockerfile
│   ├── Dockerfile.production   # Production Dockerfile
│   ├── docker-compose.yml      # Development compose
│   ├── docker-compose.production.yml  # Production compose
│   └── nginx.conf              # Nginx configuration
├── docs/                        # Documentation
│   └── DEPLOYMENT.md           # Detailed deployment guide
├── uploads/                     # User uploaded files
├── logs/                        # Application logs
├── ssl/                         # SSL certificates (for production)
├── .env.example                 # Environment variables template
├── .env.production              # Production environment variables
├── .gitignore                   # Git ignore file
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── yolov8n.pt                   # YOLO model file
└── README.md                    # This file
```

## �🚀 Deployment

### Quick Start
```bash
# Run quick deploy script
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

### Local Production
```bash
# Deploy locally with Docker Compose
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Cloud Deployment Options

#### 🟢 Google Cloud Run (Recommended - Easiest)
```bash
# Install gcloud CLI and configure
gcloud init
gcloud config set project your-project-id

# Deploy to Cloud Run
chmod +x scripts/deploy-gcp.sh
./scripts/deploy-gcp.sh
```

#### 🔵 AWS ECS (Enterprise)
```bash
# Install AWS CLI and configure
aws configure

# Deploy to AWS ECS
chmod +x scripts/deploy-aws.sh
./scripts/deploy-aws.sh
```

#### 🔷 Azure Container Instances
```bash
# Install Azure CLI and login
az login

# Deploy to Azure
chmod +x scripts/deploy-azure.sh
./scripts/deploy-azure.sh
```

### 📋 Deployment Files Created:
- `scripts/deploy.sh` - Local production deployment
- `scripts/deploy-gcp.sh` - Google Cloud Run deployment
- `scripts/deploy-aws.sh` - AWS ECS deployment
- `scripts/deploy-azure.sh` - Azure Container Instances deployment
- `scripts/quick-deploy.sh` - Interactive deployment selector
- `docs/DEPLOYMENT.md` - Detailed deployment guide
- `docker/docker-compose.production.yml` - Production Docker Compose
- `docker/Dockerfile.production` - Production Docker image
- `docker/nginx.conf` - Nginx reverse proxy configuration
- `.env.production` - Production environment template

### 🔧 Production Configuration
- Nginx reverse proxy with SSL support
- PostgreSQL database
- Rate limiting and security headers
- Health checks and monitoring
- Auto-scaling support
- Log aggregation

### 📊 Monitoring
```bash
# View logs
docker-compose -f docker/docker-compose.production.yml logs -f web

# Health check
curl http://localhost/health

# Database backup
docker-compose -f docker/docker-compose.production.yml exec db pg_dump -U visionai visionai_db > backup.sql
```

**For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## Acknowledgments

- [Ultralytics](https://ultralytics.com/) for YOLOv8
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [OpenCV](https://opencv.org/) for computer vision operations
