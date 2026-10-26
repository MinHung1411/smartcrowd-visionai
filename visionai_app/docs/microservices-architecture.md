# VisionAI Microservices Architecture

## 1. Tổng quan kiến trúc

Hệ thống được thiết kế theo mô hình Microservices với 4 services chính, phù hợp cho nhóm 4 người phát triển.

### **Cấu trúc tổng thể**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  API Gateway    │    │  AI Detection   │    │  File Storage   │
│   (React/Vue)   │◄──►│   & Auth        │◄──►│    Service      │◄──►│    Service      │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │    │   Port: 8003    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │                        │
                              ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │   User Mgmt     │    │   PostgreSQL    │    │   MinIO/S3      │
                       │   Service       │    │   (Users/Auth)  │    │   (Files)       │
                       │   Port: 8002    │    └─────────────────┘    └─────────────────┘
                       └─────────────────┘             │                        │
                              │                        ▼                        ▼
                              ▼                 ┌─────────────────┐    ┌─────────────────┐
                       ┌─────────────────┐    │   PostgreSQL    │    │   PostgreSQL    │
                       │   PostgreSQL   │    │  (Detections)   │    │   (Metadata)    │
                       │  (History)      │    └─────────────────┘    └─────────────────┘
                       └─────────────────┘
```

## 2. Chi tiết từng Service

### **Service 1: API Gateway & Authentication Service**
- **Port**: 8000
- **Team member**: Backend Lead
- **Công nghệ**: Flask + JWT + Redis + Nginx
- **Trách nhiệm**:
  - API Gateway routing và load balancing
  - User authentication & authorization
  - Rate limiting và security
  - Session management với Redis
  - CORS handling

**API Endpoints**:
```
POST   /auth/login
POST   /auth/register
POST   /auth/logout
POST   /auth/refresh
GET    /auth/profile
PUT    /auth/profile
GET    /health
```

**Database Schema**:
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    birth_date DATE,
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### **Service 2: AI Detection Service**
- **Port**: 8001
- **Team member**: AI/ML Engineer
- **Công nghệ**: FastAPI + YOLOv8 + OpenCV + NumPy
- **Trách nhiệm**:
  - Object detection với YOLOv8
  - Face detection với OpenCV
  - Color detection và analysis
  - Emotion detection
  - Image preprocessing và augmentation

**API Endpoints**:
```
POST   /detect/objects
POST   /detect/faces
POST   /detect/colors
POST   /detect/emotions
GET    /models/info
GET    /health
```

**Response Format**:
```json
{
  "success": true,
  "detection_type": "objects",
  "processing_time": 0.245,
  "objects_detected": [
    {
      "class": "person",
      "name": {"en": "person", "vi": "Người"},
      "confidence": 0.95,
      "bbox": [x, y, w, h]
    }
  ],
  "image_metadata": {
    "width": 640,
    "height": 480,
    "format": "JPEG"
  }
}
```

### **Service 3: User Management & History Service**
- **Port**: 8002
- **Team member**: Backend Developer
- **Công nghệ**: Flask + SQLAlchemy + PostgreSQL
- **Trách nhiệm**:
  - User profile management
  - Detection history tracking
  - Statistics và analytics
  - Data export (CSV, JSON)
  - Activity logging

**API Endpoints**:
```
GET    /users/profile
PUT    /users/profile
GET    /users/history
GET    /users/statistics
POST   /users/export
DELETE /users/history/{id}
GET    /admin/activity
GET    /admin/users
```

**Database Schema**:
```sql
-- Detections table
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    detection_type VARCHAR(50) NOT NULL,
    image_path VARCHAR(500),
    objects_detected JSONB,
    confidence_scores JSONB,
    processing_time FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Statistics table
CREATE TABLE detection_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    date DATE NOT NULL,
    total_detections INTEGER DEFAULT 0,
    unique_objects INTEGER DEFAULT 0,
    processing_time_total FLOAT DEFAULT 0
);
```

### **Service 4: File Management & Storage Service**
- **Port**: 8003
- **Team member**: DevOps Engineer
- **Công nghệ**: FastAPI + MinIO/AWS S3 + Redis
- **Trách nhiệm**:
  - File upload/download
  - Image optimization và compression
  - Storage management
  - CDN integration
  - File metadata management

**API Endpoints**:
```
POST   /files/upload
GET    /files/{filename}
DELETE /files/{filename}
GET    /files/metadata/{filename}
POST   /files/batch-upload
GET    /health
```

**Storage Structure**:
```
visionai-bucket/
├── uploads/
│   ├── {user_id}/
│   │   ├── original/
│   │   ├── processed/
│   │   └── thumbnails/
├── models/
│   ├── yolov8n.pt
│   ├── yolov8s.pt
│   └── face_detection.pb
└── cache/
    └── processed_images/
