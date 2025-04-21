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
      borderColor: 'rgb(0, 0, 0)',
      borderWidth: 2,
      tension: 0.3,
      fill: false
    }]
  },
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    elements: {
      point: {
        radius: 0 
      }
    },
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
const labels = Array.from({ length: MAX_POINTS }, (_, i) => (i * 15 / (MAX_POINTS - 1)).toFixed(2));

// Initialize chart with empty data
const gsrChart = new Chart(ctx_gsr, {
  type: 'line',
  data: {
    labels: labels,
    datasets: [{
      label: 'GSR',
      data: [],
      borderColor: 'rgb(0, 0, 0)',
      borderWidth: 2,
      tension: 0.3,
      fill: false
    }]
  },
  options: {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    elements: {
      point: {
        radius: 0 
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time (s)'
        },
        ticks: {
          stepSize: 25, 
          maxTicksLimit: 16
        }
      },
      y: {
        title: {
          display: true,
          text: 'Amplitude'
        },
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
    gsrChart.data.datasets[0].data =
      gsrChart.data.datasets[0].data.slice(-MAX_POINTS);
  }

  // Update chart
  gsrChart.update();
});


// Initialize queues for stress and fatigue with 200 zeros
const MAX_QUEUE_SIZE = 200;
let stressQueue = Array(MAX_QUEUE_SIZE).fill(0);
let fatigueQueue = Array(MAX_QUEUE_SIZE).fill(0);

// Add these lines to your existing JavaScript file
// The socket variable is already defined in your code

// Listen for 'predictions' events from the server
socket.on('predictions', function(data) {
    // Add new predictions to the queues and remove oldest ones
    stressQueue.push(data.stress);
    stressQueue.shift();
    
    fatigueQueue.push(data.fatigue);
    fatigueQueue.shift();
    
    // Update the progress bars
    updateBars();
});

// Function to update both progress bars
function updateBars() {
    // Get references to the progress bars
    const stressBar = document.getElementById('stress-bar');
    const fatigueBar = document.getElementById('fatigue-bar');
    const stressPercentage = document.getElementById('stress-percentage');
    const fatiguePercentage = document.getElementById('fatigue-percentage');
    
    // Calculate the sum of values in each queue
    const stressSum = stressQueue.reduce((acc, val) => acc + val, 0);
    const fatigueSum = fatigueQueue.reduce((acc, val) => acc + val, 0);
    
    // Calculate percentages
    const stressPercentValue = (stressSum / MAX_QUEUE_SIZE) * 100;
    const fatiguePercentValue = (fatigueSum / MAX_QUEUE_SIZE) * 100;
    
    // Update the progress bars
    if (stressBar) {
        stressBar.style.width = `${stressPercentValue}%`;
        updateBarColor(stressBar, stressPercentValue);
    }
    
    if (fatigueBar) {
        fatigueBar.style.width = `${fatiguePercentValue}%`;
        updateBarColor(fatigueBar, fatiguePercentValue);
    }
    
    // Update percentage text if elements exist
    if (stressPercentage) {
        stressPercentage.textContent = `${Math.round(stressPercentValue)}%`;
    }
    
    if (fatiguePercentage) {
        fatiguePercentage.textContent = `${Math.round(fatiguePercentValue)}%`;
    }
}

// Function to change bar color based on percentage
function updateBarColor(bar, percentage) {
    if (percentage < 25) {
        bar.style.backgroundColor = '#4CAF50'; // Green
    } else if (percentage < 50) {
        bar.style.backgroundColor = '#FFC107'; // Amber
    } else if (percentage < 75) {
        bar.style.backgroundColor = '#FF9800'; // Orange
    } else {
        bar.style.backgroundColor = '#F44336'; // Red
    }
}