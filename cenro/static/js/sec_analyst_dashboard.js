/**
 * Security Analyst Dashboard JavaScript
 * Handles tab switching and section navigation for the security dashboard
 */

/**
 * Tab switching function
 * @param {string} sectionName - Name of the section to display
 * @param {Event} event - Click event (optional)
 */
function showSection(sectionName, event) {
    if (event) {
        event.preventDefault();
    }
    
    // Hide all sections
    const sections = document.querySelectorAll('.dashboard-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Update sidebar active state
    const menuItems = document.querySelectorAll('#sidebar .side-menu.top li');
    menuItems.forEach(item => {
        item.classList.remove('active');
    });
    
    const activeMenuItem = document.querySelector(`#sidebar .side-menu.top li[data-section="${sectionName}"]`);
    if (activeMenuItem) {
        activeMenuItem.classList.add('active');
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a hash in the URL
    const hash = window.location.hash.substring(1); // Remove the '#'
    
    if (hash) {
        // Show the section based on hash
        showSection(hash);
    } else {
        // Show overview section by default
        showSection('overview');
    }
});

/**
 * Handle hash changes for back/forward navigation
 */
window.addEventListener('hashchange', function() {
    const hash = window.location.hash.substring(1);
    if (hash) {
        showSection(hash);
    }
});
