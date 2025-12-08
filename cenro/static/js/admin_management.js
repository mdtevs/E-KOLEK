// Admin Management specific JavaScript functions

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

// Global variables for URLs (will be set by Django template)
window.adminManagementUrls = window.adminManagementUrls || {};

function toggleBarangaySelection() {
    const roleSelect = document.getElementById('role');
    const barangaySelection = document.getElementById('barangay_selection');
    const roleDescs = document.querySelectorAll('.role-desc');
    
    // Hide all role descriptions
    roleDescs.forEach(desc => desc.style.display = 'none');
    
    if (roleSelect.value === 'operations_manager') {
        barangaySelection.style.display = 'block';
        document.getElementById('operations_manager_desc').style.display = 'block';
    } else {
        barangaySelection.style.display = 'none';
        // Clear all barangay selections when not operations manager
        const checkboxes = barangaySelection.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        // Show appropriate description
        if (roleSelect.value === 'content_rewards_manager') {
            document.getElementById('content_rewards_manager_desc').style.display = 'block';
        } else if (roleSelect.value === 'security_analyst') {
            document.getElementById('security_analyst_desc').style.display = 'block';
        }
    }
}

// Toggle all barangays function
function toggleAllBarangays(context) {
    const selectAllCheckbox = document.getElementById(`select_all_barangays_${context}`);
    const barangayCheckboxes = document.querySelectorAll(`.barangay-checkbox-${context}`);
    
    barangayCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// Update select all checkbox based on individual selections
function updateSelectAll(context) {
    const selectAllCheckbox = document.getElementById(`select_all_barangays_${context}`);
    const barangayCheckboxes = document.querySelectorAll(`.barangay-checkbox-${context}`);
    const checkedBoxes = document.querySelectorAll(`.barangay-checkbox-${context}:checked`);
    
    if (checkedBoxes.length === barangayCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedBoxes.length > 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const createAdminForm = document.getElementById('createAdminForm');
    if (createAdminForm) {
        // Email validation on blur
        const emailInput = document.getElementById('email');
        if (emailInput) {
            let emailTimeout = null;
            
            emailInput.addEventListener('blur', function() {
                const email = this.value.trim();
                const errorSpan = document.getElementById('email-error');
                const successSpan = document.getElementById('email-success');
                
                // Clear previous messages
                errorSpan.style.display = 'none';
                successSpan.style.display = 'none';
                
                if (!email) return;
                
                // Basic email validation
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    errorSpan.textContent = 'Please enter a valid email address';
                    errorSpan.style.display = 'block';
                    return;
                }
                
                // Clear timeout if user types again quickly
                clearTimeout(emailTimeout);
                
                // Check uniqueness after 500ms delay
                emailTimeout = setTimeout(function() {
                    fetch('/cenro/admin/check-email/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: 'email=' + encodeURIComponent(email)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.available) {
                            successSpan.style.display = 'block';
                            errorSpan.style.display = 'none';
                        } else {
                            errorSpan.textContent = data.message || 'This email is already registered';
                            errorSpan.style.display = 'block';
                            successSpan.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Email validation error:', error);
                    });
                }, 500);
            });
        }
        
        createAdminForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Clear all previous errors
            clearCreateFormErrors();
            
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const email = document.getElementById('email').value.trim();
            const fullName = document.getElementById('full_name').value.trim();
            const username = document.getElementById('username').value.trim();
            const role = document.getElementById('role').value;
            
            let hasError = false;
            let firstErrorField = null;
            
            // Validate full name
            if (!fullName) {
                showFieldError('full_name', 'Full name is required');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('full_name');
            }
            
            // Validate username
            if (!username) {
                showFieldError('username', 'Username is required');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('username');
            }
            
            // Validate email
            if (!email) {
                showFieldError('email', 'Email address is required');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('email');
            } else {
                // Validate email format
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    showFieldError('email', 'Please enter a valid email address');
                    hasError = true;
                    if (!firstErrorField) firstErrorField = document.getElementById('email');
                }
            }
            
            // Validate password
            if (!password) {
                showFieldError('password', 'Password is required');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('password');
            } else if (password.length < 8) {
                showFieldError('password', 'Password must be at least 8 characters long');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('password');
            }
            
            // Validate confirm password
            if (!confirmPassword) {
                showFieldError('confirm_password', 'Please confirm your password', true);
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('confirm_password');
            } else if (password !== confirmPassword) {
                showFieldError('confirm_password', 'Passwords do not match', true);
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('confirm_password');
            }
            
            // Validate role
            if (!role) {
                showFieldError('role', 'Please select a role');
                hasError = true;
                if (!firstErrorField) firstErrorField = document.getElementById('role');
            }
            
            // If role is operations_manager, check if at least one barangay is selected
            if (role === 'operations_manager') {
                const selectedBarangays = document.querySelectorAll('.barangay-checkbox-create:checked');
                if (selectedBarangays.length === 0) {
                    showFieldError('barangay', 'Please select at least one barangay for Operations Manager role');
                    hasError = true;
                }
            }
            
            // If there are errors, focus on the first error field and stop
            if (hasError) {
                if (firstErrorField) {
                    firstErrorField.focus();
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return false;
            }
            
            // All validations passed - show confirmation modal
            showConfirmation(e, 'add', 'Admin', 'createAdminForm');
        });
        
        // Helper function to show field error
        function showFieldError(fieldName, message, usePasswordMatch = false) {
            const field = document.getElementById(fieldName);
            let errorElement;
            
            if (usePasswordMatch) {
                errorElement = document.getElementById('password-match-error');
                const successElement = document.getElementById('password-match-success');
                if (successElement) successElement.style.display = 'none';
            } else {
                errorElement = document.getElementById(fieldName.replace('_', '-') + '-error');
            }
            
            if (field) {
                field.style.borderColor = '#dc2626';
                field.style.background = '#fef2f2';
            }
            
            if (errorElement) {
                errorElement.textContent = '✗ ' + message;
                errorElement.style.display = 'block';
            }
        }
        
        // Helper function to clear all form errors
        function clearCreateFormErrors() {
            // Clear all error messages
            const errorElements = [
                'full-name-error', 'username-error', 'email-error', 
                'password-error', 'password-match-error', 'role-error', 'barangay-error'
            ];
            
            errorElements.forEach(id => {
                const element = document.getElementById(id);
                if (element) element.style.display = 'none';
            });
            
            // Reset field styles
            const fields = ['full_name', 'username', 'email', 'password', 'confirm_password', 'role'];
            fields.forEach(fieldName => {
                const field = document.getElementById(fieldName);
                if (field) {
                    field.style.borderColor = '#ddd';
                    field.style.background = 'white';
                }
            });
            
            // Hide success message
            const successElement = document.getElementById('password-match-success');
            if (successElement) successElement.style.display = 'none';
        }
        
        // Real-time password matching feedback
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        const matchError = document.getElementById('password-match-error');
        const matchSuccess = document.getElementById('password-match-success');
        
        function checkPasswordMatch() {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            // Only show feedback if confirm password has content
            if (confirmPassword.length > 0) {
                if (password === confirmPassword && password.length >= 8) {
                    matchError.style.display = 'none';
                    matchSuccess.style.display = 'block';
                    confirmPasswordInput.style.borderColor = '#10b981';
                    confirmPasswordInput.style.background = '#f0fdf4';
                } else if (password !== confirmPassword) {
                    matchError.textContent = '✗ Passwords do not match';
                    matchError.style.display = 'block';
                    matchSuccess.style.display = 'none';
                    confirmPasswordInput.style.borderColor = '#dc2626';
                    confirmPasswordInput.style.background = '#fef2f2';
                } else if (password.length < 8) {
                    matchError.textContent = '✗ Password must be at least 8 characters';
                    matchError.style.display = 'block';
                    matchSuccess.style.display = 'none';
                    confirmPasswordInput.style.borderColor = '#f59e0b';
                    confirmPasswordInput.style.background = '#fffbeb';
                }
            } else {
                matchError.style.display = 'none';
                matchSuccess.style.display = 'none';
                confirmPasswordInput.style.borderColor = '#ddd';
                confirmPasswordInput.style.background = 'white';
            }
        }
        
        if (passwordInput && confirmPasswordInput) {
            passwordInput.addEventListener('input', checkPasswordMatch);
            confirmPasswordInput.addEventListener('input', checkPasswordMatch);
            
            // Clear errors on input for all fields
            document.getElementById('full_name').addEventListener('input', function() {
                this.style.borderColor = '#ddd';
                this.style.background = 'white';
                const errorEl = document.getElementById('full-name-error');
                if (errorEl) errorEl.style.display = 'none';
            });
            
            document.getElementById('username').addEventListener('input', function() {
                this.style.borderColor = '#ddd';
                this.style.background = 'white';
                const errorEl = document.getElementById('username-error');
                if (errorEl) errorEl.style.display = 'none';
            });
            
            document.getElementById('email').addEventListener('input', function() {
                this.style.borderColor = '#ddd';
                this.style.background = 'white';
            });
            
            document.getElementById('password').addEventListener('input', function() {
                if (this.value.length >= 8) {
                    this.style.borderColor = '#10b981';
                    this.style.background = '#f0fdf4';
                    const errorEl = document.getElementById('password-error');
                    if (errorEl) errorEl.style.display = 'none';
                } else if (this.value.length > 0) {
                    this.style.borderColor = '#f59e0b';
                    this.style.background = '#fffbeb';
                } else {
                    this.style.borderColor = '#ddd';
                    this.style.background = 'white';
                }
                checkPasswordMatch();
            });
            
            document.getElementById('role').addEventListener('change', function() {
                this.style.borderColor = '#ddd';
                this.style.background = 'white';
                const errorEl = document.getElementById('role-error');
                if (errorEl) errorEl.style.display = 'none';
                const barangayError = document.getElementById('barangay-error');
                if (barangayError) barangayError.style.display = 'none';
            });
        }
    }
    
    // Email validation for Edit Admin Modal
    const editEmailInput = document.getElementById('edit_email');
    if (editEmailInput) {
        let editEmailTimeout = null;
        
        editEmailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            const originalEmail = this.getAttribute('data-original-email');
            const errorSpan = document.getElementById('edit-email-error');
            const successSpan = document.getElementById('edit-email-success');
            
            // Clear previous messages
            errorSpan.style.display = 'none';
            successSpan.style.display = 'none';
            
            // Skip validation if email hasn't changed
            if (email === originalEmail) {
                successSpan.textContent = '✓ Current email';
                successSpan.style.display = 'block';
                return;
            }
            
            if (email) {
                // Basic email format validation
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(email)) {
                    errorSpan.textContent = 'Please enter a valid email address';
                    errorSpan.style.display = 'block';
                    return;
                }
                
                // Debounce the API call
                clearTimeout(editEmailTimeout);
                editEmailTimeout = setTimeout(() => {
                    // Check email availability
                    fetch('/cenro/admin/check-email/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: `email=${encodeURIComponent(email)}`
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.available) {
                            successSpan.textContent = '✓ Email is available';
                            successSpan.style.display = 'block';
                        } else {
                            errorSpan.textContent = data.message;
                            errorSpan.style.display = 'block';
                        }
                    })
                    .catch(error => {
                        console.error('Error checking email:', error);
                    });
                }, 500);
            }
        });
    }
    
});

