async function scanDevices() {
    const response = await fetch('/scan');
    const devices = await response.json();
    const list = document.getElementById('device-list');
    list.innerHTML = '';

    devices.forEach(device => {
        const card = document.createElement('div');
        card.className = 'device-card';

        const name = document.createElement('div');
        name.className = 'device-name';
        name.textContent = device.name || "Unnamed Device";
        card.appendChild(name);

        const button = document.createElement('button');
        button.className = 'connect-button';
        button.textContent = 'Connect';

        // Initial Connect logic
        button.onclick = async () => {
            try {
                const res = await fetch(`/connect?device_id=${encodeURIComponent(device.address)}`);
                const result = await res.json();
                alert(result.message);

                // On successful connect, turn it into a Disconnect button
                button.textContent = 'Disconnect';
                button.onclick = async () => {
                    try {
                        const res = await fetch(`/disconnect?device_id=${encodeURIComponent(device.address)}`);
                        const result = await res.json();
                        alert(result.message);

                        // Revert back to Connect button
                        button.textContent = 'Connect';
                        button.onclick = originalConnectHandler; // Reset to original handler
                    } catch (err) {
                        console.error("Disconnect failed", err);
                        alert("Failed to disconnect.");
                    }
                };
            } catch (err) {
                console.error("Connect failed", err);
                alert("Failed to connect.");
            }
        };

        // Save original handler to reset after disconnect
        const originalConnectHandler = button.onclick;

        card.appendChild(button);
        list.appendChild(card);
    });
}

const ppgChart = new Chart(document.getElementById('ppgChart'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'PPG Signal',
            data: [],
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    },
    options: {
        animation: false,
        responsive: true,
        scales: {
            x: {
                display: false
            }
        }
    }
});

async function fetchDataAndUpdateChart() {
    try {
        const response = await fetch('/plot_signals');
        const newData = await response.json();

        // Add new data and trim to last 15 seconds (25 * 15 = 375 samples)
        ppgChart.data.labels.push(...newData.map((_, i) => i));
        ppgChart.data.datasets[0].data.push(...newData);
        
        if (ppgChart.data.datasets[0].data.length > 375) {
            ppgChart.data.labels.splice(0, newData.length);
            ppgChart.data.datasets[0].data.splice(0, newData.length);
        }

        ppgChart.update();
    } catch (error) {
        console.error("Error fetching new data:", error);
    }
}

// Poll every second (or faster if needed)
setInterval(fetchDataAndUpdateChart, 1000);