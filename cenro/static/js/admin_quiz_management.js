/**
 * Admin Quiz Management JavaScript
 * Handles quiz management actions and interactions
 */

/**
 * Export quiz data functionality
 */
function exportQuizData() {
    alert('Quiz data export functionality will be implemented here.');
}

/**
 * Generate quiz report functionality
 */
function generateQuizReport() {
    alert('Quiz report generation functionality will be implemented here.');
}

/**
 * Initialize quiz management functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get admin learn URL from hidden element
    const urlsElement = document.getElementById('admin-urls');
    if (!urlsElement) {
        console.error('Admin URLs element not found');
        return;
    }
    
    const adminLearnUrl = urlsElement.dataset.adminLearnUrl;
    
    // Add event listeners for action buttons
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const action = target.dataset.action;
        
        switch(action) {
            case 'edit-video':
                window.location.href = adminLearnUrl;
                break;
            case 'export-quiz':
                exportQuizData();
                break;
            case 'generate-report':
                generateQuizReport();
                break;
        }
    });
});
