/**
 * Unified Confirmation Modal System
 * Reusable confirmation modal for all admin CRUD operations
 * Used across: adminuser, admincontrol, adminrewards, adminschedule, admin_management, admin_change_password
 */

// Global state for pending actions
let pendingFormId = null;
let pendingAction = null;
let pendingCallback = null;

/**
 * Show confirmation modal with customized content
 * @param {Event} event - The event object (for preventDefault)
 * @param {string} actionType - Type of action: 'add', 'edit', 'delete', 'update', 'approve', 'reject'
 * @param {string} itemType - Type of item being acted upon (e.g., 'User', 'Reward', 'Schedule')
 * @param {string|Function} formIdOrCallback - Form ID string or callback function
 * @returns {boolean} - Always returns false to prevent default form submission
 */
function showConfirmation(event, actionType, itemType, formIdOrCallback) {
  if (event) event.preventDefault();
  
  // Determine if formIdOrCallback is a function or form ID
  if (typeof formIdOrCallback === 'function') {
    pendingCallback = formIdOrCallback;
    pendingFormId = null;
  } else {
    pendingFormId = formIdOrCallback;
    pendingCallback = null;
  }
  
  pendingAction = actionType;
  
  // Close any parent edit/add modals BEFORE showing confirmation
  if (pendingFormId === 'editWasteTypeForm') {
    const modal = document.getElementById('editWasteTypeModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'editRewardCategoryForm') {
    const modal = document.getElementById('editRewardCategoryModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'editTermsForm') {
    const modal = document.getElementById('editTermsModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'addTermsForm') {
    const modal = document.getElementById('addTermsModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'addWasteTypeForm') {
    const modal = document.getElementById('addWasteTypeModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'addBarangayForm') {
    const modal = document.getElementById('addBarangayModal');
    if (modal) modal.style.display = 'none';
  } else if (pendingFormId === 'addRewardCategoryForm') {
    const modal = document.getElementById('addRewardCategoryModal');
    if (modal) modal.style.display = 'none';
  }
  
  const confirmModal = document.getElementById('confirmationModal');
  const confirmIcon = document.getElementById('confirmIcon');
  const confirmTitle = document.getElementById('confirmTitle');
  const confirmSubtitle = document.getElementById('confirmSubtitle');
  const confirmMessage = document.getElementById('confirmMessage');
  const confirmButton = document.getElementById('confirmButton');
  
  // Customize based on action type
  if (actionType === 'add') {
    confirmIcon.className = 'bx bx-plus-circle';
    confirmIcon.style.color = '#10b981';
    confirmTitle.textContent = `Add ${itemType}`;
    confirmSubtitle.textContent = `You are about to add a new ${itemType.toLowerCase()}`;
    confirmMessage.textContent = `Please review the information and confirm to proceed with adding this ${itemType.toLowerCase()}.`;
    confirmButton.innerHTML = `<i class="bx bx-check" style="font-size: 1.2rem;"></i> Yes, Add ${itemType}`;
    confirmButton.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(16, 185, 129, 0.4)';
  } else if (actionType === 'edit' || actionType === 'update') {
    confirmIcon.className = 'bx bx-edit';
    confirmIcon.style.color = '#3b82f6';
    confirmTitle.textContent = actionType === 'update' ? `Update ${itemType}` : `Edit ${itemType}`;
    confirmSubtitle.textContent = `You are about to ${actionType} this ${itemType.toLowerCase()}`;
    confirmMessage.textContent = `Please review your changes and confirm to proceed with ${actionType}ing this ${itemType.toLowerCase()}.`;
    confirmButton.innerHTML = `<i class="bx bx-check" style="font-size: 1.2rem;"></i> Yes, ${actionType === 'update' ? 'Update' : 'Edit'} ${itemType}`;
    confirmButton.style.background = 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(59, 130, 246, 0.4)';
  } else if (actionType === 'delete') {
    confirmIcon.className = 'bx bx-trash';
    confirmIcon.style.color = '#ef4444';
    confirmTitle.textContent = `Delete ${itemType}`;
    confirmSubtitle.textContent = 'This action cannot be undone';
    confirmMessage.textContent = `Are you sure you want to permanently delete this ${itemType.toLowerCase()}? All associated data will be removed.`;
    confirmButton.innerHTML = `<i class="bx bx-trash" style="font-size: 1.2rem;"></i> Yes, Delete ${itemType}`;
    confirmButton.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(239, 68, 68, 0.4)';
  } else if (actionType === 'approve') {
    confirmIcon.className = 'bx bx-check-circle';
    confirmIcon.style.color = '#10b981';
    confirmTitle.textContent = `Approve ${itemType}`;
    confirmSubtitle.textContent = `Grant access to this ${itemType.toLowerCase()}`;
    confirmMessage.textContent = `Are you sure you want to approve this ${itemType.toLowerCase()}? They will gain access to the system.`;
    confirmButton.innerHTML = `<i class="bx bx-check" style="font-size: 1.2rem;"></i> Yes, Approve`;
    confirmButton.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(16, 185, 129, 0.4)';
  } else if (actionType === 'reject') {
    confirmIcon.className = 'bx bx-x-circle';
    confirmIcon.style.color = '#ef4444';
    confirmTitle.textContent = `Reject ${itemType}`;
    confirmSubtitle.textContent = 'Deny access to this user';
    confirmMessage.textContent = `Are you sure you want to reject this ${itemType.toLowerCase()}? They will not be able to access the system.`;
    confirmButton.innerHTML = `<i class="bx bx-x" style="font-size: 1.2rem;"></i> Yes, Reject`;
    confirmButton.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(239, 68, 68, 0.4)';
  } else if (actionType === 'activate') {
    confirmIcon.className = 'bx bx-toggle-right';
    confirmIcon.style.color = '#10b981';
    confirmTitle.textContent = `Activate ${itemType}`;
    confirmSubtitle.textContent = 'Make this version active';
    confirmMessage.textContent = `Are you sure you want to activate ${itemType}? It will become the active version.`;
    confirmButton.innerHTML = `<i class="bx bx-check" style="font-size: 1.2rem;"></i> Yes, Activate`;
    confirmButton.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(16, 185, 129, 0.4)';
  } else if (actionType === 'deactivate') {
    confirmIcon.className = 'bx bx-toggle-left';
    confirmIcon.style.color = '#f59e0b';
    confirmTitle.textContent = `Deactivate ${itemType}`;
    confirmSubtitle.textContent = 'Make this version inactive';
    confirmMessage.textContent = `Are you sure you want to deactivate ${itemType}? Users will no longer see this version.`;
    confirmButton.innerHTML = `<i class="bx bx-toggle-left" style="font-size: 1.2rem;"></i> Yes, Deactivate`;
    confirmButton.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
    confirmButton.style.boxShadow = '0 4px 16px rgba(245, 158, 11, 0.4)';
  }
  
  confirmModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  return false;
}

/**
 * Close the confirmation modal
 */
function closeConfirmation() {
  const confirmModal = document.getElementById('confirmationModal');
  confirmModal.style.display = 'none';
  document.body.style.overflow = 'auto';
  pendingFormId = null;
  pendingAction = null;
  pendingCallback = null;
}

/**
 * Confirm the pending action
 */
function confirmAction() {
  // Special handling for edit user form with AJAX
  if (pendingFormId === 'editUserForm') {
    handleEditUserSubmission();
    return;
  }
  
  // If there's a callback function, execute it
  if (pendingCallback) {
    pendingCallback();
  }
  // If there's a form ID, submit the form
  else if (pendingFormId) {
    const form = document.getElementById(pendingFormId);
    if (form) {
      form.onsubmit = null; // Remove the onsubmit handler to allow submission
      form.submit();
    }
  }
  closeConfirmation();
}

/**
 * Handle edit user form submission with AJAX
 */
function handleEditUserSubmission() {
  const form = document.getElementById('editUserForm');
  const formData = new FormData(form);
  
  // Clear previous errors
  clearFieldErrors();
  
  // Close confirmation modal
  closeConfirmation();
  
  // Show loading state
  const submitButton = form.querySelector('button[type="submit"]');
  const originalButtonText = submitButton.innerHTML;
  submitButton.disabled = true;
  submitButton.innerHTML = '<i class="bx bx-loader-alt bx-spin" style="font-size: 1.2rem;"></i> Saving...';
  
  // Submit via AJAX
  fetch(form.action, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.json())
  .then(data => {
    submitButton.disabled = false;
    submitButton.innerHTML = originalButtonText;
    
    if (data.success) {
      // Success - reload the page to show updated data
      window.location.reload();
    } else {
      // Error - show field-specific error
      showFieldError(data.field, data.error);
    }
  })
  .catch(error => {
    submitButton.disabled = false;
    submitButton.innerHTML = originalButtonText;
    console.error('Error:', error);
    showFieldError('general', 'An unexpected error occurred. Please try again.');
  });
}

/**
 * Show error message for a specific field
 */
function showFieldError(field, message) {
  if (field === 'general') {
    const errorDiv = document.getElementById('edit_general_error');
    const errorMessage = document.getElementById('edit_general_error_message');
    if (errorDiv && errorMessage) {
      errorMessage.textContent = message;
      errorDiv.style.display = 'block';
    }
  } else {
    const errorDiv = document.getElementById(`edit_${field}_error`);
    const inputField = document.getElementById(`edit_${field}`);
    if (errorDiv && inputField) {
      const errorSpan = errorDiv.querySelector('span');
      if (errorSpan) {
        errorSpan.textContent = message;
      }
      errorDiv.style.display = 'flex';
      inputField.style.borderColor = '#ef4444';
      inputField.style.background = '#fef2f2';
      
      // Focus on the field with error
      inputField.focus();
    }
  }
}

/**
 * Clear all field errors
 */
function clearFieldErrors() {
  // Clear general error
  const generalError = document.getElementById('edit_general_error');
  if (generalError) {
    generalError.style.display = 'none';
  }
  
  // Clear field-specific errors
  const fieldErrors = document.querySelectorAll('.field-error');
  fieldErrors.forEach(error => {
    error.style.display = 'none';
  });
  
  // Reset input field styles
  const inputs = document.querySelectorAll('#editUserForm input[type="text"], #editUserForm input[type="email"]');
  inputs.forEach(input => {
    input.style.borderColor = '#e5e7eb';
    input.style.background = 'white';
  });
}

/**
 * Close modal when clicking outside
 */
document.addEventListener('click', function(event) {
  const confirmModal = document.getElementById('confirmationModal');
  if (event.target === confirmModal) {
    closeConfirmation();
  }
});

/**
 * Handle ESC key to close modal
 */
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    const confirmModal = document.getElementById('confirmationModal');
    if (confirmModal && confirmModal.style.display === 'flex') {
      closeConfirmation();
    }
  }
});
