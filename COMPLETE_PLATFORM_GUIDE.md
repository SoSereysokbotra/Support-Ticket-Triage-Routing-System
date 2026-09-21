# Support Ticket Triage & Routing System — Complete Platform Maturity Guide

> **Official Record of System Overhaul & Production Platform Evolution**  
> *Covering Correctness Overhaul, Phase A (CI/Security), Phase B (Kubernetes/Helm), Phase C (ArgoCD GitOps), and Phase D (Observability with Prometheus & Grafana).*

---

## 📑 Table of Contents
1. [Platform Evolution Summary & Maturity Ladder](#1-platform-evolution-summary--maturity-ladder)
2. [Pillars 1–4: Architectural Overhaul & Correctness](#2-pillars-14-architectural-overhaul--correctness)
3. [Phase A: Advanced CI & Supply-Chain Security](#3-phase-a-advanced-ci--supply-chain-security)
4. [Phase B: Kubernetes & Helm Container Orchestration (k3d)](#4-phase-b-kubernetes--helm-container-orchestration-k3d)
5. [Phase C: Declarative GitOps with ArgoCD](#5-phase-c-declarative-gitops-with-argocd)
6. [Phase D: Production Observability (Prometheus & Grafana)](#6-phase-d-production-observability-prometheus--grafana)
7. [Phase E: Dynamic Horizontal Pod Autoscaling (HPA v2)](#7-phase-e-dynamic-horizontal-pod-autoscaling-hpa-v2)
8. [Service Topology & Port Matrix](#8-service-topology--port-matrix)
9. [Operator Runbook & Automation Cheat Sheet](#9-operator-runbook--automation-cheat-sheet)

---

## 1. Platform Evolution Summary & Maturity Ladder

The project was evolved from a local Python prototype into a **Level 5 Elastic Production ML Platform** adhering to the principle:
> **"First make the system correct. Then make it automated. Then make it observable. Then make it sophisticated."**

```text
               COMPLETE MATURITY ROADMAP
────────────────────────────────────────────────────────────────
  [✓] Architectural Overhaul (Pillars 1–4: Correctness & DIP)
  [✓] Phase A: Advanced CI & Supply-Chain Security (Ruff, Pytest, Trivy, GHCR)
  [✓] Phase B: Kubernetes & Helm Container Orchestration (k3d, Traefik Ingress)
  [✓] Phase C: Declarative GitOps Continuous Delivery (ArgoCD, Self-Healing)
  [✓] Phase D: Full Production Observability (Prometheus, Grafana, MLOps KPIs)
  [✓] Phase E: Dynamic Horizontal Pod Autoscaling (HPA v2, Metrics Server)
```

| Level | Capability | Technology Applied | Status |
| :--- | :--- | :--- | :--- |
| **Level 1: Local / Containerized** | Multi-stage Docker builds, non-root execution, decoupled feature store | Docker, FastAPI, React, SQLite, Feast | **Verified** |
| **Level 2: Automated CI** | Ruff linting, clean-clone Feast bootstrap, 43 automated unit/integration tests, Trivy CVE scanning | GitHub Actions, Pytest, Ruff, Trivy | **Verified** |
| **Level 3: Container Orchestration** | Multi-node Kubernetes cluster, unified Helm chart, PVC storage, rolling updates | k3d, k3s, Helm 3, Traefik Ingress | **Verified** |
| **Level 4: Declarative GitOps** | GitHub as single source of truth, automated sync, automated drift self-healing | ArgoCD v3.5, Custom Application CRD | **Verified** |
| **Level 4+: Full Observability** | Golden Signals, real-time MLOps telemetry, in-cluster scraping, visual dashboards | Prometheus, Grafana 10.4, OpenTelemetry | **Verified** |
| **Level 5: Dynamic Autoscaling** | Elastic inference scaling (1–5 pods), CPU/RAM utilization targets, GitOps reconciliation alignment | Kubernetes HPA v2, Metrics Server | **Verified** |

---

## 2. Pillars 1–4: Architectural Overhaul & Correctness

Before adding cloud-native infrastructure, all four core areas from the senior architectural audit were resolved and verified with 43/43 passing tests.

### Pillar 1: Engineering Quality
1. **Application State Preservation on Hot-Reload / Rollback:**
   - *Problem:* In `src/presentation/api/routes/registry.py`, model promotion/rollback re-instantiated `PredictTicketUseCase` with `None` for the urgency classifier and Feast feature store, destroying VIP routing.
   - *Fix:* Preserved existing use case dependencies across reloads (`existing_urgency = getattr(...)`, `existing_store = getattr(...)`).
2. **True Vectorized Batch Inference:**
   - *Problem:* Batch prediction sequentially looped through tickets one by one ($O(N)$ HTTP overhead).
   - *Fix:* Added `batch_execute()` in `PredictTicketUseCase` that runs vectorized `predict_batch()` across the category and urgency models and fetches bulk customer features from Feast in a single query.
3. **Multi-Stage Containerfile & Non-Root Execution:**
   - *Problem:* Single-stage Dockerfile ran as root with compiler tools retained in the final image.
   - *Fix:* Built a true 2-stage build (`builder` -> `runtime`) with an unprivileged user `appuser:appuser` (UID 10001).
4. **Eliminating the Windows Host Bind-Mount Trap:**
   - *Problem:* Mounting `./mlruns.db:/app/mlruns.db` caused Docker on Windows to create an empty directory if missing on clean clones.
   - *Fix:* Relocated the tracking SQLite database to `data/mlruns.db`, safely covered by directory mount `./data:/app/data`.
5. **Hexagonal Architecture Decoupling (DIP):**
   - *Problem:* Application layer directly imported Feast infrastructure classes.
   - *Fix:* Extracted abstract port `IFeatureStore` in `src/domain/interfaces/`. The application use case depends strictly on this interface.

### Pillar 2: ML & MLOps Rigour
1. **Preventing Model Collapse / Pseudo-Labeling Feedback Loops:**
   - *Problem:* Auto-retraining models on unverified model predictions creates degenerative confirmation bias.
   - *Fix:* Updated `src/pipelines/monitoring/drift_monitoring_job.py` to route drifted production logs to `data/monitoring/drift_review_queue.csv` for human annotation / active learning curation.
2. **Side-by-Side Quality Gate Evaluation:**
   - *Problem:* Comparing a newly trained candidate on a new split against an old metric recorded on a historical split is invalid.
   - *Fix:* Updated `src/pipelines/orchestration/tasks/gate.py` to accept `benchmark_test_df` and dynamically benchmark the active production model side-by-side on the exact same holdout split.
3. **Realistic Baseline Confidence Distribution:**
   - *Problem:* Scalar baseline confidence (`0.95`) caused zero-variance KS-test statistical anomalies.
   - *Fix:* In `src/infrastructure/monitoring/drift_detector.py`, synthesized a realistic Gaussian distribution (`mean=0.92, std=0.06`).

### Pillar 3: Frontend Quality
1. **Live Production Telemetry in Agent Queue:**
   - Fixed `AgentQueue.jsx` response parser to handle raw array payloads, mapped SQLite columns, and removed false fallbacks to mock data.
2. **Dynamic Customer Input:**
   - Replaced static `<select>` with a free-text input and `<datalist>` autocomplete in `LiveTicketForm.jsx`.
3. **Dynamic Routing & SLA Display:**
   - Connected `CustomerProfileCard.jsx` to live SLA hours (`targetSlaHours`), priority level, and deterministic decision reasons returned by `RouteTicketUseCase`.

### Pillar 4: Documentation Accuracy
- Aligned `README.md`, `ARCHITECTURE.md`, and `SYSTEM_ARCHITECTURE_GUIDE.md` with runtime code, distinguishing Feast's deterministic routing role from NLP tokenization.

---

## 3. Phase A: Advanced CI & Supply-Chain Security

Phase A established continuous testing, static analysis, and security scanning on every push.

### Artifacts & Configuration
* **Linting & Testing Standards (`pyproject.toml`):**
  - Configured **Ruff** for high-speed PEP 8 formatting and linting.
  - Configured **Pytest** with `pythonpath = ["."]` and strict asyncio test scoping.
* **Feast Bootstrap for Clean Checkouts (`tests/conftest.py`):**
  - Automatically seeds `features/data/customer_features.parquet` and executes `feast apply` during test initialization so clean CI runners never fail from missing SQLite registries.
* **GitHub Actions Workflow (`.github/workflows/ci.yml`):**
  - **Stage 1 (Lint):** Runs `ruff check .` across the repository.
  - **Stage 2 (Frontend Build):** Runs `npm ci && npm run build` in `frontend/`.
  - **Stage 3 (Backend Test):** Installs Python dependencies, applies Feast store, and runs full 43-test suite.
  - **Stage 4 (Docker Build & Trivy Scan):** Builds container image and runs **Aquasecurity Trivy** to block high/critical CVEs.
  - **Stage 5 (GHCR Push):** Pushes production image to GitHub Container Registry (`ghcr.io`).

---

## 4. Phase B: Kubernetes & Helm Container Orchestration (k3d)

Phase B transitioned the application from Docker Compose to an industry-grade local Kubernetes cluster.

### Cluster Architecture
* **Cluster Engine:** `k3d` v5.9.0 managing a multi-node `k3s` cluster (`ticket-triage-cluster`) inside Docker Desktop.
* **Ingress Controller:** Built-in **Traefik Ingress** mapped from host port `8080` to cluster node load balancer (`8080:80@loadbalancer`).
* **Packaging:** Complete Helm 3 chart in `deploy/helm/ticket-triage/`:
  - `templates/deployment-api.yaml`: FastAPI backend with rolling updates, liveness/readiness probes (`/health`), and resource requests/limits.
  - `templates/deployment-frontend.yaml`: React + Nginx static server.
  - `templates/deployment-mlflow.yaml`: MLflow server with SQLite backend and artifact store persistence.
  - `templates/pvc.yaml`: PersistentVolumeClaims (`ticket-triage-data`, `ticket-triage-mlruns`) utilizing `local-path` storage class.
  - `templates/ingress.yaml`: Routes `/` to Frontend and `/api`, `/health`, `/docs`, `/openapi.json`, `/metrics` to the FastAPI backend.

### Windows Kubeconfig Host Resolution
k3d on Windows writes `server: https://host.docker.internal:<port>` in kubeconfig, which can time out on local host shells. `deploy/scripts/cluster-up.ps1` automatically patches the cluster server address to `https://127.0.0.1:<port>`.

---

## 5. Phase C: Declarative GitOps with ArgoCD

Phase C automated deployments by turning the Git repository into the single source of truth.

### Components & Deployment
* **In-Cluster ArgoCD Engine (`argocd` namespace):**
  - `argocd-server`: Exposes the Web UI (patched with `--insecure` for local HTTP access).
  - `argocd-repo-server`: Clones GitHub repositories and renders Helm charts.
  - `argocd-application-controller`: Compares live cluster state with Git target state and performs reconciliation.
  - `argocd-redis`: High-speed manifest and state cache.
* **Application Custom Resource (`deploy/argocd/application.yaml`):**
  ```yaml
  apiVersion: argoproj.io/v1alpha1
  kind: Application
  metadata:
    name: ticket-triage
    namespace: argocd
  spec:
    project: default
    source:
      repoURL: https://github.com/SoSereysokbotra/Support-Ticket-Triage-Routing-System.git
      targetRevision: develop
      path: deploy/helm/ticket-triage
      helm:
        valueFiles:
          - values.yaml
    destination:
      server: https://kubernetes.default.svc
      namespace: default
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
  ```

### Live Self-Healing & Drift Detection Verification
1. An engineer manually modified the live cluster out-of-band:
   ```powershell
   kubectl scale deployment ticket-triage-api --replicas=2
   ```
2. The ArgoCD controller detected the configuration drift against Git (`values.yaml` declared `replicaCount: 1`).
3. ArgoCD immediately self-healed the cluster, terminating the extra pod and restoring `spec.replicas = 1`.

---

## 6. Phase D: Production Observability (Prometheus & Grafana)

Phase D equipped the system with metric instrumentation, in-cluster Prometheus scraping, and visual MLOps dashboards.

### 1. Application Metric Instrumentation (`src/infrastructure/monitoring/metrics.py`)
Mounted standard Prometheus exposition format at `/metrics`:
* **HTTP Golden Signals:**
  - `http_requests_total`: Counter by `method`, `endpoint`, and `status_code`.
  - `http_request_duration_seconds`: Latency histogram with 12 distribution buckets.
* **ML & Routing Telemetry:**
  - `triage_predictions_total`: Counter labeled by `predicted_category`, `priority_level`, `assigned_team`, and `auto_routed`.
  - `triage_prediction_confidence`: Distribution of prediction confidence scores.
  - `triage_inference_latency_seconds`: Model inference latency histogram.
  - `triage_active_model_info`: Gauge reporting active production model version.

### 2. In-Cluster Prometheus Server
* **Manifests:** `deploy/helm/ticket-triage/templates/deployment-prometheus.yaml` & `configmap-prometheus.yaml`.
* **Scraping Configuration:** Continuously scrapes `ticket-triage-api:8000/metrics` every 5 seconds with `< 10ms` duration. Target status: **`up`**.

### 3. Pre-Provisioned Grafana Dashboard
* **Manifests:** `deploy/helm/ticket-triage/templates/deployment-grafana.yaml` & `configmap-grafana.yaml`.
* **Datasource:** Automatically pre-configured to connect to `http://ticket-triage-prometheus:9090`.
* **Dashboard Name:** **"Support Ticket Triage — Operations & MLOps Golden Signals"** (`uid: ticket-triage-mlops`).
* **Visual Panels:**
  1. Total Predictions Counter (Instant Gauge)
  2. Auto-Routed Tickets Count vs Human Triage Queue Count
  3. Inference Error Rate (% 5xx responses)
  4. Real-Time HTTP Request Rate (RPS by endpoint)
  5. API Latency percentiles (p50 and p95 in milliseconds)
  6. Predictions by Category Breakdown (Bar chart)
  7. Auto-Routing vs Human Escalation Ratio (Pie chart)

---

## 7. Phase E: Dynamic Horizontal Pod Autoscaling (HPA v2)

To protect the inference layer against latency degradation and compute exhaustion during peak ticket surges, the platform implements native Kubernetes **HorizontalPodAutoscaler (HPA v2)** coupled with a dedicated **Metrics Server**.

### Key Architectural Enhancements:
1. **Cluster Metrics Layer (`metrics-server`):**
   - Deployed into `kube-system` namespace to expose the `metrics.k8s.io` API.
   - Configured with `--kubelet-insecure-tls` for local containerized k3d multi-node networking.
   - Supplies sub-minute pod CPU (`kubectl top pods`) and memory consumption metrics to the Kubernetes HPA controller.
2. **Declarative HPA Spec (`deploy/helm/ticket-triage/templates/hpa.yaml`):**
   - **Target:** `ticket-triage-api` deployment.
   - **Replica Range:** `minReplicas: 1`, `maxReplicas: 5`.
   - **Target Thresholds:** CPU average utilization `60%`, Memory average utilization `80%`.
   - **Responsive Scaling Policies:**
     - **Scale-Up:** Immediate (0s stabilization window, up to 100% pod increase or +2 pods every 15s).
     - **Scale-Down:** Controlled (60s stabilization window, gradual 50% pod reduction every 30s to eliminate metric thrashing).
3. **GitOps Reconciliation Alignment (`deploy/argocd/application.yaml`):**
   - Resolves the classic GitOps vs. Autoscaling race condition where ArgoCD `selfHeal: true` would otherwise overwrite HPA scaling decisions back to `values.yaml`'s static `replicaCount: 1`.
   - Declares `spec.ignoreDifferences` targeting `ticket-triage-api` deployment at `/spec/replicas`.

---

## 8. Service Topology & Port Matrix

| Service | Port | Access URL | Authentication | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Triage Web Portal** | `8080` | [http://localhost:8080/](http://localhost:8080/) | None (Public) | React Web Application & Live Agent Queue |
| **FastAPI Backend** | `8080` | [http://localhost:8080/docs](http://localhost:8080/docs) | None (Public) | Swagger UI, Health & Inference APIs |
| **Prometheus Scrape Endpoint** | `8080` | [http://localhost:8080/metrics](http://localhost:8080/metrics) | None (Public) | Raw Prometheus exposition metric output |
| **ArgoCD GitOps Dashboard** | `8081` | [http://localhost:8081](http://localhost:8081) | `admin` / `bSdHlngsHTzwSt50` | GitOps topology, cluster sync & self-healing |
| **Grafana Observability** | `3000` | [http://localhost:3000/d/ticket-triage-mlops](http://localhost:3000/d/ticket-triage-mlops) | Anonymous Admin (None required) | Golden Signals & MLOps visual dashboard |
| **MLflow Model Registry** | `5000` | In-cluster / internal | None (Internal) | Experiment tracking & model versioning |
| **Prometheus Server** | `9090` | In-cluster / internal | None (Internal) | Time-series metric database & scraper |
| **Kubernetes Metrics Server** | `10250` | In-cluster / internal | RBAC / ServiceAccount | Real-time container resource telemetry provider |

---

## 9. Operator Runbook & Automation Cheat Sheet

All platform management tasks are encapsulated in PowerShell automation scripts under `deploy/scripts/`:

### 1. Cluster Lifecycle
* **Spin up cluster:**
  ```powershell
  .\deploy\scripts\cluster-up.ps1
  ```
* **Enable / Verify Metrics Server:**
  ```powershell
  .\deploy\scripts\enable-metrics.ps1
  ```
* **Tear down cluster and clean resources:**
  ```powershell
  .\deploy\scripts\cluster-down.ps1
  ```

### 2. Deployment & GitOps
* **Build local images & deploy via Helm:**
  ```powershell
  .\deploy\scripts\deploy.ps1
  ```
* **Install ArgoCD GitOps engine:**
  ```powershell
  .\deploy\scripts\argocd-setup.ps1
  ```
* **Launch ArgoCD Web UI:**
  ```powershell
  .\deploy\scripts\argocd-ui.ps1
  ```

### 3. Monitoring, Autoscaling & Load Testing
* **Launch Grafana Observability Dashboard:**
  ```powershell
  .\deploy\scripts\grafana-ui.ps1
  ```
* **Watch HPA Scaling in Real-Time:**
  ```powershell
  kubectl get hpa ticket-triage-api -w
  ```
* **Execute High-Concurrency Stress / Load Test:**
  ```powershell
  .\deploy\scripts\load-test.ps1 -Concurrency 30 -DurationSeconds 60
  ```
* **Query active cluster pods:**
  ```powershell
  kubectl get pods -A
  ```
