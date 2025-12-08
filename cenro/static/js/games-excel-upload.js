/**
 * Games Excel Upload Handler
 * Handles Excel file uploads for game questions, categories, and waste items
 */

/**
 * Initialize game questions Excel upload handler
 */
function initGameQuestionsUpload() {
    const form = document.getElementById('gameUploadForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleGameUpload(this, '/game-excel/upload-excel/', 'gameUploadResults', 'game questions');
    });
}

/**
 * Initialize categories Excel upload handler
 */
function initCategoriesUpload() {
    const form = document.getElementById('categoryUploadForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleGameUpload(this, '/category-excel/upload-excel/', 'categoryUploadResults', 'categories');
    });
}

/**
 * Initialize waste items Excel upload handler
 */
function initItemsUpload() {
    const form = document.getElementById('itemUploadForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleGameUpload(this, '/item-excel/upload-excel/', 'itemUploadResults', 'waste items');
    });
}

/**
 * Generic game upload handler
 * @param {HTMLFormElement} form - The form element
 * @param {string} url - Upload endpoint URL
 * @param {string} resultsDivId - Results container div ID
 * @param {string} contentType - Type of content being uploaded (for messages)
 */
function handleGameUpload(form, url, resultsDivId, contentType) {
    const formData = new FormData(form);
    const resultsDiv = document.getElementById(resultsDivId);
    
    showGameUploadLoading(resultsDiv);
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showGameUploadSuccess(resultsDiv, data, contentType, form);
        } else {
            showGameUploadError(resultsDiv, data);
        }
    })
    .catch(error => {
        showGameUploadNetworkError(resultsDiv, error);
    });
}

/**
 * Show loading state during upload
 * @param {HTMLElement} resultsDiv - Results container element
 */
function showGameUploadLoading(resultsDiv) {
    resultsDiv.style.display = 'block';
    resultsDiv.style.background = '#eff6ff';
    resultsDiv.style.border = '1px solid #3b82f6';
    resultsDiv.innerHTML = '<p style="color: #3b82f6; margin: 0;"><i class="bx bx-loader-alt bx-spin"></i> Uploading and processing...</p>';
}

/**
 * Show success message after upload
 * @param {HTMLElement} resultsDiv - Results container element
 * @param {Object} data - Response data from server
 * @param {string} contentType - Type of content uploaded
 * @param {HTMLFormElement} form - The form to reset
 */
function showGameUploadSuccess(resultsDiv, data, contentType, form) {
    resultsDiv.style.background = '#d1fae5';
    resultsDiv.style.border = '1px solid #10b981';
    resultsDiv.innerHTML = `
        <div style="color: #065f46;">
            <p style="font-weight: 600; margin: 0 0 0.5rem 0;">
                <i class='bx bx-check-circle'></i> Success! ${data.message}
            </p>
            <p style="margin: 0;">Created: <strong>${data.created_count}</strong> ${contentType}</p>
        </div>
    `;
    
    // Reset form
    form.reset();
    
    // Reload page after 2 seconds
    setTimeout(() => {
        location.reload();
    }, 2000);
}

/**
 * Show error message for failed upload
 * @param {HTMLElement} resultsDiv - Results container element
 * @param {Object} data - Response data from server containing error info
 */
function showGameUploadError(resultsDiv, data) {
    resultsDiv.style.background = '#fee2e2';
    resultsDiv.style.border = '1px solid #ef4444';
    
    let errorHtml = `
        <div style="color: #991b1b;">
            <p style="font-weight: 600; margin: 0 0 0.5rem 0;">
                <i class='bx bx-error-circle'></i> Upload Failed
            </p>
            <p style="margin: 0 0 0.5rem 0;">${data.error}</p>
    `;
    
    if (data.errors && data.errors.length > 0) {
        errorHtml += `
            <p style="margin: 0.5rem 0;"><strong>Error Details (${data.error_count} errors):</strong></p>
            <ul style="margin: 0; padding-left: 1.5rem; max-height: 200px; overflow-y: auto;">
        `;
        data.errors.forEach(err => {
            errorHtml += `<li style="margin: 0.25rem 0;">${err}</li>`;
        });
        errorHtml += '</ul>';
    }
    
    errorHtml += '</div>';
    resultsDiv.innerHTML = errorHtml;
}

/**
 * Show network error message
 * @param {HTMLElement} resultsDiv - Results container element
 * @param {Error} error - The error object
 */
function showGameUploadNetworkError(resultsDiv, error) {
    resultsDiv.style.background = '#fee2e2';
    resultsDiv.style.border = '1px solid #ef4444';
    resultsDiv.innerHTML = `
        <p style="color: #991b1b; margin: 0;">
            <i class='bx bx-error'></i> Error: ${error.message}
        </p>
    `;
}

// Initialize all upload handlers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initGameQuestionsUpload();
    initCategoriesUpload();
    initItemsUpload();
});
