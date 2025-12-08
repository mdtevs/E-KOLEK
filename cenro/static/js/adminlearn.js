/**
 * Admin Learn JavaScript - Using Unified Modal System
 * Uses window.DJANGO_URLS and window.CSRF_TOKEN from HTML
 */

// Add error handling for the entire script
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
});

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, setting up event listeners');
    
    // Set up cancel button event listener
    const cancelButton = document.getElementById('cancelEdit');
    if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Cancel button clicked via event listener');
            cancelEdit();
        });
    }
    
    // Preview YouTube thumbnail when URL changes
    const videoUrlField = document.getElementById('videoUrl');
    if (videoUrlField) {
        videoUrlField.addEventListener('input', function() {
            const url = this.value.trim();
            const preview = document.getElementById('urlPreview');
            const thumbnail = document.getElementById('thumbnailPreview');
            const thumbnailUrlField = document.getElementById('thumbnailUrl');
            
            if (url) {
                const videoId = extractYouTubeId(url);
                if (videoId) {
                    // Use high quality thumbnail
                    const thumbnailUrl = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
                    
                    // Test if high quality thumbnail exists, fallback to standard quality
                    const testImg = new Image();
                    testImg.onload = function() {
                        thumbnail.src = thumbnailUrl;
                        thumbnail.style.display = 'block';
                        // Auto-populate custom thumbnail URL field if empty
                        if (!thumbnailUrlField.value) {
                            thumbnailUrlField.value = thumbnailUrl;
                        }
                    };
                    testImg.onerror = function() {
                        // Fallback to standard quality thumbnail
                        const fallbackUrl = `https://img.youtube.com/vi/${videoId}/0.jpg`;
                        thumbnail.src = fallbackUrl;
                        thumbnail.style.display = 'block';
                        // Auto-populate custom thumbnail URL field if empty
                        if (!thumbnailUrlField.value) {
                            thumbnailUrlField.value = fallbackUrl;
                        }
                    };
                    testImg.src = thumbnailUrl;
                    
                    if (preview) {
                        preview.innerHTML = `✅ Valid YouTube Video - ID: ${videoId}`;
                        preview.style.display = 'block';
                        preview.style.color = '#047857';
                    }
                } else {
                    if (thumbnail) thumbnail.style.display = 'none';
                    if (preview) {
                        preview.innerHTML = '❌ Invalid YouTube URL - Please use a valid YouTube link';
                        preview.style.display = 'block';
                        preview.style.color = '#dc2626';
                    }
                    // Clear thumbnail URL field if URL is invalid
                    if (thumbnailUrlField) thumbnailUrlField.value = '';
                }
            } else {
                if (thumbnail) thumbnail.style.display = 'none';
                if (preview) preview.style.display = 'none';
                // Don't clear thumbnail URL field when URL is empty, user might have custom URL
            }
        });
        
        // Also trigger on paste event for instant feedback
        videoUrlField.addEventListener('paste', function() {
            // Small delay to allow paste content to be processed
            setTimeout(() => {
                this.dispatchEvent(new Event('input'));
            }, 100);
        });
    }
    
    // Update thumbnail preview when custom thumbnail URL changes
    const thumbnailUrlField = document.getElementById('thumbnailUrl');
    if (thumbnailUrlField) {
        thumbnailUrlField.addEventListener('input', function() {
            const customUrl = this.value.trim();
            const thumbnail = document.getElementById('thumbnailPreview');
            
            if (customUrl && thumbnail) {
                // Test if custom thumbnail URL is valid
                const testImg = new Image();
                testImg.onload = function() {
                    thumbnail.src = customUrl;
                    thumbnail.style.display = 'block';
                };
                testImg.onerror = function() {
                    // If custom URL fails, keep the YouTube thumbnail if available
                    const videoUrl = document.getElementById('videoUrl').value;
                    if (videoUrl) {
                        const videoId = extractYouTubeId(videoUrl);
                        if (videoId) {
                            thumbnail.src = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
                        }
                    }
                };
                testImg.src = customUrl;
            }
        });
    }
    
    // Form submission
    const videoForm = document.getElementById('videoForm');
    if (videoForm) {
        videoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            const videoId = document.getElementById('videoId').value;
            const actionType = videoId ? 'update' : 'add';
            
            // Show confirmation modal
            showConfirmation(e, actionType, 'Video', submitVideoForm);
        });
    }
});

