let allLicenses = [];
let allDevices = [];
let adminKey = localStorage.getItem('infinity_admin_key') || '';

document.addEventListener('DOMContentLoaded', () => {
    checkAdminAuth();
});

// --- ADMIN AUTHENTICATION ---

function checkAdminAuth() {
    if (adminKey) {
        document.getElementById('admin-auth-overlay').classList.add('hidden');
        document.getElementById('admin-main-wrapper').classList.remove('hidden');
        loadAllData();
        setInterval(loadAllData, 10000);
    } else {
        document.getElementById('admin-auth-overlay').classList.remove('hidden');
        document.getElementById('admin-main-wrapper').classList.add('hidden');
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    const key = document.getElementById('input-admin-key').value.trim();
    if (!key) return;

    try {
        const res = await fetch('/api/v1/admin/stats', {
            headers: {'X-Admin-Key': key}
        });
        if (res.status === 200) {
            adminKey = key;
            localStorage.setItem('infinity_admin_key', key);
            checkAdminAuth();
        } else {
            const err = document.getElementById('login-error');
            err.classList.remove('hidden');
        }
    } catch (e) {
        alert('Server unreachable');
    }
}

function logoutAdmin() {
    localStorage.removeItem('infinity_admin_key');
    adminKey = '';
    window.location.reload();
}

function showTab(tabName) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));

    const tabBtn = document.querySelector(`a[href="#${tabName}"]`);
    if (tabBtn) tabBtn.classList.add('active');

    const panel = document.getElementById(`tab-${tabName}`);
    if (panel) panel.classList.add('active');

    const titles = {
        'quick_control': 'License & Device Central Management',
        'licenses': 'License Authority Vault',
        'devices': 'Authorized Hardware Nodes (HWID)',
        'events': 'Real-Time Multi-User Heartbeats & Events',
        'broadcasts': 'Broadcast Notifications',
        'logs': 'Cryptographic Audit Trail'
    };
    document.getElementById('tab-title').innerText = titles[tabName] || 'Admin Console';
}

async function loadAllData() {
    await Promise.all([
        fetchStats(),
        fetchLicenses(),
        fetchDevices(),
        fetchEvents(),
        fetchNotifications(),
        fetchAuditLogs()
    ]);
}

async function fetchStats() {
    try {
        const res = await fetch('/api/v1/admin/stats', {headers: {'X-Admin-Key': adminKey}});
        const data = await res.json();
        const counts = `Total: ${data.total_licenses} · Active: ${data.active_licenses} · Expired: ${data.expired_licenses} · Revoked: ${data.revoked_licenses} · Suspended: ${data.suspended_licenses}`;
        const el = document.getElementById('lic-summary-counts');
        if (el) el.innerText = counts;
    } catch (e) {}
}

async function fetchLicenses() {
    try {
        const res = await fetch('/api/v1/admin/licenses', {headers: {'X-Admin-Key': adminKey}});
        allLicenses = await res.json();
        renderQuickLicensesTable(allLicenses);
        renderAllLicensesTable(allLicenses);
    } catch (e) {}
}

