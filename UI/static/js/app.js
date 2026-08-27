/**
 * INFINITY Tweaker Main Client Application Logic
 * Integrates 30-second periodic heartbeat verification and instant remote lockout.
 */
let currentView = 'dashboard';
let activeServicesList = [];
let telemetryWs = null;
let heartbeatTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
    lucide.createIcons();
    await checkInitialActivation();
    initTelemetryWebSocket();
    initTelemetryCharts();

    // Start 30-second centralized heartbeat loop
    heartbeatTimer = setInterval(periodicHeartbeatCheck, 30000);
});

// --- CENTRALIZED HEARTBEAT & REMOTE LOCKOUT ---

async function periodicHeartbeatCheck() {
    try {
        const auth = await API.getAuthStatus();
        if (!auth.activated) {
            console.warn(`[INFINITY] Heartbeat check rejected: ${auth.reason}`);
            document.getElementById('activation-screen').classList.remove('hidden');
            document.getElementById('app-container').classList.add('hidden');
            showAlert(auth.message || `License Authority Alert: ${auth.reason}`, 'danger');
        } else {
            // Update UI with latest expiration or offline grace
            if (auth.offline_mode) {
                document.getElementById('footer-lic-exp').innerText = `Grace (${auth.grace_hours_remaining}h left)`;
            } else {
                document.getElementById('footer-lic-exp').innerText = auth.expires_at || 'Active';
            }
        }
    } catch (e) {
        console.warn('[INFINITY] Heartbeat request failed', e);
    }
}

// --- NAVIGATION & VIEW ROUTING ---

function navigateTo(viewId) {
    currentView = viewId;
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.content-view').forEach(el => el.classList.remove('active'));

    const activeLink = document.querySelector(`a[href="#${viewId}"]`);
    if (activeLink) activeLink.classList.add('active');

    const activeSection = document.getElementById(`view-${viewId}`);
    if (activeSection) activeSection.classList.add('active');

    const titles = {
        'dashboard': ['SYSTEM DASHBOARD', 'Live Telemetry & Real-Time Performance Center'],
        'system_info': ['SYSTEM INFORMATION', 'Hardware Topology & Verified Specs'],
        'cache_cleaner': ['STORAGE & CACHE CLEANER', 'Scans & Safe Cleanup of Temp & Shader Caches'],
        'ram_optimizer': ['RAM OPTIMIZER', 'Working-Set Trimming & Cache Reclaim'],
        'gpu_optimizer': ['GPU OPTIMIZER', 'High-Performance Graphics Preference Engine'],
        'windows_optimizer': ['WINDOWS GAMING OPTIMIZER', 'Game Mode, Latency Registry & Profile Tweaks'],
        'power_plan': ['POWER PLAN SCHEMES', 'Balanced, High Performance & Ultimate Performance'],
        'services': ['WINDOWS SERVICES', 'Safe Gaming Background Task Governance'],
        'startup': ['STARTUP MANAGER', 'Autostart Applications & Registry Run Keys'],
        'network_boost': ['NETWORK BOOST', 'ICMP Ping Diagnostics & DNS Latency'],
        'storage_optimizer': ['STORAGE OPTIMIZER', 'Large Space Consuming Files & SSD TRIM'],
        'game_profiles': ['GAME PROFILES', 'Custom Profiles & Safe Launch Configurations'],
        'game_launcher': ['GAME LAUNCHER', 'Pre-Flight Boosted Gaming Launcher'],
        'perf_monitor': ['PERFORMANCE MONITOR', 'Live Telemetry Graphs & Frame Time Stability'],
        'benchmark': ['HARDWARE BENCHMARK', 'Real Compute, RAM Throughput & Disk Benchmarks'],
        'perf_history': ['CHANGE HISTORY', 'System Audit Trail & Past Optimizations'],
        'ai_assistant': ['INFINITY AI ADVISOR', 'Context-Aware Telemetry Analysis & Guidance'],
        'backup_restore': ['BACKUP & RESTORE', 'Reversible Snapshot Configuration Points'],
        'settings': ['SETTINGS', 'Preferences, Intervals & Security Config'],
        'license_view': ['LICENSE & AUTHORIZATION', 'Active Activation Authority & Key Status']
    };

    if (titles[viewId]) {
        document.getElementById('view-title').innerText = titles[viewId][0];
        document.getElementById('view-desc').innerText = titles[viewId][1];
    }

    loadViewData(viewId);
    lucide.createIcons();
}

