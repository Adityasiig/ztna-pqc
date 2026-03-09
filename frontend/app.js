// ── Config ───────────────────────────────────────────
const API = '';

// ── Login ────────────────────────────────────────────
async function login() {
    const user = document.getElementById('user').value.trim();
    const pass = document.getElementById('pass').value;
    const btn = document.getElementById('login-btn');
    const msg = document.getElementById('login-msg');

    if (!user || !pass) { setMsg(msg, 'Please fill in all fields.', false); return; }

    btn.disabled = true; btn.textContent = 'Signing in...';

    try {
        const res = await fetch(`${API}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const data = await res.json();

        if (data.status === 'success') {
            sessionStorage.setItem('token', data.token);
            sessionStorage.setItem('user', user);
            sessionStorage.setItem('role', data.role || 'user');
            setMsg(msg, '✓ Access granted — redirecting...', true);
            setTimeout(() => window.location = '/dashboard', 800);
        } else {
            setMsg(msg, '✗ ' + (data.message || 'Access denied'), false);
            btn.disabled = false; btn.textContent = 'Sign In';
        }
    } catch {
        setMsg(msg, '✗ Cannot reach server — is it running?', false);
        btn.disabled = false; btn.textContent = 'Sign In';
    }
}

function setMsg(el, text, ok) {
    el.textContent = text;
    el.className = `msg ${ok ? 'ok' : 'err'}`;
}

// ── Dashboard init ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('.dash-body')) return;

    if (!sessionStorage.getItem('token')) { window.location = '/'; return; }

    const userEl = document.getElementById('user-role');
    if (userEl) userEl.textContent = sessionStorage.getItem('user') + ' (' + sessionStorage.getItem('role') + ')';

    const clockEl = document.getElementById('topbar-time');
    const tick = () => { if (clockEl) clockEl.textContent = new Date().toLocaleTimeString(); };
    tick(); setInterval(tick, 1000);

    logActivity('Session started — Zero Trust active', 'ok');
    logActivity('Database: SQLite (ztna.db)', 'ok');
});

// ── Tab switching ─────────────────────────────────────
function switchTab(el) {
    const tabId = el.getAttribute('data-tab');

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('tab-' + tabId).classList.add('active');

    const titles = {
        overview: 'Overview', pqc: 'PQC Key Exchange',
        devices: 'Devices', policy: 'Policy Check', audit: 'Audit Logs'
    };
    const titleEl = document.getElementById('topbar-title');
    if (titleEl) titleEl.textContent = titles[tabId] || tabId;

    if (tabId === 'devices') loadDevices();
    if (tabId === 'audit') loadAuditLogs();
}

function logout() { sessionStorage.clear(); window.location = '/'; }

// ── PQC Key ───────────────────────────────────────────
async function generateKey() {
    const btn = document.querySelector('#tab-pqc .btn-primary');
    btn.disabled = true; btn.textContent = 'Generating…';

    try {
        const res = await fetch(`${API}/pqc-key`);
        const data = await res.json();

        document.getElementById('key-meta').innerHTML =
            `Algorithm: <b>${data.algorithm}</b> &nbsp;|&nbsp; ` +
            `Mode: <b style="color:${data.real_pqc ? 'var(--green)' : '#ca8a04'}">${data.real_pqc ? 'Real PQC' : 'Simulated'}</b> &nbsp;|&nbsp; ` +
            `Key: <b>${data.key_length_bytes} bytes</b>`;
        document.getElementById('key-box').textContent = data.public_key;
        document.getElementById('key-result').style.display = 'block';
        logActivity(`PQC key generated (${data.algorithm})`, 'ok');
    } catch {
        logActivity('PQC key generation failed', 'err');
    } finally {
        btn.disabled = false; btn.textContent = 'Generate PQC Key';
    }
}

// ── Devices ───────────────────────────────────────────
async function loadDevices() {
    const tbody = document.getElementById('device-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#888;padding:1rem">Loading…</td></tr>';

    try {
        const res = await fetch(`${API}/api/devices`);
        const devs = await res.json();
        tbody.innerHTML = '';

        if (Object.keys(devs).length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#888;padding:1rem">No devices enrolled.</td></tr>';
            return;
        }

        Object.entries(devs).forEach(([id, d]) => {
            const trusted = d.trusted === 1 || d.trusted === true;
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><code>${id}</code></td>
                <td>${d.name}</td>
                <td>${d.os}</td>
                <td class="${trusted ? 'trust-trusted' : 'trust-revoked'}">${trusted ? '✓ Trusted' : '✗ Revoked'}</td>
                <td>Level ${d.security_level}</td>
                <td style="display:flex;gap:.4rem;">
                    <button class="btn-sm ${trusted ? 'revoke' : 'grant'}" onclick="toggleDevice('${id}')">
                        ${trusted ? 'Revoke' : 'Grant'}
                    </button>
                    <button class="btn-sm remove" onclick="removeDevice('${id}')">Remove</button>
                </td>`;
            tbody.appendChild(tr);
        });
    } catch {
        tbody.innerHTML = '<tr><td colspan="6" style="color:var(--red);padding:1rem">Failed to load devices</td></tr>';
    }
}