// Barangay tooltip functionality - Using event delegation for dynamically loaded content
document.addEventListener('click', function(e) {
    // Check if clicked element is a barangay badge
    const badge = e.target.closest('.barangay-count-badge');
    
    if (badge) {
        console.log('Barangay badge clicked:', badge);
        e.stopPropagation();
        
        const wrapper = badge.closest('.barangay-tooltip-wrapper');
        const tooltip = wrapper.querySelector('.barangay-tooltip');
        
        console.log('Wrapper:', wrapper, 'Tooltip:', tooltip);
        
        // Close all other tooltips
        document.querySelectorAll('.barangay-tooltip').forEach(t => {
            if (t !== tooltip) {
                t.style.visibility = 'hidden';
                t.style.opacity = '0';
            }
        });
        
        // Toggle this tooltip
        if (tooltip.style.visibility === 'visible') {
            console.log('Hiding tooltip');
            tooltip.style.visibility = 'hidden';
            tooltip.style.opacity = '0';
        } else {
            console.log('Showing tooltip');
            tooltip.style.visibility = 'visible';
            tooltip.style.opacity = '1';
        }
    } else {
        // Close all tooltips when clicking outside
        if (!e.target.closest('.barangay-tooltip-wrapper')) {
            document.querySelectorAll('.barangay-tooltip').forEach(tooltip => {
                tooltip.style.visibility = 'hidden';
                tooltip.style.opacity = '0';
            });
        }
    }
});
// Helper function to get CSRF token
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Helper function to submit action form
function submitActionForm(action, adminId) {
    const form = document.createElement('form');
    form.method = 'post';
    form.action = window.adminManagementUrls.adminManagementUrl || '';
    
    // Add CSRF token
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getCSRFToken();
    form.appendChild(csrfInput);
    
    // Add action
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = action;
    form.appendChild(actionInput);
    
    // Add admin ID
    const adminIdInput = document.createElement('input');
    adminIdInput.type = 'hidden';
    adminIdInput.name = 'admin_id';
    adminIdInput.value = adminId;
    form.appendChild(adminIdInput);
    
    document.body.appendChild(form);
    form.submit();
}

