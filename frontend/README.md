# AutoTriage React + Tailwind CSS Frontend Portal

A modern, responsive, dark-mode **React + Vite + Tailwind CSS** frontend portal for the **Support Ticket Triage & Routing MLOps System**.

---

## ✨ Features

- **Live AI Ticket Triage Workspace**: Real-time continuous NLP inference powered by fine-tuned DistilBERT with a 350ms debounced input, dynamic confidence meter, urgency scoring, Feast VIP customer feature lookup, and full 5-class softmax probability breakdown.
- **Batch JSON Triage**: Multi-ticket batch prediction preview with instant tabular dispatch results.
- **Support Agent Triage Queue**: Interactive ticket queue with smart search, category/priority/team filtering, VIP account toggle, and a slide-over ticket inspection drawer.
- **MLOps Command Center**:
  - Live production inference telemetry (total inferences, p50 latency, mean confidence).
  - Statistical drift analyzer (Evidently AI) with two-sample Kolmogorov-Smirnov test p-values and Wasserstein distances.
  - MLflow Model Registry hot-reload panel with 1-click zero-downtime `@production` promotions and rollbacks.
  - Closed-loop retraining simulator executing the automated Prefect 3 DAG.

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
npm install
```

### 2. Start Development Server
```powershell
npm run dev
```
👉 Open browser: `http://localhost:5173`

*(Ensure the FastAPI backend is running on `http://localhost:8000` via `.\.venv\Scripts\uvicorn src.presentation.api.app:app --port 8000`)*

### 3. Production Build
```powershell
npm run build
```
The compiled bundle will be generated in `dist/`.