async function toggleDevice(id) {
    try {
        await fetch(`${API}/api/devices/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device: id })
        });
        logActivity(`Device "${id}" trust toggled`, 'ok');
        loadDevices();
    } catch { logActivity(`Toggle failed for "${id}"`, 'err'); }
}

async function removeDevice(id) {
    if (!confirm(`Remove device "${id}" from the database?`)) return;
    try {
        const res = await fetch(`${API}/api/devices/${encodeURIComponent(id)}`, { method: 'DELETE' });
        if (res.ok) { logActivity(`Device "${id}" removed`, 'ok'); loadDevices(); }
        else { logActivity(`Remove failed for "${id}"`, 'err'); }
    } catch { logActivity(`Remove failed for "${id}"`, 'err'); }
}

async function enrollDevice() {
    const id = document.getElementById('enroll-id').value.trim();
    const name = document.getElementById('enroll-name').value.trim();
    const os = document.getElementById('enroll-os').value.trim();
    const level = parseInt(document.getElementById('enroll-level').value) || 3;
    const msg = document.getElementById('enroll-msg');

    if (!id || !name || !os) { setMsg(msg, 'Fill in all fields.', false); return; }

    try {
        const res = await fetch(`${API}/api/devices/enroll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: id, name, os, security_level: level })
        });
        if (res.ok) {
            setMsg(msg, `✓ Device "${id}" enrolled successfully.`, true);
            ['enroll-id', 'enroll-name', 'enroll-os'].forEach(f => document.getElementById(f).value = '');
            document.getElementById('enroll-level').value = 3;
            logActivity(`Device enrolled: ${id} (${name})`, 'ok');
            loadDevices();
        } else {
            const err = await res.json();
            setMsg(msg, '✗ ' + (err.detail || 'Enrollment failed'), false);
        }
    } catch { setMsg(msg, '✗ Cannot reach server.', false); }
}

// ── Policy ────────────────────────────────────────────
async function checkPolicy() {
    const user = document.getElementById('pol-user').value.trim();
    const dev = document.getElementById('pol-dev').value.trim();
    const box = document.getElementById('policy-result');

    if (!user || !dev) {
        box.className = 'policy-result err'; box.style.display = 'block';
        box.textContent = 'Please enter both a username and device ID.';
        return;
    }

    try {
        const res = await fetch(`${API}/policy-check?user=${encodeURIComponent(user)}&device=${encodeURIComponent(dev)}`);
        const data = await res.json();
        const ok = data.access === 'granted';

        box.className = `policy-result ${ok ? 'ok' : 'err'}`;
        box.style.display = 'block';
        box.innerHTML = ok
            ? `✓ <b>Access Granted</b><br><small>User: ${data.user} &nbsp;|&nbsp; Device: ${data.device} &nbsp;|&nbsp; OS: ${data.device_info.os}</small>`
            : `✗ <b>Access Denied</b><br><small>${data.reason || 'Policy violation'}</small>`;

        logActivity(`Policy: ${user}@${dev} → ${data.access.toUpperCase()}`, ok ? 'ok' : 'err');
    } catch {
        box.className = 'policy-result err'; box.style.display = 'block';
        box.textContent = 'Cannot reach the policy engine.';
    }
}

// ── Audit Logs ────────────────────────────────────────
async function loadAuditLogs() {
    const tbody = document.getElementById('audit-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#888;padding:1rem">Loading…</td></tr>';

    try {
        const res = await fetch(`${API}/api/audit-logs`);
        const logs = await res.json();
        tbody.innerHTML = '';

        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#888;padding:1rem">No log entries yet.</td></tr>';
            return;
        }

        logs.forEach(l => {
            const tr = document.createElement('tr');
            const isOk = l.result === 'success' || l.result === 'info';
            tr.innerHTML = `
                <td style="color:var(--muted);font-size:.78rem">${l.ts}</td>
                <td>${l.username || '—'}</td>
                <td>${l.event}</td>
                <td class="${isOk ? 'trust-trusted' : 'trust-revoked'}">${l.result.toUpperCase()}</td>`;
            tbody.appendChild(tr);
        });
    } catch {
        tbody.innerHTML = '<tr><td colspan="4" style="color:var(--red);padding:1rem">Failed to load logs</td></tr>';
    }
}

// ── Goal File Access Demo ─────────────────────────────
async function fetchGoalFile() {
    const resDiv = document.getElementById('goal-file-result');
    resDiv.style.display = 'block';

    if (!token) {
        resDiv.innerHTML = `<span style="color:var(--error);">[ERROR] No active ZTNA Session Token. Please log in first.</span>`;
        return;
    }

    resDiv.innerHTML = '<span style="color:#888;">Connecting to Gateway...<br>Verifying Token...<br>Forwarding request to Resource Server...</span>';

    try {
        const response = await fetch(`${API}/api/fetch-goal`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();

        if (response.ok) {
            resDiv.innerHTML = `<span style="color:var(--text-accent);">[200 OK] Access Granted</span><br><br>${data.content}`;
            logActivity(`Goal file fetched successfully`, 'info');
        } else {
            resDiv.innerHTML = `<span style="color:var(--error);">[${response.status}] Access Denied</span><br><br>${data.detail}`;
            logActivity(`Goal file fetch denied: ${data.detail}`, 'error');
        }
    } catch (error) {
        resDiv.innerHTML = `<span style="color:var(--error);">Connection failed</span><br><br>${error.message}`;
        logActivity(`Goal file fetch failed`, 'error');
    }
}

// ── Live Activity Log ─────────────────────────────────
function logActivity(text, type) {
    const list = document.getElementById('log-list');
    if (!list) return;
    const time = new Date().toLocaleTimeString();
    const item = document.createElement('div');
    item.className = 'log-item';
    item.innerHTML = `<span class="log-ts">${time}</span><span class="log-${type} log-text">${text}</span>`;
    list.prepend(item);
    while (list.children.length > 50) list.removeChild(list.lastChild);
}
