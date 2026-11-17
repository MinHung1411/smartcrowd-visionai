# VisionAI Architecture Diagrams

## 1. Sơ đồ kiến trúc tổng thể (Overall Architecture)

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web Frontend<br/>React/Vue.js<br/>Port: 3000]
        Mobile[Mobile App<br/>React Native<br/>Port: 3001]
    end

    subgraph "API Gateway Layer"
        Gateway[API Gateway<br/>Nginx + Flask<br/>Port: 8000]
        LB[Load Balancer<br/>HAProxy]
    end

    subgraph "Microservices Layer"
        Auth[Authentication Service<br/>Flask + JWT<br/>Port: 8000]
        AI[AI Detection Service<br/>FastAPI + YOLOv8<br/>Port: 8001]
        User[User Management Service<br/>Flask + SQLAlchemy<br/>Port: 8002]
        File[File Storage Service<br/>FastAPI + MinIO<br/>Port: 8003]
    end

    subgraph "Data Layer"
        Redis[(Redis<br/>Sessions & Cache)]
        PG1[(PostgreSQL<br/>Users & Auth)]
        PG2[(PostgreSQL<br/>Detections & History)]
        PG3[(PostgreSQL<br/>File Metadata)]
        MinIO[MinIO/S3<br/>File Storage]
    end

    subgraph "Infrastructure Layer"
        Monitor[Monitoring<br/>Prometheus + Grafana]
        Log[Logging<br/>ELK Stack]
        K8s[Kubernetes<br/>Container Orchestration]
    end

    UI --> Gateway
    Mobile --> Gateway
    Gateway --> LB
    LB --> Auth
    LB --> AI
    LB --> User
    LB --> File

    Auth --> Redis
    Auth --> PG1
    AI --> Redis
    AI --> MinIO
    User --> PG2
    File --> PG3
    File --> MinIO

    Auth --> Monitor
    AI --> Monitor
    User --> Monitor
    File --> Monitor

    Auth --> Log
    AI --> Log
    User --> Log
    File --> Log

    K8s --> Auth
    K8s --> AI
    K8s --> User
    K8s --> File
```

## 2. Sơ đồ luồng dữ liệu (Data Flow Diagram)

```mermaid
sequenceDiagram
    participant User as User
    participant UI as Frontend
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant File as File Service
    participant AI as AI Service
    participant UserMgmt as User Service
    participant DB as Database

    User->>UI: Upload image for detection
    UI->>Gateway: POST /files/upload (with JWT)
    Gateway->>Auth: Validate JWT
    Auth-->>Gateway: User info
    Gateway->>File: Upload request
    File->>DB: Store file metadata
    File-->>Gateway: File URL
    Gateway-->>UI: Upload success

    UI->>Gateway: POST /detect/objects
    Gateway->>Auth: Validate JWT
    Auth-->>Gateway: User info
    Gateway->>AI: Detection request
    AI->>File: GET image
    File-->>AI: Image data
    AI->>AI: Process with YOLOv8
    AI->>File: Store annotated image
    AI->>UserMgmt: Save detection result
    UserMgmt->>DB: Store detection metadata
    UserMgmt-->>AI: Success
    AI-->>Gateway: Detection results
    Gateway-->>UI: Results with annotations
    UI-->>User: Display results
```

## 3. Sơ đồ Microservices Communication

```mermaid
graph LR
    subgraph "External Clients"
        Web[Web Client]
        API[API Client]
        Mobile[Mobile Client]
    end

    subgraph "API Gateway"
        Gateway[API Gateway<br/>Port: 8000]
    end

    subgraph "Core Services"
        Auth[Auth Service<br/>Port: 8000]
        AI[AI Detection<br/>Port: 8001]
        User[User Management<br/>Port: 8002]
        File[File Storage<br/>Port: 8003]
    end

    subgraph "Data Stores"
        Redis[(Redis)]
        PG[(PostgreSQL)]
        Storage[(MinIO/S3)]
    end

    subgraph "Communication Patterns"
        REST[REST APIs]
        gRPC[gRPC]
        WS[WebSocket]
        MQ[Message Queue]
    end

    Web --> Gateway
    API --> Gateway
    Mobile --> Gateway

    Gateway -.->|REST/HTTP| Auth
    Gateway -.->|REST/HTTP| AI
    Gateway -.->|REST/HTTP| User
    Gateway -.->|REST/HTTP| File

    Auth -.->|gRPC| User
    AI -.->|REST/HTTP| File
    AI -.->|WebSocket| Gateway
    User -.->|Message Queue| AI

    Auth --> Redis
    User --> PG
    File --> PG
    File --> Storage
    AI --> Redis
