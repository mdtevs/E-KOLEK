/**
 * Security Dashboard Functions
 * Handles refresh, chart animations, and auto-refresh functionality
 */

/**
 * Refresh dashboard data
 */
function refreshData() {
    location.reload();
}

/**
 * Initialize chart bar animations
 */
function initChartAnimations() {
    const chartBars = document.querySelectorAll('.chart-bar');
    chartBars.forEach((bar, index) => {
        const height = bar.getAttribute('data-height');
        setTimeout(() => {
            bar.style.height = height + 'px';
            bar.style.opacity = '1';
        }, index * 100);
    });
}

/**
 * Show auto-refresh notification
 */
function showAutoRefreshNotification() {
    const notification = document.createElement('div');
    notification.innerHTML = '<p style="text-align: center; padding: 10px; background: #f0f9ff; color: #1e40af; border-radius: 4px; margin: 10px 0;">Data refreshed automatically</p>';
    
    const container = document.querySelector('.security-container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
    }
    
    setTimeout(() => {
        location.reload();
    }, 1000);
}

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initChartAnimations();
});

/**
 * Auto-refresh every 5 minutes
 */
setInterval(showAutoRefreshNotification, 300000); // 5 minutes