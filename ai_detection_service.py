from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
from pytorch_models import AttackFingerprintClassifier, AttackPredictionLSTM
import numpy as np
import json
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Initialize models
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
fingerprint_model = AttackFingerprintClassifier().to(device)
prediction_model = AttackPredictionLSTM().to(device)

# Dummy trained weights (in production, load real trained weights)
fingerprint_model.eval()
prediction_model.eval()

attack_types = ['normal', 'http_flood', 'slowloris', 'syn_flood', 'udp_flood', 
                'dns_amplification', 'mixed_attack']

history = []
mitigation_active = False # Global mitigation state

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'models_loaded': True,
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
        'is_attack': attack_type != 'normal',
        'probabilities': probabilities.cpu().numpy().tolist()[0]
    }
    
    history.append(detection)
    if len(history) > 100:
        history.pop(0)
    
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
    app.run(host='0.0.0.0', port=5500, debug=False)