function approveAdmin(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    if (confirm(`Are you sure you want to approve the admin account: ${username}?`)) {
        submitActionForm('approve', adminId);
    }
}



function showSuspendModal(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    
    // Set the admin info in the modal
    document.getElementById('suspendAdminId').value = adminId;
    document.getElementById('suspendAdminUsername').textContent = username;
    
    // Show the modal
    const modal = document.getElementById('suspendModal');
    modal.style.display = 'flex';
}

// Edit Admin Modal Functions
function showEditAdminModal(button) {
    console.log('showEditAdminModal called', button);
    
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    const fullName = button.getAttribute('data-admin-fullname');
    const email = button.getAttribute('data-admin-email');
    const role = button.getAttribute('data-admin-role');
    
    console.log('Admin data:', { adminId, username, fullName, email, role });
    
    // Set form values
    document.getElementById('editAdminId').value = adminId;
    document.getElementById('editAdminUsername').textContent = username;
    document.getElementById('edit_full_name').value = fullName;
    document.getElementById('edit_email').value = email;
    document.getElementById('edit_role').value = role;
    
    // Store original email for validation
    document.getElementById('edit_email').setAttribute('data-original-email', email);
    
    // Show the modal
    const modal = document.getElementById('editAdminModal');
    console.log('Modal element:', modal);
    console.log('Modal current display:', modal.style.display);
    
    modal.style.display = 'flex';
    
    console.log('Modal display after setting to flex:', modal.style.display);
}