function renderQuickLicensesTable(licenses) {
    const tbody = document.querySelector('#table-quick-licenses tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    licenses.forEach(lic => {
        const tr = document.createElement('tr');
        const statusBadge = `<span class="badge badge-${lic.status.toLowerCase()}">${lic.status}</span>`;
        const expires = lic.expires_at ? new Date(lic.expires_at).toLocaleDateString() : 'Lifetime';

        tr.innerHTML = `
            <td>
                <a href="javascript:void(0)" onclick="inspectSpecificCode('${lic.code}')" style="color:var(--primary); font-family:var(--font-heading); font-weight:700; text-decoration:none;">
                    ${lic.code}
                </a>
            </td>
            <td>${lic.license_type}</td>
            <td>${statusBadge}</td>
            <td>${expires}</td>
            <td><strong>${lic.device_count}</strong> / ${lic.max_devices} <button class="btn-secondary" style="padding:2px 6px; font-size:10px;" onclick="changeDeviceLimit(${lic.id}, ${lic.max_devices})">Edit</button></td>
            <td>
                ${lic.status === 'ACTIVE' 
                    ? `<button class="btn-danger-sm" onclick="revokeLicense(${lic.id})">Revoke</button>
                       <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="suspendLicense(${lic.id})">Suspend</button>` 
                    : (lic.status === 'SUSPENDED' 
                        ? `<button class="btn-success-sm" onclick="reactivateLicense(${lic.id})">Unsuspend</button>`
                        : `<button class="btn-success-sm" onclick="reactivateLicense(${lic.id})">Reactivate</button>`)}
                <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="extendLicense(${lic.id})">+30d</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAllLicensesTable(licenses) {
    const tbody = document.querySelector('#table-all-licenses tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    licenses.forEach(lic => {
        const tr = document.createElement('tr');
        const statusBadge = `<span class="badge badge-${lic.status.toLowerCase()}">${lic.status}</span>`;
        const expires = lic.expires_at ? new Date(lic.expires_at).toLocaleDateString() : 'Lifetime';
        const created = lic.created_at ? new Date(lic.created_at).toLocaleDateString() : 'N/A';

        tr.innerHTML = `
            <td>#${lic.id}</td>
            <td><strong style="color:var(--primary); font-family:var(--font-heading);">${lic.code}</strong></td>
            <td>${lic.license_type}</td>
            <td>${statusBadge}</td>
            <td><strong>${lic.device_count}</strong> / ${lic.max_devices}</td>
            <td>${expires}</td>
            <td>${created}</td>
            <td>
                ${lic.status === 'ACTIVE' 
                    ? `<button class="btn-danger-sm" onclick="revokeLicense(${lic.id})">Revoke</button>
                       <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="suspendLicense(${lic.id})">Suspend</button>` 
                    : `<button class="btn-success-sm" onclick="reactivateLicense(${lic.id})">Reactivate</button>`}
                <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="extendLicense(${lic.id})">+30d</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterLicenses() {
    const q = document.getElementById('license-search').value.toLowerCase();
    const filtered = allLicenses.filter(l => 
        l.code.toLowerCase().includes(q) || 
        l.license_type.toLowerCase().includes(q) || 
        (l.notes && l.notes.toLowerCase().includes(q))
    );
    renderAllLicensesTable(filtered);
}

// --- GENERATE ACTIVATION CODE ---

async function handleQuickGenerate(e) {
    e.preventDefault();
    const type = document.getElementById('quick-lic-type').value;
    const devices = parseInt(document.getElementById('quick-lic-devices').value, 10);

    try {
        const res = await fetch('/api/v1/admin/licenses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-Admin-Key': adminKey},
            body: JSON.stringify({
                license_type: type,
                max_devices: devices
            })
        });
        const result = await res.json();
        alert(`New Activation Key Generated: ${result.code} (Limit: ${devices} devices)`);
        loadAllData();
    } catch (err) {
        alert('Error generating key');
    }
}

// --- DEVICES INSPECTION ---

async function fetchDevices() {
    try {
        const res = await fetch('/api/v1/admin/devices', {headers: {'X-Admin-Key': adminKey}});
        allDevices = await res.json();
        renderAllDevicesTable(allDevices);
    } catch (e) {}
}

