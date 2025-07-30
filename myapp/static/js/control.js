const startBtn = document.getElementById("startBtn");
const pauseBtn = document.getElementById("pauseBtn");
const stopBtn = document.getElementById("stopBtn");
const videoFeed = document.getElementById("videoFeed");
const staticImage = document.getElementById("staticImage");
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');

let isRunning = false;
let isPaused = false;
let countPollingInterval = null;
let loadingTimeout = null;
let isProcessing = false;

function updateButtons() {
    startBtn.disabled = isRunning || isProcessing;
    pauseBtn.disabled = !isRunning || isProcessing;
    stopBtn.disabled = !isRunning || isProcessing;
    
    // Update pause button text based on current state
    if (isPaused) {
        pauseBtn.textContent = 'Resume';
    } else {
        pauseBtn.textContent = 'Pause';
    }
}

function updateStatusGif(status) {
    if (isPaused && status === 'running') {
        return;
    }
    const statusGifs = document.querySelectorAll('.status-gif');
    statusGifs.forEach(gif => {
        gif.style.display = 'none';
    });

    const activeGif = document.querySelector(`.status-gif.${status}`);
    if (activeGif) {
        activeGif.style.display = 'flex';
        activeGif.classList.add('active');
    }
}

function toggleVideoDisplay(show) {
    if (show) {
        videoFeed.style.display = "block";
        staticImage.style.opacity = "0";
        setTimeout(() => {
            staticImage.style.display = "none";
            videoFeed.style.opacity = "1";
        }, 300);
    } else {
        staticImage.style.display = "flex";
        videoFeed.style.opacity = "0";
        updateStatusGif('waiting');
        setTimeout(() => {
            videoFeed.style.display = "none";
            staticImage.style.opacity = "1";
        }, 300);
    }
}

async function fetchWithCSRF(url, method = 'POST') {
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        console.log(`Sending ${method} request to ${url}`);
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.status === 'error') {
            console.error('Server error:', data.message);
            throw new Error(data.message);
        }
        
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        alert(`Failed to connect to server: ${error.message}`);
        return null;
    }
}

function updateStatus(status) {
    if (isPaused && status === 'running') {
        return;
    }
    statusDot.className = 'status-dot ' + status;
    
    // Update status text without background process info
    let statusTextContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusText.textContent = statusTextContent;
}

async function updateCount() {
    try {
        const response = await fetch('/api/detection/get_counts/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Count data:', data);
        
        if (data) {
            document.getElementById('suitableCount').textContent = data.suitable_count;
            document.getElementById('unsuitableCount').textContent = data.unsuitable_count;
            
            // Update status berdasarkan response dari server
            if (data.status === 'paused') {
                isPaused = true;
                pauseBtn.textContent = 'Resume';
                updateStatus('paused');
                updateStatusGif('waiting');
            } else if (data.status === 'running') {
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('running');
                updateStatusGif('running');
                // Setelah running, polling bisa diperlambat
                if (countPollingInterval) {
                    clearInterval(countPollingInterval);
                    countPollingInterval = setInterval(updateCount, 1000);
                }
            } else if (data.status === 'loading') {
                // Kamera belum siap, tetap loading
                updateStatus('loading');
                updateStatusGif('loading');
            } else if (data.status === 'stopped') {
                isRunning = false;
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('stopped');
                updateStatusGif('waiting');
            }
        }
    } catch (error) {
        console.error('Error fetching counts:', error);
        if (countPollingInterval) {
            clearInterval(countPollingInterval);
            countPollingInterval = null;
            updateStatus('stopped');
            updateStatusGif('waiting');
        }
    }
}

startBtn.addEventListener("click", async () => {
    if (isProcessing) return;
    
    isProcessing = true;
    updateButtons();
    updateStatusGif('loading');
    updateStatus('loading');
    
    const response = await fetchWithCSRF('/api/detection/start/');
    
    if (response && response.status === 'started') {
        isRunning = true;
        isPaused = false;
        
        updateButtons();
        
        if (countPollingInterval) {
            clearInterval(countPollingInterval);
        }
        
        // Start polling counts immediately - status akan berubah otomatis ketika kamera siap
        countPollingInterval = setInterval(updateCount, 500);
        
    } else {
        updateStatusGif('waiting');
        updateStatus('stopped');
        isRunning = false;
        isPaused = false;
    }
    
    isProcessing = false;
    updateButtons();
});

pauseBtn.addEventListener("click", async () => {
    if (isProcessing) return;
    
    try {
        isProcessing = true;
        updateButtons();
        
        if (!isPaused) {
            console.log("Attempting to pause...");
            const response = await fetchWithCSRF('/api/detection/pause/');
            console.log("Pause response:", response);
            
            if (response && response.status === 'paused') {
                isPaused = true;
                pauseBtn.textContent = 'Resume';
                updateStatus('paused');
                updateStatusGif('waiting');
                
                // Keep polling but reduce frequency during pause
                if (countPollingInterval) {
                    clearInterval(countPollingInterval);
                    countPollingInterval = setInterval(updateCount, 2000);
                }
            } else {
                console.error("Invalid pause response:", response);
            }
        } else {
            console.log("Attempting to resume...");
            const response = await fetchWithCSRF('/api/detection/resume/');
            console.log("Resume response:", response);
            
            if (response && response.status === 'resumed') {
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('running');
                updateStatusGif('running');
                
                // Resume normal polling frequency
                if (countPollingInterval) {
                    clearInterval(countPollingInterval);
                    countPollingInterval = setInterval(updateCount, 1000);
                }
            } else {
                console.error("Invalid resume response:", response);
            }
        }
    } catch (error) {
        console.error('Error in pause/resume:', error);
        alert('Failed to pause/resume detection');
    } finally {
        isProcessing = false;
        updateButtons();
    }
});

