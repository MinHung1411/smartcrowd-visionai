# VisionAI - Microservices Architecture Documentation

## 3.2. Thiết kế kiến trúc hệ thống

### 1. Mô hình kiến trúc hướng dịch vụ (Microservices)

#### 1.1. Tổng quan kiến trúc
VisionAI được thiết kế theo mô hình Microservices với 4 services chính tương ứng với 4 thành viên nhóm:

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (Nginx/HAProxy)                   │
│                   ┌─────────────────────────┐                   │
│                   │     Load Balancer       │                   │
│                   │   Service Discovery     │                   │
│                   │      Rate Limiting      │                   │
│                   └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
        ┌───────────▼───────────┐ ┌─────▼─────┐
        │   Service Mesh        │ │  Config   │
        │ (Istio/Consul)        │ │  Center    │
        └───────────────────────┘ └───────────┘
                    │
    ┌───────────────┼───────────────────────────────────────────┐
    │               │                   │                   │       │
┌───▼───┐    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐ │
│ Auth  │    │   User    │    │Detection  │    │ Storage   │ │
│Service│    │ Management│    │  Service  │    │ Service   │ │
│       │    │ Service   │    │           │    │           │ │
│Port:  │    │Port: 8002 │    │Port: 8003 │    │Port: 8004 │ │
│8001   │    │           │    │           │    │           │ │
└───────┘    └───────────┘    └───────────┘    └───────────┘ │
    │               │                   │                   │
    └───────┬───────┴───────┬───────┴───────┬───────┬───────┘
            │               │               │       │
    ┌───────▼───────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
    │ PostgreSQL   │ │ PostgreSQL │ │ PostgreSQL │ │   MinIO    │
    │ (Auth DB)    │ │ (User DB)  │ │ (Detection │ │ (Object    │
    │              │ │            │ │   DB)      │ │  Storage)  │
    └──────────────┘ └────────────┘ └────────────┘ └────────────┘
```

#### 1.2. Phân chia Services cho 4 thành viên

**Thành viên 1: Authentication Service**
- **Chịu trách nhiệm:** Xác thực, phân quyền, JWT tokens
- **Port:** 8001
- **Database:** PostgreSQL (auth_db)
- **Technologies:** Flask, JWT, OAuth2, Redis (session cache)

**Thành viên 2: User Management Service**
- **Chịu trách nhiệm:** CRUD users, profile, roles, permissions
- **Port:** 8002
- **Database:** PostgreSQL (user_db)
- **Technologies:** Flask, SQLAlchemy, Email services

**Thành viên 3: Detection Service**
- **Chịu trách nhiệm:** AI/ML detection, image processing, real-time analysis
- **Port:** 8003
- **Database:** PostgreSQL (detection_db)
- **Technologies:** Flask, YOLOv8, OpenCV, Redis (cache), Celery (async)

**Thành viên 4: Storage Service**
- **Chịu trách nhiệm:** File storage, backup, CDN, data retention
- **Port:** 8004
- **Storage:** MinIO (S3-compatible)
- **Technologies:** Flask, MinIO, Redis (metadata cache)

### 2. Sơ đồ kiến trúc tổng thể

#### 2.1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Web App     │  │ Mobile App  │  │ Admin Panel │  │ API Client  │   │
│  │ (React)     │  │ (React Native)│ │ (React)     │  │ (Postman)  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │        API GATEWAY              │
                    │   (Nginx + Kong/Envoy)         │
                    │  • Authentication              │
                    │  • Rate Limiting               │
                    │  • Load Balancing              │
                    │  • Request Routing             │
                    │  • API Documentation           │
                    └────────────────┬───────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │           SERVICE MESH              │
                    │         (Istio/Consul)            │
                    │  • Service Discovery             │
                    │  • Load Balancing                │
                    │  • Circuit Breaking              │
                    │  • Observability                 │
                    └──────────────────┬──────────────────┘
                                       │
    ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
    │                  │                 │                 │                  │
┌───▼────────┐   ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
│   Auth     │   │   User    │   │Detection  │   │  Storage  │   │Monitoring │
│  Service   │   │Management │   │ Service   │   │ Service   │   │ Service   │
│            │   │ Service   │   │           │   │           │   │           │
│• Login     │   │• CRUD     │   │• YOLOv8   │   │• MinIO    │   │• Prometheus│
│• JWT       │   │• Profile  │   │• OpenCV   │   │• CDN      │   │• Grafana  │
│• OAuth2    │   │• Roles    │   │• Real-time│   │• Backup   │   │• ELK Stack│
│• Sessions  │   │• Permissions│ │• Async    │   │• Metadata │   │• Jaeger   │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
       │                │                │                │                │
       └────────────────┼────────────────┼────────────────┼────────────────┘
                        │                │                │
    ┌───────────────────▼────────────────▼────────────────▼─────────────────┐
    │                           DATA LAYER                                 │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
    │  │ PostgreSQL  │  │ PostgreSQL  │  │ PostgreSQL  │  │    Redis    │ │
    │  │ (auth_db)   │  │ (user_db)   │  │ (detect_db) │  │   (Cache)   │ │
    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                     MinIO (Object Storage)                       │ │
    │  │  • Images     • Videos     • Models     • Backups               │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────────────┘
```

