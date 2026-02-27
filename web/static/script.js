let timerChart;
const maxDataPoints = 50;
const emergencyState = { north: false, south: false, east: false, west: false };

function initChart() {
    const ctx = document.getElementById('timerChart').getContext('2d');
    timerChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Timer Value',
                data: [],
                borderColor: '#00f0ff',
                borderWidth: 1,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#333' }
                },
                x: { display: false }
            },
            plugins: {
                legend: { display: false }
            },
            animation: false
        }
    });
}

function updateChart(timerValue) {
    const timestamp = new Date().toLocaleTimeString();
    timerChart.data.labels.push(timestamp);
    timerChart.data.datasets[0].data.push(timerValue);

    if (timerChart.data.labels.length > maxDataPoints) {
        timerChart.data.labels.shift();
        timerChart.data.datasets[0].data.shift();
    }
    timerChart.update();
}

function updateLights(lights) {
    // lights obj e.g., {N: 'RED', ...}
    const update = (id, colorState) => {
        const el = document.getElementById(id);
        if (el) el.className = `light ${id} ${colorState.toLowerCase()}`;
    };

    update('light-n', lights.N);
    update('light-s', lights.S);
    update('light-e', lights.E);
    update('light-w', lights.W);
}

function toggleEmergency(direction) {
    emergencyState[direction] = !emergencyState[direction];

    fetch('/emergency', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: direction, active: emergencyState[direction] })
    });

    updateEmergencyButtons();
}

function updateEmergencyButtons() {
    const directions = ['north', 'south', 'east', 'west'];
    directions.forEach(dir => {
        const btn = document.getElementById(`btn-emg-${dir}`);
        if (btn) {
            if (emergencyState[dir]) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });
}

function updateConfig() {
    const nsVal = document.getElementById('slider-ns').value;
    const ewVal = document.getElementById('slider-ew').value;

    // Update labels
    document.getElementById('val-ns').innerText = nsVal;
    document.getElementById('val-ew').innerText = ewVal;

    fetch('/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ green_ns: nsVal, green_ew: ewVal })
    });
}

function pollStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            updateLights(data.lights);
            updateChart(data.timer);

            // Update Timers
            if (data.waits) {
                const updateTimer = (id, val) => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.innerText = val > 0 ? val + 's' : 'GO';
                        el.style.color = val > 0 ? '#ff3333' : '#33ff33';
                    }
                };
                updateTimer('timer-ns', data.waits.ns);
                updateTimer('timer-ew', data.waits.ew);
            }

            // Sync buttons (optional, here just relying on local state mostly but could sync from data.emerg_status)
        });
}

window.onload = function () {
    // Only init chart if canvas exists
    if (document.getElementById('timerChart')) {
        initChart();
        setInterval(pollStatus, 200); // 5Hz update
    }

    // Check if we are on dashboard (has traffic lights)
    if (document.getElementById('light-n')) {
        // Also poll status if chart exists but maybe redundant check
        // Ideally pollStatus updates both
    }
};
