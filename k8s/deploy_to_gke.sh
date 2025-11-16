#!/bin/bash

# GKE (Google Kubernetes Engine) Deployment Script
# Deploys all 6 services together as a package with only frontend exposed
# This is different from deploy.sh (root) which deploys to Cloud Run

set -e

PROJECT_ID="parkhoai-864b2"
NAMESPACE="parkho-ai"
REGISTRY="gcr.io/${PROJECT_ID}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   GKE Deployment - All Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud not found. Please install gcloud CLI.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Check cluster connection
echo -e "${YELLOW}🔍 Checking cluster connection...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Not connected to cluster.${NC}"
    echo "Run: gcloud container clusters get-credentials YOUR_CLUSTER_NAME --region us-central1"
    exit 1
fi

echo -e "${GREEN}✅ Connected to cluster${NC}"
echo ""

# Create namespace
echo -e "${YELLOW}📦 Creating namespace...${NC}"
kubectl apply -f namespace.yaml
echo -e "${GREEN}✅ Namespace created${NC}"
echo ""

# Apply ConfigMap
echo -e "${YELLOW}⚙️  Applying ConfigMap...${NC}"
kubectl apply -f configmap.yaml
echo -e "${GREEN}✅ ConfigMap applied${NC}"
echo ""

# Check if secrets exist
if kubectl get secret parkho-secrets -n ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}🔐 Secrets already exist. Skipping...${NC}"
    echo -e "${YELLOW}   Update them with: kubectl edit secret parkho-secrets -n ${NAMESPACE}${NC}"
else
    echo -e "${YELLOW}🔐 Creating secrets...${NC}"
    echo -e "${RED}⚠️  WARNING: Using default secrets from secrets.yaml${NC}"
    echo -e "${YELLOW}   Please update secrets.yaml with your actual values!${NC}"
    read -p "Continue with default secrets? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Update secrets.yaml and run again."
        exit 1
    fi
    kubectl apply -f secrets.yaml
fi
echo -e "${GREEN}✅ Secrets ready${NC}"
echo ""

# Create PersistentVolumes
echo -e "${YELLOW}💾 Creating PersistentVolumes...${NC}"
kubectl apply -f persistent-volumes.yaml
echo -e "${GREEN}✅ PersistentVolumes created${NC}"
echo ""

# Deploy PostgreSQL
echo -e "${YELLOW}🐘 Deploying PostgreSQL...${NC}"
kubectl apply -f postgres-deployment.yaml
echo -e "${GREEN}✅ PostgreSQL deployed${NC}"

# Wait for PostgreSQL
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=120s || true
echo ""

# Deploy MinIO
echo -e "${YELLOW}📦 Deploying MinIO...${NC}"
kubectl apply -f minio-deployment.yaml
echo -e "${GREEN}✅ MinIO deployed${NC}"

# Wait for MinIO
echo -e "${YELLOW}⏳ Waiting for MinIO to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=minio -n ${NAMESPACE} --timeout=120s || true
echo ""

# Deploy Qdrant
echo -e "${YELLOW}🔍 Deploying Qdrant...${NC}"
kubectl apply -f qdrant-deployment.yaml
echo -e "${GREEN}✅ Qdrant deployed${NC}"

# Wait for Qdrant
echo -e "${YELLOW}⏳ Waiting for Qdrant to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=qdrant -n ${NAMESPACE} --timeout=120s || true
echo ""

# Deploy Services
echo -e "${YELLOW}🌐 Deploying Services...${NC}"
kubectl apply -f services.yaml
echo -e "${GREEN}✅ Services deployed${NC}"
echo ""

# Deploy RAG Engine
echo -e "${YELLOW}🤖 Deploying RAG Engine...${NC}"
kubectl apply -f rag-engine-deployment.yaml
echo -e "${GREEN}✅ RAG Engine deployed${NC}"
echo ""

# Deploy Backend
echo -e "${YELLOW}⚙️  Deploying Backend...${NC}"
kubectl apply -f backend-deployment.yaml
echo -e "${GREEN}✅ Backend deployed${NC}"
echo ""

# Deploy Frontend
echo -e "${YELLOW}🎨 Deploying Frontend...${NC}"
kubectl apply -f frontend-deployment.yaml
echo -e "${GREEN}✅ Frontend deployed${NC}"
echo ""

# Deploy Ingress
echo -e "${YELLOW}🚪 Deploying Ingress...${NC}"
echo -e "${YELLOW}   Make sure to update ingress.yaml with your domain!${NC}"
kubectl apply -f ingress.yaml
echo -e "${GREEN}✅ Ingress deployed${NC}"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Status:${NC}"
kubectl get pods -n ${NAMESPACE}
echo ""
echo -e "${BLUE}🌐 Services:${NC}"
kubectl get svc -n ${NAMESPACE}
echo ""
echo -e "${BLUE}🚪 Ingress:${NC}"
kubectl get ingress -n ${NAMESPACE}
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Wait for all pods to be running: kubectl get pods -n ${NAMESPACE} -w"
echo "2. Initialize database schema (see README.md)"
echo "3. Get Ingress IP: kubectl get ingress parkho-ai-ingress -n ${NAMESPACE}"
echo "4. Configure DNS to point to Ingress IP"
echo "5. View logs: kubectl logs -n ${NAMESPACE} -l app=frontend --tail=50"
echo ""