#### 2.2. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────┘

USER REQUEST FLOW:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│ API Gateway │───▶│ Auth Service│───▶│   Redis     │
│             │    │             │    │             │    │ (Session)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐    ┌─────────────┐
                    │   Service   │    │ PostgreSQL  │
                    │   Mesh      │    │ (auth_db)   │
                    └─────────────┘    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Target      │
                    │ Service     │
                    └─────────────┘

DETECTION PROCESS FLOW:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Camera    │───▶│ Detection  │───▶│   MinIO     │───▶│ PostgreSQL  │
│   Stream    │    │ Service    │    │ (Storage)   │    │ (detect_db) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐    ┌─────────────┐
                    │    Redis    │    │   Kafka     │
                    │   (Cache)   │    │ (Events)    │
                    └─────────────┘    └─────────────┘

USER MANAGEMENT FLOW:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Admin     │───▶│ User Mgmt   │───▶│ PostgreSQL  │───▶│   Redis     │
│   Panel     │    │ Service     │    │ (user_db)   │    │ (Cache)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Email     │
                    │  Service    │
                    └─────────────┘
```

#### 2.3. API Gateway Configuration

```yaml
# docker-compose.gateway.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - auth-service
      - user-service
      - detection-service
      - storage-service

  kong:
    image: kong:latest
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_DATABASE: kong
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kong
    ports:
      - "8000:8000"
      - "8001:8001"
    depends_on:
      - postgres

  consul:
    image: consul:latest
    ports:
      - "8500:8500"
    command: agent -server -bootstrap -ui -client=0.0.0.0
```

#### 2.4. Service Communication

**Synchronous Communication:**
- REST APIs between services
- gRPC for high-performance internal communication
- HTTP/2 with TLS encryption

**Asynchronous Communication:**
- Apache Kafka for event streaming
- Redis Pub/Sub for real-time notifications
- Celery for background tasks

**Service Discovery:**
- Consul for service registration and discovery
- Health checks and load balancing
- Configuration management

#### 2.5. Database Design per Service

**Auth Service Database:**
```sql
-- auth_db
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**User Management Service Database:**
```sql
-- user_db
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    birth_date DATE,
    location VARCHAR(200),
    avatar_url VARCHAR(500),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id)
);
```

