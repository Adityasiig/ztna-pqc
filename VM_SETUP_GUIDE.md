# ZTNA Simulation Environment Setup (VirtualBox)

## Network Topology
- **Host-Only Adapter**: Subnet `192.168.56.0/24`
- **VM1 (Client)**: `192.168.56.10`
- **VM2 (Gateway)**: `192.168.56.20`
- **VM3 (Resource Server)**: `192.168.56.30`

## VM1: Client Setup
1. OS: Ubuntu Desktop 24.04
2. Install Python 3 & `requests`
3. Run `python3 client.py` to initiate access.

## VM2: ZTNA Gateway Setup
1. OS: Ubuntu Server 24.04
2. Install `liboqs` and `oqs-openssl`.
3. Run `python3 app.py` (Flask server).
4. Configure Policy Engine with the `devices` database logic.

## VM3: Resource Server Setup
1. OS: Ubuntu Server 24.04
2. Run a simple API (e.g., Nginx or Flask) that only accepts connections from `192.168.56.20` (VM2).
3. Firewall: `sudo ufw allow from 192.168.56.20 to any port 80/443`

## Testing the ZTNA Flow
1. **Initial State**: Accessing `192.168.56.30` from `VM1` directly should fail (blocked by firewall).
2. **Authorized Flow**:
   - VM1 performs Health Check with VM2.
   - VM1 logs into VM2 (PQC Handshake).
   - VM2 validates identity and device posture.
   - VM2 proxies/tokens the request to VM3.
3. **Audit**: Check `access_logs` for success/denial records.
