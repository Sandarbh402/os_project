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
    print(f"[*] orders-service running (PID: {os.getpid()}). Connecting to {TARGET_HOST}:{TARGET_PORT}...")
    fail_count = 0
    
    while True:
        success = attempt_connect()
        if success:
            if fail_count > 0:
                print(f"[RECOVERED] Successfully reconnected to database ({TARGET_HOST}:{TARGET_PORT})")
                fail_count = 0
            else:
                print(f"[HEALTHY] Connected to backend database ({TARGET_HOST}:{TARGET_PORT})")
            time.sleep(1.0)
        else:
            fail_count += 1
            # Maintain aggressive reconnect storm (20 connects/sec) for eBPF sensing,
            # but throttle console output so logs remain clear and readable
            if fail_count == 1 or fail_count % 20 == 0:
                print(f"[RETRY STORM] Database unreachable ({TARGET_HOST}:{TARGET_PORT})! Retrying every 50ms (Attempts: {fail_count})...")
            time.sleep(0.05)

if __name__ == "__main__":
    main()
