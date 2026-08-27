let allLicenses = [];

document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    setInterval(loadAllData, 10000); // Auto-sync every 10s
});

function showTab(tabName) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));

    const tabBtn = document.querySelector(`a[href="#${tabName}"]`);
    if (tabBtn) tabBtn.classList.add('active');

    const panel = document.getElementById(`tab-${tabName}`);
    if (panel) panel.classList.add('active');

    const titles = {
        'dashboard': 'Centralized Multi-User System Telemetry',
        'licenses': 'License Key Vault & Authority',
        'devices': 'Authorized Hardware Nodes (HWID)',
        'events': 'Real-Time Multi-User Heartbeats & Events',
        'broadcasts': 'Broadcast Notifications',
        'updates': 'Release Distribution Pipeline',
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
        const res = await fetch('/api/v1/admin/stats');
        const data = await res.json();
        document.getElementById('stat-total-licenses').innerText = data.total_licenses;
        document.getElementById('stat-active-licenses').innerText = `${data.active_licenses} Active`;
        document.getElementById('stat-online-clients').innerText = data.online_clients;
        document.getElementById('stat-total-devices').innerText = data.total_devices;
        document.getElementById('stat-active-devices').innerText = `${data.active_devices} Bound`;
        document.getElementById('stat-revoked-expired').innerText = data.revoked_licenses + data.expired_licenses;
        document.getElementById('stat-suspended').innerText = `${data.suspended_licenses} Suspended`;
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

async function fetchLicenses() {
    try {
        const res = await fetch('/api/v1/admin/licenses');
        allLicenses = await res.json();
        renderLicensesTable(allLicenses);
        renderRecentLicenses(allLicenses.slice(0, 5));
    } catch (e) {
        console.error('Failed to load licenses', e);
    }
}

function renderLicensesTable(licenses) {
    const tbody = document.querySelector('#table-all-licenses tbody');
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
            <td><strong>${lic.device_count}</strong> / ${lic.max_devices} <button class="btn-secondary" style="padding:2px 6px; font-size:10px;" onclick="changeDeviceLimit(${lic.id}, ${lic.max_devices})">Edit</button></td>
            <td>${expires}</td>
            <td>${created}</td>
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

function renderRecentLicenses(licenses) {
    const tbody = document.querySelector('#table-recent-licenses tbody');
    tbody.innerHTML = '';

    licenses.forEach(lic => {
        const tr = document.createElement('tr');
        const statusBadge = `<span class="badge badge-${lic.status.toLowerCase()}">${lic.status}</span>`;
        const expires = lic.expires_at ? new Date(lic.expires_at).toLocaleDateString() : 'Lifetime';

        tr.innerHTML = `
            <td><strong style="color:var(--primary); font-family:var(--font-heading);">${lic.code}</strong></td>
            <td>${lic.license_type}</td>
            <td>${statusBadge}</td>
            <td>${expires}</td>
            <td>${lic.device_count} / ${lic.max_devices}</td>
            <td>
                ${lic.status === 'ACTIVE' 
                    ? `<button class="btn-danger-sm" onclick="revokeLicense(${lic.id})">Revoke</button>` 
                    : `<button class="btn-success-sm" onclick="reactivateLicense(${lic.id})">Reactivate</button>`}
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
    renderLicensesTable(filtered);
}

async function fetchDevices() {
    try {
        const res = await fetch('/api/v1/admin/devices');
        const devices = await res.json();
        const tbody = document.querySelector('#table-devices tbody');
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
    } catch (e) {
        console.error('Failed to load devices', e);
    }
}

async function fetchEvents() {
    try {
        const res = await fetch('/api/v1/admin/events');
        const events = await res.json();
        const tbody = document.querySelector('#table-events tbody');
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
    } catch (e) {
        console.error('Failed to load events', e);
    }
}

async function fetchNotifications() {
    try {
        const res = await fetch('/api/v1/notifications');
        const list = await res.json();
        const container = document.getElementById('broadcasts-list');
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
    } catch (e) {
        console.error('Failed to load notifications', e);
    }
}

async function fetchAuditLogs() {
    try {
        const res = await fetch('/api/v1/admin/logs');
        const logs = await res.json();
        const tbody = document.querySelector('#table-audit-logs tbody');
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
    } catch (e) {
        console.error('Failed to load logs', e);
    }
}

// Modal handlers
function openCreateModal() {
    document.getElementById('modal-create-license').classList.add('active');
}

function closeCreateModal() {
    document.getElementById('modal-create-license').classList.remove('active');
}

async function handleCreateLicense(e) {
    e.preventDefault();
    const type = document.getElementById('modal-lic-type').value;
    const devices = parseInt(document.getElementById('modal-lic-devices').value, 10);
    const code = document.getElementById('modal-lic-code').value.trim() || null;
    const notes = document.getElementById('modal-lic-notes').value.trim() || null;

    try {
        const res = await fetch('/api/v1/admin/licenses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                license_type: type,
                max_devices: devices,
                custom_code: code,
                notes: notes
            })
        });
        const result = await res.json();
        closeCreateModal();
        alert(`Activation Key Created: ${result.code}`);
        loadAllData();
    } catch (err) {
        alert('Error generating license');
    }
}

async function revokeLicense(id) {
    if (!confirm('Are you sure you want to REVOKE this license? All connected clients will be locked out immediately.')) return;
    await fetch(`/api/v1/admin/licenses/${id}/revoke`, {method: 'POST'});
    loadAllData();
}

async function suspendLicense(id) {
    if (!confirm('Suspend this license? Connected rigs will have premium features suspended on next heartbeat.')) return;
    await fetch(`/api/v1/admin/licenses/${id}/suspend`, {method: 'POST'});
    loadAllData();
}

async function reactivateLicense(id) {
    await fetch(`/api/v1/admin/licenses/${id}/reactivate`, {method: 'POST'});
    loadAllData();
}

async function extendLicense(id) {
    await fetch(`/api/v1/admin/licenses/${id}/extend?days=30`, {method: 'POST'});
    loadAllData();
}

async function changeDeviceLimit(id, currentLimit) {
    const newLim = prompt(`Enter new maximum device limit for license #${id}:`, currentLimit);
    if (!newLim || isNaN(newLim)) return;
    await fetch(`/api/v1/admin/licenses/${id}/set-limit`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({new_limit: parseInt(newLim, 10)})
    });
    loadAllData();
}

async function deactivateDevice(id) {
    if (!confirm('Deauthorize this hardware ID from the license?')) return;
    await fetch(`/api/v1/admin/devices/${id}/deactivate`, {method: 'POST'});
    loadAllData();
}

async function handleSendNotification(e) {
    e.preventDefault();
    const title = document.getElementById('notif-title').value;
    const level = document.getElementById('notif-level').value;
    const message = document.getElementById('notif-message').value;

    await fetch('/api/v1/admin/notifications', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, level, message})
    });
    document.getElementById('form-broadcast').reset();
    fetchNotifications();
    alert('Broadcast notification sent!');
}

async function handlePublishRelease(e) {
    e.preventDefault();
    const version = document.getElementById('update-version').value;
    const min_supported_version = document.getElementById('update-min-ver').value;
    const download_url = document.getElementById('update-url').value;
    const checksum_sha256 = document.getElementById('update-sha').value;
    const release_notes = document.getElementById('update-notes').value;
    const is_critical = document.getElementById('update-critical').checked;

    await fetch('/api/v1/admin/updates/publish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            version,
            min_supported_version,
            download_url,
            checksum_sha256,
            release_notes,
            is_critical
        })
    });
    alert('Release manifest published successfully!');
    document.getElementById('form-update').reset();
}
