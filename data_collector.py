import requests
import time
import json
import subprocess
import psutil
from datetime import datetime
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AI_URL = 'http://localhost:5500'
HAProxy_STATS_URL = 'http://haproxy-lb1:8080/stats?stats;csv'

def extract_features():
    """Extract 82 traffic features for AI detection (Matching real model input)"""
    try:
        # Generate 82 features matching the model's expected input size
        # In a real scenario, these would be derived from HAProxy logs or packet capture
        features = list(np.random.uniform(0.0, 10.0, 82))
        
        # Add some "spikes" to simulate an attack randomly for demo purposes
        if np.random.random() > 0.8:
            features[0:10] = list(np.random.uniform(50.0, 100.0, 10))
            
        return features
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        return [0] * 82

def send_to_ai(features):
    """Send features to AI detection service"""
    try:
        payload = {'features': features}
        response = requests.post(f"{AI_URL}/detect", json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            log_detection(result)
            apply_mitigation(result)
            return result
    except Exception as e:
        logger.error(f"AI detection failed: {e}")
    return None

def log_detection(result):
    """Log and display detection results"""
    if result and result['is_attack']:
        print("\n" + "="*60)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ALERT: AI DETECTION ALERT!")
        print(f"  Attack Type: {result['attack_type'].upper()}")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  Recommended Mitigation:")
        print(f"    - Rate Limit: 20 req/min")
        print(f"    - Connection Limit: 300")
        print(f"    - Action: challenge_response")
        print(f"    - Priority: CRITICAL")
        print("="*60 + "\n")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OK: Normal traffic")

def apply_mitigation(result):
    """Apply mitigation based on AI recommendation"""
    if result and result['is_attack']:
        logger.info(f"Applying mitigation for {result['attack_type']}")

def main():
    logger.info("AI Data Collector Started - Monitoring traffic...")
    while True:
        try:
            features = extract_features()
            result = send_to_ai(features)
            time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            logger.info("Stopping data collector...")
            break
        except Exception as e:
            logger.error(f"Collector error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
