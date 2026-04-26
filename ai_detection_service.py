from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
from pytorch_models import AttackFingerprintClassifier, AttackPredictionLSTM
import numpy as np
import json
import os
from datetime import datetime
import logging
from prometheus_client import start_http_server, Gauge, Counter
from haproxy_controller import HAProxyController

app = Flask(__name__)
CORS(app)

# Prometheus Metrics
RECENT_ATTACKS_GAUGE = Gauge('guardian_recent_attacks', 'Number of attacks detected in the last window')
TOTAL_DETECTIONS_COUNTER = Counter('guardian_total_detections', 'Total number of traffic detections')
ATTACK_CONFIDENCE_GAUGE = Gauge('guardian_attack_confidence', 'Confidence level of the last detected attack')

# Initialize HAProxy Controller
haproxy = HAProxyController()

# Initialize models
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Paths
MODEL_DIR = 'models'
FINGERPRINT_PATH = os.path.join(MODEL_DIR, 'fingerprint.pt')
LSTM_PATH = os.path.join(MODEL_DIR, 'lstm.pt')

# Default sizes (will be updated from weights if available)
input_size_fingerprint = 15
input_size_lstm = 15
num_classes = 5 # BENIGN, dns_amplification, http_flood, syn_flood, udp_flood

# Dynamic Model Loading
try:
    if os.path.exists(FINGERPRINT_PATH):
        sd = torch.load(FINGERPRINT_PATH, map_location=device)
        input_size_fingerprint = sd['fc1.weight'].shape[1]
        num_classes = sd['fc4.weight'].shape[0]
        fingerprint_model = AttackFingerprintClassifier(input_size=input_size_fingerprint, num_classes=num_classes).to(device)
        fingerprint_model.load_state_dict(sd)
        logging.info(f"Loaded real fingerprint model weights. Input size: {input_size_fingerprint}, Classes: {num_classes}")
    else:
        fingerprint_model = AttackFingerprintClassifier(input_size=input_size_fingerprint, num_classes=num_classes).to(device)
        logging.warning("Fingerprint model weights not found. Using initialized weights.")
    
    if os.path.exists(LSTM_PATH):
        sd_lstm = torch.load(LSTM_PATH, map_location=device)
        input_size_lstm = sd_lstm['lstm.weight_ih_l0'].shape[1]
        prediction_model = AttackPredictionLSTM(input_size=input_size_lstm).to(device)
        prediction_model.load_state_dict(sd_lstm)
        logging.info(f"Loaded real prediction model weights. Input size: {input_size_lstm}")
    else:
        prediction_model = AttackPredictionLSTM(input_size=input_size_lstm).to(device)
        logging.warning("Prediction model weights not found. Using initialized weights.")
except Exception as e:
    logging.error(f"Error loading model weights: {e}")
    # Fallback to defaults if loading fails
    fingerprint_model = AttackFingerprintClassifier(input_size=input_size_fingerprint, num_classes=num_classes).to(device)
    prediction_model = AttackPredictionLSTM(input_size=input_size_lstm).to(device)

fingerprint_model.eval()
prediction_model.eval()

# Updated attack types matching the training LabelEncoder
attack_types = ['BENIGN', 'dns_amplification', 'http_flood', 'syn_flood', 'udp_flood']

history = []
mitigation_active = False

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': os.path.exists(FINGERPRINT_PATH),
        'device': str(device)
    })

@app.route('/detect', methods=['POST'])
def detect_attack():
    data = request.json
    features = np.array([data['features']]).astype(np.float32)
    
    with torch.no_grad():
        features_tensor = torch.tensor(features).to(device)
        outputs = fingerprint_model(features_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
        
        attack_type = attack_types[predicted.item()]
        confidence_val = confidence.item() * 100
    
    detection = {
        'timestamp': datetime.now().isoformat(),
        'attack_type': attack_type,
        'confidence': confidence_val,
        'is_attack': attack_type != 'BENIGN',
        'probabilities': probabilities.cpu().numpy().tolist()[0]
    }
    
    history.append(detection)
    if len(history) > 100:
        history.pop(0)
    
    # Update Metrics
    TOTAL_DETECTIONS_COUNTER.inc()
    RECENT_ATTACKS_GAUGE.set(len([h for h in history[-20:] if h['is_attack']]))
    if detection['is_attack']:
        ATTACK_CONFIDENCE_GAUGE.set(confidence_val)
    
    return jsonify(detection)

@app.route('/predict', methods=['POST'])
def predict_attack():
    data = request.json
    time_series = np.array([data['time_series']]).astype(np.float32)
    
    with torch.no_grad():
        time_series_tensor = torch.tensor(time_series).to(device)
        prediction = prediction_model(time_series_tensor)
        risk_prob = torch.sigmoid(prediction).item()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'risk_probability': risk_prob * 100,
        'risk_level': 'HIGH' if risk_prob > 0.7 else 'MEDIUM' if risk_prob > 0.4 else 'LOW'
    })

@app.route('/stats', methods=['GET'])
def stats():
    recent_attacks = [h for h in history[-20:] if h['is_attack']]
    attack_counts = {}
    for h in history:
        atype = h['attack_type']
        attack_counts[atype] = attack_counts.get(atype, 0) + 1
        
    return jsonify({
        'total_detections': len(history),
        'recent_attacks_count': len(recent_attacks),
        'attack_type_distribution': attack_counts,
        'mitigation_active': mitigation_active,
        'current_risk_level': 'HIGH' if len(recent_attacks) > 5 else 'MEDIUM' if len(recent_attacks) > 2 else 'LOW'
    })

@app.route('/history', methods=['GET'])
def detection_history():
    return jsonify(history[-50:])

@app.route('/mitigation/toggle', methods=['POST'])
def toggle_mitigation():
    global mitigation_active
    data = request.json
    mitigation_active = data.get('active', not mitigation_active)
    
    # Real Mitigation Action: Communicate with HAProxy
    if mitigation_active:
        # In a real scenario, we'd block specific offending IPs.
        # Here we apply a global rate limit for demonstration.
        haproxy.set_rate_limit("0.0.0.0/0", limit=50) 
        logging.info("Applied global rate limit via HAProxy.")
    else:
        haproxy.clear_table()
        logging.info("Cleared HAProxy mitigation tables.")

    return jsonify({
        'status': 'success',
        'mitigation_active': mitigation_active,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/mitigation/status', methods=['GET'])
def mitigation_status():
    return jsonify({
        'mitigation_active': mitigation_active,
        'strategies': ['rate_limiting', 'connection_throttling'] if mitigation_active else []
    })

if __name__ == '__main__':
    # Start Prometheus metrics server on port 8000
    start_http_server(8000)
    logging.info("Prometheus metrics server started on port 8000")
    
    app.run(host='0.0.0.0', port=5500, debug=False)
