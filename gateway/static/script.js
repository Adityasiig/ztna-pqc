document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const navItems = document.querySelectorAll('.nav-item');
    const tabOverlays = document.querySelectorAll('.tab-overlay');
    const dashboardView = document.getElementById('dashboard-view');
    const utcClockEl = document.getElementById('utc-clock');
    const globalTrustValEl = document.getElementById('global-trust-val');

    // Topo Elements
    const simTrigger = document.getElementById('sim-trigger');
    const simLog = document.getElementById('sim-log');
    const topoNodes = {
        user: document.querySelector('.n-user'),
        device: document.querySelector('.n-device'),
        idp: document.querySelector('.n-idp'),
        policy: document.querySelector('.n-policy'),
        gateway: document.querySelector('.n-gateway'),
        kms: document.querySelector('.n-kms'),
        asset: document.querySelector('.n-asset'),
        resource: document.querySelector('.n-resource')
    };
    const topoLinks = document.querySelectorAll('.link');

    // Analysis Elements
    const trustGauge = document.getElementById('trust-gauge');
    const trustGaugeTxt = document.getElementById('trust-gauge-txt');
    const pqcLatTxt = document.getElementById('pqc-lat-txt');
    const anomalyCanvas = document.getElementById('anomaly-canvas');
    const v3Stream = document.getElementById('v3-stream');

    // Overlays
    const deviceBody = document.getElementById('v3-device-body');
    const policyGrid = document.getElementById('v3-policy-grid');
    const fullLogs = document.getElementById('v3-full-logs');

    let currentTab = 'dashboard';
    let lastLogCount = 0;

    // --- Navigation ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    function switchTab(tabId) {
        currentTab = tabId;
        navItems.forEach(i => i.classList.remove('active'));
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

        tabOverlays.forEach(o => o.classList.remove('active'));

        if (tabId === 'dashboard') {
            dashboardView.style.display = 'grid';
        } else {
            dashboardView.style.display = 'none';
            document.getElementById(`${tabId}-view`).classList.add('active');
            fetchTabData(tabId);
        }
    }

    // --- Data Heartbeat ---
    async function heartbeat() {
        const now = new Date();
        utcClockEl.innerText = now.toISOString().split('T')[1].split('.')[0] + " UTC";

        if (currentTab !== 'dashboard') return;

        try {
            const res = await fetch('/api/status');
            const data = await res.json();

            // Stats Update
            const trust = (98 + (Math.random() * 0.5)).toFixed(1);
            if (globalTrustValEl) globalTrustValEl.innerText = trust + "%";
            if (trustGaugeTxt) trustGaugeTxt.innerText = Math.floor(trust);
            if (trustGauge) {
                const offset = 220 - (parseFloat(trust) / 100) * 220;
                trustGauge.style.strokeDashoffset = offset;
            }
            if (pqcLatTxt) pqcLatTxt.innerText = (10 + Math.random() * 5).toFixed(0) + "ms";

            // Telemetry Update
            if (data.logs.length !== lastLogCount) {
                renderTelemetry(data.logs);
                lastLogCount = data.logs.length;
                if (data.logs[0].event.includes('Login success')) executeSimulation();
            }
        } catch (err) { console.error("HUD Heartbeat Fail:", err); }
    }

    // --- Simulation ---
    if (simTrigger) {
        simTrigger.addEventListener('click', () => {
            simTrigger.disabled = true;
            simTrigger.innerText = "PROTOCOL_EXECUTING...";
            executeSimulation();
        });
    }

    async function executeSimulation() {
        const steps = [
            { n: ['user'], l: ['l1', 'l2'], msg: "V3.1_INIT_IDENTITY_PROX" },
            { n: ['device', 'idp'], l: ['l3', 'l4'], msg: "V3.1_VERIFYING_POSTURE" },
            { n: ['policy'], l: ['l5'], msg: "V3.1_POL_DECISION_PEP" },
            { n: ['gateway'], l: ['l6', 'l7'], msg: "V3.1_NEGOTIATING_KYBER_768" },
            { n: ['kms', 'asset'], l: ['l8', 'l9'], msg: "V3.1_WRAP_COMPLETED" },
            { n: ['resource'], l: [], msg: "V3.1_ACCESS_GRANTED_SECURE" }
        ];

        for (const s of steps) {
            simLog.innerText = `${s.msg} [${new Date().toLocaleTimeString()}]`;
            s.n.forEach(k => topoNodes[k].classList.add('active'));
            s.l.forEach(id => {
                const link = document.querySelector(`.${id}`);
                if (link) link.classList.add('active');
            });
            await new Promise(r => setTimeout(r, 1000));
        }

        setTimeout(() => {
            Object.values(topoNodes).forEach(n => n?.classList.remove('active'));
            topoLinks.forEach(l => l.classList.remove('active'));
            simTrigger.disabled = false;
            simTrigger.innerText = "EXECUTE_PQC_SIMULATION";
            simLog.innerText = "V3.1_COMMAND_SYNC_OK";
        }, 4000);
    }

    // --- Waveform ---
    const ctx = anomalyCanvas?.getContext('2d');
    if (ctx) {
        let off = 0;
        function draw() {
            ctx.clearRect(0, 0, anomalyCanvas.width, anomalyCanvas.height);
            ctx.strokeStyle = '#00f2ff';
            ctx.lineWidth = 1;
            ctx.beginPath();
            for (let i = 0; i < anomalyCanvas.width; i++) {
                const y = 30 + Math.sin(i * 0.05 + off) * 8 + Math.random() * 3;
                ctx.lineTo(i, y);
            }
            ctx.stroke();
            off += 0.15;
            requestAnimationFrame(draw);
        }
        draw();
    }

    // --- Tab Renderers ---
    async function fetchTabData(tabId) {
        const urls = { devices: '/api/devices', policies: '/api/policies', logs: '/api/logs' };
        try {
            const r = await fetch(urls[tabId]);
            const d = await r.json();
            if (tabId === 'devices') renderDevices(d);
            else if (tabId === 'policies') renderPolicies(d);
            else if (tabId === 'logs') renderFullLogs(d);
        } catch (e) { console.error("Tab Sync Fail:", e); }
    }

    function renderTelemetry(logs) {
        if (!v3Stream) return;
        v3Stream.innerHTML = '';
        logs.slice(0, 12).forEach(l => {
            const d = document.createElement('div');
            d.className = 'stream-row';
            d.innerHTML = `
                <div class="timestamp">${l.time}</div>
                <div class="event-msg">${l.event}</div>
                <div class="event-status ${l.status === 'success' ? 'ok' : 'warn'}">${l.status.toUpperCase()}</div>
            `;
            v3Stream.prepend(d);
        });
    }

    function renderDevices(devs) {
        if (!deviceBody) return;
        deviceBody.innerHTML = '';
        Object.keys(devs).forEach(id => {
            const v = devs[id];
            const t = document.createElement('tr');
            t.innerHTML = `
                <td><code>${id}</code></td><td>${v.os}</td>
                <td style="color:${v.trusted ? 'var(--lime)' : 'var(--danger)'}">${v.trusted ? 'TRUSTED' : 'REVOKED'}</td>
                <td>LVL_${v.security_level}</td>
                <td><button class="btn-v3" onclick="toggleDevice('${id}')">${v.trusted ? 'REVOKE' : 'GRANT'}</button></td>
            `;
            deviceBody.appendChild(t);
        });
    }

    function renderPolicies(pols) {
        if (!policyGrid) return;
        policyGrid.innerHTML = '';
        pols.forEach(p => {
            const d = document.createElement('div');
            d.className = 'gauge-card';
            d.innerHTML = `
                <div class="panel-title">${p.name}</div>
                <div class="dim" style="font-size:0.6rem">ACT: ${p.action.toUpperCase()}</div>
                <div class="cyan" style="font-size:0.6rem">ROL: ${p.conditions.role}</div>
            `;
            policyGrid.appendChild(d);
        });
    }

    function renderFullLogs(logs) {
        if (!fullLogs) return;
        fullLogs.innerHTML = '';
        logs.forEach(l => {
            const r = document.createElement('div');
            r.className = 'stream-row';
            r.innerHTML = `<div class="timestamp">${l.time}</div><div class="event-msg">${l.event}</div><div class="event-status ok">SUCCESS</div>`;
            fullLogs.prepend(r);
        });
    }

    window.toggleDevice = async (id) => {
        await fetch('/api/devices/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: id })
        });
        fetchTabData('devices');
    };

    setInterval(heartbeat, 1000);
    heartbeat();
});
