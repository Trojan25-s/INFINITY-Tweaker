/**
 * INFINITY Tweaker Real-Time Charts (Chart.js)
 */
let chartCpuRam = null;
let chartFrametime = null;

const MAX_HISTORY_POINTS = 20;
const telemLabels = Array(MAX_HISTORY_POINTS).fill('');
const cpuHistory = Array(MAX_HISTORY_POINTS).fill(0);
const ramHistory = Array(MAX_HISTORY_POINTS).fill(0);
const fpsHistory = Array(MAX_HISTORY_POINTS).fill(60);
const ftHistory = Array(MAX_HISTORY_POINTS).fill(16.6);

function initTelemetryCharts() {
    const ctx1 = document.getElementById('chart-cpu-ram');
    if (ctx1) {
        chartCpuRam = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: telemLabels,
                datasets: [
                    {
                        label: 'CPU Usage %',
                        data: cpuHistory,
                        borderColor: '#00f0ff',
                        backgroundColor: 'rgba(0, 240, 255, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'RAM Usage %',
                        data: ramHistory,
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.05)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                    x: { display: false }
                },
                plugins: { legend: { labels: { color: '#e2e8f0' } } }
            }
        });
    }

    const ctx2 = document.getElementById('chart-frametime');
    if (ctx2) {
        chartFrametime = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: telemLabels,
                datasets: [
                    {
                        label: 'Frame Time (ms)',
                        data: ftHistory,
                        borderColor: '#ffb800',
                        borderWidth: 2,
                        tension: 0.2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'FPS Output',
                        data: fpsHistory,
                        borderColor: '#9d4edd',
                        borderWidth: 2,
                        tension: 0.2,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { min: 0, max: 50, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y1: { min: 0, max: 240, position: 'right', grid: { display: false } },
                    x: { display: false }
                },
                plugins: { legend: { labels: { color: '#e2e8f0' } } }
            }
        });
    }
}

function updateTelemetryCharts(data) {
    if (!chartCpuRam || !chartFrametime) return;

    cpuHistory.push(data.cpu_usage || 0);
    cpuHistory.shift();

    ramHistory.push(data.ram_usage || 0);
    ramHistory.shift();

    fpsHistory.push(data.estimated_fps || 60);
    fpsHistory.shift();

    ftHistory.push(data.frame_time_ms || 16.6);
    ftHistory.shift();

    chartCpuRam.update('none');
    chartFrametime.update('none');
}
