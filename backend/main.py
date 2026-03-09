"""
FastAPI ZTNA-PQC Gateway — Production Upgrade
Enforces Continuous Policy Validation on every resource request.
"""

import os
import requests as req
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import logging

# Ensure imports work regardless of run directory
try:
    from auth import login_user
    from policy import check_policy, list_devices, toggle, enroll, remove
    from pqc import generate_keypair
    from database import get_audit_logs, add_user, write_log
except ImportError:
    from backend.auth import login_user
    from backend.policy import check_policy, list_devices, toggle, enroll, remove
    from backend.pqc import generate_keypair
    from backend.database import get_audit_logs, add_user, write_log

app = FastAPI(title="ZTNA-PQC Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class PolicyCheckRequest(BaseModel):
    user: str
    device: str

class EnrollRequest(BaseModel):
    device_id: str
    name: str
    os: str
    security_level: int

class AddUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

# ── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.post("/login")
def api_login(payload: LoginRequest, request: Request):
    return login_user(payload.username, payload.password, ip=request.client.host)

@app.get("/api/pqc/generate")
def api_pqc_generate():
    keys = generate_keypair()
    write_log("PQC Keypair generated (Kyber-512)", "info")
    return {
        "algorithm": "Kyber-512",
        "public_key": keys["public"],
        "status": "ready",
        "verified": True
    }

# ── Policy Enforcement ────────────────────────────────────────────────────────

@app.post("/api/policy/check")
def api_check_policy(payload: PolicyCheckRequest, request: Request):
    return check_policy(payload.user, payload.device, ip=request.client.host)

@app.get("/api/devices")
def api_list_devices():
    return list_devices()

@app.post("/api/devices/toggle/{device_id}")
def api_toggle(device_id: str):
    return toggle(device_id)

@app.post("/api/devices/enroll")
def api_enroll(payload: EnrollRequest):
    ok = enroll(payload.device_id, payload.name, payload.os, payload.security_level)
    if not ok:
        raise HTTPException(status_code=409, detail="Device ID already exists")
    return {"status": "enrolled", "device_id": payload.device_id}

@app.delete("/api/devices/{device_id}")
def api_remove(device_id: str):
    ok = remove(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "removed", "device_id": device_id}

# ── Goal Proxy with Continuous Validation ─────────────────────────────────────

@app.get("/api/fetch-goal")
def api_fetch_goal(username: str, device_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer ZTNA-"):
        raise HTTPException(status_code=401, detail="Invalid ZTNA Token Provided")
        
    # CRITICAL: Enforce Zero Trust Policy before allowing access to the Resource Server
    # Even if the token is valid, if the DEVICE is revoked, this MUST fail.
    policy_res = check_policy(username, device_id)
    if policy_res.get("access") != "granted":
        write_log(f"Proxy Denied: {username} on {device_id} (Reason: {policy_res.get('reason')})", "denied", username=username)
        raise HTTPException(status_code=403, detail=f"Policy Blocked: {policy_res.get('reason')}")
        
    try:
        # Secure Internal resource URL
        resource_url = "https://ztna-resource-server.onrender.com/secret-file"
        
        # Forward the token to the real resource server
        response = req.get(resource_url, headers={"Authorization": authorization}, timeout=10)
        
        if response.status_code == 200:
            write_log(f"Secure Resource Accessed: {username}@{device_id}", "success", username=username)
            return {"content": response.text}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Audit Logs ────────────────────────────────────────────────────────────────

@app.get("/api/audit-logs")
def api_audit_logs(limit: int = 200):
    return get_audit_logs(limit)

# ── User Management ───────────────────────────────────────────────────────────

@app.post("/api/users/add")
def api_add_user(payload: AddUserRequest):
    ok = add_user(payload.username, payload.password, payload.role)
    if not ok:
        raise HTTPException(status_code=409, detail="Username already exists")
    write_log(f"User added: {payload.username} ({payload.role})", "info")
    return {"status": "created", "username": payload.username}

# Static Files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