function renderAllDevicesTable(devices) {
    const tbody = document.querySelector('#table-all-devices tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    devices.forEach(dev => {
        const tr = document.createElement('tr');
        const statusBadge = dev.is_active 
            ? '<span class="badge badge-active">Authorized</span>' 
            : '<span class="badge badge-revoked">Deactivated</span>';
        const lastSeen = dev.last_seen ? new Date(dev.last_seen).toLocaleString() : 'N/A';

        tr.innerHTML = `
            <td>#${dev.id}</td>
            <td><strong style="color:var(--primary);">${dev.license_code}</strong></td>
            <td>${dev.device_name}</td>
            <td>${dev.os_info}</td>
            <td><span class="badge badge-accent">${dev.app_version}</span></td>
            <td><code style="font-size:11px; color:var(--text-muted);">${dev.hwid.substring(0, 16)}...</code></td>
            <td>${lastSeen}</td>
            <td>${statusBadge}</td>
            <td>
                ${dev.is_active ? `<button class="btn-danger-sm" onclick="deactivateDevice(${dev.id})">Deauthorize</button>` : '—'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function inspectSpecificCode(code) {
    document.getElementById('inspect-code-input').value = code;
    inspectDevicesForCode();
}

function inspectDevicesForCode() {
    const code = document.getElementById('inspect-code-input').value.trim().toUpperCase();
    if (!code) {
        alert('Please enter an activation code to inspect.');
        return;
    }

    const matchingDevices = allDevices.filter(d => d.license_code.toUpperCase() === code);
    const tbody = document.querySelector('#table-license-devices tbody');
    tbody.innerHTML = '';

    if (matchingDevices.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-muted text-center">No devices have activated code <strong>${code}</strong> yet.</td></tr>`;
        return;
    }

    matchingDevices.forEach(dev => {
        const tr = document.createElement('tr');
        const statusBadge = dev.is_active 
            ? '<span class="badge badge-active">Authorized</span>' 
            : '<span class="badge badge-revoked">Deactivated</span>';
        const lastSeen = dev.last_seen ? new Date(dev.last_seen).toLocaleString() : 'N/A';

        tr.innerHTML = `
            <td>#${dev.id}</td>
            <td><strong>${dev.device_name}</strong> (${dev.os_info})</td>
            <td>${statusBadge}</td>
            <td>${lastSeen}</td>
            <td><code style="font-size:11px;">${dev.hwid.substring(0, 16)}...</code></td>
            <td>
                ${dev.is_active ? `<button class="btn-danger-sm" onclick="deactivateDevice(${dev.id})">Deauthorize</button>` : '—'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// --- REMOTE ACTIONS ---

async function revokeLicense(id) {
    if (!confirm('Are you sure you want to REVOKE this license? Connected users will be locked out immediately.')) return;
    await fetch(`/api/v1/admin/licenses/${id}/revoke`, {method: 'POST', headers: {'X-Admin-Key': adminKey}});
    loadAllData();
}

async function suspendLicense(id) {
    if (!confirm('Suspend this license? Users will be paused on next heartbeat.')) return;
    await fetch(`/api/v1/admin/licenses/${id}/suspend`, {method: 'POST', headers: {'X-Admin-Key': adminKey}});
    loadAllData();
}

async function reactivateLicense(id) {
    await fetch(`/api/v1/admin/licenses/${id}/reactivate`, {method: 'POST', headers: {'X-Admin-Key': adminKey}});
    loadAllData();
}

async function extendLicense(id) {
    await fetch(`/api/v1/admin/licenses/${id}/extend?days=30`, {method: 'POST', headers: {'X-Admin-Key': adminKey}});
    loadAllData();
}

async function changeDeviceLimit(id, currentLimit) {
    const newLim = prompt(`Enter new maximum device limit for license #${id}:`, currentLimit);
    if (!newLim || isNaN(newLim)) return;
    await fetch(`/api/v1/admin/licenses/${id}/set-limit`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-Admin-Key': adminKey},
        body: JSON.stringify({new_limit: parseInt(newLim, 10)})
    });
    loadAllData();
}

async function deactivateDevice(id) {
    if (!confirm('Deauthorize this hardware ID from the license?')) return;
    await fetch(`/api/v1/admin/devices/${id}/deactivate`, {method: 'POST', headers: {'X-Admin-Key': adminKey}});
    loadAllData();
}

async function fetchEvents() {
    try {
        const res = await fetch('/api/v1/admin/events', {headers: {'X-Admin-Key': adminKey}});
        const events = await res.json();
        const tbody = document.querySelector('#table-events tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        events.forEach(ev => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(ev.created_at).toLocaleString()}</td>
                <td><span class="badge badge-accent">${ev.event_type}</span></td>
                <td><strong>${ev.license_code}</strong></td>
                <td><code style="font-size:11px;">${ev.hwid ? ev.hwid.substring(0, 16) + '...' : '—'}</code></td>
                <td>${ev.details || '—'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {}
}

async function fetchNotifications() {
    try {
        const res = await fetch('/api/v1/notifications');
        const list = await res.json();
        const container = document.getElementById('broadcasts-list');
        if (!container) return;
        container.innerHTML = '';

        list.forEach(n => {
            const item = document.createElement('div');
            item.className = `notif-card-item ${n.level}`;
            item.innerHTML = `
                <div style="font-weight:700; color:#fff; font-size:14px; margin-bottom:4px;">${n.title}</div>
                <div style="font-size:13px; color:var(--text-muted);">${n.message}</div>
                <div style="font-size:10px; color:var(--text-muted); margin-top:6px;">Broadcasted: ${new Date(n.created_at).toLocaleString()}</div>
            `;
            container.appendChild(item);
        });
    } catch (e) {}
}

async function fetchAuditLogs() {
    try {
        const res = await fetch('/api/v1/admin/logs', {headers: {'X-Admin-Key': adminKey}});
        const logs = await res.json();
        const tbody = document.querySelector('#table-audit-logs tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        logs.forEach(l => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(l.timestamp).toLocaleString()}</td>
                <td><span class="badge" style="background:#1e2638; color:#fff;">${l.action}</span></td>
                <td>${l.license_code || '—'}</td>
                <td>${l.details || '—'}</td>
                <td>${l.ip_address || '127.0.0.1'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {}
}

async function handleSendNotification(e) {
    e.preventDefault();
    const title = document.getElementById('notif-title').value;
    const level = document.getElementById('notif-level').value;
    const message = document.getElementById('notif-message').value;

    await fetch('/api/v1/admin/notifications', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-Admin-Key': adminKey},
        body: JSON.stringify({title, level, message})
    });
    document.getElementById('form-broadcast').reset();
    fetchNotifications();
    alert('Broadcast notification sent!');
}