// Submit video form after confirmation
async function submitVideoForm() {
    const videoId = document.getElementById('videoId').value;
    const formData = new FormData();
    
    // Use CSRF token from window (passed from Django)
    if (!window.CSRF_TOKEN) {
        showErrorNotification('CSRF token not found. Please refresh the page.');
        return;
    }
    
    formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
    formData.append('title', document.getElementById('videoTitle').value);
    formData.append('description', document.getElementById('videoDescription').value);
    formData.append('video_url', document.getElementById('videoUrl').value);
    formData.append('thumbnail_url', document.getElementById('thumbnailUrl').value);
    formData.append('points_reward', document.getElementById('pointsReward').value);
    formData.append('is_active', document.getElementById('isActive').checked);
    
    if (videoId) {
        formData.append('video_id', videoId);
    }
    
    try {
        // Use URLs from window (passed from Django)
        const url = videoId ? window.DJANGO_URLS.editVideo : window.DJANGO_URLS.addVideo;
        const response = await AdminUtils.fetchWithCSRF(url, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessNotification(videoId ? 'Video updated successfully!' : 'Video added successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorNotification('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showErrorNotification('Error: ' + error.message);
    }
}

function extractYouTubeId(url) {
    // Handle various YouTube URL formats
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/watch\?.*&v=)([a-zA-Z0-9_-]{11})/,
        /^([a-zA-Z0-9_-]{11})$/ // Direct video ID
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return null;
}

// Handle edit video button clicks
function editVideoHandler(button) {
    console.log('Edit video handler called');
    const data = button.dataset;
    editVideo(
        data.videoId,
        data.title,
        data.description,
        data.videoUrl,
        data.thumbnailUrl,
        data.points,
        data.active === 'true'
    );
}

// Handle toggle video button clicks
function toggleVideoHandler(button) {
    console.log('Toggle video handler called');
    const data = button.dataset;
    const newStatus = data.newStatus === 'true';
    const actionType = newStatus ? 'activate' : 'deactivate';
    
    // Show confirmation modal before toggling
    showConfirmation(null, actionType, 'Video', () => toggleVideo(data.videoId, newStatus));
}

// Handle delete video button clicks
function deleteVideoHandler(button) {
    console.log('Delete video handler called');
    const data = button.dataset;
    
    // Show confirmation modal before deleting
    showConfirmation(null, 'delete', 'Video', () => deleteVideo(data.videoId));
}

function editVideo(id, title, description, video_url, thumbnail_url, points, isActive) {
    console.log('Edit video function called with ID:', id);
    
    document.getElementById('videoId').value = id;
    document.getElementById('videoTitle').value = title;
    document.getElementById('videoDescription').value = description;
    document.getElementById('videoUrl').value = video_url;
    document.getElementById('thumbnailUrl').value = thumbnail_url || '';
    document.getElementById('pointsReward').value = points;
    document.getElementById('isActive').checked = isActive;
    
    const saveButtonText = document.getElementById('saveButtonText');
    if (saveButtonText) {
        saveButtonText.textContent = 'Update Video';
    }
    
    const cancelButton = document.getElementById('cancelEdit');
    if (cancelButton) {
        cancelButton.style.display = 'inline-block';
    }
    
    // Trigger URL preview
    const videoUrlField = document.getElementById('videoUrl');
    if (videoUrlField) {
        videoUrlField.dispatchEvent(new Event('input'));
    }
    
    // Scroll to form
    const form = document.querySelector('.video-form');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

function cancelEdit() {
    console.log('Cancel edit function called');
    
    try {
        // Reset the form
        const form = document.getElementById('videoForm');
        if (form) {
            form.reset();
        }
        
        // Clear all form fields explicitly
        const fields = [
            { id: 'videoId', value: '' },
            { id: 'videoTitle', value: '' },
            { id: 'videoDescription', value: '' },
            { id: 'videoUrl', value: '' },
            { id: 'thumbnailUrl', value: '' },
            { id: 'pointsReward', value: '0' }
        ];
        
        fields.forEach(field => {
            const element = document.getElementById(field.id);
            if (element) {
                element.value = field.value;
            }
        });
        
        // Reset checkbox
        const isActiveCheckbox = document.getElementById('isActive');
        if (isActiveCheckbox) {
            isActiveCheckbox.checked = true;
        }
        
        // Reset button states
        const saveButtonText = document.getElementById('saveButtonText');
        if (saveButtonText) {
            saveButtonText.textContent = 'Save Video';
        }
        
        const cancelButton = document.getElementById('cancelEdit');
        if (cancelButton) {
            cancelButton.style.display = 'none';
        }
        
        // Hide preview elements
        const thumbnailPreview = document.getElementById('thumbnailPreview');
        if (thumbnailPreview) {
            thumbnailPreview.style.display = 'none';
        }
        
        const urlPreview = document.getElementById('urlPreview');
        if (urlPreview) {
            urlPreview.style.display = 'none';
        }
        
        console.log('Cancel edit completed successfully');
        
    } catch (error) {
        console.error('Error in cancelEdit:', error);
        showErrorNotification('Error canceling edit: ' + error.message);
    }
}

async function toggleVideo(videoId, newStatus) {
    console.log('Toggle video called for ID:', videoId, 'New status:', newStatus);
    
    try {
        if (!window.CSRF_TOKEN) {
            showErrorNotification('CSRF token not found. Please refresh the page.');
            return;
        }
        
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
        formData.append('video_id', videoId);
        formData.append('is_active', newStatus);
        
        const response = await AdminUtils.fetchWithCSRF(window.DJANGO_URLS.toggleVideo, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessNotification(newStatus ? 'Video activated successfully!' : 'Video deactivated successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorNotification('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Toggle video error:', error);
        showErrorNotification('Error: ' + error.message);
    }
}

async function deleteVideo(videoId) {
    console.log('Delete video called for ID:', videoId);
    
    try {
        if (!window.CSRF_TOKEN) {
            showErrorNotification('CSRF token not found. Please refresh the page.');
            return;
        }
        
        const response = await AdminUtils.fetchWithCSRF(window.DJANGO_URLS.deleteVideo, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_id: videoId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessNotification('Video deleted successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorNotification('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Delete video error:', error);
        showErrorNotification('Error: ' + error.message);
    }
}

// Helper functions for notifications
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
        z-index: 10002;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notification.innerHTML = `<i class='bx bx-check-circle' style='font-size: 1.5rem;'></i> ${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
        z-index: 10002;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        animation: slideIn 0.3s ease;
    `;
    notification.innerHTML = `<i class='bx bx-error-circle' style='font-size: 1.5rem;'></i> ${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Add animation styles
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
`;
document.head.appendChild(style);
