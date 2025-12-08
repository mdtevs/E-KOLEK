/**
 * Admin Analytics Dashboard JavaScript
 * Handles charts, filters, tabs, file uploads, and year comparison functionality
 */

/* ==================== TAB MANAGEMENT ==================== */

/**
 * Switch between different data view tabs
 * @param {Event} event - Click event
 * @param {string} tabId - ID of tab content to show
 */
function switchTab(event, tabId) {
  // Hide all tab contents
  const tabContents = document.querySelectorAll('.tab-content');
  tabContents.forEach(content => {
    content.classList.remove('active');
  });
  
  // Remove active class from all buttons
  const tabButtons = document.querySelectorAll('.tab-button');
  tabButtons.forEach(button => {
    button.classList.remove('active');
  });
  
  // Show selected tab content
  document.getElementById(tabId).classList.add('active');
  
  // Add active class to clicked button
  event.currentTarget.classList.add('active');
  
  // Save tab state for persistence
  if (window.TabPersistence) {
    window.TabPersistence.saveTabState(tabId);
  }
}

/**
 * Toggle collapsible insight sections
 * @param {HTMLElement} element - Element to toggle
 */
function toggleCollapse(element) {
  element.classList.toggle('collapsed');
}

/* ==================== YEAR FILTER MANAGEMENT ==================== */

/**
 * Set year filter and submit form with loading indicator
 * @param {string} yearType - Type of year filter (current, 2024, 2023, compare, all)
 */
function setYearFilter(yearType) {
  const form = document.getElementById('filterForm');
  const yearFilterInput = document.getElementById('year_filter');
  const startDateInput = document.getElementById('start_date');
  const endDateInput = document.getElementById('end_date');
  
  yearFilterInput.value = yearType;
  
  const currentYear = new Date().getFullYear();
  
  // Set date ranges based on year selection
  switch(yearType) {
    case 'current':
      startDateInput.value = `${currentYear}-01-01`;
      endDateInput.value = `${currentYear}-12-31`;
      break;
    case '2024':
      startDateInput.value = '2024-01-01';
      endDateInput.value = '2024-12-31';
      break;
    case '2023':
      startDateInput.value = '2023-01-01';
      endDateInput.value = '2023-12-31';
      break;
    case 'compare':
      // For comparison, keep dates empty and let backend handle
      startDateInput.value = '';
      endDateInput.value = '';
      break;
    case 'all':
      startDateInput.value = '';
      endDateInput.value = '';
      break;
  }
  
  // Submit form with smooth loading indicator
  const filterSection = document.querySelector('.filter-section');
  filterSection.style.opacity = '0.6';
  filterSection.style.pointerEvents = 'none';
  
  form.submit();
}

/**
 * Toggle year selector dropdown visibility
 */
function toggleYearDropdown() {
  const dropdown = document.getElementById('yearDropdown');
  const icon = document.getElementById('yearDropdownIcon');
  const isActive = dropdown.classList.contains('active');
  
  if (isActive) {
    dropdown.classList.remove('active');
    icon.style.transform = 'rotate(0deg)';
  } else {
    dropdown.classList.add('active');
    icon.style.transform = 'rotate(180deg)';
  }
}

/**
 * Select a specific year from dropdown
 * @param {string} year - Year value to filter by
 * @param {string} displayText - Text to display in selector
 */
function selectYear(year, displayText) {
  document.getElementById('selectedYearText').textContent = displayText;
  toggleYearDropdown();
  setYearFilter(year);
}

/**
 * Clear all year filters and reload page
 */
function clearYearFilter() {
  const url = new URL(window.location.href);
  url.searchParams.delete('year_filter');
  url.searchParams.delete('compare_year1');
  url.searchParams.delete('compare_year2');
  window.location.href = url.toString();
}

/* ==================== YEAR COMPARISON MODAL ==================== */

/**
 * Open year comparison modal with animation
 */
function openComparisonModal() {
  const modal = document.getElementById('comparisonModal');
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  
  // Animate modal appearance
  setTimeout(() => {
    modal.querySelector('.comparison-modal-content').style.opacity = '1';
    modal.querySelector('.comparison-modal-content').style.transform = 'translateY(0)';
  }, 10);
}

/**
 * Close year comparison modal with animation
 */
function closeComparisonModal() {
  const modal = document.getElementById('comparisonModal');
  const modalContent = modal.querySelector('.comparison-modal-content');
  
  // Animate modal disappearance
  modalContent.style.opacity = '0';
  modalContent.style.transform = 'translateY(50px)';
  
  setTimeout(() => {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Reset form
    document.getElementById('compareYear1').value = '';
    document.getElementById('compareYear2').value = '';
  }, 300);
}

/* ==================== FILE UPLOAD HANDLING ==================== */

/**
 * Handle Excel file upload for waste data import
 * @param {File} file - Excel file to upload
 */