**Detection Service Database:**
```sql
-- detect_db
CREATE TABLE detections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    detection_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    bounding_boxes JSONB NOT NULL,
    objects_detected JSONB NOT NULL,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE detection_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    accuracy FLOAT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Storage Service Metadata:**
```sql
-- storage_db
CREATE TABLE file_metadata (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    user_id INTEGER NOT NULL,
    bucket_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

#### 2.6. Monitoring & Observability

**Monitoring Stack:**
- **Prometheus:** Metrics collection
- **Grafana:** Visualization and dashboards
- **Jaeger:** Distributed tracing
- **ELK Stack:** Elasticsearch, Logstash, Kibana for logging

**Key Metrics:**
- Service health and performance
- API response times and error rates
- Database query performance
- Resource utilization (CPU, memory, disk)
- Business metrics (detections per minute, user activity)

#### 2.7. Security Architecture

**Authentication & Authorization:**
- JWT tokens with refresh token mechanism
- OAuth2 integration for third-party auth
- Role-based access control (RBAC)
- API rate limiting and throttling

**Network Security:**
- mTLS for service-to-service communication
- Network segmentation with Kubernetes Network Policies
- DDoS protection at API Gateway level
- Web Application Firewall (WAF)

**Data Security:**
- Encryption at rest (database, storage)
- Encryption in transit (TLS 1.3)
- Data masking for sensitive information
- Regular security audits and penetration testing

#### 2.8. Deployment Architecture

**Container Orchestration:**
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  auth-service:
    build: ./services/auth
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-auth:5432/auth_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres-auth
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  user-service:
    build: ./services/user-management
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-user:5432/user_db
      - EMAIL_SERVICE_URL=http://email-service:8080
    depends_on:
      - postgres-user
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  detection-service:
    build: ./services/detection
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-detection:5432/detect_db
      - MINIO_URL=http://minio:9000
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - postgres-detection
      - minio
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  storage-service:
    build: ./services/storage
    environment:
      - MINIO_URL=http://minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    depends_on:
      - minio
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

**CI/CD Pipeline:**
- GitHub Actions for automated testing and deployment
- Docker multi-stage builds for optimization
- Blue-green deployment strategy
- Automated rollback on failure

#### 2.9. Scaling Strategy

**Horizontal Scaling:**
- Stateless services for easy scaling
- Load balancing across multiple instances
- Database read replicas for read-heavy workloads
- CDN for static content delivery

**Vertical Scaling:**
- Resource monitoring and auto-scaling
- GPU instances for AI/ML workloads
- Memory optimization for caching layers

#### 2.10. Disaster Recovery & Backup

**Backup Strategy:**
- Automated daily database backups
- Point-in-time recovery capability
- Cross-region replication
- Regular backup restoration testing

**High Availability:**
- Multi-zone deployment
- Automatic failover mechanisms
- Health checks and circuit breakers
- Graceful degradation during outages

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- Set up development environment
- Implement basic services structure
- Configure API Gateway and Service Mesh
- Set up monitoring and logging

### Phase 2: Core Services (Week 3-4)
- Authentication Service implementation
- User Management Service implementation
- Basic Detection Service setup
- Storage Service integration

### Phase 3: Advanced Features (Week 5-6)
- Real-time detection capabilities
- Advanced security features
- Performance optimization
- Comprehensive testing

### Phase 4: Production Deployment (Week 7-8)
- Production environment setup
- CI/CD pipeline implementation
- Load testing and optimization
- Documentation and training

---

## 5. Technology Stack Summary

| Service | Technology | Database | Cache | Message Queue |
|---------|------------|----------|-------|---------------|
| Auth Service | Flask + JWT | PostgreSQL | Redis | - |
| User Management | Flask + SQLAlchemy | PostgreSQL | Redis | Kafka |
| Detection Service | Flask + YOLOv8 | PostgreSQL | Redis | Kafka + Celery |
| Storage Service | Flask + MinIO | PostgreSQL | Redis | - |
| API Gateway | Nginx + Kong | - | - | - |
| Monitoring | Prometheus + Grafana | - | - | - |
| Logging | ELK Stack | - | - | - |

---

## 6. Team Responsibilities

| Member | Service | Primary Responsibilities |
|--------|---------|------------------------|
| Member 1 | Auth Service | Authentication, JWT, OAuth2, Security |
| Member 2 | User Management | CRUD operations, Profile, Roles, Email |
| Member 3 | Detection Service | AI/ML, YOLOv8, Image Processing, Real-time |
| Member 4 | Storage Service | File storage, MinIO, CDN, Backup |

---

*This architecture provides scalability, maintainability, and clear separation of concerns for a 4-person team working on the VisionAI system.*
