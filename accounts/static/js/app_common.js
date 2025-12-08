/**
 * Common utilities for user-facing pages with CSRF token handling
 * This file provides shared functionality for forms and AJAX requests
 */

window.AppUtils = (function() {
    'use strict';

    /**
     * Get CSRF token from multiple possible sources
     * @return {string|null} CSRF token or null if not found
     */
    function getCSRFToken() {
        // Try multiple sources for maximum compatibility
        
        // 1. From meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // 2. From window variable (set by Django template)
        if (window.CSRF_TOKEN) {
            return window.CSRF_TOKEN;
        }
        
        // 3. From hidden input (if any forms exist)
        const hiddenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (hiddenInput) {
            return hiddenInput.value;
        }
        
        // 4. From cookie (fallback)
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        
        console.warn('CSRF token not found in any expected location');
        return null;
    }

    /**
     * Create FormData with CSRF token automatically included
     * @param {Object} data - Key-value pairs to include in FormData
     * @return {FormData} FormData object with CSRF token
     */
    function createFormDataWithCSRF(data = {}) {
        const formData = new FormData();
        
        // Add CSRF token
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }
        
        // Add other data
        Object.entries(data).forEach(([key, value]) => {
            if (value instanceof File || value instanceof Blob) {
                formData.append(key, value);
            } else if (Array.isArray(value)) {
                // Handle arrays (e.g., for multiple select)
                value.forEach(item => formData.append(key, item));
            } else {
                formData.append(key, String(value));
            }
        });
        
        return formData;
    }

    /**
     * Enhanced fetch function with automatic CSRF token handling
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @return {Promise} Fetch promise
     */
    function fetchWithCSRF(url, options = {}) {
        const csrfToken = getCSRFToken();
        
        if (!csrfToken) {
            console.error('Cannot make request: CSRF token not available');
            return Promise.reject(new Error('CSRF token not available'));
        }
        
        // Prepare headers
        const headers = new Headers(options.headers || {});
        
        // Add CSRF token to headers
        headers.set('X-CSRFToken', csrfToken);
        
        // If sending JSON, ensure content type is set
        if (options.body && typeof options.body === 'string') {
            if (!headers.has('Content-Type')) {
                headers.set('Content-Type', 'application/json');
            }
        }
        
        // Merge options
        const fetchOptions = {
            ...options,
            headers: headers,
            credentials: 'same-origin' // Include cookies for authentication
        };
        
        return fetch(url, fetchOptions);
    }

    /**
     * Submit a form via AJAX with CSRF protection
     * @param {HTMLFormElement|FormData} form - Form element or FormData
     * @param {string} url - Submission URL (optional, uses form action if not provided)
     * @param {Object} options - Additional options
     * @return {Promise} Fetch promise
     */
    function submitFormWithCSRF(form, url = null, options = {}) {
        let formData;
        let submitUrl = url;
        
        if (form instanceof HTMLFormElement) {
            formData = new FormData(form);
            submitUrl = url || form.action;
            
            // Ensure CSRF token is included
            const csrfToken = getCSRFToken();
            if (csrfToken && !formData.has('csrfmiddlewaretoken')) {
                formData.append('csrfmiddlewaretoken', csrfToken);
            }
        } else if (form instanceof FormData) {
            formData = form;
            // CSRF token should already be added via createFormDataWithCSRF
        } else {
            throw new Error('First parameter must be HTMLFormElement or FormData');
        }
        
        const fetchOptions = {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            ...options
        };
        
        // Don't set Content-Type header for FormData - browser will set it with boundary
        delete fetchOptions.headers?.['Content-Type'];
        
        return fetchWithCSRF(submitUrl, fetchOptions);
    }

    /**
     * Utility to handle common AJAX form submission patterns
     * @param {string} formSelector - CSS selector for the form
     * @param {Object} options - Configuration options
     */
    function setupFormAjax(formSelector, options = {}) {
        const form = document.querySelector(formSelector);
        if (!form) {
            console.warn(`Form not found: ${formSelector}`);
            return;
        }
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
            const originalText = submitBtn ? submitBtn.textContent : '';
            
            // Show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = options.loadingText || 'Loading...';
            }
            
            submitFormWithCSRF(form, options.url)
                .then(response => {
                    if (options.onSuccess) {
                        return options.onSuccess(response, form);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data && data.success) {
                        if (options.onDataSuccess) {
                            options.onDataSuccess(data, form);
                        }
                    } else if (data && data.error) {
                        if (options.onError) {
                            options.onError(data.error, form);
                        } else {
                            alert(data.error);
                        }
                    }
                })
                .catch(error => {
                    console.error('Form submission error:', error);
                    if (options.onError) {
                        options.onError(error.message, form);
                    } else {
                        alert('An error occurred. Please try again.');
                    }
                })
                .finally(() => {
                    // Restore button state
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = originalText;
                    }
                });
        });
    }

    // Public API
    return {
        getCSRFToken,
        createFormDataWithCSRF,
        fetchWithCSRF,
        submitFormWithCSRF,
        setupFormAjax
    };
})();

// Auto-initialize common functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add any common initialization here if needed
});