function handleFileUpload(file) {
  if (!file.name.match(/\.(xlsx|xls)$/)) {
    showMessage('Please select a valid Excel file (.xlsx or .xls)', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('excel_file', file);

  const uploadMessage = document.getElementById('uploadMessage');
  const uploadProgress = document.getElementById('uploadProgress');
  const uploadProgressFill = document.getElementById('uploadProgressFill');

  // Show progress bar
  uploadProgress.style.display = 'block';
  uploadProgressFill.style.width = '0%';
  uploadMessage.innerHTML = '';

  // Simulate progress (since we can't track actual upload progress easily)
  let progress = 0;
  const progressInterval = setInterval(() => {
    progress += 10;
    uploadProgressFill.style.width = progress + '%';
    if (progress >= 90) {
      clearInterval(progressInterval);
    }
  }, 200);

  // Get CSRF token
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(window.UPLOAD_URL, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrftoken
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    clearInterval(progressInterval);
    uploadProgressFill.style.width = '100%';
    
    setTimeout(() => {
      uploadProgress.style.display = 'none';
      uploadProgressFill.style.width = '0%';
    }, 1000);

    if (data.success) {
      let message = `Successfully processed ${data.success_count} transactions`;
      if (data.error_count > 0) {
        message += `. ${data.error_count} errors encountered.`;
        if (data.errors && data.errors.length > 0) {
          message += '<br><br><strong>Errors:</strong><ul>';
          data.errors.forEach(error => {
            message += `<li>${error}</li>`;
          });
          message += '</ul>';
        }
        showMessage(message, 'warning');
      } else {
        showMessage(message, 'success');
        // Reload page after 2 seconds to show updated data
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      }
    } else {
      showMessage('Error: ' + data.error, 'error');
    }
  })
  .catch(error => {
    clearInterval(progressInterval);
    uploadProgress.style.display = 'none';
    uploadProgressFill.style.width = '0%';
    showMessage('Failed to upload file: ' + error.message, 'error');
  });
}

/**
 * Show upload message with appropriate styling
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, warning, error)
 */
function showMessage(message, type) {
  const alertClass = type === 'success' ? 'alert-success' : (type === 'warning' ? 'alert-warning' : 'alert-error');
  const icon = type === 'success' ? 'bx-check-circle' : (type === 'warning' ? 'bx-error-circle' : 'bx-x-circle');
  
  const uploadMessage = document.getElementById('uploadMessage');
  uploadMessage.innerHTML = `
    <div class="alert ${alertClass}">
      <i class='bx ${icon}'></i>
      <div>${message}</div>
    </div>
  `;
}

/* ==================== EVENT LISTENERS ==================== */

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  // File upload area events
  const fileUploadArea = document.getElementById('fileUploadArea');
  const fileInput = document.getElementById('excelFileInput');
  
  if (fileUploadArea && fileInput) {
    fileUploadArea.addEventListener('click', function() {
      fileInput.click();
    });

    fileUploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      fileUploadArea.classList.add('dragging');
    });

    fileUploadArea.addEventListener('dragleave', function() {
      fileUploadArea.classList.remove('dragging');
    });

    fileUploadArea.addEventListener('drop', function(e) {
      e.preventDefault();
      fileUploadArea.classList.remove('dragging');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUpload(files[0]);
      }
    });

    fileInput.addEventListener('change', function() {
      if (fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
      }
    });
  }
  
  // Close dropdown when clicking outside
  document.addEventListener('click', function(event) {
    const yearSelector = document.querySelector('.year-selector-container');
    const dropdown = document.getElementById('yearDropdown');
    const icon = document.getElementById('yearDropdownIcon');
    
    if (yearSelector && dropdown && icon && !yearSelector.contains(event.target)) {
      dropdown.classList.remove('active');
      icon.style.transform = 'rotate(0deg)';
    }
  });

  // Close comparison modal when clicking outside
  document.addEventListener('click', function(event) {
    const modal = document.getElementById('comparisonModal');
    if (modal && event.target === modal) {
      closeComparisonModal();
    }
  });

  // Prevent selecting same year in both comparison dropdowns
  const compareYear1 = document.getElementById('compareYear1');
  const compareYear2 = document.getElementById('compareYear2');
  
  if (compareYear1 && compareYear2) {
    compareYear1.addEventListener('change', function() {
      const selectedYear = this.value;
      
      Array.from(compareYear2.options).forEach(option => {
        if (option.value === selectedYear && selectedYear !== '') {
          option.disabled = true;
          option.style.color = '#ccc';
        } else {
          option.disabled = false;
          option.style.color = '';
        }
      });
    });

    compareYear2.addEventListener('change', function() {
      const selectedYear = this.value;
      
      Array.from(compareYear1.options).forEach(option => {
        if (option.value === selectedYear && selectedYear !== '') {
          option.disabled = true;
          option.style.color = '#ccc';
        } else {
          option.disabled = false;
          option.style.color = '';
        }
      });
    });
  }
  
  // Initialize tab persistence
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-button',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
});
