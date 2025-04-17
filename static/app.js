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

const socket = io("http://localhost:5000");

const ctx = document.getElementById('ppgChart').getContext('2d');

const MAX_POINTS = 375;  // 25 samples * 15 seconds

// Initialize chart with empty data
const ppgChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: Array(MAX_POINTS).fill(''), // blank x-axis labels for now
    datasets: [{
      label: 'PPG',
      data: [],
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 2,
      tension: 0.3,
      fill: false
    }]
  },
  options: {
    animation: false,
    scales: {
      x: {
        display: false
      },
      y: {
        beginAtZero: false
      }
    }
  }
});

// When new PPG data comes in
socket.on('ppg_data', (msg) => {
  const newData = msg.data;  // array of numbers

  // Append new data to existing chart dataset
  ppgChart.data.datasets[0].data.push(...newData);

  // Keep only the last MAX_POINTS
  if (ppgChart.data.datasets[0].data.length > MAX_POINTS) {
    ppgChart.data.datasets[0].data =
      ppgChart.data.datasets[0].data.slice(-MAX_POINTS);
  }

  // Update chart
  ppgChart.update();
});

const ctx_gsr = document.getElementById('gsrChart').getContext('2d');

// Initialize chart with empty data
const gsrChart = new Chart(ctx_gsr, {
  type: 'line',
  data: {
    labels: Array(MAX_POINTS).fill(''), // blank x-axis labels for now
    datasets: [{
      label: 'GSR',
      data: [],
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 2,
      tension: 0.3,
      fill: false
    }]
  },
  options: {
    animation: false,
    scales: {
      x: {
        display: false
      },
      y: {
        beginAtZero: false
      }
    }
  }
});

// When new PPG data comes in
socket.on('gsr_data', (msg) => {
  const newData = msg.data;  // array of numbers

  // Append new data to existing chart dataset
  gsrChart.data.datasets[0].data.push(...newData);

  // Keep only the last MAX_POINTS
  if (gsrChart.data.datasets[0].data.length > MAX_POINTS) {
    gsrChartChart.data.datasets[0].data =
      gsrChart.data.datasets[0].data.slice(-MAX_POINTS);
  }

  // Update chart
  gsrChart.update();
});
