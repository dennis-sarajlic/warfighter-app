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

const SAMPLE_RATE = 25;  // 25 Hz
const MAX_SECONDS = 15;  // 15 seconds display window
const MAX_POINTS = MAX_SECONDS * SAMPLE_RATE + 1;  // 376 samples (includes point at 0s and 15s)

// Initialize chart with empty data
const ppgChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: Array(MAX_POINTS).fill(''), // Will be populated with time values
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
        title: {
          display: true,
          text: 'Time (s)'
        },
        ticks: {
          autoSkip: false,
          callback: function(value, index) {
            // Only show ticks at each second (every 25 points, plus the first point)
            return index % SAMPLE_RATE === 0 ? (index / SAMPLE_RATE) : '';
          }
        }
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

  // Update x-axis labels based on current data points
  ppgChart.data.labels = Array(ppgChart.data.datasets[0].data.length).fill('');

  // Update chart
  ppgChart.update();
});

const ctx_gsr = document.getElementById('gsrChart').getContext('2d');

// Initialize chart with empty data
const gsrChart = new Chart(ctx_gsr, {
  type: 'line',
  data: {
    labels: Array(MAX_POINTS).fill(''),
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
          autoSkip: false,
          callback: function(value, index) {
            // Only show ticks at each second (every 25 points, plus the first point)
            return index % SAMPLE_RATE === 0 ? (index / SAMPLE_RATE) : '';
          }
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

// When new GSR data comes in
socket.on('gsr_data', (msg) => {
  const newData = msg.data;  // array of numbers

  // Append new data to existing chart dataset
  gsrChart.data.datasets[0].data.push(...newData);

  // Keep only the last MAX_POINTS
  if (gsrChart.data.datasets[0].data.length > MAX_POINTS) {
    gsrChart.data.datasets[0].data =
      gsrChart.data.datasets[0].data.slice(-MAX_POINTS);
  }

  // Update x-axis labels based on current data points
  gsrChart.data.labels = Array(gsrChart.data.datasets[0].data.length).fill('');

  // Update chart
  gsrChart.update();
});

// Initialize queues for stress with 200 zeros
const MAX_QUEUE_SIZE = 200;
let stressQueue = Array(MAX_QUEUE_SIZE).fill(0);

// Add these lines to your existing JavaScript file
// The socket variable is already defined in your code

// Listen for 'predictions' events from the server
socket.on('predictions', function(data) {
    // Add new predictions to the queues and remove oldest ones
    stressQueue.push(data.stress);
    stressQueue.shift();

    // Update the progress bars
    updateBars();

    const stressProba = data.stress_proba;
  
    // Convert to percentage (0-100)
    const stressPercentage = Math.round(stressProba * 100);
    
    // Update the progress bar width
    const stressBar = document.getElementById('stress-proba-bar');
    stressBar.style.width = `${stressPercentage}%`;
    
    // Update the percentage text
    const percentageText = document.getElementById('stress-proba-percentage');
    percentageText.textContent = `${stressPercentage}%`;
    
    // Set color based on stress level
    if (stressPercentage < 30) {
      stressBar.style.backgroundColor = '#4CAF50'; // Green for low stress
    } else if (stressPercentage < 70) {
      stressBar.style.backgroundColor = '#FFC107'; // Yellow/amber for medium stress
    } else {
      stressBar.style.backgroundColor = '#F44336'; // Red for high stress
    }
});

// Function to update both progress bars
function updateBars() {
    // Get references to the progress bars
    const stressBar = document.getElementById('stress-bar');
    const stressPercentage = document.getElementById('stress-percentage');
    
    // Calculate the sum of values in each queue
    const stressSum = stressQueue.reduce((acc, val) => acc + val, 0);
    
    // Calculate percentages
    const stressPercentValue = (stressSum / MAX_QUEUE_SIZE) * 100;
    
    // Update the progress bars
    if (stressBar) {
        stressBar.style.width = `${stressPercentValue}%`;
        updateBarColor(stressBar, stressPercentValue);
    }
    
    // Update percentage text if elements exist
    if (stressPercentage) {
        stressPercentage.textContent = `${Math.round(stressPercentValue)}%`;
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

// Add event listeners once DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Reset database button
  const resetDbBtn = document.getElementById('reset-db-btn');
  if (resetDbBtn) {
      resetDbBtn.addEventListener('click', resetDatabase);
  }
  
  // Export CSV button
  const exportCsvBtn = document.getElementById('export-csv-btn');
  if (exportCsvBtn) {
      exportCsvBtn.addEventListener('click', exportCsv);
  }
});

// Function to reset the database
async function resetDatabase() {
  // Show confirmation dialog
  if (!confirm('Are you sure you want to reset the database? This will delete all signal data.')) {
      return; // User cancelled
  }
  
  try {
      const response = await fetch('/reset_db', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          }
      });
      
      const result = await response.json();
      
      if (result.success) {
          alert(result.message);
          
          // Clear charts
          if (ppgChart && ppgChart.data && ppgChart.data.datasets) {
              ppgChart.data.datasets[0].data = [];
              ppgChart.update();
          }
          
          if (gsrChart && gsrChart.data && gsrChart.data.datasets) {
              gsrChart.data.datasets[0].data = [];
              gsrChart.update();
          }
      } else {
          alert('Failed to reset database: ' + result.message);
      }
  } catch (error) {
      console.error('Error resetting database:', error);
      alert('An error occurred while resetting the database.');
  }
}

// Function to export data as CSV
function exportCsv() {
  // Since this is a file download, we'll navigate to the URL directly
  window.location.href = '/export_csv';
}
