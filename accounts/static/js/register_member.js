// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

// ========================================
// REAL-TIME VALIDATION FOR PHONE & EMAIL
// ========================================

// Phone number validation
const phoneInput = document.getElementById('id_phone');
if (phoneInput) {
  let phoneValidationTimeout = null;
  
  // Clear error message when user starts typing
  phoneInput.addEventListener('input', function() {
    // Remove validation error when user modifies the input
    removeFieldError(this);
    // Reset border color to neutral while typing
    this.style.borderColor = '#e5e7eb';
    this.style.borderWidth = '2px';
    this.style.borderStyle = 'solid';
  });
  
  phoneInput.addEventListener('blur', function() {
    const phoneNumber = this.value.trim();
    
    if (!phoneNumber) {
      return; // Don't validate empty input
    }
    
    // Clear previous timeout
    if (phoneValidationTimeout) {
      clearTimeout(phoneValidationTimeout);
    }
    
    // Debounce the validation call
    phoneValidationTimeout = setTimeout(() => {
      // Show validating state
      phoneInput.style.borderColor = '#f59e0b'; // Orange
      phoneInput.style.borderWidth = '2px';
      phoneInput.style.borderStyle = 'solid';
      
      fetch('/api/check-phone/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: `phone=${encodeURIComponent(phoneNumber)}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.available) {
          // Phone is available
          phoneInput.style.borderColor = '#059669'; // Green
          phoneInput.style.borderWidth = '2px';
          phoneInput.style.borderStyle = 'solid';
          removeFieldError(phoneInput);
        } else {
          // Phone is already taken
          phoneInput.style.borderColor = '#dc2626'; // Red
          phoneInput.style.borderWidth = '2px';
          phoneInput.style.borderStyle = 'solid';
          showFieldError(phoneInput, data.message || 'This phone number is already registered');
        }
      })
      .catch(error => {
        console.error('Phone validation error:', error);
        phoneInput.style.borderColor = ''; // Reset
      });
    }, 500); // Wait 500ms after user stops typing
  });
}

// Email validation
const emailInput = document.getElementById('id_email');
if (emailInput) {
  let emailValidationTimeout = null;
  
  // Clear error message when user starts typing
  emailInput.addEventListener('input', function() {
    // Remove validation error when user modifies the input
    removeFieldError(this);
    // Reset border color to neutral while typing
    this.style.borderColor = '#e5e7eb';
    this.style.borderWidth = '2px';
    this.style.borderStyle = 'solid';
  });
  
  emailInput.addEventListener('blur', function() {
    const email = this.value.trim();
    
    if (!email) {
      return; // Don't validate empty input
    }
    
    // Clear previous timeout
    if (emailValidationTimeout) {
      clearTimeout(emailValidationTimeout);
    }
    
    // Debounce the validation call
    emailValidationTimeout = setTimeout(() => {
      // Show validating state
      emailInput.style.borderColor = '#f59e0b'; // Orange
      emailInput.style.borderWidth = '2px';
      emailInput.style.borderStyle = 'solid';
      
      fetch('/api/check-email/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: `email=${encodeURIComponent(email)}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.available) {
          // Email is available
          emailInput.style.borderColor = '#059669'; // Green
          emailInput.style.borderWidth = '2px';
          emailInput.style.borderStyle = 'solid';
          removeFieldError(emailInput);
        } else {
          // Email is already taken
          emailInput.style.borderColor = '#dc2626'; // Red
          emailInput.style.borderWidth = '2px';
          emailInput.style.borderStyle = 'solid';
          showFieldError(emailInput, data.message || 'This email address is already registered');
        }
      })
      .catch(error => {
        console.error('Email validation error:', error);
        emailInput.style.borderColor = ''; // Reset
      });
    }, 500); // Wait 500ms after user stops typing
  });
}

// Helper function to show field-specific error message
function showFieldError(inputElement, message) {
  // Remove any existing error message
  removeFieldError(inputElement);
  
  // Create error message element
  const errorDiv = document.createElement('p');
  errorDiv.className = 'error-text field-validation-error';
  errorDiv.style.cssText = 'color: #dc2626; font-size: 0.875rem; margin-top: 0.25rem;';
  errorDiv.textContent = message;
  
  // Insert after the input element (inside the same container)
  inputElement.insertAdjacentElement('afterend', errorDiv);
}

// Helper function to remove field error message
function removeFieldError(inputElement) {
  // Look for error message that's a sibling of the input
  const nextElement = inputElement.nextElementSibling;
  if (nextElement && nextElement.classList.contains('field-validation-error')) {
    nextElement.remove();
  }
}

// ========================================
// PASSWORD TOGGLE FUNCTIONALITY
// ========================================

// Password toggle functionality
const togglePassword1 = document.getElementById('togglePassword1');
if (togglePassword1) {
  togglePassword1.addEventListener('click', function () {
    const passwordInput = document.getElementById('id_password1');
    const eyeIcon = document.getElementById('eyeIcon1');
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      eyeIcon.innerHTML = '<circle cx="12" cy="12" r="3"/><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><line x1="4" y1="4" x2="20" y2="20" stroke="#dc2626" stroke-width="2"/>';
    } else {
      passwordInput.type = 'password';
      eyeIcon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
    }
  });
}