```

## 4. Sơ đồ Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        WAF[WAF/Firewall<br/>DDoS Protection]
        Gateway[API Gateway<br/>Rate Limiting<br/>CORS & Security Headers]
        Mesh[Service Mesh<br/>mTLS Encryption<br/>Service-to-Service Auth]
        App[Application Layer<br/>JWT Tokens<br/>RBAC]
        Data[Data Layer<br/>Encryption at Rest<br/>Database Security]
    end

    subgraph "Authentication Flow"
        User[User Request]
        Login[Login Endpoint]
        JWT[JWT Token]
        Validate[Token Validation]
        Access[Access Granted]
    end

    subgraph "Authorization Flow"
        Roles[User Roles]
        Permissions[Permissions]
        RBAC[RBAC Engine]
        Resources[Resource Access]
    end

    User --> WAF
    WAF --> Gateway
    Gateway --> Mesh
    Mesh --> App
    App --> Data

    User --> Login
    Login --> JWT
    JWT --> Validate
    Validate --> Access

    Roles --> RBAC
    Permissions --> RBAC
    RBAC --> Resources
```

## 5. Sơ đồ Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DevLocal[Local Development<br/>Docker Compose]
        DevK8s[Dev Cluster<br/>Minikube]
    end

    subgraph "Staging Environment"
        StagingK8s[Staging Cluster<br/>3 Nodes]
        StagingDB[(Staging DB)]
        StagingStorage[(Staging Storage)]
    end

    subgraph "Production Environment"
        ProdK8s[Production Cluster<br/>5+ Nodes]
        ProdLB[Load Balancer]
        ProdCDN[CDN]
        ProdDB[(Production DB<br/>Primary-Replica)]
        ProdStorage[(Production Storage<br/>MinIO Cluster)]
    end

    subgraph "CI/CD Pipeline"
        Git[Git Repository]
        Build[Build Pipeline]
        Test[Test Pipeline]
        Deploy[Deploy Pipeline]
        Monitor[Monitoring]
    end

    DevLocal --> DevK8s
    DevK8s --> StagingK8s
    StagingK8s --> ProdK8s

    ProdK8s --> ProdLB
    ProdLB --> ProdCDN
    ProdK8s --> ProdDB
    ProdK8s --> ProdStorage

    Git --> Build
    Build --> Test
    Test --> Deploy
    Deploy --> Monitor
    Monitor --> Git
```

## 6. Sơ đồ Monitoring & Observability

```mermaid
graph TB
    subgraph "Application Layer"
        Services[Microservices]
        Containers[Containers]
        Pods[Kubernetes Pods]
    end

    subgraph "Monitoring Stack"
        Prometheus[Prometheus<br/>Metrics Collection]
        Grafana[Grafana<br/>Visualization]
        Jaeger[Jaeger<br/>Distributed Tracing]
        Alert[AlertManager<br/>Alerting]
    end

    subgraph "Logging Stack"
        Fluent[Fluentd/Fluent Bit<br/>Log Collection]
        Elasticsearch[Elasticsearch<br/>Log Storage]
        Kibana[Kibana<br/>Log Analysis]
    end

    subgraph "Business Metrics"
        BusinessAPI[Business API<br/>Custom Metrics]
        Dashboard[Business Dashboard<br/>KPI Tracking]
    end

    Services --> Prometheus
    Containers --> Prometheus
    Pods --> Prometheus

    Prometheus --> Grafana
    Prometheus --> Alert

    Services --> Jaeger
    Jaeger --> Grafana

    Services --> Fluent
    Fluent --> Elasticsearch
    Elasticsearch --> Kibana

    BusinessAPI --> Dashboard
    Dashboard --> Grafana
```

## 7. Sơ đồ Database Architecture

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        date birth_date
        string location
        timestamp created_at
        timestamp last_login
    }

    DETECTIONS {
        int id PK
        int user_id FK
        string detection_type
        string image_path
        jsonb objects_detected
        jsonb confidence_scores
        float processing_time
        timestamp timestamp
    }

    FILES {
        int id PK
        string filename
        string original_name
        string mime_type
        int file_size
        string storage_path
        int user_id FK
        timestamp uploaded_at
        timestamp last_accessed
    }

    DETECTION_STATS {
        int id PK
        int user_id FK
        date date
        int total_detections
        int unique_objects
        float processing_time_total
        jsonb object_counts
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string resource
        jsonb details
        timestamp timestamp
        string ip_address
    }

    USERS ||--o{ DETECTIONS : "has"
    USERS ||--o{ FILES : "uploads"
    USERS ||--o{ DETECTION_STATS : "generates"
    USERS ||--o{ AUDIT_LOGS : "performs"
    DETECTIONS ||--o| FILES : "references"
```

