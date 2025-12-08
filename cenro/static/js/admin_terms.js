/**
 * Admin Terms & Conditions Management JavaScript
 * Handles CRUD operations, file uploads, and auto-content extraction
 */

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

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// ========================================
// MODAL FUNCTIONS
// ========================================

function openAddTermsModal() {
    document.getElementById('addTermsModal').style.display = 'flex';
    // Reset form
    document.getElementById('addTermsForm').reset();
    document.getElementById('add_upload_progress').style.display = 'none';
}

function closeAddTermsModal() {
    document.getElementById('addTermsModal').style.display = 'none';
    document.getElementById('addTermsForm').reset();
}

function openEditTermsModal(termsId) {
    // Fetch terms data and populate form
    fetch(`/api/terms/${termsId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const terms = data.terms;
                document.getElementById('edit_terms_id').value = terms.id;
                document.getElementById('edit_language').value = terms.language;
                document.getElementById('edit_title').value = terms.title;
                document.getElementById('edit_version').value = terms.version;
                document.getElementById('edit_content').value = terms.content;
                document.getElementById('edit_is_active').checked = terms.is_active;
                
                // Set form action
                document.getElementById('editTermsForm').action = `/admincontrol/edit-terms/${termsId}/`;
                
                // Show current file if exists
                if (terms.file_url) {
                    document.getElementById('edit_current_file').style.display = 'block';
                    document.getElementById('edit_file_name').textContent = terms.file_name || 'Existing file';
                } else {
                    document.getElementById('edit_current_file').style.display = 'none';
                }
                
                document.getElementById('editTermsModal').style.display = 'flex';
            }
        })
        .catch(error => {
            console.error('Error fetching terms:', error);
            showErrorNotification('Error loading terms data');
        });
}

function closeEditTermsModal() {
    document.getElementById('editTermsModal').style.display = 'none';
    document.getElementById('editTermsForm').reset();
}

function viewTermsModal(id, title, version, content, language, fileUrl) {
    document.getElementById('view_title').textContent = title;
    
    // Set language badge
    const languageBadge = language === 'english' 
        ? '<span style="background: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem;">English</span>'
        : '<span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem;">Tagalog</span>';
    document.getElementById('view_language_badge').innerHTML = languageBadge;
    
    // Set version badge
    document.getElementById('view_version_badge').innerHTML = 
        `<span style="background: #f3f4f6; color: #374151; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem;">Version ${version}</span>`;
    
    // Set content
    document.getElementById('view_content').textContent = content;
    
    // Handle file link
    if (fileUrl && fileUrl !== 'null') {
        document.getElementById('view_file_link').style.display = 'block';
        document.getElementById('view_file_url').href = fileUrl;
    } else {
        document.getElementById('view_file_link').style.display = 'none';
    }
    
    document.getElementById('viewTermsModal').style.display = 'flex';
}

function closeViewTermsModal() {
    document.getElementById('viewTermsModal').style.display = 'none';
}

// ========================================
// FILE UPLOAD HANDLERS
// ========================================

async function handleFileUploadAdd(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
        showErrorNotification('Please upload a PDF or DOC file');
        event.target.value = '';
        return;
    }
    
    // Show progress
    document.getElementById('add_upload_progress').style.display = 'block';
    document.getElementById('add_progress_bar').style.width = '30%';
    document.getElementById('add_progress_text').textContent = 'Uploading and extracting content...';
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/extract-file-content/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            document.getElementById('add_progress_bar').style.width = '100%';
            document.getElementById('add_progress_text').textContent = 'Content extracted successfully!';
            document.getElementById('add_progress_text').style.color = '#10b981';
            
            // Auto-fill fields
            if (data.suggested_title) {
                document.getElementById('add_title').value = data.suggested_title;
            }
            if (data.suggested_version) {
                document.getElementById('add_version').value = data.suggested_version;
            }
            if (data.content) {
                document.getElementById('add_content').value = data.content;
            }
            
            // Hide progress after 2 seconds
            setTimeout(() => {
                document.getElementById('add_upload_progress').style.display = 'none';
                document.getElementById('add_progress_bar').style.width = '0%';
                document.getElementById('add_progress_text').style.color = '#6b7280';
            }, 2000);
        } else {
            throw new Error(data.error || 'Failed to extract content');
        }
    } catch (error) {
        console.error('Error extracting content:', error);
        document.getElementById('add_progress_text').textContent = 'Error: ' + error.message;
        document.getElementById('add_progress_text').style.color = '#ef4444';
        
        // Hide progress after 3 seconds
        setTimeout(() => {
            document.getElementById('add_upload_progress').style.display = 'none';
            document.getElementById('add_progress_bar').style.width = '0%';
            document.getElementById('add_progress_text').style.color = '#6b7280';
        }, 3000);
    }
}

async function handleFileUploadEdit(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
        showErrorNotification('Please upload a PDF or DOC file');
        event.target.value = '';
        return;
    }
    
    // Ask if user wants to auto-extract
    if (!confirm('Do you want to extract and replace the content from this file?')) {
        return;
    }
    
    // Show progress
    document.getElementById('edit_upload_progress').style.display = 'block';
    document.getElementById('edit_progress_bar').style.width = '30%';
    document.getElementById('edit_progress_text').textContent = 'Uploading and extracting content...';
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/extract-file-content/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update progress
            document.getElementById('edit_progress_bar').style.width = '100%';
            document.getElementById('edit_progress_text').textContent = 'Content extracted successfully!';
            document.getElementById('edit_progress_text').style.color = '#10b981';
            
            // Auto-fill content
            if (data.content) {
                document.getElementById('edit_content').value = data.content;
            }
            if (data.suggested_title && confirm('Update title to: "' + data.suggested_title + '"?')) {
                document.getElementById('edit_title').value = data.suggested_title;
            }
            if (data.suggested_version && confirm('Update version to: "' + data.suggested_version + '"?')) {
                document.getElementById('edit_version').value = data.suggested_version;
            }
            
            // Hide progress after 2 seconds
            setTimeout(() => {
                document.getElementById('edit_upload_progress').style.display = 'none';
                document.getElementById('edit_progress_bar').style.width = '0%';
                document.getElementById('edit_progress_text').style.color = '#6b7280';
            }, 2000);
        } else {
            throw new Error(data.error || 'Failed to extract content');
        }
    } catch (error) {
        console.error('Error extracting content:', error);
        document.getElementById('edit_progress_text').textContent = 'Error: ' + error.message;
        document.getElementById('edit_progress_text').style.color = '#ef4444';
        
        // Hide progress after 3 seconds
        setTimeout(() => {
            document.getElementById('edit_upload_progress').style.display = 'none';
            document.getElementById('edit_progress_bar').style.width = '0%';
            document.getElementById('edit_progress_text').style.color = '#6b7280';
        }, 3000);
    }
}

// ========================================
// FORM VALIDATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Add form validation
    const addForm = document.getElementById('addTermsForm');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            const content = document.getElementById('add_content').value.trim();
            if (content.length < 100) {
                e.preventDefault();
                showErrorNotification('Terms and Conditions content must be at least 100 characters long.');
                return false;
            }
        });
    }
    
    const editForm = document.getElementById('editTermsForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            const content = document.getElementById('edit_content').value.trim();
            if (content.length < 100) {
                e.preventDefault();
                showErrorNotification('Terms and Conditions content must be at least 100 characters long.');
                return false;
            }
        });
    }
    
    // Add event listeners for view buttons using data attributes
    document.querySelectorAll('.view-terms-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            const title = this.dataset.title;
            const version = this.dataset.version;
            const content = this.dataset.content;
            const language = this.dataset.language;
            const fileUrl = this.dataset.file || null;
            
            viewTermsModal(id, title, version, content, language, fileUrl);
        });
    });
});

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.style.display = 'none';
    }
});

console.log('Admin Terms & Conditions management loaded successfully');