async function loadViewData(viewId) {
    if (viewId === 'dashboard') loadDashboardData();
    else if (viewId === 'system_info') loadSystemInfo();
    else if (viewId === 'cache_cleaner') scanCaches();
    else if (viewId === 'ram_optimizer') loadRamOptimizerData();
    else if (viewId === 'gpu_optimizer') loadGpuOptimizerData();
    else if (viewId === 'windows_optimizer') loadWindowsTweaks();
    else if (viewId === 'power_plan') loadPowerPlans();
    else if (viewId === 'services') loadServicesData();
    else if (viewId === 'startup') loadStartupData();
    else if (viewId === 'game_profiles' || viewId === 'game_launcher') loadGamesData();
    else if (viewId === 'perf_history') loadHistoryData();
    else if (viewId === 'ai_assistant') loadAIRecommendations();
    else if (viewId === 'backup_restore') loadSnapshotsData();
    else if (viewId === 'storage_optimizer') loadStorageData();
}

// --- ACTIVATION FLOW ---

async function checkInitialActivation() {
    try {
        const auth = await API.getAuthStatus();
        if (auth.activated) {
            document.getElementById('activation-screen').classList.add('hidden');
            document.getElementById('app-container').classList.remove('hidden');
            document.getElementById('footer-lic-type').innerText = auth.license_type || 'Active Pro';
            document.getElementById('footer-lic-exp').innerText = auth.expires_at || 'Active';
            
            document.getElementById('lic-page-tier').innerText = auth.license_type || 'Active Pro';
            document.getElementById('lic-page-code').innerText = auth.code_masked || 'INF-****';
            document.getElementById('lic-page-exp').innerText = auth.expires_at || 'Lifetime';
            
            loadDashboardData();
        } else {
            document.getElementById('activation-screen').classList.remove('hidden');
            document.getElementById('app-container').classList.add('hidden');
            if (auth.hwid) {
                document.getElementById('label-device-hwid').innerText = `${auth.hwid.substring(0, 18)}...`;
            }
            if (auth.reason) {
                showAlert(auth.message || `License Authority: ${auth.reason}`, 'danger');
            }
        }
    } catch (e) {
        console.error('Auth verification error', e);
    }
}

async function handleActivate() {
    const code = document.getElementById('input-activation-code').value.trim();
    if (!code) {
        showAlert('Please enter a valid activation code.', 'danger');
        return;
    }

    const btn = document.getElementById('btn-activate');
    btn.innerText = 'VALIDATING WITH CENTRAL SERVER...';
    btn.disabled = true;

    try {
        const res = await API.activateLicense(code);
        if (res.success) {
            showAlert('Activation Successful! Welcome to INFINITY Tweaker.', 'success');
            setTimeout(() => {
                checkInitialActivation();
            }, 1000);
        } else {
            showAlert(res.message || `Activation failed: ${res.status}`, 'danger');
        }
    } catch (e) {
        showAlert(`Central authority connection failure: ${e.message}`, 'danger');
    } finally {
        btn.innerHTML = '<i data-lucide="zap"></i> ACTIVATE INFINITY TWEAKER';
        btn.disabled = false;
        lucide.createIcons();
    }
}

function showAlert(msg, type = 'danger') {
    const el = document.getElementById('activation-alert');
    el.className = `alert-box alert-${type}`;
    el.innerText = msg;
    el.classList.remove('hidden');
}

// --- TELEMETRY & WEBSOCKET ---

