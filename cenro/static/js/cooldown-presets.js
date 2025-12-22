/**
 * Game Cooldown Configuration with Day-based Presets
 * Automatically converts days to hours for smoother UX
 */

// Convert days to hours and minutes
function convertDaysToTime(days) {
    const totalHours = days * 24;
    return {
        hours: totalHours,
        minutes: 0,
        days: days
    };
}

// Format duration for display
function formatDuration(days, hours) {
    if (days === 0 && hours === 0) {
        return 'No cooldown (unlimited plays)';
    }
    
    if (days === 1) {
        return `1 day (24 hours)`;
    } else if (days > 1 && days < 7) {
        return `${days} days (${hours} hours)`;
    } else if (days === 7) {
        return `1 week (7 days / ${hours} hours)`;
    } else if (days === 14) {
        return `2 weeks (14 days / ${hours} hours)`;
    } else if (days === 30) {
        return `1 month (30 days / ${hours} hours)`;
    } else {
        return `${days} days (${hours} hours)`;
    }
}

// Set cooldown using preset buttons
function setCooldown(gameType, days) {
    const converted = convertDaysToTime(days);
    
    // Update hidden fields
    document.getElementById(`${gameType}-cooldown_hours`).value = converted.hours;
    document.getElementById(`${gameType}-cooldown_minutes`).value = converted.minutes;
    
    // Update visible days input
    document.getElementById(`${gameType}-days`).value = days;
    
    // Update display
    updateDurationDisplay(gameType, days, converted.hours);
    
    // Visual feedback for selected preset
    const actualGameType = gameType === 'default' ? 'default' : gameType.replace('dragdrop', 'dragdrop');
    const form = document.getElementById(`${actualGameType}-cooldown-form`);
    if (form) {
        const buttons = form.querySelectorAll('.preset-btn');
        buttons.forEach(btn => {
            btn.style.borderColor = '#e5e7eb';
            btn.style.background = 'white';
            btn.style.color = '#374151';
            btn.style.fontWeight = '600';
        });
        
        // Highlight selected button with smooth transition
        if (event && event.target) {
            event.target.style.borderColor = '#667eea';
            event.target.style.background = 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)';
            event.target.style.color = '#667eea';
            event.target.style.fontWeight = '700';
            event.target.style.transform = 'scale(1.05)';
            event.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.2)';
        }
    }
}

// Update cooldown from manual days input
function updateCooldownFromDays(gameType) {
    const daysInput = document.getElementById(`${gameType}-days`);
    let days = parseInt(daysInput.value) || 0;
    
    // Clamp to valid range
    if (days < 0) days = 0;
    if (days > 30) days = 30;
    daysInput.value = days;
    
    const converted = convertDaysToTime(days);
    
    // Update hidden fields
    document.getElementById(`${gameType}-cooldown_hours`).value = converted.hours;
    document.getElementById(`${gameType}-cooldown_minutes`).value = converted.minutes;
    
    // Update display
    updateDurationDisplay(gameType, days, converted.hours);
    
    // Reset preset button highlights
    const actualGameType = gameType === 'default' ? 'default' : gameType.replace('dragdrop', 'dragdrop');
    const form = document.getElementById(`${actualGameType}-cooldown-form`);
    if (form) {
        const buttons = form.querySelectorAll('.preset-btn');
        buttons.forEach(btn => {
            btn.style.borderColor = '#e5e7eb';
            btn.style.background = 'white';
            btn.style.color = '#374151';
            btn.style.fontWeight = '600';
            btn.style.transform = 'scale(1)';
            btn.style.boxShadow = 'none';
        });
    }
}

// Update the duration display text
function updateDurationDisplay(gameType, days, hours) {
    const displayElement = document.getElementById(`${gameType}-duration-display`);
    if (displayElement) {
        displayElement.textContent = formatDuration(days, hours);
    }
}

// Load existing cooldown values from backend and convert to days
function loadExistingCooldowns() {
    // This will be populated by Django template values
    const cooldowns = {
        quiz: {
            hours: parseInt(document.getElementById('quiz-cooldown_hours').value) || 0,
            minutes: parseInt(document.getElementById('quiz-cooldown_minutes').value) || 0
        },
        dragdrop: {
            hours: parseInt(document.getElementById('dragdrop-cooldown_hours').value) || 0,
            minutes: parseInt(document.getElementById('dragdrop-cooldown_minutes').value) || 0
        },
        default: {
            hours: parseInt(document.getElementById('default-cooldown_hours').value) || 0,
            minutes: parseInt(document.getElementById('default-cooldown_minutes').value) || 0
        }
    };
    
    // Convert hours to days and update displays
    Object.keys(cooldowns).forEach(gameType => {
        const hours = cooldowns[gameType].hours;
        const days = Math.floor(hours / 24);
        
        // Update days input
        const daysInput = document.getElementById(`${gameType}-days`);
        if (daysInput) {
            daysInput.value = days;
        }
        
        // Update display
        updateDurationDisplay(gameType, days, hours);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadExistingCooldowns();
    
    // Add preset button hover effects
    const presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            if (this.style.borderColor !== 'rgb(102, 126, 234)') {
                this.style.borderColor = '#cbd5e1';
                this.style.background = '#f8fafc';
            }
        });
        btn.addEventListener('mouseleave', function() {
            if (this.style.borderColor !== 'rgb(102, 126, 234)') {
                this.style.borderColor = '#e5e7eb';
                this.style.background = 'white';
            }
        });
    });
});