const togglePassword2 = document.getElementById('togglePassword2');
if (togglePassword2) {
  togglePassword2.addEventListener('click', function () {
    const passwordInput = document.getElementById('id_password2');
    const eyeIcon = document.getElementById('eyeIcon2');
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      eyeIcon.innerHTML = '<circle cx="12" cy="12" r="3"/><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><line x1="4" y1="4" x2="20" y2="20" stroke="#dc2626" stroke-width="2"/>';
    } else {
      passwordInput.type = 'password';
      eyeIcon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
    }
  });
}

// Auto-uppercase family code input
const familyCodeInput = document.getElementById('id_family_code');
if (familyCodeInput) {
  familyCodeInput.addEventListener('input', function(e) {
    e.target.value = e.target.value.toUpperCase();
  });
}

// ========================================
// OTP VERIFICATION SYSTEM
// ========================================
let otpTimer = null;
let otpExpiryTime = null;

// Send OTP Button
const sendOtpBtn = document.getElementById('sendOtpBtn');
console.log('Send OTP Button:', sendOtpBtn);

if (sendOtpBtn) {
  sendOtpBtn.addEventListener('click', function() {
    console.log('=== Send OTP button clicked! ===');
    const phoneInput = document.getElementById('id_phone');
    const phoneNumber = phoneInput.value.trim();
    const sendOtpBtn = this;
  
    console.log('Phone number:', phoneNumber);
    console.log('CSRF Token:', window.CSRF_TOKEN);
  
  // Validate phone number
  if (!phoneNumber) {
    console.log('ERROR: Phone number is empty');
    showMessage('Please enter your phone number first', 'error');
    phoneInput.focus();
    return;
  }
  
  // Disable button and show loading
  sendOtpBtn.disabled = true;
  sendOtpBtn.textContent = 'Sending...';
  
  console.log('Sending OTP request to /otp/send/');
  
  // Send OTP via AJAX
  fetch('/otp/send/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': window.CSRF_TOKEN
    },
    body: `phone_number=${encodeURIComponent(phoneNumber)}`
  })
  .then(response => {
    console.log('Response status:', response.status);
    console.log('Response OK:', response.ok);
    return response.json();
  })
  .then(data => {
    console.log('Response data:', data);
    if (data.success) {
      console.log('OTP sent successfully!');
      // Show OTP verification section
      document.getElementById('otpVerificationSection').style.display = 'block';
      sendOtpBtn.textContent = 'OTP Sent';
      sendOtpBtn.style.background = '#059669';
      
      // Disable phone input to prevent changes
      phoneInput.readOnly = true;
      phoneInput.style.background = '#f3f4f6';
      
      // Start countdown timer
      startOtpTimer();
      
      showMessage('OTP sent successfully! Check your phone.', 'success');
      
      // Focus on OTP input
      document.getElementById('id_otp_code').focus();
    } else {
      console.log('OTP send failed:', data.error);
      sendOtpBtn.disabled = false;
      sendOtpBtn.textContent = 'Send OTP';
      showMessage(data.error || 'Failed to send OTP. Please try again.', 'error');
    }
  })
  .catch(error => {
    console.error('=== FETCH ERROR ===');
    console.error('Error type:', error.name);
    console.error('Error message:', error.message);
    console.error('Full error:', error);
    sendOtpBtn.disabled = false;
    sendOtpBtn.textContent = 'Send OTP';
    showMessage('Network error. Please check your connection.', 'error');
  });
  }); // End sendOtpBtn click handler
} else {
  console.error('Send OTP button not found!');
}

