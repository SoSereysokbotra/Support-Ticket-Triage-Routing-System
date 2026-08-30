# Support Ticket Triage & Routing System

A production-grade, self-improving MLOps system that automatically categorizes, prioritizes, and routes enterprise support tickets with continuous monitoring and automated retraining.

---

## 🏛 Clean / Hexagonal Architecture

Following Domain-Driven Design (DDD) principles:

```
src/
├── domain/                    # Pure Python business entities & interfaces (Zero framework imports)
│   ├── entities/              #   Ticket, Category, Urgency
│   ├── value_objects/         #   PredictionResult, RoutingDecision
│   └── interfaces/            #   ITicketClassifier (Model Port)
├── application/               # Orchestrates use cases and business workflows
│   ├── use_cases/             #   PredictTicketUseCase, RouteTicketUseCase
│   └── dto/                   #   TicketInputDTO, TriageResponseDTO
├── infrastructure/            # Concrete technical adapters
│   ├── models/                #   DistilBertTicketClassifier, BaselineTfidfClassifier
│   └── data/                  #   DatasetLoader (Ingestion & Stratified Splits)
├── presentation/              # Delivery mechanism (HTTP API)
│   └── api/                   #   FastAPI app, /health, /api/v1/predict
└── pipelines/                 # Standalone training & evaluation pipelines
    └── training/              #   train_distilbert.py, evaluate.py
```

---

## 🚀 Quickstart Guide

### 1. Setup Virtual Environment & Install Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```powershell
.\.venv\Scripts\pytest tests/ -v
```

### 3. Run Benchmark Evaluation (Baseline TF-IDF)
```powershell
.\.venv\Scripts\python src/pipelines/training/evaluate.py
```

### 4. Fine-Tune DistilBERT Baseline
```powershell
.\.venv\Scripts\python src/pipelines/training/train_distilbert.py
```

### 5. Start FastAPI Serving Service
```powershell
.\.venv\Scripts\uvicorn src.presentation.api.app:app --host 127.0.0.1 --port 8000 --reload
```

---

## 📡 API Endpoints

- **Health Check**: `GET /health`
- **Single Ticket Triage**: `POST /api/v1/predict`
  ```json
  {
    "text": "My laptop monitor is flickering constantly and going black when I move the hinge.",
    "title": "Flickering screen",
    "customer_id": "CUST-1042",
    "urgency_hint": "High"
  }
  ```
- **Batch Triage**: `POST /api/v1/predict/batch`
