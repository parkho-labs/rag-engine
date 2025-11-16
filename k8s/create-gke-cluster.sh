#!/bin/bash

# Create GKE Cluster - Simple

set -e

PROJECT_ID="parkhoai-864b2"
REGION="us-central1"
CLUSTER_NAME="parkho-ai-cluster"

echo "🚀 Creating GKE cluster: ${CLUSTER_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Enable APIs
gcloud services enable container.googleapis.com compute.googleapis.com --quiet

# Create cluster
gcloud container clusters create ${CLUSTER_NAME} \
    --region=${REGION} \
    --num-nodes=2 \
    --machine-type=e2-standard-2 \
    --disk-size=30 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5

# Get credentials
gcloud container clusters get-credentials ${CLUSTER_NAME} --region ${REGION}

echo "✅ Cluster created and connected!"
echo ""
echo "Next: ./build-images.sh && ./deploy_to_gke.sh"
