
  // Tab switching functionality with persistence
  function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
      tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
      button.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Save tab state for persistence
    if (window.TabPersistence) {
      window.TabPersistence.saveTabState(tabName);
    }
  }

  /**
   * Validate phone number format (11 digits starting with 09)
   */
  function validatePhoneNumber(phoneInput) {
    const phone = phoneInput.value.trim();
    const phoneError = document.getElementById('edit_phone_error');
    const phoneErrorSpan = phoneError ? phoneError.querySelector('span') : null;
    
    // Remove non-digit characters
    const digitsOnly = phone.replace(/\D/g, '');
    
    // Check if it's exactly 11 digits and starts with 09
    if (digitsOnly.length !== 11) {
      if (phoneError && phoneErrorSpan) {
        phoneErrorSpan.textContent = 'Phone number must be exactly 11 digits';
        phoneError.style.display = 'flex';
      }
      phoneInput.setCustomValidity('Phone number must be exactly 11 digits');
      return false;
    } else if (!digitsOnly.startsWith('09')) {
      if (phoneError && phoneErrorSpan) {
        phoneErrorSpan.textContent = 'Phone number must start with 09';
        phoneError.style.display = 'flex';
      }
      phoneInput.setCustomValidity('Phone number must start with 09');
      return false;
    } else {
      if (phoneError) {
        phoneError.style.display = 'none';
      }
      phoneInput.setCustomValidity('');
      // Update the input with digits only
      phoneInput.value = digitsOnly;
      return true;
    }
  }

  /**
   * Set max date for date of birth field to today
   */
  function setMaxDateForBirthday() {
    const dateInput = document.getElementById('edit_date_of_birth');
    if (dateInput) {
      const today = new Date().toISOString().split('T')[0];
      dateInput.setAttribute('max', today);
    }
  }

  function openEditModalFromData(button) {
    const id = button.getAttribute('data-user-id');
    const username = button.getAttribute('data-username');
    const full_name = button.getAttribute('data-full-name');
    const email = button.getAttribute('data-email');
    const phone = button.getAttribute('data-phone');
    const date_of_birth = button.getAttribute('data-date-of-birth');
    const gender = button.getAttribute('data-gender');
    const family_name = button.getAttribute('data-family-name');
    const family_code = button.getAttribute('data-family-code');
    const is_representative = button.getAttribute('data-is-representative') === 'true';
    
    openEditModal(id, username, full_name, email, phone, date_of_birth, gender, family_name, family_code, is_representative);
  }

  function openEditModal(id, username, full_name, email, phone, date_of_birth, gender, family_name, family_code, is_representative) {
    // Clear any previous errors
    if (typeof clearFieldErrors === 'function') {
      clearFieldErrors();
    }
    
    // Set max date for birthday field
    setMaxDateForBirthday();
    
    document.getElementById('edit_user_id').value = id;
    document.getElementById('edit_username').value = username;
    document.getElementById('edit_full_name').value = full_name;
    document.getElementById('edit_email').value = email || '';
    document.getElementById('edit_phone').value = phone;
    document.getElementById('edit_date_of_birth').value = date_of_birth || '';
    
    // Normalize gender value to match the select options (male, female, other)
    const genderSelect = document.getElementById('edit_gender');
    const normalizedGender = gender ? gender.toLowerCase() : '';
    genderSelect.value = normalizedGender;
    
    document.getElementById('edit_family_name').value = family_name;
    document.getElementById('edit_family_code').value = family_code;
    
    // Set family representative role
    const roleSelect = document.getElementById('edit_is_representative');
    roleSelect.value = is_representative ? 'true' : 'false';

    document.getElementById('editUserModal').style.display = 'flex';
  }

  function closeUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
  }

  function openDeleteModal(userId) {
    document.getElementById('delete_user_id').value = userId;
    document.getElementById('deleteConfirmModal').style.display = 'flex';
  }

  function closeDeleteModal() {
    document.getElementById('deleteConfirmModal').style.display = 'none';
  }

/**
 * Auto-hide admin messages after 3 seconds
 */
document.addEventListener('DOMContentLoaded', function() {
  // Initialize tab persistence
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-button',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
  
  // Set max date for birthday field on page load
  setMaxDateForBirthday();
  
  // Add phone number validation
  const phoneInput = document.getElementById('edit_phone');
  if (phoneInput) {
    // Validate on input (real-time)
    phoneInput.addEventListener('input', function(e) {
      // Remove non-digit characters as user types
      let value = e.target.value.replace(/\D/g, '');
      // Limit to 11 digits
      if (value.length > 11) {
        value = value.slice(0, 11);
      }
      e.target.value = value;
      
      // Show validation feedback if length is sufficient
      if (value.length >= 2) {
        validatePhoneNumber(e.target);
      }
    });
    
    // Validate on blur (when user leaves the field)
    phoneInput.addEventListener('blur', function(e) {
      if (e.target.value.trim() !== '') {
        validatePhoneNumber(e.target);
      }
    });
    
    // Prevent non-numeric input
    phoneInput.addEventListener('keypress', function(e) {
      if (!/\d/.test(e.key) && e.key !== 'Backspace' && e.key !== 'Delete' && e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' && e.key !== 'Tab') {
        e.preventDefault();
      }
    });
  }
  
  // Add form submission validation
  const editForm = document.getElementById('editUserForm');
  if (editForm) {
    editForm.addEventListener('submit', function(e) {
      const phoneField = document.getElementById('edit_phone');
      if (phoneField && !validatePhoneNumber(phoneField)) {
        e.preventDefault();
        phoneField.focus();
        return false;
      }
      
      // Validate date of birth is not in the future
      const dateField = document.getElementById('edit_date_of_birth');
      if (dateField && dateField.value) {
        const selectedDate = new Date(dateField.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate > today) {
          e.preventDefault();
          alert('Date of birth cannot be in the future.');
          dateField.focus();
          return false;
        }
      }
    });
  }
  
  const messages = document.querySelectorAll('.admin-message');
  messages.forEach(function(message) {
    setTimeout(function() {
      message.classList.add('fade-out');
      setTimeout(function() {
        message.remove();
        // Remove container if all messages are gone
        const container = document.querySelector('.admin-messages');
        if (container && container.querySelectorAll('.admin-message').length === 0) {
          container.remove();
        }
      }, 500); // Wait for fade-out animation to complete
    }, 3000); // 3 seconds
  });
});
