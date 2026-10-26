#!/bin/bash

# Production Deploy Script for VisionAI Object Detection

echo "🚀 Starting Production Deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Set environment variables
export $(cat .env.production | xargs)

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker/docker-compose.production.yml down

# Build new images
echo "🔨 Building production images..."
docker-compose -f docker/docker-compose.production.yml build --no-cache

# Start services
echo "🚀 Starting production services..."
docker-compose -f docker/docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker/docker-compose.production.yml ps

# Initialize database
echo "🗄️ Initializing database..."
docker-compose -f docker/docker-compose.production.yml exec web python scripts/init_db.py

# Health check
echo "🏥 Performing health check..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! Application is healthy."
else
    echo "❌ Health check failed. Please check logs."
    docker-compose -f docker/docker-compose.production.yml logs web
    exit 1
fi

echo "🎉 Production deployment completed!"
echo "🌐 Application is available at: http://localhost"
echo "📊 Monitor logs with: docker-compose -f docker/docker-compose.production.yml logs -f"
