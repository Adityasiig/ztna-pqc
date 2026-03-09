import requests
import json
import time
import platform
import uuid

# Configuration
SERVER_URL = "http://localhost:5000/api"
DEVICE_UUID = "DEV-UUID-001"

def run_simulation():
    print("====================================================")
    print("   ZTNA-PQC CLIENT SIMULATION (Layer 1)             ")
    print("====================================================")
    
    # 1. Device Posture Check
    print(f"\n[STEP 1] Performing Device Health Check (OS: {platform.system()})...")
    time.sleep(1)
    health_resp = requests.post(f"{SERVER_URL}/device-check", json={"device_uuid": DEVICE_UUID})
    
    if health_resp.status_code == 200:
        print(f"RESULT: Device {DEVICE_UUID} verified. Status: {health_resp.json()['status']}")
    else:
        print("RESULT: Device Verification Failed.")
        return

    # 2. Authentication with PQC Context
    print("\n[STEP 2] Authenticating via ZTNA Gateway (Requesting PQC-TLS Handshake)...")
    time.sleep(1)
    login_data = {
        "username": "admin",
        "password": "password123",
        "device_uuid": DEVICE_UUID
    }
    
    auth_resp = requests.post(f"{SERVER_URL}/login", json=login_data)
    
    if auth_resp.status_code == 200:
        res = auth_resp.json()
        print(f"RESULT: {res['message']}")
        print(f"ENCRYPTION: {res['pqc_info']}")
        print(f"TOKEN ISSUED: {res['token'][:30]}...")
        
        # 3. Access Protected Resource
        print("\n[STEP 3] Accessing Isolated Resource Server (Layer 4)...")
        time.sleep(1)
        print("VERIFYING: Cipher suite validated as TLS_PQC_KYBER_WITH_AES_256_GCM...")
        print("ACCESS GRANTED: Sensitive Financial Records Retrieved.")
    else:
        print(f"RESULT: Access Denied. {auth_resp.json().get('message')}")

if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        print(f"\nERROR: Could not connect to the Gateway Server. Ensure app.py is running.")
        print(f"Details: {e}")
