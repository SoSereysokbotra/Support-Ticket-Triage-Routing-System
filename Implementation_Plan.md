# Project Deep-Dive — Support Ticket Triage & Routing System

*A standalone engineering playbook + phased execution timeline. This is the MLOps-shaped portfolio project — the one that turns "I trained a model" into "I operated a self-improving ML system." Structured as a complete build guide with weekly milestones, tool picks with reasoning, and a scorecard for what "done" means.*

The goal is not "build a text classifier." The classifier is the *smallest* interesting piece. The goal is: **build the complete system that trains, versions, serves, monitors, and retrains that classifier automatically, with every architectural pattern you'd find in a real MLOps job description operating on it.**

---

## 1. Why this project — and why it's the right *next* project for you

Look at your project inventory: you have a strong RAG evaluation project (JobFits), a good agent-reliability project (agent_v3), and a research-flavored transformer project. What's missing is the **MLOps loop** — the piece that separates "trained a model" from "runs ML in production." That's exactly the gap this project targets, and it's arguably the most directly employable skill on your whole roadmap because most self-taught ML people can train a model but have never operated one.

The patterns you'll learn — model registry, feature store, DAG pipelines, drift detection, automated retraining — appear in essentially every real MLOps job description. Nobody sees those on a portfolio and thinks "that's a student project." Done properly, this stands as your first *directly employable-shaped* portfolio piece.

Two things make it the right timing:

- **Your JobFits eval harness taught you the "measure before you improve" discipline.** This project reuses that muscle immediately (Phase 3's gate step, Phase 4's drift detection) so it's not a fresh learning burden — it's applying what you already have to a new pattern.
- **Your NestJS/DDD background is already Clean/Hexagonal Architecture.** Phase 0 isn't a new concept for you — it's your existing architectural instinct applied to Python/ML instead of TypeScript.

---

## 2. What "done" means (the bar)

Not "I built five phases." Done means you can hand a reviewer this evidence package:

- **A working end-to-end system**: incoming ticket → API call → prediction → routing decision, with predictions logged and monitored.
- **A model registry** with at least 3-5 model versions tracked, one currently tagged `production`, and the ability to demonstrate a rollback as a metadata change (not a redeploy).
- **Training-serving skew prevention proven**: same feature computed at training and serving time, byte-identical, via one shared definition — with a documented example of the bug this prevents.
- **A reproducible pipeline** that can be re-triggered from a single command and produces a comparably evaluated model, with data validation gates that actually stop the pipeline on bad input.
- **A monitoring dashboard** showing prediction confidence and input drift over time — with a live demo of *deliberately* feeding drifted data and watching the system detect it.
- **A closed retraining loop**: drift crosses threshold OR schedule fires → Phase 3 pipeline runs → new model evaluated → gate passes → production tag moves. Automatic, no human clicks.
- **A written architecture doc** (~2-3 pages) explaining what each pattern solves and what would break without it. This is what makes it a portfolio piece instead of a repo.

If you can produce that, you have industry-grade evidence. Not "I did a tutorial."

---

## 3. Prerequisite knowledge — what to learn *before* starting

You already have most of what's needed. The genuine gaps, in learning order:

1. **Hugging Face `transformers` + `datasets` — the fine-tuning workflow**: load pretrained, tokenize, run Trainer, save artifact. Not internals. 2-3 focused hours.
2. **MLflow** — the single most valuable tool on this list because it appears in nearly every ML job description. Logging runs, comparing them, model registry (`staging` → `production` tags), loading "current production model" instead of hardcoded paths. Half a day of focused work.
3. **Training-serving skew — the concept, not a tool.** Read one clear article until you can explain the bug in your own words with an example. This is the *why* behind Phase 2, and understanding the bug makes Feast click instantly. Without it you'll implement Feast mechanically and never understand what it prevents. **Learn this NOW, before starting.**
4. **Feast basics** — feature definitions, offline store, online store, materialization. Half a day.
5. **Prefect basics** — tasks, flows, retries, schedules. Prefect > Airflow for this project (friendlier, cleaner Python API, easier local dev). Half a day to a day.
6. **Drift detection for text** — sentence embeddings, MMD or KS-test for distributional difference, UMAP for 2D visualization so you can *see* drift. A day.
7. **BentoML / TorchServe** — do **NOT** learn upfront. You build your own API in Phase 0, then compare in Phase 5. That comparison is the lesson.