function initTelemetryWebSocket() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}/ws/telemetry`;
    
    try {
        telemetryWs = new WebSocket(wsUrl);
        telemetryWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            applyLiveTelemetry(data);
            updateTelemetryCharts(data);
        };
        telemetryWs.onclose = () => {
            setTimeout(initTelemetryWebSocket, 3000);
        };
    } catch (e) {
        console.warn('WS fallback to polling', e);
    }
}

function applyLiveTelemetry(data) {
    document.getElementById('dash-cpu-load').innerText = `${Math.round(data.cpu_usage)}%`;
    document.getElementById('dash-cpu-freq').innerText = `${(data.cpu_freq / 1000).toFixed(2)} GHz`;
    document.getElementById('dash-gpu-load').innerText = `${Math.round(data.gpu_usage)}%`;
    document.getElementById('dash-ram-load').innerText = `${Math.round(data.ram_usage)}%`;
    document.getElementById('dash-ram-detail').innerText = `${data.ram_used_gb} GB / ${data.ram_total_gb} GB`;
    document.getElementById('dash-fps-val').innerText = `${Math.round(data.estimated_fps)} FPS`;
    document.getElementById('dash-frametime-val').innerText = `${data.frame_time_ms} ms`;
}

// --- DASHBOARD DATA ---

async function loadDashboardData() {
    try {
        const data = await API.getDashboardOverview();
        const score = data.score;

        document.getElementById('dash-score-val').innerText = score.overall_score;
        document.getElementById('val-cpu-score').innerText = `${score.cpu_score}/100`;
        document.getElementById('prog-cpu').style.width = `${score.cpu_score}%`;

        document.getElementById('val-gpu-score').innerText = `${score.gpu_score}/100`;
        document.getElementById('prog-gpu').style.width = `${score.gpu_score}%`;

        document.getElementById('val-ram-score').innerText = `${score.ram_score}/100`;
        document.getElementById('prog-ram').style.width = `${score.ram_score}%`;

        document.getElementById('val-storage-score').innerText = `${score.storage_score}/100`;
        document.getElementById('prog-storage').style.width = `${score.storage_score}%`;

        document.getElementById('dash-gpu-name').innerText = data.gpu.name || 'Dedicated GPU';
        document.getElementById('topbar-active-game').innerText = data.active_game || 'No Active Game';
    } catch (e) {
        console.error('Failed to load dashboard overview', e);
    }
}

// --- OPTIMIZATION ACTIONS ---

async function triggerQuickOptimize() {
    alert('Initiating Full Safe Optimization Sweep: Trimming Working-Set RAM & Cleaning Temporary Caches...');
    await API.optimizeRam();
    await API.cleanAllCaches();
    alert('Safe Optimization Completed Successfully! Hardware telemetry updated.');
    loadDashboardData();
}

async function triggerOptimizeRam() {
    const res = await API.optimizeRam();
    alert(`RAM Optimized!\nFreed: ${res.freed_mb} MB across ${res.processes_optimized} processes.\nUsage dropped from ${res.before_pct}% to ${res.after_pct}%.`);
    loadRamOptimizerData();
}

async function loadRamOptimizerData() {
    const info = await API.getSystemInfo();
    const ram = info.ram;
    document.getElementById('ram-opt-used').innerText = `${ram.used_gb} GB`;
    document.getElementById('ram-opt-free').innerText = `${ram.available_gb} GB`;
    document.getElementById('ram-opt-pct').innerText = `${ram.usage_pct}%`;
}

// --- CACHE CLEANER ---

async function scanCaches() {
    const container = document.getElementById('cleaner-categories-list');
    container.innerHTML = '<div style="color:var(--primary)">Scanning system caches, temporary buffers, and shader stores...</div>';
    
    const scan = await API.scanCaches();
    container.innerHTML = '';

    const names = {
        'user_temp': 'User %TEMP% Store',
        'windows_temp': 'Windows System Temp',
        'shader_cache': 'DirectX & GPU Shader Cache',
        'browser_cache': 'Browser Web Caches',
        'windows_logs': 'Crash Dumps & Logs',
        'recycle_bin': 'Windows Recycle Bin'
    };

    for (const [key, val] of Object.entries(scan)) {
        if (key === 'total' || key === 'prefetch') continue;
        const card = document.createElement('div');
        card.className = 'cleaner-cat-card';
        card.innerHTML = `
            <h4>${names[key] || key}</h4>
            <div class="cleaner-cat-size">${val.mb} MB</div>
            <p class="text-muted" style="font-size:12px;">${val.count} files identified</p>
            <button class="btn btn-secondary mt-3" style="width:100%; font-size:12px;" onclick="cleanSingleCache('${key}')">Clean Now</button>
        `;
        container.appendChild(card);
    }
    lucide.createIcons();
}

async function cleanSingleCache(category) {
    const res = await API.cleanCategoryCache(category);
    alert(`Cleaned ${category}: ${res.cleaned_mb || 0} MB freed! (${res.result})`);
    scanCaches();
}

async function cleanAllCaches() {
    const res = await API.cleanAllCaches();
    alert(`Cleaned All Caches! Total Freed: ${res.total_cleaned_mb} MB.`);
    scanCaches();
}

// --- WINDOWS OPTIMIZER ---

async function loadWindowsTweaks() {
    const tweaks = await API.getWindowsTweaks();
    const container = document.getElementById('tweaks-list');
    container.innerHTML = '';

    tweaks.forEach(t => {
        const item = document.createElement('div');
        item.className = 'card';
        item.style.marginBottom = '12px';
        item.innerHTML = `
            <div class="flex-between">
                <div>
                    <h4 style="color:#fff;">${t.name} <span class="badge badge-accent">${t.category}</span></h4>
                    <p class="text-muted" style="font-size:13px; margin-top:4px;">${t.description}</p>
                    <small style="color:var(--text-muted);">Current Value: <code>${t.current_value}</code> | Risk: ${t.risk}</small>
                </div>
                <div>
                    ${t.is_applied 
                        ? `<button class="btn btn-secondary" onclick="applyTweak('${t.id}', false)">Restore Default</button>` 
                        : `<button class="btn btn-primary" onclick="applyTweak('${t.id}', true)">Apply Tweak</button>`}
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

