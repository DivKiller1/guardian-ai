from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import random
import requests
import os

app = Flask(__name__)
CORS(app)

AI_SERVICE_URL = os.getenv('AI_URL', 'http://ai-detection:5500')

def check_mitigation():
    try:
        response = requests.get(f"{AI_SERVICE_URL}/mitigation/status", timeout=1)
        if response.status_code == 200:
            return response.json().get('mitigation_active', False)
    except:
        pass
    return False

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/api/data', methods=['GET'])
def get_data():
    # Simulate database query
    time.sleep(random.uniform(0.01, 0.1))
    return jsonify({
        'data': [random.randint(1, 1000) for _ in range(10)],
        'timestamp': time.time()
    })

@app.route('/', methods=['GET'])
def home():
    mitigation_active = check_mitigation()
    
    # Simulate mitigation effect: Latency or blocking
    if mitigation_active:
        # In a real scenario, we might block specific IPs. 
        # Here we simulate a "protected" state.
        time.sleep(random.uniform(0.1, 0.3)) # Extra latency for protection
        return jsonify({
            'message': 'DDoS Protected API (Mitigation Active)',
            'status': 'protected',
            'protection_level': 'HIGH'
        })
        
    return jsonify({'message': 'DDoS Protected API', 'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
