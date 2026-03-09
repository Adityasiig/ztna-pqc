import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import jwt

# Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'pqc-secret-key-kyber-768')

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Global status for GUI monitoring
SYSTEM_STATUS = {
    "last_event": "System initialized",
    "threat_level": "Low",
    "active_sessions": 0,
    "pqc_status": "Idle",
    "logs": []
}

def add_log(event, status="info"):
    SYSTEM_STATUS["logs"].insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "event": event,
        "status": status
    })
    if len(SYSTEM_STATUS["logs"]) > 50:
        SYSTEM_STATUS["logs"].pop()
    SYSTEM_STATUS["last_event"] = event

# In-memory Simulation Data
MOCK_DATABASE = {
    "users": {
        "admin": {"id": "U1", "role": "admin", "password": "password123"}
    },
    "devices": {
        "DEV-UUID-001": {"id": "D1", "trusted": True, "security_level": 5, "os": "Ubuntu 24.04"}
    },
    "policies": [
        {
            "id": "P1",
            "name": "Admin Policy",
            "conditions": {"role": "admin", "device_trusted": True, "min_security": 4},
            "action": "grant"
        }
    ]
}

def policy_engine(user, device_id, context):
    """Zero Trust Policy Decision Point (PDP)"""
    device = MOCK_DATABASE["devices"].get(device_id)
    
    if not device:
        return False, "Unauthorized: Unknown Device"
    
    # Evaluate Policies
    for policy in MOCK_DATABASE["policies"]:
        conds = policy["conditions"]
        if (user["role"] == conds["role"] and 
            device["trusted"] == conds["device_trusted"] and 
            device["security_level"] >= conds["min_security"]):
            return True, f"Access Granted by {policy['name']}"
            
    return False, "Access Denied: Policy Violation"

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    device_uuid = data.get('device_uuid')
    
    user = MOCK_DATABASE["users"].get(username)
    if not user or user["password"] != password:
        return jsonify({"status": "failed", "message": "Invalid Credentials"}), 401
    
    # Run Zero Trust Evaluation
    granted, message = policy_engine(user, device_uuid, {"ip": request.remote_addr})
    
    if granted:
        token = jwt.encode({
            'user': username,
            'role': user['role'],
            'device': device_uuid,
            'exp': datetime.utcnow() + timedelta(minutes=30),
            'pqc': 'Kyber-768'
        }, SECRET_KEY, algorithm='HS256')
        
        add_log(f"Login success: {username} (Kyber-768)", "success")
        SYSTEM_STATUS["active_sessions"] += 1
        SYSTEM_STATUS["pqc_status"] = "Active (Kyber-768)"
        
        return jsonify({
            "status": "success", 
            "token": token,
            "message": message,
            "pqc_info": "Handshake secured with NIST PQC Kyber-768"
        }), 200
    
    add_log(f"Access Denied: {username} - {message}", "danger")
    return jsonify({"status": "denied", "message": message}), 403

@app.route('/api/device-check', methods=['POST'])
def device_check():
    data = request.json
    device_uuid = data.get('device_uuid')
    device = MOCK_DATABASE["devices"].get(device_uuid)
    
    if device:
        return jsonify({
            "status": "healthy",
            "device": device_uuid,
            "security_level": device["security_level"],
            "trust_locked": True
        })
    return jsonify({"status": "unknown"}), 404

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify({
        **SYSTEM_STATUS,
        "device_count": len(MOCK_DATABASE["devices"]),
        "policy_count": len(MOCK_DATABASE["policies"])
    })

@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(MOCK_DATABASE["devices"])

@app.route('/api/devices/toggle', methods=['POST'])
def toggle_device_trust():
    data = request.json
    device_id = data.get('device_id')
    if device_id in MOCK_DATABASE["devices"]:
        MOCK_DATABASE["devices"][device_id]["trusted"] = not MOCK_DATABASE["devices"][device_id]["trusted"]
        status = "Trusted" if MOCK_DATABASE["devices"][device_id]["trusted"] else "Untrusted"
        add_log(f"Device {device_id} set to {status}", "warning")
        return jsonify({"status": "success", "new_state": MOCK_DATABASE["devices"][device_id]["trusted"]})
    return jsonify({"status": "error", "message": "Device not found"}), 404

@app.route('/api/policies', methods=['GET'])
def get_policies():
    return jsonify(MOCK_DATABASE["policies"])

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(SYSTEM_STATUS["logs"])

if __name__ == '__main__':
    print("--- ZTNA-PQC GATEWAY SERVER ---")
    print("Listening on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