stopBtn.addEventListener("click", async () => {
    if (isProcessing) return;
    
    isProcessing = true;
    updateButtons();
    
    const response = await fetchWithCSRF('/api/detection/stop/');
    if (response && response.status === 'stopped') {
        isRunning = false;
        isPaused = false;
        
        if (countPollingInterval) {
            clearInterval(countPollingInterval);
            countPollingInterval = null;
        }
        
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
            loadingTimeout = null;
        }
        
        updateStatus('stopped');
        updateStatusGif('waiting');
        pauseBtn.textContent = 'Pause';
        
        document.getElementById('suitableCount').textContent = '0';
        document.getElementById('unsuitableCount').textContent = '0';
    }
    
    isProcessing = false;
    updateButtons();
});

async function checkServerConnection() {
    try {
        const response = await fetch('/api/detection/get_counts/');
        return response.ok;
    } catch (error) {
        console.error('Server connection check failed:', error);
        return false;
    }
}

// Handle page visibility changes untuk optimasi polling
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Halaman tidak terlihat - perlambat polling atau hentikan sementara
        console.log("Page hidden - slowing down polling");
        if (countPollingInterval && isRunning) {
            clearInterval(countPollingInterval);
            // Polling setiap 5 detik saat halaman tersembunyi
            countPollingInterval = setInterval(updateCount, 5000);
        }
    } else {
        // Halaman terlihat kembali - kembalikan polling normal
        console.log("Page visible - restoring normal polling");
        if (countPollingInterval && isRunning) {
            clearInterval(countPollingInterval);
            // Polling normal setiap 1 detik
            countPollingInterval = setInterval(updateCount, 1000);
            // Update segera saat kembali ke halaman
            updateCount();
        }
    }
});

document.addEventListener('DOMContentLoaded', async () => {
    isProcessing = false;
    updateButtons();

    // Cek status detection server saat halaman dimuat
    const serverConnected = await checkServerConnection();
    if (!serverConnected) {
        alert('Warning: Cannot connect to detection server. Please check if the server is running.');
        updateStatusGif('waiting');
        updateStatus('stopped');
        return;
    }

    // Restore status dari detection server
    await restoreDetectionStatus();
});

async function restoreDetectionStatus() {
    try {
        console.log("Checking detection server status...");
        const response = await fetch('/api/detection/get_counts/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Current server status:', data);
        
        if (data) {
            // Update counts dari server
            document.getElementById('suitableCount').textContent = data.suitable_count || '0';
            document.getElementById('unsuitableCount').textContent = data.unsuitable_count || '0';
            
            // Restore status berdasarkan kondisi server
            if (data.status === 'running') {
                console.log("Detection is currently running - restoring state");
                isRunning = true;
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('running');
                updateStatusGif('running');
                
                // Tampilkan notifikasi bahwa deteksi masih berjalan
                if (data.suitable_count > 0 || data.unsuitable_count > 0) {
                    showNotification('Detection is running in background! Current counts restored.', 'success');
                }
                
                // Start polling untuk update real-time
                if (countPollingInterval) {
                    clearInterval(countPollingInterval);
                }
                countPollingInterval = setInterval(updateCount, 1000);
                
            } else if (data.status === 'paused') {
                console.log("Detection is currently paused - restoring state");
                isRunning = true;
                isPaused = true;
                pauseBtn.textContent = 'Resume';
                updateStatus('paused');
                updateStatusGif('waiting');
                
                showNotification('Detection is paused. Click Resume to continue.', 'info');
                
            } else if (data.status === 'loading') {
                console.log("Detection is loading - restoring state");
                isRunning = true;
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('loading');
                updateStatusGif('loading');
                
                showNotification('Detection is starting up...', 'info');
                
                // Start polling untuk menunggu sampai ready
                if (countPollingInterval) {
                    clearInterval(countPollingInterval);
                }
                countPollingInterval = setInterval(updateCount, 500);
                
            } else {
                console.log("Detection is stopped");
                isRunning = false;
                isPaused = false;
                pauseBtn.textContent = 'Pause';
                updateStatus('stopped');
                updateStatusGif('waiting');
            }
            
            updateButtons();
            
        } else {
            // Default state jika tidak ada response
            updateStatusGif('waiting');
            updateStatus('stopped');
        }
        
    } catch (error) {
        console.error('Error restoring detection status:', error);
        updateStatusGif('waiting');
        updateStatus('stopped');
        isRunning = false;
        isPaused = false;
        updateButtons();
    }
}

function showNotification(message, type = 'info') {
    // Buat elemen notifikasi
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999;
        max-width: 400px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Tambahkan ke body
    document.body.appendChild(notification);
    
    // Auto remove setelah 5 detik
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}
