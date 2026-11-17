# Production Deployment Guide - VisionAI Object Detection

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Production Deployment](#local-production-deployment)
3. [Cloud Deployment Options](#cloud-deployment-options)
4. [AWS ECS Deployment](#aws-ecs-deployment)
5. [Google Cloud Run Deployment](#google-cloud-run-deployment)
6. [Azure Container Instances Deployment](#azure-container-instances-deployment)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)

## 🔧 Prerequisites

### Required Tools:
- Docker and Docker Compose
- Cloud provider CLI (AWS CLI, gcloud, or Azure CLI)
- Git
- Domain name (optional, for custom domain)

### System Requirements:
- Minimum 2 CPU cores
- Minimum 4GB RAM
- Minimum 20GB storage
- PostgreSQL database

## 🏠 Local Production Deployment

### Step 1: Configure Environment
```bash
# Copy production environment template
cp .env.example .env.production

# Edit production environment variables
nano .env.production
```

### Step 2: Deploy Locally
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

### Step 3: Access Application
- URL: http://localhost
- Health Check: http://localhost/health

## ☁️ Cloud Deployment Options

Choose one of the following cloud providers:

### 1. AWS ECS (Recommended for Enterprise)
- **Pros**: Scalable, secure, integrated AWS services
- **Cons**: More complex setup
- **Cost**: ~$50-200/month

### 2. Google Cloud Run (Recommended for Simplicity)
- **Pros**: Serverless, easy to deploy, auto-scaling
- **Cons**: Limited configuration options
- **Cost**: ~$30-150/month

### 3. Azure Container Instances (Recommended for Microsoft Stack)
- **Pros**: Easy setup, good Azure integration
- **Cons**: Less scalable than ECS
- **Cost**: ~$40-180/month

## 🚀 AWS ECS Deployment

### Prerequisites
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
```

### Step 1: Deploy to AWS
```bash
# Make deploy script executable
chmod +x deploy-aws.sh

# Run AWS deployment
./deploy-aws.sh
```

### Step 2: Configure Load Balancer
1. Go to AWS EC2 Console
2. Find your Load Balancer
3. Configure SSL certificate (optional)
4. Set up custom domain (optional)

### Step 3: Monitor Deployment
```bash
# Check service status
aws ecs describe-services --cluster visionai-cluster --services visionai-service

# View logs
aws logs tail /ecs/visionai-app --follow
```

## ☁️ Google Cloud Run Deployment

### Prerequisites
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Set project
gcloud config set project your-gcp-project-id
```

### Step 1: Deploy to GCP
```bash
# Make deploy script executable
chmod +x deploy-gcp.sh

# Run GCP deployment
./deploy-gcp.sh
```

### Step 2: Configure Custom Domain (Optional)
```bash
# Map custom domain
gcloud run services update-traffic visionai-app \
    --region us-central1 \
    --set-tags visionai-app
```

### Step 3: Monitor Deployment
```bash
# View logs
gcloud logs tail /run.googleapis.com/v2/visionai-app --region us-central1

# Check service status
gcloud run services describe visionai-app --region us-central1
```

## 🔷 Azure Container Instances Deployment

### Prerequisites
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login
```

### Step 1: Deploy to Azure
```bash
# Make deploy script executable
chmod +x deploy-azure.sh

# Run Azure deployment
./deploy-azure.sh
```

### Step 2: Configure DNS (Optional)
```bash
# Configure custom domain
az container app update \
    --resource-group visionai-rg \
    --name visionai-app \
    --set-traffic-weight=100
```

### Step 3: Monitor Deployment
```bash
# View logs
az container logs --resource-group visionai-rg --name visionai-app

# Check status
az container show --resource-group visionai-rg --name visionai-app
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Application health
curl https://your-domain.com/health

# Database connectivity
docker-compose exec web python -c "from app import db; print('Database OK' if db.engine.execute('SELECT 1').scalar() else 'Database Error')"
```

### Log Management
```bash
# View application logs
docker-compose logs -f web

# View database logs
docker-compose logs -f db

# View nginx logs
docker-compose logs -f nginx
```

### Backup Strategy
```bash
# Database backup
docker-compose exec db pg_dump -U visionai visionai_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose exec -T db psql -U visionai visionai_db < backup_file.sql
```

### Scaling
```bash
# Scale web service
docker-compose -f docker-compose.production.yml up -d --scale web=3

# Auto-scaling (Cloud Run)
gcloud run services update visionai-app \
    --region us-central1 \
    --max-instances 10 \
    --min-instances 1
```

## 🔒 Security Considerations

### SSL/TLS Configuration
1. Obtain SSL certificate (Let's Encrypt recommended)
2. Configure nginx with SSL
3. Update environment variables
4. Test HTTPS configuration

### Environment Security
- Use strong secrets
- Rotate keys regularly
- Enable IAM roles
- Configure firewall rules

### Database Security
- Use strong passwords
- Enable SSL connections
- Regular backups
- Monitor access logs

## 🚨 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   docker-compose logs web
   # Check for missing dependencies or configuration errors
   ```

2. **Database connection failed**
   ```bash
   docker-compose logs db
   # Check database credentials and network connectivity
   ```

3. **High memory usage**
   ```bash
   docker stats
   # Monitor resource usage and adjust limits
   ```

4. **Slow response times**
   ```bash
   # Check nginx configuration
   # Monitor database performance
   # Review application logs
   ```

### Performance Optimization

1. **Database Optimization**
   - Add indexes to frequently queried columns
   - Optimize queries
   - Use connection pooling

2. **Application Caching**
   - Implement Redis for session storage
   - Cache static assets
   - Use CDN for media files

3. **Load Balancing**
   - Configure multiple instances
   - Use health checks
   - Implement failover

## 📞 Support

For deployment issues:
1. Check logs for error messages
2. Verify environment configuration
3. Review cloud provider documentation
4. Contact support with detailed error logs

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Cloud Run
        run: ./deploy-gcp.sh
```

### GitLab CI Example
```yaml
deploy_production:
  stage: deploy
  script:
    - ./deploy-gcp.sh
  only:
    - main
```

---

**🎉 Congratulations! Your VisionAI Object Detection system is now running in production!**
