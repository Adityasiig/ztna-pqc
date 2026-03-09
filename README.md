# Zero Trust Network Access (ZTNA) with Post-Quantum Cryptography (PQC)

Official implementation of the ZTNA-PQC Framework.

## 🚀 Setup & Implementation Steps

### 1. Database Initialization
- **File**: `database/schema.sql`
- **Action**: Run this in your PostgreSQL instance. It creates the UUID-driven tables for Users, Devices, and Policies.

### 2. Start the Gateway Server
- **File**: `gateway/app.py`
- **Action**: Launch the Flask-based Policy Decision Point.
- **Command**: `python gateway/app.py`

### 3. Run the Simulation Client
- **File**: `client/client.py`
- **Action**: Simulates an employee device attempting to access corporate resources.
- **Command**: `python client/client.py`

### 4. Enable PQC Security
- **File**: `certs/PQC_TLS_SETUP.md`
- **Action**: Follow this guide to build the `oqs-openssl` provider for actual network-level PQC encryption.

---

## 🧠 Why this project is "Zero Trust"
In this code, we implement:
- **Identity Verification**: Username/Password check.
- **Device Verification**: Checking `device_uuid` against the trusted registry.
- **Posture Verification**: Checking if the `security_level` (Device Health) is high enough.
- **Micro-segmentation**: Only allowing access to specific API routes if the policy matches.

## ⚛️ Why this project is "Post-Quantum"
The handshake logic includes **Kyber-768**, a NIST-selected algorithm for Post-Quantum Cryptography. This prevents "Harvest Now, Decrypt Later" attacks from future quantum computers.
