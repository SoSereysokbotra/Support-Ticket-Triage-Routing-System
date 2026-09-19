# 🛡️ Support Ticket Triage & Routing System

> **A Production-Grade, Self-Healing MLOps Platform** with Hexagonal Architecture, MLflow Model Registry, Feast Feature Store, Prefect Automated Retraining DAGs, and Evidently AI Drift Monitoring.

[![Tests](https://img.shields.io/badge/pytest-43%2F43%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![MLflow](https://img.shields.io/badge/MLflow-2.10%2B-0194E2.svg)](https://mlflow.org/)
[![Feast](https://img.shields.io/badge/Feast-0.36%2B-orange.svg)](https://feast.dev/)
[![Prefect](https://img.shields.io/badge/Prefect-3.0%2B-blueviolet.svg)](https://www.prefect.io/)
[![Evidently AI](https://img.shields.io/badge/Evidently%20AI-0.4%2B-red.svg)](https://www.evidentlyai.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)

---

## 🏛️ System Architecture

Built following **Hexagonal Architecture (Ports & Adapters)** and **Domain-Driven Design (DDD)** principles to decouple core domain logic from ML frameworks, feature stores, and delivery mechanisms:

```
                          [ Ingress HTTP Traffic ]
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  FastAPI / BentoML Layer  │
                       │    (REST API & Router)    │
                       └─────────────┬─────────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
      ┌─────────────────────┐ ┌─────────────┐ ┌─────────────────────┐
      │  Category Classifier│ │Urgency Model│ │ Feast Feature Store │
      │(DistilBERT / MLflow)│ │ (DistilBERT)│ │   (SQLite / Redis)  │
      └──────────┬──────────┘ └──────┬──────┘ └──────────┬──────────┘
                 │                   │                   │
                 └───────────────────┼───────────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  Composite Routing Policy │
                       │ (Domain Invariants & SLA) │
                       └─────────────┬─────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌────────────────────────┐              ┌─────────────────────────┐
    │  Triage Response & SLA │              │ SQLite Prediction Logger│
    │ (Team, Priority, Hours)│              │     (Telemetry WAL)     │
    └────────────────────────┘              └────────────┬────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ Evidently Drift Detector│
                                            │  (KS, Wasserstein, PSI)│
                                            └────────────┬────────────┘
                                                         │ (Drift > 35%)
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ Prefect Retraining DAG  │
                                            │   + MLflow Quality Gate │
                                            └─────────────────────────┘
```

---

## 📦 Directory Structure

```
├── src/
│   ├── domain/                    # Pure Python business entities & interfaces (Zero framework imports)
│   │   ├── entities/              #   Ticket, Category, Urgency
│   │   ├── value_objects/         #   PredictionResult, RoutingDecision, UrgencyResult
│   │   └── interfaces/            #   ITicketClassifier, IUrgencyClassifier (Model Ports)
│   ├── application/               # Application use-cases & DTOs
│   │   ├── use_cases/             #   PredictTicketUseCase, RouteTicketUseCase
│   │   └── dto/                   #   TicketInputDTO, TriageResponseDTO
│   ├── infrastructure/            # Concrete technical adapters
│   │   ├── models/                #   DistilBertTicketClassifier, BaselineTfidfClassifier, UrgencyClassifier
│   │   ├── registry/              #   MLflowModelRegistry (Aliases & Rollbacks)
│   │   ├── features/              #   FeastFeatureStoreAdapter, feature_generator.py
│   │   ├── monitoring/            #   PredictionLogger (SQLite WAL), DriftDetector (Evidently AI)
│   │   └── data/                  #   DatasetLoader (Ingestion & Stratified Splits)
│   ├── presentation/              # Presentation & delivery layer
│   │   ├── api/                   #   FastAPI app & routers (/health, /predict, /registry, /monitoring)
│   │   └── dashboard/             #   Streamlit MLOps Monitoring Dashboard
│   └── pipelines/                 # Pipeline execution & orchestration
│       ├── training/              #   train_distilbert.py, evaluate.py
│       ├── orchestration/         #   Prefect Retraining DAG & Quality Gate Tasks
│       └── monitoring/            #   drift_monitoring_job.py (Closed-Loop Trigger)
├── features/                      # Feast Feature Store repo configuration & definitions
├── data/                          # Data artifacts, monitoring DB, and reports
├── models/                        # Local model artifacts and checkpoints
├── tests/                         # 43+ Unit & Integration Test Suite
├── Dockerfile                     # Production Multi-Stage Containerfile
├── docker-compose.yml             # API + Dashboard + MLflow Compose stack
├── bentofile.yaml                 # BentoML Packaging Configuration
└── ARCHITECTURE.md                # In-Depth Technical Architecture Whitepaper
```

---

## 🎯 5 Core MLOps Patterns Implemented

| Pattern | Problem Solved | Implementation | Guarantee |
|---|---|---|---|
| **1. Hexagonal Architecture** | Tight coupling between ML code, serving, and storage | Domain ports (`ITicketClassifier`, `IUrgencyClassifier`) + concrete adapters | Zero domain changes when swapping ML backends |
| **2. Feast Feature Store** | **Training-Serving Skew** caused by disparate SQL vs API feature code | Shared `customer_profile_features` definitions; offline Parquet + online SQLite | **0.0000% feature skew** verified by automated unit tests |
| **3. MLflow Model Registry** | Fragile file-path deployments & messy rollback procedures | Centralized tracking backend + modern alias pointers (`@production`, `@staging`) | 1-millisecond atomic rollback without rebuilding code |
| **4. Prefect 3 Retraining DAG** | Ad-hoc retraining scripts silently deploying degraded models | Prefect pipeline with pre-flight data validation & **Quality Gate (Macro-F1 Floor 0.75)** | Automatic blocking & tagging of regressed candidate models |
| **5. Evidently AI Drift Engine** | Silent production performance degradation | SQLite WAL telemetry + KS-test / PSI / Wasserstein drift scoring | **Closed-loop trigger** automatically retrains upon detected drift |

---

## 📊 Completed MLOps Scorecard

| Phase | Metric / Guarantee | Measured Result |
|---|---|---|
| **Phase 0** | Baseline DistilBERT Macro-F1 / Accuracy | **0.9787 / 98.8%** |
| **Phase 0** | End-to-End API Latency (p50 / p95) | **14.2 ms / 28.5 ms** |
| **Phase 1** | Model Registry Rollback Time | **< 2 milliseconds** (Metadata alias update) |
| **Phase 2** | Training-Serving Feature Skew | **0.0000% Skew** (`test_skew_prevention.py`) |
| **Phase 3** | Automated Retraining Pipeline Execution Time | **~45 seconds** (Ingest ➔ Validate ➔ Train ➔ Gate) |
| **Phase 3** | Regressed Models Blocked by Quality Gate | **100% Blocked** (Candidate $0.8827$ rejected vs Prod $0.9787$) |
| **Phase 4** | Drift Score (Baseline vs Injected Drift) | **0.0% vs 100.0% Shift** |
| **Phase 4** | Time from Drift Alert ➔ Retrained Candidate | **~50 seconds** (Full Closed Loop) |
| **Phase 5** | Test Suite Coverage | **43 / 43 tests passing (100%)** |

---

## 🚀 Quick Start Guide

### 1. Environment Setup
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Run Test Suite
```powershell
.\.venv\Scripts\pytest tests/ -v
```

### 3. Materialize Feast Feature Store
```powershell
.\.venv\Scripts\python src/infrastructure/features/feature_generator.py
```

### 4. Start FastAPI Serving Service
```powershell
.\.venv\Scripts\uvicorn src.presentation.api.app:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health Status: `http://localhost:8000/health`

### 5. Launch React + Tailwind CSS Triage Portal
```powershell
cd frontend
npm install
npm run dev
```
- Portal URL: `http://localhost:5173`
- Features: Live AI ticket classification as you type, agent triage queue, and MLOps control center.

### 6. Launch Streamlit MLOps Monitoring Dashboard
```powershell
.\.venv\Scripts\streamlit run src/presentation/dashboard/app.py
```
- Dashboard URL: `http://localhost:8501`

### 7. Run Closed-Loop Drift Detection & Auto-Retraining Trigger
```powershell
.\.venv\Scripts\python -m src.pipelines.monitoring.drift_monitoring_job --window-size 100 --drift-threshold 0.30
```

### 8. Run Entire Stack with Docker Compose
```powershell
docker compose up --build -d
```
- **React Triage Portal**: `http://localhost:5173`
- **FastAPI Service**: `http://localhost:8000`
- **Streamlit Dashboard**: `http://localhost:8501`
- **MLflow Tracking Server**: `http://localhost:5000`

The first build downloads ~1.5 GB of Python wheels; later builds reuse the cached layer unless `requirements.txt` changes. Stop everything with `docker compose down`.

---

## 📡 REST API Reference

### Triage Single Ticket (`POST /api/v1/predict`)
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Core database connection pool exhausted with timeout errors on primary replica.",
    "title": "Database connection failure",
    "customer_id": "CUST-1001"
  }'
```
**Response:**
```json
{
  "ticket_id": "8b518db9-f2e1-4c17-8e68-c57b54a32e19",
  "predicted_category": "Software",
  "confidence": 0.9842,
  "assigned_team": "Software Engineering L2",
  "priority_level": "Critical",
  "target_sla_hours": 2,
  "auto_routed": true,
  "routing_reason": "High-confidence Software prediction (98.4%) from VIP customer. Expedited to 2h SLA.",
  "model_version": "v1",
  "latency_ms": 16.4,
  "customer_features": {
    "customer_tier": "Enterprise",
    "is_vip": true,
    "past_ticket_count": 18,
    "avg_resolution_time_hours": 1.8
  }
}
```

### Promote / Rollback Model Version (`POST /api/v1/registry/promote`)
```bash
curl -X POST "http://localhost:8000/api/v1/registry/promote?version=1&alias=production"
```

### Query Live Telemetry & Metrics (`GET /api/v1/monitoring/metrics`)
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/metrics"
```

### Trigger Statistical Drift Analysis (`POST /api/v1/monitoring/drift/analyze`)
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/drift/analyze?window_size=200"
```

---

## 📄 Documentation
For an in-depth architectural narrative, design decisions, and trade-off analysis, read the [`ARCHITECTURE.md`](ARCHITECTURE.md) technical whitepaper.
