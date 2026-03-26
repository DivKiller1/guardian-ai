# DDoS Protection AI

An AI-powered DDoS detection and mitigation system with real-time monitoring and attack simulation.

## System Components
- **AI Detection Service**: Flask-based backend using PyTorch models to detect malicious traffic patterns.
- **Data Collector**: Script for gathering and processing network traffic data.
- **DDoS Simulator**: tool for testing system resilience against various DDoS attack vectors.
- **Frontend**: Modern React-based dashboard for real-time visualization of traffic and protection status.

## Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Node.js & npm

### Local Deployment
The easiest way to run the entire stack is using Docker Compose:
```bash
docker-compose -f docker-compose-v2.yml up --build
```

### Manual Setup

#### Backend
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the detection service:
   ```bash
   python ai_detection_service.py
   ```

#### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```

## Architecture
This project implements a multi-layered defense strategy, combining traditional threshold-based detection with advanced machine learning models for anomaly detection.
