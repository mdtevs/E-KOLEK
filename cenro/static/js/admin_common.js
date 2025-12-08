/**
 * Common utilities for admin pages
 * Handles CSRF tokens, common API patterns, etc.
 */

// Notification helper functions
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'custom-notification success';
    notification.innerHTML = `
        <i class='bx bx-check-circle'></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

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

// CSRF Token utilities
const AdminUtils = {
    /**
     * Get CSRF token from various sources
     */
    getCSRFToken: function() {
        // Try window variable first (set by Django template)
        if (window.CSRF_TOKEN) {
            return window.CSRF_TOKEN;
        }
        
        // Try meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try cookie
        const cookieValue = this.getCookie('csrftoken');
        if (cookieValue) {
            return cookieValue;
        }
        
        console.error('CSRF token not found');
        return null;
    },
    
    /**
     * Get cookie value by name
     */
    getCookie: function(name) {
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
    },
    
    /**
     * Create FormData with CSRF token
     */
    createFormDataWithCSRF: function(data = {}) {
        const formData = new FormData();
        const csrfToken = this.getCSRFToken();
        
        if (!csrfToken) {
            throw new Error('CSRF token not available');
        }
        
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        // Add provided data
        Object.entries(data).forEach(([key, value]) => {
            if (value instanceof File) {
                formData.append(key, value);
            } else if (typeof value === 'object') {
                formData.append(key, JSON.stringify(value));
            } else {
                formData.append(key, value);
            }
        });
        
        return formData;
    },
    
    /**
     * Make authenticated fetch request with CSRF token
     */
    fetchWithCSRF: async function(url, options = {}) {
        const csrfToken = this.getCSRFToken();
        
        if (!csrfToken) {
            throw new Error('CSRF token not available');
        }
        
        // Default options
        const defaultOptions = {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            }
        };
        
        // Merge options
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        return fetch(url, mergedOptions);
    },
    
    /**
     * Handle API response with common error handling
     */
    handleResponse: async function(response, successMessage = 'Operation successful') {
        if (response.ok) {
            const data = await response.json();
            if (successMessage) {
                showSuccessNotification(successMessage + (data.question_id ? ` (ID: ${data.question_id})` : ''));
            }
            return data;
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            const errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
            showErrorNotification('Error: ' + errorMessage);
            console.error('API Error:', errorData);
            throw new Error(errorMessage);
        }
    },
    
    /**
     * Validate form inputs
     */
    validateForm: function(formId, rules = {}) {
        const form = document.getElementById(formId);
        if (!form) {
            console.error(`Form with ID '${formId}' not found`);
            return false;
        }
        
        let isValid = true;
        const errors = [];
        
        Object.entries(rules).forEach(([fieldId, rule]) => {
            const field = document.getElementById(fieldId);
            if (!field) {
                console.error(`Field with ID '${fieldId}' not found`);
                isValid = false;
                return;
            }
            
            const value = field.value.trim();
            
            if (rule.required && !value) {
                errors.push(`${rule.label || fieldId} is required`);
                isValid = false;
            }
            
            if (rule.minLength && value.length < rule.minLength) {
                errors.push(`${rule.label || fieldId} must be at least ${rule.minLength} characters`);
                isValid = false;
            }
            
            if (rule.maxLength && value.length > rule.maxLength) {
                errors.push(`${rule.label || fieldId} must be no more than ${rule.maxLength} characters`);
                isValid = false;
            }
        });
        
        if (!isValid) {
            showErrorNotification('Validation errors:\n' + errors.join('\n'));
        }
        
        return isValid;
    }
};

// Make it globally available
window.AdminUtils = AdminUtils;
