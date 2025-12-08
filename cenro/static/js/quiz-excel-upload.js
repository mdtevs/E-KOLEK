/**
 * Excel Upload Handlers for Quiz Management
 * Handles file upload, validation, and result display for quiz Excel imports
 */

/**
 * Initialize quiz Excel upload handler
 */
function initQuizExcelUpload() {
  const form = document.getElementById('quizUploadForm');
  if (!form) return;

  form.addEventListener('submit', handleQuizUpload);
}

/**
 * Handle quiz Excel file upload
 * @param {Event} e - Form submit event
 */
function handleQuizUpload(e) {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const resultsDiv = document.getElementById('quizUploadResults');
  
  // Get CSRF token from window.CSRF_TOKEN or QUIZ_CONFIG
  const csrfToken = window.CSRF_TOKEN || (typeof QUIZ_CONFIG !== 'undefined' ? QUIZ_CONFIG.csrfToken : '');
  
  // Show loading state
  showUploadLoading(resultsDiv, 'Uploading and processing...');
  
  fetch('/quiz-excel/upload-excel/', {
    method: 'POST',
    body: formData,
    headers: {
      'X-CSRFToken': csrfToken
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showUploadSuccess(resultsDiv, data);
      
      // Reset form
      e.target.reset();
      
      // Reload page after 2 seconds
      setTimeout(() => location.reload(), 2000);
    } else {
      showUploadError(resultsDiv, data);
    }
  })
  .catch(error => {
    showUploadNetworkError(resultsDiv, error);
  });
}

/**
 * Show upload loading state
 * @param {HTMLElement} resultsDiv - Results container
 * @param {string} message - Loading message
 */
function showUploadLoading(resultsDiv, message) {
  resultsDiv.style.display = 'block';
  resultsDiv.style.background = '#eff6ff';
  resultsDiv.style.border = '1px solid #3b82f6';
  resultsDiv.innerHTML = `<p style="color: #3b82f6; margin: 0;"><i class="bx bx-loader-alt bx-spin"></i> ${message}</p>`;
}

/**
 * Show upload success
 * @param {HTMLElement} resultsDiv - Results container
 * @param {Object} data - Success response data
 */
function showUploadSuccess(resultsDiv, data) {
  resultsDiv.style.background = '#d1fae5';
  resultsDiv.style.border = '1px solid #10b981';
  resultsDiv.innerHTML = `
    <div style="color: #065f46;">
      <p style="font-weight: 600; margin: 0 0 0.5rem 0;">
        <i class='bx bx-check-circle'></i> Success! ${data.message}
      </p>
      <p style="margin: 0;">Created: <strong>${data.created_count}</strong> quiz questions</p>
    </div>
  `;
}

/**
 * Show upload error
 * @param {HTMLElement} resultsDiv - Results container
 * @param {Object} data - Error response data
 */
function showUploadError(resultsDiv, data) {
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
 * Show network error
 * @param {HTMLElement} resultsDiv - Results container
 * @param {Error} error - Error object
 */
function showUploadNetworkError(resultsDiv, error) {
  resultsDiv.style.background = '#fee2e2';
  resultsDiv.style.border = '1px solid #ef4444';
  resultsDiv.innerHTML = `
    <p style="color: #991b1b; margin: 0;">
      <i class='bx bx-error'></i> Error: ${error.message}
    </p>
  `;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initQuizExcelUpload);
