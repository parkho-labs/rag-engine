# 🚀 Next Steps - Simple Checklist

## Current Status
✅ Dockerfile optimized (saves 349MB)
✅ Build script has caching enabled
✅ Secrets updated
✅ Cluster connected

## What to Do Next

### Step 1: Rebuild Images (with optimizations)

```bash
cd rag-engine/k8s
./build-images.sh
```

This will:
- Build images with optimized Dockerfile (smaller size)
- Use cache for faster builds
- Push to GCR

**Time:** ~10-20 minutes (first time), much faster on rebuilds

---

### Step 2: Deploy Everything

```bash
./deploy_to_gke.sh
```

This deploys all 6 services to Kubernetes.

---

### Step 3: Check Status

```bash
# Watch pods starting
kubectl get pods -n parkho-ai -w

# Check when all are ready
kubectl get pods -n parkho-ai
```

Wait until all pods show `Running` status.

---

### Step 4: Initialize Database

```bash
# Get postgres pod name
POD_NAME=$(kubectl get pod -n parkho-ai -l app=postgres -o jsonpath='{.items[0].metadata.name}')

# Initialize schema
kubectl exec -n parkho-ai $POD_NAME -- psql -U postgres -d rag_engine -f /docker-entrypoint-initdb.d/schema.sql
```

---

### Step 5: Get Frontend URL

```bash
# Get Ingress IP
kubectl get ingress -n parkho-ai

# View logs if needed
kubectl logs -n parkho-ai -l app=frontend --tail=50
```

---

## Quick Commands Reference

```bash
# Check everything
kubectl get all -n parkho-ai

# View logs
kubectl logs -n parkho-ai -l app=rag-engine --tail=50
kubectl logs -n parkho-ai -l app=backend --tail=50
kubectl logs -n parkho-ai -l app=frontend --tail=50

# Restart if needed
kubectl rollout restart deployment -n parkho-ai
```

---

## That's It! 🎉

Your services will be running and only frontend is exposed publicly.

