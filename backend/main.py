"""
FastAPI ZTNA-PQC Backend — Production Upgrade
New endpoints: device enroll/remove, audit logs, user add
"""

import os
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
from datetime import datetime

from auth import login_user
from policy import check_policy, list_devices, toggle, enroll, remove
from pqc import generate_keypair, USE_REAL_PQC
from database import get_audit_logs, add_user, write_log


# ── Pydantic models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class ToggleRequest(BaseModel):
    device: str

class EnrollRequest(BaseModel):
    device_id: str
    name: str
    os: str
    security_level: int = 3

class AddUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(title="ZTNA-PQC Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    page = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(page) if os.path.exists(page) else {"ZTNA": "Running"}

@app.get("/dashboard")
def serve_dashboard():
    page = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(page):
        return FileResponse(page)
    raise HTTPException(status_code=404)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/login")
def login(payload: LoginRequest, request: Request):
    return login_user(payload.username, payload.password, ip=request.client.host)


# ── PQC ───────────────────────────────────────────────────────────────────────

@app.get("/pqc-key")
def pqc_key():
    public, _ = generate_keypair()
    write_log("PQC keypair generated", "info")
    return {
        "public_key": public.hex(),
        "algorithm": "Kyber-512",
        "real_pqc": USE_REAL_PQC,
        "key_length_bytes": len(public),
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


# ── Policy ────────────────────────────────────────────────────────────────────

@app.get("/policy-check")
def policy(user: str, device: str, request: Request):
    return check_policy(user, device, ip=request.client.host)


# ── Devices ───────────────────────────────────────────────────────────────────

@app.get("/api/devices")
def api_get_devices():
    devs = list_devices()
    # Return as dict keyed by device_id for frontend compatibility
    return {d["device_id"]: d for d in devs}

@app.post("/api/devices/toggle")
def api_toggle(payload: ToggleRequest):
    result = toggle(payload.device)
    if result is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return result

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


# ── Audit Logs ────────────────────────────────────────────────────────────────

@app.get("/api/audit-logs")
def api_audit_logs(limit: int = 200):
    return get_audit_logs(limit)


# ── Goal Proxy ────────────────────────────────────────────────────────────────
import requests as req

@app.get("/api/fetch-goal")
def api_fetch_goal(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No ZTNA Token Provided")
        
    try:
        # Production ready mapping. You can change this URL if your resource server moves.
        resource_url = "https://ztna-resource-server.onrender.com/secret-file"
        
        # Forward the token to the real resource server
        response = req.get(resource_url, headers={"Authorization": authorization})
        
        if response.status_code == 200:
            return {"content": response.text}
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── User Management ───────────────────────────────────────────────────────────

@app.post("/api/users/add")
def api_add_user(payload: AddUserRequest):
    ok = add_user(payload.username, payload.password, payload.role)
    if not ok:
        raise HTTPException(status_code=409, detail="Username already exists")
    write_log(f"User added: {payload.username} ({payload.role})", "info")
    return {"status": "created", "username": payload.username}