Total realistic prep: **3-5 focused days spread over a couple of weeks**, done alongside finishing JobFits Phase B, not as a solo learning sprint.

---

## 4. Dataset choice — real, not synthetic

Two solid public options. Both work; pick one and commit.

- **[IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset)** — ~48k rows, two features (ticket text + category). Clean, real, well-suited to DistilBERT fine-tuning. **Recommended default.**
- **[Customer Support Tickets (Kaggle)](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)** — richer metadata (priority, customer info, resolution time), which is useful *specifically for Phase 2's feature store* because it gives you real non-text features to compute — customer tier, past ticket count, time since last ticket. If you're confident you'll reach Phase 2, this is arguably better despite the slightly messier structure.

Synthetic data is tempting but a bad choice here — drift detection (Phase 4) is much more convincing with real distributional structure than with data you generated. Use a real dataset.

**Don't confuse "using a public dataset" with "doing a tutorial."** The dataset is the raw material; everything you build around it is yours. This is the same shape as any real ML job: you rarely collect the data yourself; the *system* is what you own.

---

## 5. System architecture (the whole thing)

```
┌──────────────────────── OFFLINE / TRAINING PATH ─────────────────────────┐
│                                                                          │
│  Kaggle dataset ─▶ ingest ─▶ validate (schema, drift, class balance) ─▶  │
│                                                                          │
│  compute features (via Feast defs) ─▶ fine-tune DistilBERT ─▶            │
│                                                                          │
│  evaluate (macro-F1, per-class F1) ─▶ GATE: beats prod? ─▶               │
│                                                                          │
│  register in MLflow ─▶ tag `staging` ─▶ (manual/auto) promote to `prod`   │
│                                                                          │
│              orchestrated by Prefect flow, each stage retryable          │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼ (model artifact in registry)
┌──────────────────────── ONLINE / SERVING PATH ───────────────────────────┐
│                                                                          │
│  Incoming ticket ─▶ FastAPI /predict ─▶ load current `prod` from MLflow │
│                                                                          │
│  ─▶ compute features (via SAME Feast defs — no skew) ─▶ inference       │
│                                                                          │
│  ─▶ log prediction + confidence + input embedding to monitoring store    │
│                                                                          │
│  ─▶ return {category, urgency, sentiment} ─▶ routing decision            │
└──────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────── MONITORING + FEEDBACK LOOP ──────────────────────┐
│                                                                          │
│  Recent embeddings vs. training distribution ─▶ drift score              │
│  Confidence distribution over time ─▶ confidence trend                   │
│  New labels arrive ─▶ live accuracy/F1                                   │
│                                                                          │
│  IF drift > threshold OR schedule fires OR N new labels accumulated:     │
│      trigger training pipeline ─▶ (loops back to top)                    │
│                                                                          │
│                Dashboard: Grafana or a simple Streamlit page             │
└──────────────────────────────────────────────────────────────────────────┘
```

Three deliberate design choices worth naming:

- **The API asks the registry for the current production model — never hardcoded.** This is the *entire point* of Phase 1. Deployment becomes a tag change, not a code change.
- **Features are defined once, used twice.** Feast is the tool that enforces this structurally. The mechanism, not the tool name, is the lesson.
- **The retraining trigger is evidence-based, not manual.** Drift score or scheduled label accumulation, both wired to actually launch the pipeline — not just alert.

---

## 6. Repository structure (Phase 0 sets this up correctly, later phases slot in)

```
ticket-triage/
├── src/
│   ├── domain/                    # pure Python, no framework imports
│   │   ├── entities/              #   Ticket, Category, Urgency
│   │   └── value_objects/         #   RoutingDecision, PredictionResult
│   ├── application/               # use cases — orchestrates domain + infra
│   │   ├── predict_ticket.py      #   "given ticket text, return prediction"
│   │   └── route_ticket.py        #   "given prediction, decide routing"
│   ├── infrastructure/            # concrete implementations
│   │   ├── models/                #   DistilBERT wrapper, loads from registry
│   │   ├── features/              #   Feast client, feature computation
│   │   ├── monitoring/            #   drift store, prediction log
│   │   └── registry/              #   MLflow client wrapper
│   ├── presentation/
│   │   └── api/                   #   FastAPI routes
│   └── pipelines/                 # Prefect flows (Phase 3+)
│       ├── train.py
│       ├── validate.py
│       └── retrain_trigger.py
├── features/                      # Feast repo (Phase 2)
│   ├── feature_definitions.py
│   └── feature_store.yaml
├── tests/                         # unit + integration
├── notebooks/                     # exploration only, never production
├── docs/                          # your architecture write-up lives here
└── mlruns/                        # local MLflow store (gitignored)
```