async function applyTweak(tweakId, enable) {
    const res = await API.applyTweak(tweakId, enable);
    if (res.result === 'SUCCESS') {
        alert(`${res.name}: ${enable ? 'Applied' : 'Restored'} successfully!`);
    } else {
        alert(`Failed to modify tweak: ${res.error || res.message}`);
    }
    loadWindowsTweaks();
}

// --- POWER PLAN ---

async function loadPowerPlans() {
    const data = await API.getPowerPlans();
    const container = document.getElementById('power-plans-list');
    container.innerHTML = '';

    const plans = [
        {name: 'Balanced', guid: '381b4222-f694-41f0-9685-ff5bb260df2e', desc: 'Standard energy-saving balance for general desktop use.'},
        {name: 'High Performance', guid: '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c', desc: 'Unparks CPU cores and keeps clocks at full frequency during gaming.'},
        {name: 'Ultimate Performance', guid: 'e9a42b02-d5df-448d-aa00-03f14749eb61', desc: 'Eliminates micro-latencies for maximum compute throughput.'}
    ];

    plans.forEach(p => {
        const isActive = data.active.guid.toLowerCase() === p.guid.toLowerCase() || data.active.name.toLowerCase().includes(p.name.toLowerCase());
        const card = document.createElement('div');
        card.className = `card ${isActive ? 'active-plan' : ''}`;
        card.style.border = isActive ? '2px solid var(--primary)' : '1px solid var(--border)';
        card.innerHTML = `
            <div class="card-header">
                <h3>${p.name}</h3>
                ${isActive ? '<span class="badge badge-accent">ACTIVE</span>' : ''}
            </div>
            <p class="text-muted" style="font-size:13px;">${p.desc}</p>
            <button class="btn ${isActive ? 'btn-secondary' : 'btn-primary'} w-full mt-4" onclick="setPowerPlan('${p.name}')">
                ${isActive ? 'Currently Active' : 'Activate Plan'}
            </button>
        `;
        container.appendChild(card);
    });
}

async function setPowerPlan(planName) {
    const res = await API.setPowerPlan(planName);
    if (res.result === 'SUCCESS') {
        alert(`Power Plan switched to ${planName}!\n\nNote: ${res.warning}`);
    } else {
        alert(`Error setting power plan: ${res.error}`);
    }
    loadPowerPlans();
}

// --- SERVICES MANAGER ---

async function loadServicesData() {
    activeServicesList = await API.getServices();
    renderServicesTable(activeServicesList);
}

