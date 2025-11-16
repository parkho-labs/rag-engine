#!/bin/bash

# Build and Push Docker Images Script
# Run from: rag-engine/k8s/
# Builds images for all 3 repos: frontend, backend, rag-engine

set -e

PROJECT_ID="parkhoai-864b2"
REGISTRY="gcr.io/${PROJECT_ID}"

# Get the root directory (parkho-labs)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Build and Push Docker Images${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Root directory: ${ROOT_DIR}${NC}"
echo ""

# Check if directories exist
if [ ! -d "$ROOT_DIR/parkho-ai-frontend" ]; then
    echo -e "${RED}❌ parkho-ai-frontend not found at: $ROOT_DIR/parkho-ai-frontend${NC}"
    exit 1
fi

if [ ! -d "$ROOT_DIR/parkho-ai-backend" ]; then
    echo -e "${RED}❌ parkho-ai-backend not found at: $ROOT_DIR/parkho-ai-backend${NC}"
    exit 1
fi

if [ ! -d "$ROOT_DIR/rag-engine" ]; then
    echo -e "${RED}❌ rag-engine not found at: $ROOT_DIR/rag-engine${NC}"
    exit 1
fi

# Authenticate with GCR
echo -e "${YELLOW}🔐 Authenticating with GCR...${NC}"
gcloud auth configure-docker --quiet
echo -e "${GREEN}✅ Authenticated${NC}"
echo ""

# Enable BuildKit for faster builds with cache
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
echo -e "${YELLOW}🔧 Enabled BuildKit for caching${NC}"
echo ""

# Build and push RAG Engine (for linux/amd64 - GKE platform)
# Using cache for faster rebuilds
echo -e "${YELLOW}🤖 Building RAG Engine (linux/amd64) with cache...${NC}"
cd "$ROOT_DIR/rag-engine"
docker buildx build \
    --platform linux/amd64 \
    -t ${REGISTRY}/rag-engine-api:latest \
    --cache-from type=registry,ref=${REGISTRY}/rag-engine-api:buildcache \
    --cache-to type=registry,ref=${REGISTRY}/rag-engine-api:buildcache,mode=max \
    --push .
echo -e "${GREEN}✅ RAG Engine built and pushed${NC}"
echo ""

# Build and push Backend (for linux/amd64)
echo -e "${YELLOW}⚙️  Building Backend (linux/amd64) with cache...${NC}"
cd "$ROOT_DIR/parkho-ai-backend"
docker buildx build \
    --platform linux/amd64 \
    -t ${REGISTRY}/parkho-ai-backend:latest \
    --cache-from type=registry,ref=${REGISTRY}/parkho-ai-backend:buildcache \
    --cache-to type=registry,ref=${REGISTRY}/parkho-ai-backend:buildcache,mode=max \
    --push .
echo -e "${GREEN}✅ Backend built and pushed${NC}"
echo ""

# Build and push Frontend (for linux/amd64)
echo -e "${YELLOW}🎨 Building Frontend (linux/amd64) with cache...${NC}"
cd "$ROOT_DIR/parkho-ai-frontend"
docker buildx build \
    --platform linux/amd64 \
    -t ${REGISTRY}/parkho-ai-frontend:latest \
    --cache-from type=registry,ref=${REGISTRY}/parkho-ai-frontend:buildcache \
    --cache-to type=registry,ref=${REGISTRY}/parkho-ai-frontend:buildcache,mode=max \
    --push .
echo -e "${GREEN}✅ Frontend built and pushed${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✅ All Images Built and Pushed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Images:${NC}"
echo "  - ${REGISTRY}/rag-engine-api:latest"
echo "  - ${REGISTRY}/parkho-ai-backend:latest"
echo "  - ${REGISTRY}/parkho-ai-frontend:latest"
echo ""
echo -e "${YELLOW}Next: Run ./deploy.sh to deploy to Kubernetes${NC}"
echo ""