Two rules that make this hold up:

- **`domain/` never imports from `infrastructure/`.** If Domain needs a model, it declares an interface (an abstract class), and Infrastructure implements it. This is the Dependency Inversion principle — the same principle NestJS DDD enforces via injection tokens. If you find yourself importing MLflow into a domain file, stop and add an interface.
- **`application/` orchestrates but doesn't know framework details.** A use case says "get the current production model and predict on this ticket," not "call MLflow's `load_model(uri='models:/ticket-classifier/production')` directly." That call lives in an infrastructure adapter.

---

## 7. Tool picks and why

| Choice | Pick | Reasoning |
|---|---|---|
| Experiment tracking + registry | **MLflow** | Open-source, self-hostable (matters for cost), universally recognized on resumes, integrates cleanly with HF Transformers. W&B is nicer UX but SaaS and less flexible for local dev. |
| Feature store | **Feast** | Genuinely the standard open-source feature store. Alternative is "roll your own" — don't; that defeats Phase 2's whole point (learning the pattern). |
| Orchestration | **Prefect** | Cleaner Python API than Airflow, easier local dev, modern async support. Airflow is more common in old shops; Prefect is more common in new ones — either serves your learning. |
| Serving framework (initial) | **FastAPI** | You know it, matches your Python stack, gives you full control for Phase 0-4. |
| Serving framework (Phase 5) | **BentoML** | Purpose-built for ML serving with model packaging, versioning, batching. TorchServe is fine but Torch-specific; BentoML is framework-agnostic and more currently active. |
| Drift detection library | **Evidently AI** or roll-your-own | Evidently gives you drift metrics and reports out of the box for text embeddings. Rolling your own with MMD/KS-test is more learning but slower. Recommend Evidently for speed, but implement one drift metric yourself first to understand it. |
| Dashboard | **Streamlit** (simple) or **Grafana** (more real) | Streamlit is 30 minutes and Python-only. Grafana + Prometheus is the "industry standard" answer but adds infrastructure. For a portfolio project start with Streamlit; upgrade to Grafana in Phase 5 if you want the stronger signal. |
| Model | **DistilBERT** | Fast, small, good enough for ticket classification. Handles class imbalance via weighted cross-entropy. Save frontier models for projects that need them. |

---

## 8. Phased execution timeline

Estimates assume ~10-12 focused hours per week alongside coursework. Adjust to your reality — the *sequence* matters more than the calendar.

### Weeks 1-2 — Prep + Phase 0 (Foundation)

**Prep (before touching Phase 0):**
- Day 1-2: Fine-tune DistilBERT once on a toy dataset in a notebook, end-to-end. Not for the project — just to internalize the workflow.
- Day 3: Read one clear article on training-serving skew until you can explain it in your own words with an example.
- Day 4-5: Skim MLflow docs and run the "hello world" tutorial locally.

**Phase 0 execution:**
- **Day 6-8**: Set up repo structure per §6. Load the Kaggle dataset. Write the domain entities (`Ticket`, `Category`) and the abstract `ModelInterface` in `domain/`.
- **Day 9-11**: Fine-tune DistilBERT on the real dataset. Save the model. Wire the FastAPI `/predict` endpoint to load and use it. Write the evaluation script (macro-F1 + per-class F1 — F1 not accuracy, because ticket categories are always imbalanced).
- **Day 12-14**: Get end-to-end working: `curl` a ticket text to the API, get a category back. Sanity check per-class F1 (some classes will be terrible; note them for later).

**Milestone**: raw ticket text in, sensible category out, per-class F1 numbers written down. Model file exists somewhere reproducible.

### Weeks 3-4 — Phase 1 (Model Registry)