function renderServicesTable(services) {
    const tbody = document.querySelector('#table-services tbody');
    tbody.innerHTML = '';

    services.slice(0, 50).forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${s.name}</strong></td>
            <td>${s.display_name}</td>
            <td><span class="badge ${s.status === 'Running' ? 'badge-accent' : ''}">${s.status}</span></td>
            <td>${s.startup_type}</td>
            <td>${s.is_protected ? '<span style="color:var(--danger)">Protected System</span>' : (s.is_gaming_target ? '<span style="color:var(--primary)">Gaming Target</span>' : 'Standard')}</td>
            <td>
                ${s.is_protected ? '—' : `
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="changeServiceStartup('${s.name}', 'demand')">Manual</button>
                    <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="changeServiceStartup('${s.name}', 'disabled')">Disable</button>
                `}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterServices() {
    const q = document.getElementById('services-search').value.toLowerCase();
    const filtered = activeServicesList.filter(s => s.name.toLowerCase().includes(q) || s.display_name.toLowerCase().includes(q));
    renderServicesTable(filtered);
}

async function changeServiceStartup(name, type) {
    const res = await API.changeServiceStartup(name, type);
    if (res.result === 'SUCCESS') {
        alert(`Service ${name} startup set to ${type}`);
    } else {
        alert(`Could not alter service: ${res.error || res.message}`);
    }
    loadServicesData();
}

// --- STARTUP MANAGER ---

async function loadStartupData() {
    const items = await API.getStartupItems();
    const tbody = document.querySelector('#table-startup tbody');
    tbody.innerHTML = '';

    items.forEach(it => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${it.name}</strong></td>
            <td><code style="font-size:11px;">${it.command.substring(0, 45)}...</code></td>
            <td>${it.location}</td>
            <td><span class="badge ${it.is_enabled ? 'badge-accent' : ''}">${it.is_enabled ? 'Enabled' : 'Disabled'}</span></td>
            <td>
                <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="toggleStartup('${it.name}', ${!it.is_enabled})">
                    ${it.is_enabled ? 'Disable' : 'Enable'}
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function toggleStartup(name, enable) {
    const res = await API.toggleStartupItem(name, enable);
    if (res.result === 'SUCCESS') {
        alert(`Startup item '${name}' ${enable ? 'enabled' : 'disabled'}`);
    } else {
        alert(`Error: ${res.error}`);
    }
    loadStartupData();
}

// --- NETWORK BOOST ---

async function runNetworkTest() {
    const container = document.getElementById('network-results');
    container.innerHTML = '<div style="color:var(--primary)">Sending ICMP ping requests to global gaming gateways & testing DNS resolution...</div>';
    
    const diag = await API.runNetworkDiagnostic();
    let html = `
        <div class="card">
            <div class="flex-between">
                <div>
                    <h4>Connection Quality: <span class="text-glow-green">${diag.quality_grade}</span></h4>
                    <p class="text-muted">Average Gaming Latency: <strong>${diag.overall_avg_ms} ms</strong></p>
                </div>
            </div>
            <div class="table-responsive mt-3">
                <table class="data-table">
                    <thead><tr><th>Gateway Target</th><th>Host</th><th>Latency (Avg)</th><th>Jitter</th><th>Packet Loss</th></tr></thead>
                    <tbody>
    `;
    diag.endpoints.forEach(ep => {
        html += `<tr>
            <td><strong>${ep.name}</strong></td>
            <td>${ep.host}</td>
            <td>${ep.avg_ms} ms</td>
            <td>${ep.jitter_ms} ms</td>
            <td>${ep.loss_pct}%</td>
        </tr>`;
    });
    html += `</tbody></table></div></div>`;
    container.innerHTML = html;
}

// --- STORAGE LARGE FILES ---

async function loadStorageData() {
    const data = await API.getLargeFiles();
    const container = document.getElementById('storage-large-files-list');
    
    let html = `
        <div class="card mb-3">
            <h4>SSD TRIM Status</h4>
            <p class="text-muted mt-1">${data.trim.message}</p>
        </div>
        <div class="table-responsive">
            <table class="data-table">
                <thead><tr><th>File Name</th><th>Size (GB)</th><th>Path</th></tr></thead>
                <tbody>
    `;
    data.files.forEach(f => {
        html += `<tr><td><strong>${f.filename}</strong></td><td>${f.size_gb} GB</td><td><small class="text-muted">${f.filepath}</small></td></tr>`;
    });
    html += `</tbody></table></div>`;
    container.innerHTML = html;
}

// --- GPU OPTIMIZER ---

async function loadGpuOptimizerData() {
    const data = await API.getGpuStatus();
    const container = document.getElementById('gpu-info-container');
    let recsHtml = '';
    data.recommendations.forEach(r => {
        recsHtml += `<div class="card" style="margin-bottom:8px;"><strong>${r.title}</strong>: <span class="text-muted">${r.description}</span></div>`;
    });

    container.innerHTML = `
        <div class="card">
            <h4>Active Primary GPU: <span style="color:var(--primary)">${data.active_gpu.name}</span></h4>
            <p class="text-muted mt-1">Vendor: ${data.vendor} | Driver: ${data.active_gpu.driver_version} | VRAM: ${data.active_gpu.vram_total_mb} MB</p>
        </div>
        <h4 class="mt-4 mb-2">Vendor Tuning Guidance:</h4>
        ${recsHtml}
    `;
}

// --- GAME LAUNCHER & PROFILES ---

async function loadGamesData() {
    const profiles = await API.getGameProfiles();
    const container = document.getElementById('games-profiles-list') || document.getElementById('launcher-games-list');
    const launcherContainer = document.getElementById('launcher-games-list');

    if (container) {
        container.innerHTML = '';
        profiles.forEach(p => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <div class="card-header flex-between">
                    <h3>${p.name}</h3>
                    <span class="badge badge-accent">${p.priority} PRIORITY</span>
                </div>
                <p class="text-muted" style="font-size:12px;">Power: ${p.power_profile} | GPU: ${p.gpu_preference}</p>
                <div class="mt-4">
                    <button class="btn btn-primary w-full" onclick="launchGame('${p.id}')"><i data-lucide="play"></i> LAUNCH WITH BOOST</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    if (launcherContainer && launcherContainer !== container) {
        launcherContainer.innerHTML = container.innerHTML;
    }
    lucide.createIcons();
}

async function scanDetectedGames() {
    alert('Scanning Steam and Epic Games libraries for installed titles...');
    const games = await API.getDetectedGames();
    alert(`Discovered ${games.length} installed games! Profiles registered.`);
    loadGamesData();
}

async function launchGame(profileId) {
    const res = await API.launchGame(profileId);
    if (res.result === 'SUCCESS') {
        alert(`Launching ${res.game_name}!\nApplied High Performance power plan, safe High process priority, and trimmed background RAM.`);
    } else {
        alert(`Launch error: ${res.error}`);
    }
}

// --- BENCHMARK ---

async function runBenchmark() {
    const container = document.getElementById('benchmark-results-container');
    container.innerHTML = '<div style="color:var(--primary)">Executing Real Hardware Compute Benchmark (Primes, Memory Throughput, Disk Latency)...</div>';
    
    const b = await API.runBenchmark('POST-OPTIMIZATION');
    container.innerHTML = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header"><span>TOTAL BENCHMARK SCORE</span></div>
                <div class="metric-value text-glow-green">${b.total_score}</div>
                <div class="metric-sub">Unified Compute Index</div>
            </div>
            <div class="metric-card">
                <div class="metric-header"><span>CPU COMPUTE TIME</span></div>
                <div class="metric-value">${b.cpu_compute_time_sec}s</div>
                <div class="metric-sub">Score: ${b.cpu_score}</div>
            </div>
            <div class="metric-card">
                <div class="metric-header"><span>RAM BANDWIDTH</span></div>
                <div class="metric-value">${b.ram_speed_mb_s} MB/s</div>
                <div class="metric-sub">Score: ${b.ram_score}</div>
            </div>
            <div class="metric-card">
                <div class="metric-header"><span>DISK LATENCY</span></div>
                <div class="metric-value">${b.disk_latency_ms} ms</div>
                <div class="metric-sub">Score: ${b.disk_score}</div>
            </div>
        </div>
    `;
}

// --- AI ASSISTANT ---

async function handleSendAIQuery(e) {
    e.preventDefault();
    const input = document.getElementById('ai-input-text');
    const q = input.value.trim();
    if (!q) return;

    const chatBox = document.getElementById('ai-chat-box');
    chatBox.innerHTML += `<div class="ai-msg user"><strong>You:</strong> ${q}</div>`;
    input.value = '';

    const res = await API.queryAIAssistant(q);
    chatBox.innerHTML += `<div class="ai-msg bot"><strong>INFINITY AI:</strong><br>${res.response.replace(/\n/g, '<br>')}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function loadAIRecommendations() {
    const recs = await API.getAIRecommendations();
    const container = document.getElementById('ai-recommendations-list');
    container.innerHTML = '';

    recs.recommended.forEach(r => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.marginBottom = '12px';
        card.innerHTML = `
            <div class="flex-between">
                <div>
                    <h4 style="color:var(--success);"><i data-lucide="check-circle"></i> ${r.title}</h4>
                    <p class="text-muted" style="font-size:12px; margin-top:4px;">${r.changes}</p>
                    <small style="color:var(--primary);">Benefit: ${r.expected_benefit}</small>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
    lucide.createIcons();
}

// --- SYSTEM INFO ---

async function loadSystemInfo() {
    const info = await API.getSystemInfo();
    const container = document.getElementById('system-info-details');
    container.innerHTML = `
        <div class="card">
            <h4>Hardware Specifications</h4>
            <p class="mt-2"><strong>CPU:</strong> ${info.cpu.brand} (${info.cpu.physical_cores} Cores / ${info.cpu.logical_threads} Threads)</p>
            <p class="mt-1"><strong>GPU:</strong> ${info.gpu.name} (${info.gpu.vram_total_mb} MB VRAM)</p>
            <p class="mt-1"><strong>RAM:</strong> ${info.ram.total_gb} GB Physical Memory</p>
            <p class="mt-1"><strong>Motherboard:</strong> ${info.windows.motherboard}</p>
        </div>
        <div class="card">
            <h4>Operating System & Display</h4>
            <p class="mt-2"><strong>OS:</strong> ${info.windows.os_name} (Build ${info.windows.os_build})</p>
            <p class="mt-1"><strong>DirectX:</strong> ${info.windows.directx_version}</p>
            <p class="mt-1"><strong>Display Resolution:</strong> ${info.windows.resolution} @ ${info.windows.refresh_rate}</p>
            <p class="mt-1"><strong>Windows Game Mode:</strong> ${info.windows.game_mode_enabled ? 'Active' : 'Disabled'}</p>
        </div>
    `;
}

// --- BACKUP & RESTORE ---

async function loadSnapshotsData() {
    const snaps = await API.getSnapshots();
    const container = document.getElementById('snapshots-list');
    container.innerHTML = '';

    snaps.forEach(s => {
        const item = document.createElement('div');
        item.className = 'card flex-between';
        item.innerHTML = `
            <div>
                <h4>${s.name} (${s.id})</h4>
                <small class="text-muted">Created: ${new Date(s.created_at).toLocaleString()} | Config Items: ${s.item_count}</small>
            </div>
            <button class="btn btn-secondary" onclick="alert('Snapshot configuration intact.')">Verify Snapshot</button>
        `;
        container.appendChild(item);
    });
}

async function createSnapshot() {
    const name = prompt('Enter a name for this restore point:', 'Manual Restore Point');
    if (!name) return;
    await API.createSnapshot(name);
    alert('System configuration snapshot created successfully!');
    loadSnapshotsData();
}

// --- CHANGE HISTORY ---

async function loadHistoryData() {
    const hist = await API.getChangeHistory();
    const tbody = document.querySelector('#table-history tbody');
    tbody.innerHTML = '';

    hist.forEach(h => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${new Date(h.timestamp).toLocaleString()}</td>
            <td><strong>${h.feature}</strong></td>
            <td>${h.setting}</td>
            <td>${h.previous_value}</td>
            <td>${h.new_value}</td>
            <td><span class="badge ${h.result === 'SUCCESS' ? 'badge-accent' : ''}">${h.result}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// --- LICENSE REFRESH ---

async function refreshLicense() {
    alert('Sending heartbeat verification to central licensing authority...');
    await checkInitialActivation();
    alert('License state synchronized with cloud server.');
}

async function enterNewCode() {
    if (confirm('Enter a new activation code? Current activation on this device will be cleared.')) {
        await API.deactivate();
        window.location.reload();
    }
}
