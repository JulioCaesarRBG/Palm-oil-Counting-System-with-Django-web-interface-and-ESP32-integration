// Fungsi untuk mengecek status deteksi
async function checkDetectionStatus() {
    try {
        const response = await fetch('/api/detection/get_counts/');
        const data = await response.json();
        
        // Update status dot dan text di semua halaman
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (statusDot && statusText) {
            if (data.debug_window_shown) {
                statusDot.className = 'status-dot running';
                statusText.textContent = 'Running';
            }
        }

        // Update counts jika elemen ada (halaman control)
        const suitableCount = document.getElementById('suitableCount');
        const unsuitableCount = document.getElementById('unsuitableCount');
        if (suitableCount && unsuitableCount) {
            suitableCount.textContent = data.suitable_count;
            unsuitableCount.textContent = data.unsuitable_count;
        }

        // Jika di halaman control, update status gif
        const statusGifs = document.querySelectorAll('.status-gif');
        if (statusGifs.length > 0) {
            statusGifs.forEach(gif => gif.style.display = 'none');
            if (data.debug_window_shown) {
                document.querySelector('.status-gif.running').style.display = 'flex';
            } else {
                document.querySelector('.status-gif.waiting').style.display = 'flex';
            }
        }

    } catch (error) {
        console.error('Error checking detection status:', error);
    }
}

// Mulai polling ketika dokumen dimuat
document.addEventListener('DOMContentLoaded', () => {
    // Polling setiap 1 detik
    setInterval(checkDetectionStatus, 1000);
}); 