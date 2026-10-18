const API_URL = 'http://localhost:8000';

const domElements = {
    sensorGrid: document.getElementById('sensor-grid'),
    alertsContainer: document.getElementById('alerts-container'),
    activeSensors: document.getElementById('active-sensors'),
    totalLeaks: document.getElementById('total-leaks')
};

let previousAlertsCount = 0;
let totalLeaksCount = 0;

async function fetchSensors() {
    try {
        const response = await fetch(`${API_URL}/sensors`);
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        renderSensors(data.sensors);
    } catch (error) {
        console.error("Failed to fetch sensors:", error);
        if (domElements.sensorGrid.querySelector('.loader-spinner')) {
             domElements.sensorGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--danger);">Unable to connect to backend. Is main.py running?</div>';
        }
    }
}

async function fetchAlerts() {
    try {
        const response = await fetch(`${API_URL}/alerts`);
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        renderAlerts(data.alerts);
    } catch (error) {
        console.error("Failed to fetch alerts:", error);
    }
}

function calculateBarWidth(value, max) {
    const percentage = (value / max) * 100;
    return Math.min(Math.max(percentage, 5), 100); // 5% min to 100% max
}

function renderSensors(sensors) {
    if (sensors.length === 0) {
        domElements.sensorGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; opacity: 0.5;">Awaiting sensor telemetry...</div>';
        return;
    }

    domElements.activeSensors.textContent = sensors.length;
    let html = '';
    
    // Sort sensors so leaks appear first
    sensors.sort((a, b) => {
        if (a.status === 'leak_detected' && b.status !== 'leak_detected') return -1;
        if (b.status === 'leak_detected' && a.status !== 'leak_detected') return 1;
        return a.sensor_id.localeCompare(b.sensor_id);
    });

    sensors.forEach(sensor => {
        const isLeak = sensor.status === 'leak_detected';
        const cardClass = isLeak ? 'sensor-card leak' : 'sensor-card';
        const statusText = isLeak ? 'LEAK DETECTED' : 'NORMAL';
        const statusClass = `status-${sensor.status}`;
        
        // Dynamic bar widths
        const lowFreqWidth = calculateBarWidth(sensor.low_freq, 100);
        const highFreqWidth = calculateBarWidth(sensor.high_freq, 120);

        html += `
            <div class="${cardClass}">
                <div class="sensor-header">
                    <span class="sensor-id">${sensor.sensor_id}</span>
                    <span class="sensor-status ${statusClass}">${statusText}</span>
                </div>
                <div class="audio-metrics">
                    <div class="metric">
                        <span class="m-label">Low Freq (Traffic)</span>
                        <span class="m-value">${sensor.low_freq.toFixed(1)} dB</span>
                        <div class="bar-bg"><div class="bar-fill fill-low" style="width: ${lowFreqWidth}%"></div></div>
                    </div>
                    <div class="metric">
                        <span class="m-label">High Freq (Hiss)</span>
                        <span class="m-value">${sensor.high_freq.toFixed(1)} dB</span>
                        <div class="bar-bg"><div class="bar-fill fill-high" style="width: ${highFreqWidth}%"></div></div>
                    </div>
                </div>
                <div style="font-size: 0.75rem; opacity: 0.5; margin-top: auto; padding-top: 10px; text-align: right;">
                    Last ping: ${new Date(sensor.last_seen).toLocaleTimeString()}
                </div>
            </div>
        `;
    });

    domElements.sensorGrid.innerHTML = html;
}

function renderAlerts(alerts) {
    if (alerts.length === 0) {
        return; 
    }

    // Only re-render if we have new alerts
    if (alerts.length > previousAlertsCount) {
        let html = '';
        const recentAlerts = [...alerts].reverse(); // Show newest at top
        
        recentAlerts.forEach(alert => {
            html += `
                <div class="alert-item">
                    <h4>
                        ${alert.sensor_id}
                        <span class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </h4>
                    <span class="alert-desc">${alert.message}</span>
                </div>
            `;
        });
        
        domElements.alertsContainer.innerHTML = html;
        previousAlertsCount = alerts.length;
        
        // Update stats
        totalLeaksCount = alerts.length;
        domElements.totalLeaks.textContent = totalLeaksCount;
    }
}

// Initial fetch
fetchSensors();
fetchAlerts();

// Polling interval (1 second)
setInterval(() => {
    fetchSensors();
    fetchAlerts();
}, 1000);