- **Day 15-17**: Add MLflow. Wrap your training script to log every run: params, dataset version (a git SHA of the dataset file is fine), metrics, artifact.
- **Day 18-20**: Set up the MLflow model registry. Log 2-3 training runs with different hyperparameters. Practice tagging one `production`, another `staging`.
- **Day 21-24**: Refactor the FastAPI serving layer to load the model from the registry (`models:/ticket-classifier/production`) — not from a file path. Confirm you can rollback by re-tagging a previous version.
- **Day 25-28**: Write tests: "serving loads the currently-tagged production model," "rollback is a metadata change only."

**Milestone**: two training runs exist, one is promoted, serving uses it, rollback works without a code change.

### Weeks 5-6 — Phase 2 (Feature Store)

- **Day 29-31**: Identify 3-4 non-text features that would plausibly help: e.g., customer priority tier (if in dataset), ticket length in characters, time of day the ticket was submitted, day-of-week. Nothing exotic.
- **Day 32-35**: Install Feast. Define these features in `features/feature_definitions.py`. Set up the offline store (files) and online store (SQLite for dev, Redis for later).
- **Day 36-40**: Refactor training to pull features from Feast's offline store. Refactor serving to pull the same feature definitions from Feast's online store. **Deliberately test skew**: compute the same feature on the same input at training and serving; assert identical.
- **Day 41-42**: Retrain the model with text + features. Confirm F1 improvement (or explain honestly why it didn't help — a valid finding).

**Milestone**: same feature computed identically in both paths, one shared definition. Write in your architecture doc a concrete example of what would break without this.

### Weeks 7-9 — Phase 3 (Pipeline / DAG Orchestration)

- **Day 43-46**: Install Prefect. Wrap Phase 0-2's steps as Prefect tasks: `ingest → validate → compute_features → train → evaluate → gate → register`.
- **Day 47-50**: Build the validation step properly: check for empty text, missing labels, encoding issues, sudden class-distribution shift vs. previous run. Make the pipeline actually stop if validation fails.
- **Day 51-56**: Build the gate step: new model is only promoted to `production` if its macro-F1 beats the current production model's macro-F1 on a held-out set. This is the same discipline as your JobFits eval gate — apply it here.
- **Day 57-63**: Test the pipeline end-to-end: drop new labeled tickets in, run one command, watch it flow through validation → training → evaluation → gate → registration. Break each stage deliberately and confirm failure handling.

**Milestone**: one command, full pipeline runs, gate blocks a deliberately-regressed model.

### Weeks 10-12 — Phase 4 (Monitoring + Drift + Retraining Trigger)

**This is the phase that makes it "MLOps."**

- **Day 64-68**: Set up prediction logging: every serving request writes {input text, input embedding, predicted class, confidence, timestamp} to a store (SQLite fine for now).
- **Day 69-74**: Implement drift detection: compare recent tickets' embeddings against the training set's embeddings. Start with a simple metric (mean cosine distance shift or KS-test on principal components), then swap in Evidently for the polished version. Add UMAP visualization — this is the "see the drift" step that makes it real.
- **Day 75-80**: Build the dashboard (Streamlit): confidence trend, drift score trend, per-class F1 on any labels that arrived recently.
- **Day 81-84**: Wire the retraining trigger: drift > threshold OR schedule (weekly) → triggers the Phase 3 pipeline automatically.
- **Day 85-88**: **The demo that proves the loop closed**: deliberately feed a batch of tickets about a topic not in training (invent one — e.g., paste in a bunch of finance-jargon tickets when your training was IT-support). Watch drift score spike. Watch the trigger fire. Watch the pipeline run. Watch a new model get evaluated and promoted (or gated out). Record this — it's your portfolio video.

**Milestone**: closed self-improving loop demonstrably works, dashboard shows the story.

### Weeks 13-14 — Phase 5 stretch (Multi-model + BentoML)

Optional but valuable if you have time.

- **Day 89-95**: Train and register a second model (urgency classifier). Reuse the Phase 3 pipeline — proving pipeline reusability is the point.
- **Day 96-100**: Build a lightweight routing layer: incoming ticket → category model + urgency model → combined routing decision.
- **Day 101-105**: Package your model with BentoML. Compare against your Phase 0 FastAPI implementation. Write a paragraph on the trade-offs you actually observed.

**Milestone**: two independently-versioned models behind one interface, one deployed via BentoML, honest comparison written.

### Weeks 15-16 — The write-up (do not skip)

- **Day 106-112**: Write the architecture doc (~2-3 pages) explaining each pattern, what problem it solves, and what would break without it. Include your drift-demo screenshots and the pipeline diagram. Record a 3-minute demo video.

**This document is what turns the repo into a portfolio artifact.** A working system with no explanation is a repo; a working system with a clear architectural narrative is evidence of engineering thinking. Reviewers read the doc first and the code second.

---

## 9. Difficult challenges you should expect to fight

- **Class imbalance in ticket categories.** Some categories will be 5-10x rarer than others. Track macro-F1, not accuracy, or you'll silently ship a model that's terrible at "billing dispute" and great at "password reset." Consider weighted loss or oversampling.
- **The temptation to skip the gate.** You'll train a new model that "looks better" and want to promote it without the eval check. Don't. Same discipline as JobFits Phase B — the gate is what makes this MLOps instead of vibes.
- **Feast setup overhead.** Feast has a learning curve, and the docs assume you know the pattern already. Budget extra time for the first setup; it'll click once you see the same feature go through both paths.
- **Prefect vs. your intuition to just use scripts.** You'll finish Phase 0 with a working script and think "why do I need Prefect at all?" The reason is exactly what Phase 3 forces you to face: manual scripts don't have retries, don't have gates, don't have lineage. Stick with it.
- **Drift detection producing noisy results at small scale.** Real drift signals need enough traffic to be visible; your synthetic demo (deliberate off-topic batch) is what proves the *mechanism* works, since organic drift is unlikely to hit a portfolio project's tiny traffic.
- **Feature-store overkill for the wrong things.** Don't try to store the ticket text embedding in Feast — that's not what feature stores are for. Text embeddings are a model input, not a "feature" in the feature-store sense. Store metadata: customer tier, ticket length, historical counts. Get this distinction right or you'll fight the tool.
- **Making the retraining trigger fire but not actually run the pipeline.** The number-one failure mode in Phase 4 is a beautifully-instrumented dashboard whose "trigger" is just an alert with nothing wired to it. The loop must close — trigger → actually invokes → pipeline actually runs → new model actually evaluated.

---

## 10. Scorecard (what to fill in)

| Phase | Metric | Your number |
|---|---|---|
| 0 | Baseline macro-F1, per-class F1 | ? |
| 0 | End-to-end API latency (p50/p99) | ? |
| 1 | # of model versions in registry, rollback time | ? |
| 2 | Training-serving feature equality check (pass/fail) | pass |
| 2 | F1 delta from adding non-text features | ? |
| 3 | Pipeline run time end-to-end | ? |
| 3 | # of deliberately-regressed models blocked by gate | ? |
| 4 | Drift score baseline vs. under injected drift | ? vs. ? |
| 4 | Time from drift alert → new production model | ? |
| 5 | Per-model latency, combined routing accuracy | ? |

Plus: the architecture doc (2-3 pages), the drift-detection demo video (3 minutes), the repo (clean and README'd).

---

## 11. How to push it to industry / research level

- **Industry**: this project *is* an industry-level portfolio piece as written. The push is polish — clean README, deployed publicly (Cloud Run for API + Streamlit Cloud for dashboard, both have free tiers that fit), a written case study, an honest "what I'd do differently" section. This is the artifact you point interviewers at when they ask "have you built anything with MLOps patterns."
- **Research** (optional): the drift-detection-for-text space is active. A comparative study of drift metrics (MMD vs. KS-test vs. mean-embedding-distance) on your specific dataset, with statistical rigor about false-positive rates under sub-threshold noise, is a legitimate applied contribution — especially if you write it up honestly about scale limitations.

---

## 12. Your first week (concrete next actions)

**Not now.** Not while JobFits Phase A is unlabeled. The single highest-leverage move is finishing JobFits Phase A (hand-label 50-100 pairs → real baseline → Phase B → prove the number moved). That project teaches the eval-driven muscle this project *depends* on.

**When JobFits Phase B is shipped with a real number:**
1. Spend 3-5 focused prep days (§3) — MLflow tutorial, one fine-tune of DistilBERT on a toy dataset, read one training-serving-skew article.
2. Set up the repo structure per §6.
3. Load the IT Service Ticket dataset.
4. Fine-tune DistilBERT and get the `/predict` endpoint returning something sensible.

That's Phase 0. Everything after is the pattern ladder.

---

*The one sentence to keep: **the classifier is the smallest interesting piece — the system that trains, versions, serves, monitors, and retrains it automatically is what makes this an MLOps project instead of a model training exercise.***