#!/bin/bash
# Deployment script for project_workflow_72717da5

echo "Building Docker image..."
docker build -t project_workflow_72717da5 .

echo "Starting services..."
docker-compose up -d

echo "Deployment complete!"
