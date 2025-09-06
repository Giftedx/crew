# Kubernetes Manifests

This folder contains minimal manifests to run the API (FastAPI + Alert adapter) in Kubernetes.

Files:

- `api-deployment.yaml` – Deployment running `uvicorn server.app:create_app --factory`
- `api-service.yaml` – ClusterIP service exposing port 8000
- `api-configmap.yaml` – Non-secret environment defaults
- `api-secret.yaml` – Secrets (Discord, OpenRouter/OpenAI, etc.)
- `qdrant-*.yaml` – In-cluster Qdrant deployment, service and PVC

Quick start:

1. Build & push an image containing your code (example):
   - `docker build -t your-registry/udi-bot:latest .`
   - `docker push your-registry/udi-bot:latest`
2. Edit `ops/deployment/k8s/api-deployment.yaml` and replace `your-registry/udi-bot:latest` with your image reference.
3. Apply manifests:
   - `kubectl apply -f ops/deployment/k8s/api-configmap.yaml`
   - `kubectl apply -f ops/deployment/k8s/api-secret.yaml`          # edit placeholders first
   - `kubectl apply -f ops/deployment/k8s/qdrant-pvc.yaml`
   - `kubectl apply -f ops/deployment/k8s/qdrant-deployment.yaml`
   - `kubectl apply -f ops/deployment/k8s/qdrant-service.yaml`
   - `kubectl apply -f ops/deployment/k8s/api-deployment.yaml`
   - `kubectl apply -f ops/deployment/k8s/api-service.yaml`
4. (Optional) Expose via Ingress or port-forward:
   - `kubectl port-forward svc/udi-api 8000:8000`
   - Navigate to `http://localhost:8000/health`

Env & secrets:

- Base env is supplied via `api-configmap.yaml` (non-sensitive) and `api-secret.yaml` (sensitive).
- For Alertmanager → Discord:
  - Set `DISCORD_ALERT_WEBHOOK` in `api-secret.yaml` and reference via `envFrom` (already included).

Qdrant:

- The manifests include an in-cluster Qdrant. The API deployment points `QDRANT_URL` at the `qdrant` service.

Prometheus/Grafana:

- Import dashboards from `ops/grafana/dashboards/`.
- Load alert rules from `ops/alerts/prometheus/alerts.yml` into Prometheus.
