#!/usr/bin/env python3
"""
Simulated Microservice (Victim App)
Demonstrates:
 - Healthy operational state when Redis is reachable (1 query/sec).
 - Unbounded, aggressive retry storm when Redis becomes unreachable (20 reconnects/sec).
"""

import os
import sys
import time
import socket

TARGET_HOST = os.environ.get("TARGET_HOST", "redis")
TARGET_PORT = int(os.environ.get("TARGET_PORT", "6379"))

def attempt_connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect((TARGET_HOST, TARGET_PORT))
        s.close()
        return True
    except Exception:
        return False

def main():
    print(f"[*] orders-service started (PID: {os.getpid()}). Connecting to {TARGET_HOST}:{TARGET_PORT}...")
    
    while True:
        success = attempt_connect()
        if success:
            print(f"[HEALTHY] Successfully connected to {TARGET_HOST}:{TARGET_PORT}")
            time.sleep(1.0)
        else:
            # Failure / Unreachable -> Trigger rapid connection retry storm
            print(f"[ERROR] Failed connecting to {TARGET_HOST}:{TARGET_PORT}. Retrying immediately...")
            time.sleep(0.05)

if __name__ == "__main__":
    main()