function closeEditAdminModal() {
    const modal = document.getElementById('editAdminModal');
    modal.style.display = 'none';
    // Clear error messages
    document.getElementById('edit-email-error').style.display = 'none';
    document.getElementById('edit-email-success').style.display = 'none';
}

// Delete Admin Modal Functions
function showDeleteAdminModal(button) {
    console.log('showDeleteAdminModal called', button);
    
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    
    console.log('Delete Admin data:', { adminId, username });
    
    // Set form values
    document.getElementById('deleteAdminId').value = adminId;
    document.getElementById('deleteAdminUsername').textContent = username;
    
    // Reset form
    document.getElementById('deletion_reason').value = '';
    document.getElementById('confirmDelete').checked = false;
    
    // Show the modal
    const modal = document.getElementById('deleteAdminModal');
    console.log('Delete Modal element:', modal);
    console.log('Delete Modal current display:', modal.style.display);
    
    modal.style.display = 'flex';
    
    console.log('Delete Modal display after setting to flex:', modal.style.display);
}

function closeDeleteAdminModal() {
    const modal = document.getElementById('deleteAdminModal');
    modal.style.display = 'none';
}

function showSuspendModal(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    
    // Set the admin info in the modal
    document.getElementById('suspendAdminId').value = adminId;
    document.getElementById('suspendAdminUsername').textContent = username;
    
    // Show the modal
    const modal = document.getElementById('suspendModal');
    modal.style.display = 'flex';
}

function reactivateAdmin(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    if (confirm(`Are you sure you want to reactivate the admin account: ${username}?`)) {
        submitActionForm('reactivate', adminId);
    }
}

function unsuspendAdmin(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    if (confirm(`Are you sure you want to unsuspend the admin account: ${username}?`)) {
        submitActionForm('unsuspend', adminId);
    }
}

