import requests
import json
import time

# Configuration (Update these to your Render URLs once deployed!)
# Example: GATEWAY_URL = "https://ztna-gateway-xyz.onrender.com"
GATEWAY_URL = "https://ztna-gateway.onrender.com"
RESOURCE_SERVER_URL = "https://ztna-resource-server.onrender.com"
GOAL_ENDPOINT = f"{RESOURCE_SERVER_URL}/secret-file"

def print_step(msg):
    print(f"\n[+] {msg}")
    time.sleep(1)

def main():
    print("=== ZTNA-PQC Goal File Access Demo ===\n")
    
    # ---------------------------------------------------------
    # STEP 1: Direct Access Attempt (The Old Way)
    # ---------------------------------------------------------
    print_step("Attempting to access the Goal File directly (NO ZTNA TOKEN)...")
    try:
        res = requests.get(GOAL_ENDPOINT)
        if res.status_code == 401:
            print(f"    -> [ACCESS DENIED HTTP 401]: {res.json()['detail']}")
        else:
            print(f"    -> Unexpected Response: {res.status_code}")
    except requests.exceptions.ConnectionError:
        print("    -> ERROR: Resource Server is not running on port 8080!")
        return

    # ---------------------------------------------------------
    # STEP 2: Authenticate via ZTNA Gateway
    # ---------------------------------------------------------
    print_step("Connecting to ZTNA Policy Enforcement Point (Gateway) to authenticate...")
    login_payload = {
        "username": "admin",
        "password": "password123"
    }
    
    try:
        auth_res = requests.post(f"{GATEWAY_URL}/login", json=login_payload)
        auth_data = auth_res.json()
    except requests.exceptions.ConnectionError:
        print("    -> ERROR: ZTNA Gateway is not running on port 8000!")
        return

    if auth_data.get("status") == "success":
        token = auth_data["token"]
        print(f"    -> [AUTHENTICATED] Received ZTNA Token: {token}")
    else:
        print("    -> [LOGIN FAILED] Cannot proceed.")
        return

    # ---------------------------------------------------------
    # STEP 3: Access Goal File WITH Token
    # ---------------------------------------------------------
    print_step("Attempting to access Goal File WITH verified ZTNA Token...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    final_res = requests.get(GOAL_ENDPOINT, headers=headers)
    
    if final_res.status_code == 200:
        print(f"    -> [ACCESS GRANTED HTTP 200]")
        print("\n================== GOAL FILE CONTENTS ==================\n")
        print(final_res.text)
        print("\n========================================================")
    else:
        print(f"    -> [ACCESS DENIED] {final_res.text}")

if __name__ == "__main__":
    main()
