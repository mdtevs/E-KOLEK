// Game Cooldown Editor Modal

let currentGameType = '';
const gameColors = {
    'quiz': '#667eea',
    'drag_drop': '#10b981',
    'all': '#f59e0b'
};

const gameNames = {
    'quiz': 'Quiz Game',
    'drag_drop': 'Drag & Drop Game',
    'all': 'Default (All Games)'
};

function openCooldownEditor(gameType, hours, minutes, isActive) {
    currentGameType = gameType;
    
    // Update modal styling based on game type
    const modalIcon = document.getElementById('modalIcon');
    const modalTitle = document.getElementById('modalTitle');
    modalIcon.style.color = gameColors[gameType];
    modalTitle.textContent = `Edit ${gameNames[gameType]} Cooldown`;
    
    // Populate form fields
    document.getElementById('editor_game_type').value = gameType;
    document.getElementById('editor_cooldown_hours').value = hours;
    document.getElementById('editor_cooldown_minutes').value = minutes;
    document.getElementById('editor_is_active').checked = isActive;
    
    // Update toggle switch appearance
    updateToggleSwitch(isActive);
    
    // Update duration preview
    updateDurationPreview();
    
    // Update duration settings visibility
    updateDurationSettingsVisibility(isActive);
    
    // Show modal
    document.getElementById('cooldownEditorModal').style.display = 'flex';
}

function closeCooldownEditor() {
    document.getElementById('cooldownEditorModal').style.display = 'none';
}

function updateToggleSwitch(isActive) {
    const toggleSwitch = document.querySelector('.toggle-switch');
    const toggleSlider = document.querySelector('.toggle-slider');
    
    if (isActive) {
        toggleSwitch.style.background = '#10b981';
        toggleSlider.style.left = '27px';
    } else {
        toggleSwitch.style.background = '#cbd5e1';
        toggleSlider.style.left = '3px';
    }
}

function updateDurationSettingsVisibility(isActive) {
    const durationSettings = document.getElementById('durationSettings');
    if (isActive) {
        durationSettings.style.display = 'block';
        durationSettings.style.opacity = '1';
    } else {
        durationSettings.style.display = 'none';
    }
}

function updateDurationPreview() {
    const hours = parseInt(document.getElementById('editor_cooldown_hours').value) || 0;
    const minutes = parseInt(document.getElementById('editor_cooldown_minutes').value) || 0;
    const preview = document.getElementById('durationPreview');
    
    if (hours === 0 && minutes === 0) {
        preview.textContent = 'No cooldown';
        preview.style.color = '#94a3b8';
    } else {
        let text = '';
        if (hours > 0) {
            text += `${hours} hour${hours !== 1 ? 's' : ''}`;
        }
        if (minutes > 0) {
            if (hours > 0) text += ' ';
            text += `${minutes} minute${minutes !== 1 ? 's' : ''}`;
        }
        preview.textContent = text;
        preview.style.color = '#15803d';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Toggle switch click handler
    const activeCheckbox = document.getElementById('editor_is_active');
    if (activeCheckbox) {
        activeCheckbox.addEventListener('change', function() {
            updateToggleSwitch(this.checked);
            updateDurationSettingsVisibility(this.checked);
        });
    }
    
    // Duration input change handlers
    const hoursInput = document.getElementById('editor_cooldown_hours');
    const minutesInput = document.getElementById('editor_cooldown_minutes');
    
    if (hoursInput) {
        hoursInput.addEventListener('input', updateDurationPreview);
    }
    
    if (minutesInput) {
        minutesInput.addEventListener('input', updateDurationPreview);
    }
    
    // Form submission
    const form = document.getElementById('cooldown-editor-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN || '{{ csrf_token }}');
            
            // Show loading state
            const submitBtn = document.getElementById('saveCooldownBtn');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bx bx-loader bx-spin"></i> Saving...';
            
            try {
                const response = await fetch('/cenro/api/game/cooldown/update/', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    body: formData
                });
                
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned invalid response. Please ensure you are logged in.');
                }
                
                const data = await response.json();
                
                if (data.success) {
                    // Show success notification
                    showNotification('Success!', 'Game cooldown updated successfully', 'success');
                    
                    // Close modal
                    closeCooldownEditor();
                    
                    // Reload page after a short delay
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showNotification('Error', data.error || 'Failed to update cooldown', 'error');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Error', error.message, 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    }
    
    // Close modal on overlay click
    const modal = document.getElementById('cooldownEditorModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeCooldownEditor();
            }
        });
    }
});

function showNotification(title, message, type) {
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? '#10b981' : '#ef4444';
    const icon = type === 'success' ? 'bx-check-circle' : 'bx-x-circle';
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: start; gap: 12px;">
            <i class='bx ${icon}' style="font-size: 1.5rem;"></i>
            <div>
                <div style="font-weight: 700; margin-bottom: 4px;">${title}</div>
                <div style="font-size: 0.9rem; opacity: 0.95;">${message}</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.2s ease-out;
    }
    
    .modal-content {
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        animation: scaleIn 0.3s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes scaleIn {
        from {
            transform: scale(0.9);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .cooldown-card {
        transition: all 0.3s ease;
    }
    
    .cooldown-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12) !important;
    }
    
    .toggle-switch {
        cursor: pointer;
    }
    
    #editor_cooldown_hours:focus,
    #editor_cooldown_minutes:focus {
        border-color: #667eea;
        outline: none;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
`;
document.head.appendChild(style);