function showEditBarangayModal(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    
    // Set the admin info in the modal
    document.getElementById('editBarangayAdminId').value = adminId;
    document.getElementById('editBarangayAdminUsername').textContent = username;
    
    // Fetch current barangay assignments using dynamic URL
    const getBarangaysUrl = window.adminManagementUrls.getBarangaysUrl?.replace('PLACEHOLDER_ADMIN_ID', adminId) || `/cenro/admin/get-barangays/${adminId}/`;
    
    fetch(getBarangaysUrl)
        .then(response => response.json())
        .then(data => {
            // Clear all checkboxes first
            const checkboxes = document.querySelectorAll('#editBarangayModal input[name="barangays"]');
            checkboxes.forEach(cb => cb.checked = false);
            
            // Check the assigned barangays
            data.assigned_barangays.forEach(barangayId => {
                const checkbox = document.getElementById(`edit_barangay_${barangayId}`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
            
            // Update "Select All" checkbox state
            updateSelectAll('edit');
        })
        .catch(error => {
            console.error('Error fetching barangays:', error);
            showErrorNotification('Error loading barangay assignments. Please try again.');
        });
    
    // Show the modal
    const modal = document.getElementById('editBarangayModal');
    modal.style.display = 'flex';
}

function closeEditBarangayModal() {
    const modal = document.getElementById('editBarangayModal');
    modal.style.display = 'none';
    // Clear all checkboxes
    const checkboxes = document.querySelectorAll('#editBarangayModal input[name="barangays"]');
    checkboxes.forEach(cb => cb.checked = false);
    // Reset select all checkbox
    const selectAllCheckbox = document.getElementById('select_all_barangays_edit');
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
}

function closeSuspendModal() {
    const modal = document.getElementById('suspendModal');
    modal.style.display = 'none';
    // Clear the form
    const suspensionReason = document.getElementById('suspensionReason');
    if (suspensionReason) {
        suspensionReason.value = '';
    }
}



// Close modal when clicking outside of it
window.onclick = function(event) {
    const suspendModal = document.getElementById('suspendModal');
    const editBarangayModal = document.getElementById('editBarangayModal');
    const editAdminModal = document.getElementById('editAdminModal');
    const deleteAdminModal = document.getElementById('deleteAdminModal');
    
    if (event.target == suspendModal) {
        closeSuspendModal();
    }
    if (event.target == editBarangayModal) {
        closeEditBarangayModal();
    }
    if (event.target == editAdminModal) {
        closeEditAdminModal();
    }
    if (event.target == deleteAdminModal) {
        closeDeleteAdminModal();
    }
}

// Tab switching functionality with persistence
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    const clickedButton = event.target.closest('.tab-button');
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
    
    // Save tab state for persistence
    if (window.TabPersistence) {
        window.TabPersistence.saveTabState(tabName);
    }
}

// Reset Password Functions
function showResetPasswordModal(button) {
    const adminId = button.getAttribute('data-admin-id');
    const adminUsername = button.getAttribute('data-admin-username');
    
    if (!adminId || !adminUsername) {
        console.error('Missing admin ID or username');
        return;
    }
    
    // Set modal data
    document.getElementById('resetAdminId').value = adminId;
    document.getElementById('resetAdminUsername').textContent = adminUsername;
    
    // Reset form
    document.getElementById('resetPasswordForm').reset();
    document.getElementById('confirmReset').checked = false;
    
    // Show modal
    document.getElementById('resetPasswordModal').style.display = 'flex';
}

function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').style.display = 'none';
}

function closePasswordResetSuccessModal() {
    document.getElementById('passwordResetSuccessModal').style.display = 'none';
}

function copyPassword() {
    const passwordElement = document.getElementById('tempPassword');
    const password = passwordElement.textContent;
    
    if (password && password !== 'Loading...') {
        // Try to use the modern clipboard API
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(password).then(function() {
                showCopySuccess();
            }).catch(function() {
                fallbackCopyPassword(password);
            });
        } else {
            fallbackCopyPassword(password);
        }
    }
}

function fallbackCopyPassword(password) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = password;
    textArea.style.position = 'absolute';
    textArea.style.left = '-999999px';
    
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccess();
    } catch (err) {
        console.error('Failed to copy password: ', err);
        showErrorNotification('Failed to copy password. Please copy manually: ' + password);
    }
    
    document.body.removeChild(textArea);
}

function showCopySuccess() {
    const copyButtons = document.querySelectorAll('button[onclick="copyPassword()"]');
    copyButtons.forEach(button => {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bx bx-check" style="margin-right: 5px;"></i>Copied!';
        button.style.backgroundColor = '#10b981';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.backgroundColor = '';
        }, 2000);
    });
}

// Handle reset password form submission
document.addEventListener('DOMContentLoaded', function() {
    const resetPasswordForm = document.getElementById('resetPasswordForm');
    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const adminUsername = document.getElementById('resetAdminUsername').textContent;
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="bx bx-loader-alt bx-spin" style="margin-right: 5px;"></i>Resetting...';
            submitButton.disabled = true;
            
            // Submit the form
            fetch(window.adminManagementUrls.adminManagementUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close reset modal
                    closeResetPasswordModal();
                    
                    // Show success modal with temporary password
                    document.getElementById('resetSuccessUsername').textContent = adminUsername;
                    document.getElementById('tempPassword').textContent = data.temporary_password;
                    document.getElementById('passwordResetSuccessModal').style.display = 'flex';
                } else {
                    showErrorNotification(data.message || 'Failed to reset password. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorNotification('An error occurred while resetting the password. Please try again.');
            })
            .finally(() => {
                // Restore button state
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
            });
        });
    }
});

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const resetModal = document.getElementById('resetPasswordModal');
    const successModal = document.getElementById('passwordResetSuccessModal');
    
    if (event.target === resetModal) {
        closeResetPasswordModal();
    }
    
    if (event.target === successModal) {
        closePasswordResetSuccessModal();
    }
});

