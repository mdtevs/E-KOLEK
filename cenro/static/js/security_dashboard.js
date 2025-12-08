// Security Dashboard JavaScript

// Notification helper function
function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'custom-notification error';
    notification.innerHTML = `
        <i class='bx bx-error-circle'></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Tab Switching with persistence
function switchTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Show selected tab
  const selectedTab = document.getElementById(tabName + '-tab');
  if (selectedTab) {
    selectedTab.classList.add('active');
    event.target.closest('.tab-btn').classList.add('active');
  }
  
  // Save tab state for persistence
  if (window.TabPersistence) {
    window.TabPersistence.saveTabState(tabName);
  }
}

// Initialize tab persistence on page load
document.addEventListener('DOMContentLoaded', function() {
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-btn',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
});

// Refresh Dashboard
function refreshDashboard() {
  location.reload();
}

// Filter Security Logs
function filterSecurityLogs(filter) {
  const rows = document.querySelectorAll('#securityLogsTable tr');
  rows.forEach(row => {
    if (filter === 'all') {
      row.style.display = '';
    } else if (filter === 'failed' && row.classList.contains('failed')) {
      row.style.display = '';
    } else if (filter === 'success' && row.classList.contains('success')) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}

// Filter Redemptions
function filterRedemptions(filter) {
  const rows = document.querySelectorAll('#redemptionsTable tr');
  const now = new Date();
  
  rows.forEach(row => {
    const dateCell = row.cells[0];
    if (!dateCell) return;
    
    const dateText = dateCell.textContent.trim();
    const rowDate = new Date(dateText);
    
    if (filter === 'all') {
      row.style.display = '';
    } else if (filter === 'today') {
      const isToday = rowDate.toDateString() === now.toDateString();
      row.style.display = isToday ? '' : 'none';
    } else if (filter === 'week') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      row.style.display = rowDate >= weekAgo ? '' : 'none';
    } else if (filter === 'month') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      row.style.display = rowDate >= monthAgo ? '' : 'none';
    }
  });
}

// Generate Report
function generateReport() {
  const reportType = document.getElementById('reportType').value;
  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;
  const format = document.getElementById('reportFormat').value;
  
  if (!startDate || !endDate) {
    showErrorNotification('Please select both start and end dates');
    return;
  }
  
  // Show loading state
  const btn = event.target;
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Generating...';
  
  // Get CSRF token
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                    document.querySelector('meta[name="csrf-token"]')?.content;
  
  // Make AJAX request to generate report
  fetch('/cenro/api/generate-report/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
      report_type: reportType,
      start_date: startDate,
      end_date: endDate,
      format: format
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Report generation failed');
    }
    return response.blob();
  })
  .then(blob => {
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security_report_${reportType}_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    // Show success message
    showNotification('Report generated successfully!', 'success');
    
    // Reset button
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  })
  .catch(error => {
    console.error('Error generating report:', error);
    showNotification('Error generating report. Please try again.', 'error');
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  });
}

// Show Notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    animation: slideInRight 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// Auto-refresh Dashboard Data (AJAX)
function autoRefreshData() {
  console.log('Auto-refreshing dashboard data...');
  
  // Fetch updated metrics without full page reload
  fetch('/cenro/api/dashboard-metrics/', {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.json())
  .then(data => {
    // Update metrics on page
    updateMetrics(data);
  })
  .catch(error => {
    console.error('Error refreshing data:', error);
  });
}

// Update Metrics
function updateMetrics(data) {
  // Update metric values without full page reload
  const metrics = {
    'total_users': data.total_users,
    'login_attempts_24h': data.login_attempts_24h,
    'redemptions_today': data.redemptions_today,
    'admin_actions_today': data.admin_actions_today
  };
  
  Object.keys(metrics).forEach(key => {
    const element = document.querySelector(`[data-metric="${key}"]`);
    if (element) {
      element.textContent = metrics[key];
    }
  });
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
  // Set default dates for report generator
  const today = new Date();
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  
  const endDateInput = document.getElementById('endDate');
  const startDateInput = document.getElementById('startDate');
  
  if (endDateInput && !endDateInput.value) {
    endDateInput.value = today.toISOString().split('T')[0];
  }
  
  if (startDateInput && !startDateInput.value) {
    startDateInput.value = weekAgo.toISOString().split('T')[0];
  }
  
  // Auto-refresh every 5 minutes
  setInterval(autoRefreshData, 300000);
});

// Export functions for global access
window.switchTab = switchTab;
window.refreshDashboard = refreshDashboard;
window.filterSecurityLogs = filterSecurityLogs;
window.filterRedemptions = filterRedemptions;
window.generateReport = generateReport;
