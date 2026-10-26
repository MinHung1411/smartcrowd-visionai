#!/bin/bash

# Azure Container Instances Deployment Script for VisionAI Object Detection

echo "☁️ Starting Azure Container Instances Deployment..."

# Configuration
RESOURCE_GROUP="visionai-rg"
LOCATION="eastus"
CONTAINER_NAME="visionai-app"
CONTAINER_REGISTRY="visionaicr"

# Login to Azure
echo "🔐 Logging into Azure..."
az login

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
echo "🏗️ Creating Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $CONTAINER_REGISTRY --sku Basic

# Build and push Docker image
echo "🐳 Building and pushing Docker image..."
az acr build --registry $CONTAINER_REGISTRY --image $CONTAINER_NAME:latest .

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY --query loginServer --output tsv)

# Deploy to Container Instances
echo "🚀 Deploying to Container Instances..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $ACR_LOGIN_SERVER/$CONTAINER_NAME:latest \
    --cpu 1 \
    --memory 2 \
    --ports 5000 \
    --environment-variables FLASK_ENV=production SECRET_KEY="your-production-secret-key" \
    --dns-name-label visionai-app-$(date +%s) \
    --assign-identity [system] \
    --role "Reader" \
    --scope /subscriptions/$(az account show --query id --output tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$CONTAINER_REGISTRY

# Get container IP
CONTAINER_IP=$(az container show \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --query ipAddress.ip --output tsv)

CONTAINER_FQDN=$(az container show \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --query ipAddress.fqdn --output tsv)

echo "✅ Azure Container Instances deployment completed!"
echo "🌐 Application URL: http://$CONTAINER_FQDN:5000"
echo "🌐 Application IP: http://$CONTAINER_IP:5000"
echo "📊 View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