// Verify OTP Button
const verifyOtpBtn = document.getElementById('verifyOtpBtn');
if (verifyOtpBtn) {
  verifyOtpBtn.addEventListener('click', function() {
    const otpInput = document.getElementById('id_otp_code');
    const otpCode = otpInput.value.trim();
    const phoneNumber = document.getElementById('id_phone').value.trim();
    const verifyBtn = this;
  
  // Validate OTP code
  if (!otpCode || otpCode.length !== 6) {
    showMessage('Please enter the 6-digit OTP code', 'error');
    otpInput.focus();
    return;
  }
  
  // Disable button and show loading
  verifyBtn.disabled = true;
  verifyBtn.textContent = 'Verifying...';
  
  // Verify OTP via AJAX
  fetch('/otp/verify/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': window.CSRF_TOKEN
    },
    body: `phone_number=${encodeURIComponent(phoneNumber)}&otp=${encodeURIComponent(otpCode)}`
  })
  .then(response => {
    // Check if response is ok (status 200-299) or has JSON content
    if (!response.ok) {
      // For 400/401/403 etc, still try to parse JSON error message
      return response.json().then(data => {
        // Return error data but mark as failed
        return { success: false, error: data.error || 'Invalid OTP code. Please try again.' };
      }).catch(() => {
        // If JSON parsing fails, return generic error
        return { success: false, error: 'Invalid OTP code. Please try again.' };
      });
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      // Mark as verified
      document.getElementById('otp_verified').value = 'true';
      
      // Hide the entire OTP verification section
      document.getElementById('otpVerificationSection').style.display = 'none';
      
      // Update the Send OTP button to show "Verified" with checkmark
      const sendOtpBtn = document.getElementById('sendOtpBtn');
      sendOtpBtn.textContent = '✓ Verified';
      sendOtpBtn.style.background = '#059669';
      sendOtpBtn.disabled = true;
      
      // Add verified indicator to phone input
      const phoneInput = document.getElementById('id_phone');
      phoneInput.style.borderColor = '#059669';
      phoneInput.style.borderWidth = '2px';
      
      // Enable submit button only if email is also verified
      const emailVerified = document.getElementById('email_otp_verified') ? document.getElementById('email_otp_verified').value === 'true' : false;
      const submitBtn = document.getElementById('submitBtn');
      if (emailVerified) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
        const originalText = submitBtn.getAttribute('data-original-text');
        submitBtn.textContent = originalText || 'Join Family';
      }
      
      // Clear timer
      if (otpTimer) {
        clearInterval(otpTimer);
      }
      
      showMessage('Phone number verified successfully!', 'success');
    } else {
      verifyBtn.disabled = false;
      verifyBtn.textContent = 'Verify OTP';
      showMessage(data.error || 'Invalid OTP code. Please try again.', 'error');
    }
  })
  .catch(error => {
    console.error('Network Error:', error);
    verifyBtn.disabled = false;
    verifyBtn.textContent = 'Verify OTP';
    // Only show network error for actual network failures (not HTTP errors)
    showMessage('Network error. Please check your connection.', 'error');
  });
  });
} else {
  console.error('Verify OTP button not found!');
}

// Resend OTP Button
const resendOtpBtn = document.getElementById('resendOtpBtn');
if (resendOtpBtn) {
  resendOtpBtn.addEventListener('click', function() {
    const phoneNumber = document.getElementById('id_phone').value.trim();
    const resendBtn = this;
  
  resendBtn.disabled = true;
  resendBtn.textContent = 'Resending...';
  
  fetch('/otp/send/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': window.CSRF_TOKEN
    },
    body: `phone_number=${encodeURIComponent(phoneNumber)}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      resendBtn.disabled = false;
      resendBtn.textContent = 'Resend OTP';
      startOtpTimer();
      showMessage('OTP resent successfully!', 'success');
    } else {
      resendBtn.disabled = false;
      resendBtn.textContent = 'Resend OTP';
      showMessage(data.error || 'Failed to resend OTP.', 'error');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    resendBtn.disabled = false;
    resendBtn.textContent = 'Resend OTP';
    showMessage('Network error. Please check your connection.', 'error');
  });
  });
} else {
  console.error('Resend OTP button not found!');
}

// Start OTP expiry timer (5 minutes)
function startOtpTimer() {
  otpExpiryTime = Date.now() + (5 * 60 * 1000); // 5 minutes from now
  
  if (otpTimer) {
    clearInterval(otpTimer);
  }
  
  otpTimer = setInterval(function() {
    const remaining = otpExpiryTime - Date.now();
    
    if (remaining <= 0) {
      clearInterval(otpTimer);
      document.getElementById('otpTimer').textContent = 'OTP expired. Please resend.';
      document.getElementById('otpTimer').style.color = '#dc2626';
    } else {
      const minutes = Math.floor(remaining / 60000);
      const seconds = Math.floor((remaining % 60000) / 1000);
      document.getElementById('otpTimer').textContent = `OTP expires in ${minutes}:${seconds.toString().padStart(2, '0')}`;
      document.getElementById('otpTimer').style.color = '#059669';
    }
  }, 1000);
}

// Show message helper
function showMessage(message, type) {
  const statusDiv = document.getElementById('otpStatusMessage');
  statusDiv.innerHTML = `<p style="color: ${type === 'success' ? '#059669' : '#dc2626'}; font-weight: 600; font-size: 0.9rem;">${message}</p>`;
  
  // Clear message after 5 seconds
  setTimeout(() => {
    statusDiv.innerHTML = '';
  }, 5000);
}

// Form submission validation
const signupForm = document.querySelector('.signup-form');
if (signupForm) {
  const submitBtn = document.getElementById('submitBtn');
  if (submitBtn && submitBtn.textContent) {
    // Store original text
    submitBtn.setAttribute('data-original-text', submitBtn.textContent.replace(' (Verify Phone & Email First)', ''));
  }

  signupForm.addEventListener('submit', function(e) {
    const otpVerified = document.getElementById('otp_verified').value;
    const emailVerified = document.getElementById('email_otp_verified').value;
    
    if (otpVerified !== 'true') {
      e.preventDefault();
      showMessage('Please verify your phone number before joining.', 'error');
      document.getElementById('id_phone').scrollIntoView({ behavior: 'smooth' });
      return false;
    }
    
    if (emailVerified !== 'true') {
      e.preventDefault();
      showMessage('Please verify your email address before joining.', 'error');
      document.getElementById('id_email').scrollIntoView({ behavior: 'smooth' });
      return false;
    }
  });
}

}); // End DOMContentLoaded