## 8. Sơ đồ Scaling Strategy

```mermaid
graph TB
    subgraph "Auto Scaling"
        HPA[Horizontal Pod Autoscaler]
        VPA[Vertical Pod Autoscaler]
        CA[Cluster Autoscaler]
    end

    subgraph "Load Distribution"
        LB[Load Balancer]
        Ingress[Ingress Controller]
        Service[ClusterIP Services]
    end

    subgraph "Service Instances"
        Auth1[Auth Service - Pod 1]
        Auth2[Auth Service - Pod 2]
        Auth3[Auth Service - Pod 3]
        
        AI1[AI Service - Pod 1]
        AI2[AI Service - Pod 2]
        
        User1[User Service - Pod 1]
        User2[User Service - Pod 2]
        
        File1[File Service - Pod 1]
        File2[File Service - Pod 2]
    end

    subgraph "Data Scaling"
        RedisCluster[Redis Cluster]
        PGMaster[(PostgreSQL Master)]
        PGReplica1[(PostgreSQL Replica 1)]
        PGReplica2[(PostgreSQL Replica 2)]
        MinIOCluster[MinIO Cluster]
    end

    HPA --> LB
    VPA --> LB
    CA --> LB

    LB --> Ingress
    Ingress --> Service

    Service --> Auth1
    Service --> Auth2
    Service --> Auth3
    Service --> AI1
    Service --> AI2
    Service --> User1
    Service --> User2
    Service --> File1
    Service --> File2

    Auth1 --> RedisCluster
    Auth2 --> RedisCluster
    Auth3 --> RedisCluster

    User1 --> PGMaster
    User2 --> PGMaster
    PGMaster --> PGReplica1
    PGMaster --> PGReplica2

    File1 --> MinIOCluster
    File2 --> MinIOCluster
```

## 9. Sơ đồ Disaster Recovery

```mermaid
graph TB
    subgraph "Primary Region"
        PrimaryK8s[Primary K8s Cluster]
        PrimaryDB[(Primary Database)]
        PrimaryStorage[(Primary Storage)]
        PrimaryBackup[Backup System]
    end

    subgraph "Backup Region"
        BackupK8s[Backup K8s Cluster]
        BackupDB[(Backup Database)]
        BackupStorage[(Backup Storage)]
        BackupRestore[Restore System]
    end

    subgraph "Recovery Process"
        Monitor[Health Monitoring]
        Failover[Automatic Failover]
        DNS[DNS Failover]
        Traffic[Traffic Routing]
    end

    PrimaryK8s --> PrimaryDB
    PrimaryK8s --> PrimaryStorage
    PrimaryDB --> PrimaryBackup
    PrimaryStorage --> PrimaryBackup

    PrimaryBackup --> BackupDB
    PrimaryBackup --> BackupStorage

    Monitor --> Failover
    Failover --> DNS
    DNS --> Traffic
    Traffic --> BackupK8s

    BackupK8s --> BackupDB
    BackupK8s --> BackupStorage
    BackupRestore --> BackupK8s
```

## 10. Sơ đồ Development Workflow

```mermaid
graph LR
    subgraph "Development Team"
        Dev1[Backend Lead<br/>Auth Service]
        Dev2[AI Engineer<br/>AI Service]
        Dev3[Backend Dev<br/>User Service]
        Dev4[DevOps Engineer<br/>File Service]
    end

    subgraph "Development Process"
        Plan[Planning<br/>Jira/Trello]
        Code[Code Development<br/>Git]
        Review[Code Review<br/>Pull Request]
        Test[Testing<br/>Unit/Integration]
        Build[Build Pipeline<br/>Docker]
        Deploy[Deployment<br/>K8s]
        Monitor[Monitoring<br/>Prometheus]
    end

    subgraph "Tools & Infrastructure"
        Git[Git Repository]
        CI[CI/CD Pipeline]
        Registry[Container Registry]
        K8s[Kubernetes Cluster]
        MonitorStack[Monitoring Stack]
    end

    Dev1 --> Plan
    Dev2 --> Plan
    Dev3 --> Plan
    Dev4 --> Plan

    Plan --> Code
    Code --> Review
    Review --> Test
    Test --> Build
    Build --> Deploy
    Deploy --> Monitor

    Code --> Git
    Build --> CI
    Build --> Registry
    Deploy --> K8s
    Monitor --> MonitorStack
```