```

## 3. Data Flow Architecture

### **Authentication Flow**:
```
1. User → Frontend: Login credentials
2. Frontend → API Gateway: POST /auth/login
3. API Gateway → Redis: Verify credentials
4. API Gateway ← Redis: User data + JWT token
5. Frontend ← API Gateway: JWT token
6. Frontend stores JWT for subsequent requests
```

### **Detection Flow**:
```
1. User → Frontend: Upload image
2. Frontend → File Service: POST /files/upload
3. File Service → MinIO: Store original image
4. Frontend → AI Service: POST /detect/objects
5. AI Service → File Service: GET image
6. AI Service → MinIO: Store processed image
7. AI Service → History Service: POST detection result
8. History Service → PostgreSQL: Store detection metadata
9. Frontend ← AI Service: Detection results
```

## 4. Communication Patterns

### **Synchronous Communication**:
- **REST APIs**: HTTP/REST giữa services
- **gRPC**: High-performance communication cho AI processing
- **WebSocket**: Real-time updates cho camera detection

### **Asynchronous Communication**:
- **Message Queue**: Redis/RabbitMQ cho background tasks
- **Event Bus**: Pub/Sub cho service events
- **Webhooks**: External integrations

### **Service Discovery**:
- **Consul**: Service registration và discovery
- **Health Checks**: Monitoring service availability
- **Load Balancing**: Nginx/HAProxy

## 5. Security Architecture

### **Authentication & Authorization**:
- **JWT Tokens**: Stateless authentication
- **OAuth 2.0**: Third-party integrations
- **RBAC**: Role-based access control
- **API Keys**: Service-to-service communication

### **Security Layers**:
```
┌─────────────────┐
│   WAF/Firewall  │
└─────────────────┘
┌─────────────────┐
│   API Gateway   │ ← Rate limiting, CORS, Security headers
└─────────────────┘
┌─────────────────┐
│   Service Mesh  │ ← mTLS, Service-to-service auth
└─────────────────┘
┌─────────────────┐
│   Database      │ ← Encryption at rest
└─────────────────┘
```

## 6. Deployment Architecture

### **Container Strategy**:
```yaml
# docker-compose.microservices.yml
version: '3.8'
services:
  api-gateway:
    build: ./services/api-gateway
    ports: ["8000:8000"]
    depends_on: [redis, postgres-users]
  
  ai-detection:
    build: ./services/ai-detection
    ports: ["8001:8001"]
    depends_on: [redis, minio]
  
  user-management:
    build: ./services/user-management
    ports: ["8002:8002"]
    depends_on: [postgres-history]
  
  file-storage:
    build: ./services/file-storage
    ports: ["8003:8003"]
    depends_on: [minio, redis]
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  postgres-users:
    image: postgres:13
    environment:
      POSTGRES_DB: users_db
  
  postgres-history:
    image: postgres:13
    environment:
      POSTGRES_DB: history_db
  
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
```

### **Kubernetes Deployment**:
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: visionai

---
# k8s/api-gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: visionai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: visionai/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

## 7. Monitoring & Observability

### **Monitoring Stack**:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Logging and analysis

### **Key Metrics**:
- Request latency and throughput
- Error rates and types
- Resource utilization (CPU, memory, disk)
- Database performance
- AI model inference time

### **Alerting**:
- Service health checks
- Performance thresholds
- Security events
- Resource limits

## 8. Scalability Strategy

### **Horizontal Scaling**:
- **Stateless services**: Easy scaling with containers
- **Database sharding**: Partition data by user_id
- **CDN integration**: Global file distribution
- **Caching layers**: Redis for frequently accessed data

### **Auto-scaling**:
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-detection-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-detection
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 9. Development Workflow

### **Team Structure**:
1. **Backend Lead** (Service 1): API Gateway & Authentication
2. **AI/ML Engineer** (Service 2): AI Detection Service
3. **Backend Developer** (Service 3): User Management & History
4. **DevOps Engineer** (Service 4): File Storage & Infrastructure

### **CI/CD Pipeline**:
```yaml
# .github/workflows/deploy.yml
name: Deploy Microservices
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build images
        run: |
          docker build -t visionai/api-gateway ./services/api-gateway
          docker build -t visionai/ai-detection ./services/ai-detection
          docker build -t visionai/user-management ./services/user-management
          docker build -t visionai/file-storage ./services/file-storage
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: kubectl apply -f k8s/
```

## 10. Migration Strategy

### **Phase 1: Foundation** (2 weeks)
- Setup infrastructure and monitoring
- Implement API Gateway with basic routing
- Migrate authentication system

### **Phase 2: Core Services** (3 weeks)
- Develop AI Detection Service
- Implement File Storage Service
- Migrate existing detection logic

### **Phase 3: User Services** (2 weeks)
- Build User Management Service
- Migrate history and statistics
- Implement data export features

### **Phase 4: Integration & Testing** (1 week)
- End-to-end testing
- Performance optimization
- Documentation and deployment

## 11. Technology Stack Summary

| Service | Framework | Database | Storage | Monitoring |
|---------|-----------|----------|---------|------------|
| API Gateway | Flask + Nginx | Redis | - | Prometheus |
| AI Detection | FastAPI | - | MinIO | Jaeger |
| User Management | Flask | PostgreSQL | - | Grafana |
| File Storage | FastAPI | PostgreSQL | MinIO/S3 | ELK Stack |

## 12. Cost Optimization

### **Resource Optimization**:
- **Spot instances** for non-critical workloads
- **Auto-scaling** to match demand
- **Image compression** to reduce storage costs
- **Caching** to reduce database queries

### **Monitoring Costs**:
- **Resource usage tracking**
- **Performance metrics**
- **Cost per request analysis**
- **Storage utilization**
