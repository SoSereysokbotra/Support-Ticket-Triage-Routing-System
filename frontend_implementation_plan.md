# Frontend Implementation Plan: Support Ticket Triage & MLOps Portal (React + Tailwind CSS)

A modern, high-performance, dark-mode **React + Vite + Tailwind CSS** frontend that connects directly to our FastAPI backend (`http://localhost:8000`), providing an enterprise triage workspace for customers, support agents, and MLOps engineers.

---

## 🎨 UI/UX & Aesthetic Philosophy
- **Theme**: Sleek Dark Glassmorphism (`#0B0F19` deep obsidian background, frosted glass panels with `backdrop-blur-md`, glowing borders, and curated gradient accents).
- **Typography**: Modern typography with crisp font hierarchies (Inter / Outfit).
- **Interactivity & Micro-Animations**: Smooth Framer Motion transitions, real-time AI confidence meters, live debounced inference as users type, SLA countdown rings, and instant batch triage previews.
- **Iconography**: Lucide React icons for crisp visuals across all views.

---

## 🏗️ Architecture & Project Structure

We will initialize the frontend in a dedicated `frontend/` directory:

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── assets/                  # SVG assets, logos, illustration badges
    ├── components/              # Modular UI components
    │   ├── common/              #   Button, Card, Badge, Modal, Tooltip, Toast, GlassPanel
    │   ├── layout/              #   Navbar, Sidebar, AppLayout, Footer
    │   ├── triage/              #   LiveTicketForm, PredictionMeter, SlaBadge, TeamBadge
    │   ├── queue/               #   TicketQueueTable, QueueFilterBar, TicketDetailDrawer
    │   └── mlops/               #   DriftGauge, TelemetryCards, ModelRegistryPanel, RetrainTriggerModal
    ├── services/                # Backend API client layer (Axios / Fetch)
    │   ├── api.js               #   Base Axios instance with error handling
    │   ├── ticketService.js     #   /api/v1/predict, /api/v1/predict/batch
    │   ├── monitoringService.js #   /api/v1/monitoring/metrics, /logs, /drift/analyze
    │   └── registryService.js   #   /api/v1/registry/promote, /rollback
    ├── hooks/                   # Custom React hooks
    │   ├── useDebounce.js       #   Debounces live ticket text for real-time AI inference
    │   ├── useLivePrediction.js #   Streaming prediction state
    │   └── useMonitoring.js     #   Polling / SWR for telemetry metrics
    ├── context/                 # Global state (Theme, Active User, Toast notifications)
    ├── views/                   # Full application pages
    │   ├── TriagePortal.jsx     #   Customer / Agent interactive ticket submission & live AI triage
    │   ├── AgentQueue.jsx       #   Live triage queue table with search, filter, and quick resolve
    │   └── MLOpsControl.jsx     #   Model registry, drift analysis, hot-reloading, & pipeline trigger
    ├── App.jsx                  # Route definitions & layout wrappers
    └── main.jsx                 # React root entry point
```

---

## 📋 Phase-by-Phase Roadmap

### 🔹 Phase F1: Project Setup, Design System & Core Layout
- **Goal**: Initialize Vite + React, configure Tailwind CSS with custom glassmorphism color palette and tokens, create reusable UI primitives (`GlassPanel`, `Badge`, `Button`, `ConfidenceBar`).
- **Deliverables**:
  1. Scaffold Vite app in `./frontend` with `npx -y create-vite@latest frontend --template react`.
  2. Configure `tailwind.config.js` with glowing accent colors (`cyan-500`, `indigo-500`, `rose-500`, `emerald-500`, `amber-500`) and custom glass utilities.
  3. Install dependencies (`lucide-react`, `axios`, `framer-motion`, `clsx`, `tailwind-merge`).
  4. Create `AppLayout` with responsive collapsible Sidebar and Header showing backend API health status (`/api/v1/health`).

---

### 🔹 Phase F2: Live AI Ticket Triage Workspace (Customer & Agent View)
- **Goal**: Build the core interactive triage page where users type tickets and receive real-time AI predictions.
- **Deliverables**:
  1. **Interactive Form**: Inputs for Title, Description, Customer ID dropdown (with VIP/Enterprise badges), and Urgency hints.
  2. **Real-time Live Inference**: As the user types (300ms debounce), automatically call `/api/v1/predict` and display:
     - Predicted Category badge with glowing confidence score ($0\% - 100\%$).
     - Urgency badge (`Low`, `Medium`, `High`, `Critical`).
     - Auto-assigned team and calculated SLA Target (e.g. `2 hours - Expedited for VIP`).
     - Full probability breakdown chart across all 5 classes.
  3. **Batch Submission Tab**: CSV drag-and-drop or multi-ticket textarea sending batch requests to `/api/v1/predict/batch` with instant results summary.

---

### 🔹 Phase F3: Agent Triage Queue & Ticket Management
- **Goal**: Build an enterprise support ticket queue for support agents to review, filter, and inspect incoming routed tickets.
- **Deliverables**:
  1. **Dynamic Queue Table**: Displays Ticket ID, Title, Customer Tier, Predicted Category, Urgency, SLA Timer, Assigned Team, and Routing Status (`Auto-Routed` vs `Human Review`).
  2. **Smart Filters & Search**: Filter by Team, Urgency, Category, or VIP status.
  3. **Ticket Inspection Drawer**: Slide-over modal showing full ticket payload, raw model probabilities, customer historical features from Feast, and 1-click re-routing actions.

---

### 🔹 Phase F4: MLOps Command Center & Drift Monitoring
- **Goal**: Visual control center for ML engineers to monitor production telemetry, analyze drift, and control models.
- **Deliverables**:
  1. **Telemetry KPI Cards**: Total Inferences, Avg Latency (p50/p99), Mean Confidence %, VIP Escalation Rate.
  2. **Evidently AI Statistical Drift Panel**: Trigger `/api/v1/monitoring/drift/analyze` with configurable window size; visualize feature drift and Kolmogorov-Smirnov p-values.
  3. **Model Registry & Hot-Reloading Panel**: View active `@production` and `@staging` versions, trigger instant zero-downtime rollback or promotion (`/api/v1/registry/promote`).
  4. **Closed-Loop Trigger Button**: 1-click dispatch to generate synthetic drift data and trigger the Prefect retraining pipeline with live status indicators.

---

### 🔹 Phase F5: Polish, End-to-End Testing & Build Validation
- **Goal**: Polish transitions, add responsive mobile styles, test API error handling (e.g. backend offline fallback), and create a production build.
- **Deliverables**:
  1. Toast notifications for all network events (success, error, copy to clipboard).
  2. Build validation (`npm run build`).
  3. Document frontend setup in `README.md`.

---

## 🧪 Verification Plan

### Automated Tests & Builds
- Run `npm run build` in `frontend/` to confirm clean compilation with 0 bundle errors.

### Manual End-to-End Verification
- **Live Typing Triage**: Type "Database query timeout and connection drop" → assert category updates to `Database` or `Software` and confidence meter animates.
- **VIP Customer Feature Integration**: Select `CUST-1001` (Enterprise VIP) → assert SLA drops to 2 hours and priority escalates to Critical.
- **Hot-Reload Rollback**: Promote version in MLOps tab → assert active version changes without restarting FastAPI.
- **Backend Offline Handling**: When FastAPI is stopped, assert clean toast error and retry banner appears.