// Admin History Functions
function filterHistory() {
    const actionFilter = document.getElementById('actionFilter').value;
    const adminFilter = document.getElementById('adminFilter').value;
    const limitFilter = document.getElementById('limitFilter').value;
    
    const rows = document.querySelectorAll('.history-record');
    let visibleCount = 0;
    
    rows.forEach(row => {
        const rowAction = row.getAttribute('data-action');
        const rowAdmin = row.getAttribute('data-admin');
        
        let showRow = true;
        
        // Filter by action
        if (actionFilter && rowAction !== actionFilter) {
            showRow = false;
        }
        
        // Filter by admin
        if (adminFilter && rowAdmin !== adminFilter) {
            showRow = false;
        }
        
        // Apply limit
        if (showRow && visibleCount >= parseInt(limitFilter)) {
            showRow = false;
        }
        
        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update empty state
    const tbody = document.getElementById('historyTableBody');
    const emptyRow = tbody.querySelector('tr:last-child');
    
    if (visibleCount === 0 && rows.length > 0) {
        // Show "no results" message
        if (!emptyRow || emptyRow.cells.length !== 1) {
            const noResultsRow = document.createElement('tr');
            noResultsRow.innerHTML = `
                <td colspan="6" style="text-align: center; padding: 40px; color: #666;">
                    <i class='bx bx-search' style="font-size: 3rem; color: #d1d5db; margin-bottom: 15px; display: block;"></i>
                    <h4>No matching records found</h4>
                    <p>Try adjusting your filters to see more results.</p>
                </td>
            `;
            tbody.appendChild(noResultsRow);
        }
    } else if (visibleCount > 0 && emptyRow && emptyRow.cells.length === 1) {
        // Remove "no results" message
        emptyRow.remove();
    }
}

function refreshHistory() {
    // Reload the page with history tab active
    const url = new URL(window.location);
    url.searchParams.set('tab', 'history');
    window.location.href = url.toString();
}

// Unlock Admin Function (for automatically locked accounts)
function unlockAdmin(button) {
    const adminId = button.getAttribute('data-admin-id');
    const username = button.getAttribute('data-admin-username');
    if (confirm(`Are you sure you want to unlock the admin account: ${username}? This will reset their failed login attempts and allow them to login.`)) {
        submitActionForm('unlock', adminId);
    }
}

// Initialize tab persistence and history tab on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tab persistence
    if (window.TabPersistence) {
        window.TabPersistence.init({
            tabButtonsSelector: '.tab-button',
            tabContentsSelector: '.tab-content',
            activeClass: 'active'
        });
    }
    
    // Check for URL parameter (takes precedence over saved state)
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    
    if (activeTab) {
        // Use a small delay to ensure tab persistence init is complete
        setTimeout(() => {
            switchTab(activeTab);
        }, 100);
    }
});

// Ensure all functions are globally accessible for onclick handlers
window.showEditAdminModal = showEditAdminModal;
window.closeEditAdminModal = closeEditAdminModal;
window.showDeleteAdminModal = showDeleteAdminModal;
window.closeDeleteAdminModal = closeDeleteAdminModal;
window.showSuspendModal = showSuspendModal;
window.closeSuspendModal = closeSuspendModal;
window.showResetPasswordModal = showResetPasswordModal;
window.closeResetPasswordModal = closeResetPasswordModal;
window.showEditBarangayModal = showEditBarangayModal;
window.closeEditBarangayModal = closeEditBarangayModal;
window.approveAdmin = approveAdmin;
window.unsuspendAdmin = unsuspendAdmin;
window.unlockAdmin = unlockAdmin;
window.toggleBarangaySelection = toggleBarangaySelection;
window.toggleAllBarangays = toggleAllBarangays;
window.updateSelectAll = updateSelectAll;
window.switchTab = switchTab;
window.closePasswordResetSuccessModal = closePasswordResetSuccessModal;
window.copyToClipboard = copyToClipboard;
