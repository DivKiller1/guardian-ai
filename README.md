# Guardian AI — DDoS Detection & Mitigation Platform

> **PyTorch · HAProxy · Prometheus · Grafana · Docker**

An autonomous DDoS defence system that combines deep learning-based traffic classification with real-time load balancer control. When an attack is detected, the system dynamically injects rate-limiting rules into HAProxy — no manual intervention required.

---

## What It Does

Guardian AI sits in front of your infrastructure and monitors traffic in real time. It classifies incoming network flows using a trained PyTorch model, predicts attack risk using an LSTM, and — when confidence crosses a threshold — automatically commands HAProxy to throttle offending traffic patterns via its Runtime API.

The entire detection-to-mitigation loop is autonomous.

---

## Model Performance

Trained on the **CIC-DDoS2019** dataset (University of New Brunswick) — a real-world network capture dataset used widely in security research.

| Attack Class       | Precision | Recall |
|--------------------|-----------|--------|
| BENIGN             | 99.3%     | 99.7%  |
| DNS Amplification  | 98.4%     | 90.7%  |
| SYN Flood          | 96.8%     | 92.7%  |
| UDP Flood          | 84.5%     | 93.9%  |
| HTTP Flood         | 82.0%     | 99.5%  |
| **Overall**        | **92.6%** |        |

HTTP flood precision is intentionally lower — distinguishing HTTP flood from legitimate bursts at the flow level is a known hard problem in network security.

---

## Architecture

```
Internet Traffic
      │
      ▼
┌─────────────────────────────┐
│   HAProxy Load Balancers    │  ← 3 nodes, stick-table rate limiting
│   (lb1, lb2, lb3)          │  ← Runtime API on TCP :9999
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Backend API Replicas      │  ← 3 FastAPI instances
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   AI Detection Service      │
│   ├── AttackFingerprint     │  ← Multiclass classifier (PyTorch)
│   ├── AttackPredictionLSTM  │  ← Temporal risk predictor
│   └── HAProxy Controller   │  ← Live socket commands to load balancer
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│   Observability Stack       │
│   ├── Prometheus            │  ← Scrapes /metrics endpoint
│   ├── Alertmanager          │  ← Fires on attack_count > 5
│   └── Grafana               │  ← Auto-provisioned dashboards
└─────────────────────────────┘
```

---

## Key Technical Decisions

**Why dual-model?**
The classifier (`AttackFingerprintClassifier`) identifies *what* kind of attack is happening. The LSTM (`AttackPredictionLSTM`) looks at a rolling 10-packet window to predict *whether* an attack is about to start. Together they reduce false positives from one-off traffic spikes.

**Why HAProxy Runtime API over config reload?**
A config reload causes a brief service interruption. The Runtime API (`set table entry`) injects rate limits into HAProxy's stick-table without downtime — critical for a mitigation system.

**Why WeightedRandomSampler?**
CIC-DDoS2019 is heavily imbalanced (~70% BENIGN). Without weighted sampling, a naive model achieves high accuracy by predicting BENIGN for everything. WeightedRandomSampler ensures minority attack classes are seen proportionally during training.

---

## Stack

| Layer | Technology |
|---|---|
| AI / ML | PyTorch, LSTM, Multiclass Classifier |
| Load Balancing | HAProxy (3 nodes, stick-tables, Runtime API) |
| Backend | FastAPI (3 replicas) |
| Monitoring | Prometheus, Alertmanager, Grafana |
| Containerisation | Docker Compose |
| Dataset | CIC-DDoS2019 (UNB) |

---

## Quick Start

```bash
# Deploy the full stack — AI engine, 3x HAProxy, 3x API, monitoring
docker compose -f docker-compose-v2.yml up --build -d
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| AI Detection API | http://localhost:8001 |

---

## Training Your Own Model

```bash
# 1. Download CIC-DDoS2019 CSVs from https://www.unb.ca/cic/datasets/ddos-2019.html
# 2. Place CSVs in data/dataset/
# 3. Run training

python train.py

# Outputs: models/fingerprint.pt, models/lstm.pt, models/training_report.json
```

The training script handles column normalisation, Inf/NaN cleaning, label mapping, and class imbalance automatically.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/detect` | POST | Classify a traffic flow and get risk score |
| `/predict` | POST | Get LSTM risk prediction for a sequence |
| `/mitigation/toggle` | POST | Enable/disable HAProxy rate limiting |
| `/stats` | GET | Current detection counts and system status |
| `/metrics` | GET | Prometheus metrics endpoint |

---

## Project Structure

```
guardian-ai/
├── ai_detection_service.py   # Core FastAPI app + inference logic
├── pytorch_models.py         # Model architecture definitions
├── haproxy_controller.py     # HAProxy Runtime API client
├── train.py                  # Training pipeline (CIC-DDoS2019)
├── enhanced_ddos_simulator.py # Attack traffic simulator for testing
├── models/
│   └── training_report.json  # Verified training metrics
├── haproxy/
│   └── haproxy-lb1.cfg       # HAProxy config with stick-table
├── monitoring/
│   ├── prometheus.yml
│   ├── alert_rules.yml
│   ├── alertmanager.yml
│   └── grafana/              # Auto-provisioned datasource + dashboards
├── frontend/                 # Real-time monitoring dashboard
└── docker-compose-v2.yml     # Full stack orchestration
```
