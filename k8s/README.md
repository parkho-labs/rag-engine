# 🚀 Deploy to GKE - Simple Guide

Deploy all 6 services to Google Kubernetes Engine.

## 📋 What Gets Deployed

1. Frontend (parkho-ai-frontend)
2. Backend (parkho-ai-backend)
3. RAG Engine
4. PostgreSQL
5. MinIO
6. Qdrant

**Only Frontend is exposed publicly** - everything else is internal.

## 🚀 3 Simple Steps

### Step 1: Create GKE Cluster

```bash
cd rag-engine/k8s
./create-gke-cluster.sh
```

Follow the prompts. Takes 5-10 minutes.

### Step 2: Build Docker Images

```bash
./build-images.sh
```

Builds all 3 images and pushes to GCR.

### Step 3: Deploy Everything

```bash
./deploy_to_gke.sh
```

Deploys all 6 services to Kubernetes.

## ⚙️ Before Deploying

Update these files:

1. **secrets.yaml** - Add your API keys and passwords
2. **ingress.yaml** - Change `your-domain.com` to your actual domain

## ✅ Check Status

```bash
kubectl get pods -n parkho-ai
kubectl get svc -n parkho-ai
kubectl get ingress -n parkho-ai
```

## 🔍 View Logs

```bash
kubectl logs -n parkho-ai -l app=frontend --tail=50
kubectl logs -n parkho-ai -l app=rag-engine --tail=50
```

## 🗑️ Delete Everything

```bash
kubectl delete namespace parkho-ai
```

That's it! Simple and straightforward. 🎉
