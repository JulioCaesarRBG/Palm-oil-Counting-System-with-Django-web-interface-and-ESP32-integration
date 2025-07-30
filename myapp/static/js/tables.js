document.addEventListener('DOMContentLoaded', function() {
    const filterBtn = document.getElementById('filterBtn');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    const todayBtn = document.getElementById('todayBtn');
    const tableBody = document.querySelector('#resultsTable tbody');
    const originalRows = Array.from(tableBody.querySelectorAll('tr:not(.no-data-row)'));
    
    // Handle image errors
    document.querySelectorAll('.table-image').forEach(img => {
        img.addEventListener('error', function() {
            this.src = '/static/images/no-image.png';
        });
    });
    
    // Image Modal Elements
    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalImageTitle = document.getElementById('modalImageTitle');
    const modalImageDetails = document.getElementById('modalImageDetails');
    const imageModalClose = document.getElementById('imageModalClose');
    
    // Pagination elements
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const pageInfo = document.getElementById('pageInfo');
    let currentPage = 0;
    const rowsPerPage = 10;
    let filteredRows = [...originalRows];
    
    // Tambahkan variabel untuk popup
    const overlay = document.getElementById('overlay');
    const pageInputPopup = document.getElementById('pageInputPopup');
    const pageNumberInput = document.getElementById('pageNumberInput');
    const goToPageBtn = document.getElementById('goToPageBtn');
    const cancelPageBtn = document.getElementById('cancelPageBtn');
    let totalPages = 1;
    
    // Image Modal Functions
    function openImageModal(imageSrc, imageDate, suitableCount, unsuitableCount) {
        modalImage.src = imageSrc;
        modalImageTitle.textContent = `Session - ${imageDate}`;
        modalImageDetails.innerHTML = `
            Suitable Count: ${suitableCount} | Unsuitable Count: ${unsuitableCount}<br>
            <small>Click outside, press ESC, or click × to close</small>
        `;
        imageModal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }
    
    function closeImageModal() {
        imageModal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
    }
    
    // Event listeners for image modal
    imageModalClose.addEventListener('click', closeImageModal);
    
    imageModal.addEventListener('click', function(e) {
        if (e.target === imageModal) {
            closeImageModal();
        }
    });
    
    // Keyboard support for modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && imageModal.style.display === 'block') {
            closeImageModal();
        }
    });
    
    // Add click event to all table images (including dynamically loaded ones)
    function addImageClickEvents() {
        document.querySelectorAll('.table-image').forEach(img => {
            // Remove existing listeners to prevent duplicates
            img.removeEventListener('click', handleImageClick);
            img.addEventListener('click', handleImageClick);
        });
    }
    
    function handleImageClick(e) {
        const img = e.target;
        const imageSrc = img.src;
        const imageDate = img.getAttribute('data-date') || 'Unknown Date';
        const suitableCount = img.getAttribute('data-suitable') || '0';
        const unsuitableCount = img.getAttribute('data-unsuitable') || '0';
        
        openImageModal(imageSrc, imageDate, suitableCount, unsuitableCount);
    }
    
    // Initialize image click events
    addImageClickEvents();
    
    function showPage(page) {
        const start = page * rowsPerPage;
        const end = start + rowsPerPage;
        
        // Sembunyikan SEMUA row terlebih dahulu (termasuk yang tidak dalam filteredRows)
        originalRows.forEach(row => row.style.display = 'none');
        
        // Tampilkan hanya baris yang terfilter untuk halaman yang aktif
        filteredRows.slice(start, end).forEach(row => row.style.display = '');
        
        // Re-add image click events for visible rows
        addImageClickEvents();
        
        // Update informasi halaman
        totalPages = Math.ceil(filteredRows.length / rowsPerPage);
        pageInfo.textContent = `Page ${page + 1} of ${totalPages}`;
        
        // Update status tombol
        prevBtn.disabled = page === 0;
        nextBtn.disabled = page >= totalPages - 1;
        
        // Log untuk debugging
        console.log(`Showing page ${page + 1} of ${totalPages}`);
        console.log(`Showing rows ${start + 1} to ${Math.min(end, filteredRows.length)} of ${filteredRows.length} filtered rows`);
    }
    
    function updatePagination() {
        currentPage = 0; // Reset ke halaman pertama
        showPage(currentPage);
    }
    
    prevBtn.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            showPage(currentPage);
        }
    });
    
    nextBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredRows.length / rowsPerPage);
        if (currentPage < totalPages - 1) {
            currentPage++;
            showPage(currentPage);
        }
    });

    // Today button event listener
    todayBtn.addEventListener('click', function() {
        const today = new Date().toISOString().split('T')[0];
        console.log('Today button clicked, setting dates to:', today);
        startDate.value = today;
        endDate.value = today;
        
        // Debug: print all row dates
        console.log('All row dates in table:');
        originalRows.forEach((row, index) => {
            const rowDate = row.getAttribute('data-date');
            console.log(`Row ${index + 1}: ${rowDate}`);
        });
        
        filterBtn.click(); // Trigger filter
    });

    filterBtn.addEventListener('click', function() {
        console.log('Filter button clicked');
        console.log('Start date:', startDate.value);
        console.log('End date:', endDate.value);
        
        // Sembunyikan semua row asli terlebih dahulu
        originalRows.forEach(row => row.style.display = 'none');
        
        if (!startDate.value && !endDate.value) {
            filteredRows = [...originalRows];
            console.log('No filters applied, showing all rows');
        } else {
            filteredRows = originalRows.filter(row => {
                // Gunakan data-date attribute yang berisi format YYYY-MM-DD
                const rowDate = row.getAttribute('data-date');
                
                if (!rowDate) {
                    console.warn('Row missing data-date attribute');
                    return false;
                }
                
                const isAfterStart = !startDate.value || rowDate >= startDate.value;
                const isBeforeEnd = !endDate.value || rowDate <= endDate.value;
                
                const includeRow = isAfterStart && isBeforeEnd;
                console.log(`Row date: ${rowDate}, Include: ${includeRow}`);
                
                return includeRow;
            });
        }

        console.log(`Filtered ${filteredRows.length} rows from ${originalRows.length} total rows`);

        let noDataRow = tableBody.querySelector('.no-data-row');
        
        if (filteredRows.length === 0) {
            // Pastikan semua row asli disembunyikan
            originalRows.forEach(row => row.style.display = 'none');
            
            // Tampilkan pesan no data
            if (!noDataRow) {
                noDataRow = document.createElement('tr');
                noDataRow.className = 'no-data-row';
                noDataRow.innerHTML = '<td colspan="4" style="text-align: center; padding: 20px; color: #888;">No data available for selected date range.</td>';
                tableBody.appendChild(noDataRow);
            }
            noDataRow.style.display = '';
            prevBtn.disabled = true;
            nextBtn.disabled = true;
            pageInfo.textContent = 'Page 0 of 0';
        } else {
            // Sembunyikan pesan no data
            if (noDataRow) noDataRow.style.display = 'none';
            
            // Update pagination dan tampilkan row yang sesuai
            updatePagination();
            
            // Re-add image click events after filtering
            addImageClickEvents();
        }
    });

    // Clear filter button
    const clearBtn = document.createElement('button');
    clearBtn.textContent = 'Clear Filter';
    clearBtn.className = 'btn btn-secondary';
    clearBtn.style.marginLeft = '10px';
    document.querySelector('.filter-section').appendChild(clearBtn);

    clearBtn.addEventListener('click', function() {
        console.log('Clear filter clicked');
        startDate.value = '';
        endDate.value = '';
        filteredRows = [...originalRows];
        
        // Sembunyikan pesan no data
        const noDataRow = tableBody.querySelector('.no-data-row');
        if (noDataRow) noDataRow.style.display = 'none';
        
        // Reset pagination dan tampilkan semua data
        updatePagination();
        
        // Re-add image click events after clearing filter
        addImageClickEvents();
    });

    // Fungsi untuk menampilkan popup
    function showPageInputPopup() {
        overlay.style.display = 'block';
        pageInputPopup.style.display = 'block';
        pageNumberInput.value = currentPage + 1;
        pageNumberInput.min = 1;
        pageNumberInput.max = totalPages;
        pageNumberInput.focus();
    }

    // Fungsi untuk menyembunyikan popup
    function hidePageInputPopup() {
        overlay.style.display = 'none';
        pageInputPopup.style.display = 'none';
    }

    // Event listener untuk pageInfo click
    pageInfo.addEventListener('click', showPageInputPopup);

    // Event listener untuk tombol Go
    goToPageBtn.addEventListener('click', () => {
        const pageNumber = parseInt(pageNumberInput.value);
        if (pageNumber >= 1 && pageNumber <= totalPages) {
            currentPage = pageNumber - 1;
            showPage(currentPage);
            hidePageInputPopup();
        } else {
            alert(`Please enter a number between 1 and ${totalPages}`);
        }
    });

    // Event listener untuk tombol Cancel
    cancelPageBtn.addEventListener('click', hidePageInputPopup);

    // Event listener untuk overlay click
    overlay.addEventListener('click', hidePageInputPopup);

    // Event listener untuk Enter key pada input
    pageNumberInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            goToPageBtn.click();
        } else if (event.key === 'Escape') {
            hidePageInputPopup();
        }
    });

    // Initialize pagination
    console.log('Initializing table with', originalRows.length, 'rows');
    
    // Ensure all original rows have data-date attribute
    originalRows.forEach((row, index) => {
        const dateAttr = row.getAttribute('data-date');
        if (!dateAttr) {
            console.warn(`Row ${index + 1} missing data-date attribute`);
        } else {
            console.log(`Row ${index + 1} date: ${dateAttr}`);
        }
    });
    
    updatePagination();
});
