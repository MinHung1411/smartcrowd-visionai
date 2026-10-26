#!/bin/bash

# AWS ECS Deployment Script for VisionAI Object Detection

echo "☁️ Starting AWS ECS Deployment..."

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="visionai-app"
ECS_CLUSTER="visionai-cluster"
ECS_SERVICE="visionai-service"
ECS_TASK_DEFINITION="visionai-task"

# AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Build and push Docker image to ECR
echo "🏗️ Building and pushing Docker image to ECR..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# Build Docker image
docker build -f Dockerfile.production -t $ECR_REPOSITORY:latest .

# Tag and push to ECR
docker tag $ECR_REPOSITORY:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest

# Create ECS cluster if it doesn't exist
echo "🔧 Setting up ECS cluster..."
aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION || \
aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION

# Create task definition
echo "📋 Creating task definition..."
cat > task-definition.json <<EOF
{
  "family": "$ECS_TASK_DEFINITION",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "visionai-web",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-production-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/visionai-app",
          "awslogs-region": $AWS_REGION,
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

# Create ECS service
echo "🚀 Creating ECS service..."
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION || \
aws ecs create-service \
  --cluster $ECS_CLUSTER \
  --service-name $ECS_SERVICE \
  --task-definition $ECS_TASK_DEFINITION \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345678],securityGroups=[sg-12345678],assignPublicIp=ENABLED}" \
  --region $AWS_REGION

# Update service with new task definition
echo "🔄 Updating ECS service..."
aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service $ECS_SERVICE \
  --task-definition $ECS_TASK_DEFINITION \
  --force-new-deployment \
  --region $AWS_REGION

echo "✅ AWS ECS deployment completed!"
echo "🌐 Check your AWS console for the load balancer URL"
