/**
 * Reset Password Page JavaScript
 * Handles password validation and visibility toggle
 */

// DOM Elements
const newPasswordInput = document.getElementById('newPassword');
const confirmPasswordInput = document.getElementById('confirmPassword');
const submitBtn = document.getElementById('submitBtn');
const form = document.getElementById('resetForm');

// Password requirements
const requirements = {
  length: { 
    element: document.getElementById('req-length'), 
    test: (pw) => pw.length >= 8 
  },
  uppercase: { 
    element: document.getElementById('req-uppercase'), 
    test: (pw) => /[A-Z]/.test(pw) 
  },
  lowercase: { 
    element: document.getElementById('req-lowercase'), 
    test: (pw) => /[a-z]/.test(pw) 
  },
  number: { 
    element: document.getElementById('req-number'), 
    test: (pw) => /\d/.test(pw) 
  },
  match: { 
    element: document.getElementById('req-match'), 
    test: () => newPasswordInput.value === confirmPasswordInput.value && newPasswordInput.value.length > 0 
  }
};

/**
 * Validate password against requirements
 * @returns {boolean} - True if all requirements met
 */
function validatePassword() {
  const password = newPasswordInput.value;
  let allValid = true;

  // Check each requirement
  Object.keys(requirements).forEach(key => {
    const req = requirements[key];
    const isValid = req.test(password);
    
    if (isValid) {
      req.element.classList.remove('invalid');
      req.element.classList.add('valid');
    } else {
      req.element.classList.remove('valid');
      req.element.classList.add('invalid');
      allValid = false;
    }
  });

  // Enable/disable submit button
  submitBtn.disabled = !allValid;
  submitBtn.style.opacity = allValid ? '1' : '0.6';
  submitBtn.style.cursor = allValid ? 'pointer' : 'not-allowed';

  return allValid;
}

/**
 * Toggle password visibility
 * @param {string} inputId - ID of password input
 * @param {string} iconId - ID of eye icon
 */
function togglePassword(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  
  if (input.type === 'password') {
    input.type = 'text';
    icon.innerHTML = '<path d="M1 1l22 22"/><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 7 11 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 1 12s4 7 11 7a9.74 9.74 0 0 0 5.39-1.61"/>';
  } else {
    input.type = 'password';
    icon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
  }
}

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
  // Validate on input
  newPasswordInput.addEventListener('input', validatePassword);
  confirmPasswordInput.addEventListener('input', validatePassword);

  // Form submission validation
  form.addEventListener('submit', (e) => {
    if (!validatePassword()) {
      e.preventDefault();
      alert('Please ensure all password requirements are met');
    }
  });

  // Initial validation
  validatePassword();

  // Make togglePassword function global
  window.togglePassword = togglePassword;
});
