#!/bin/bash

# Quick Deploy Script - Choose your cloud provider

echo "🚀 VisionAI Object Detection - Quick Deploy"
echo "=========================================="
echo ""
echo "Choose deployment option:"
echo "1) Local Production (Docker Compose)"
echo "2) AWS ECS"
echo "3) Google Cloud Run"
echo "4) Azure Container Instances"
echo "5) Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "🏠 Starting Local Production Deployment..."
        ./scripts/deploy.sh
        ;;
    2)
        echo "☁️ Starting AWS ECS Deployment..."
        ./scripts/deploy-aws.sh
        ;;
    3)
        echo "☁️ Starting Google Cloud Run Deployment..."
        ./scripts/deploy-gcp.sh
        ;;
    4)
        echo "☁️ Starting Azure Container Instances Deployment..."
        ./scripts/deploy-azure.sh
        ;;
    5)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please select 1-5."
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment completed!"
echo "📖 For detailed instructions, see docs/DEPLOYMENT.md"
echo "🐛 For issues, check logs and troubleshooting section"
