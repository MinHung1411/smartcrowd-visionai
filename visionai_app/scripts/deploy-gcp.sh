#!/bin/bash

# Google Cloud Run Deployment Script for VisionAI Object Detection

echo "☁️ Starting Google Cloud Run Deployment..."

# Configuration
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="visionai-app"
REPO_NAME="visionai-repo"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories describe $REPO_NAME --location=$REGION 2>/dev/null || \
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="VisionAI Docker repository"

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build and push Docker image
echo "🏗️ Building and pushing Docker image..."
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME"

docker build -f Dockerfile.production -t $IMAGE_NAME:latest .
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 1 \
    --set-env-vars FLASK_ENV=production \
    --set-env-vars SECRET_KEY="your-production-secret-key" \
    --timeout 300s \
    --concurrency 10

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format="value(status.url)")

echo "✅ Google Cloud Run deployment completed!"
echo "🌐 Application URL: $SERVICE_URL"
echo "📊 View logs: gcloud logs tail /run.googleapis.com/v2/$SERVICE_NAME --region $REGION"
