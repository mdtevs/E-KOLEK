/**
 * Verify OTP Page JavaScript
 * Handles OTP input, validation, resend functionality, and form submission
 */

// DOM Elements
const otpInputs = document.querySelectorAll('.otp-input');
const otpCodeInput = document.getElementById('otp_code');
const form = document.getElementById('otpForm');
const resendBtn = document.getElementById('resendBtn');
const timerText = document.getElementById('timerText');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Resend timer variables
let countdown = 60;
let timerInterval;

/**
 * Show message to user
 * @param {string} message - Message to display
 * @param {string} type - Message type ('error' or 'success')
 */
function showMessage(message, type) {
  const messageDiv = document.getElementById('dynamicMessage');
  
  // Set the appropriate class
  if (type === 'error') {
    messageDiv.className = 'error-message';
  } else {
    messageDiv.className = 'success-message';
  }
  
  messageDiv.textContent = message;
  messageDiv.style.display = 'block';
  
  // Scroll to message
  messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  
  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      hideMessage();
    }, 5000);
  }
}

/**
 * Hide message
 */
function hideMessage() {
  const messageDiv = document.getElementById('dynamicMessage');
  messageDiv.style.display = 'none';
}

/**
 * Update hidden OTP code input with current values
 */
function updateOtpCode() {
  const otp = Array.from(otpInputs).map(input => input.value).join('');
  otpCodeInput.value = otp;
}

/**
 * Start resend countdown timer
 */
function startTimer() {
  resendBtn.disabled = true;
  resendBtn.style.display = 'none';
  timerText.style.display = 'inline';
  countdown = 60;

  timerInterval = setInterval(() => {
    countdown--;
    timerText.textContent = `Resend in ${countdown}s`;

    if (countdown <= 0) {
      clearInterval(timerInterval);
      resendBtn.disabled = false;
      resendBtn.style.display = 'inline';
      timerText.style.display = 'none';
    }
  }, 1000);
}

/**
 * Resend OTP code
 */
function resendCode() {
  if (resendBtn.disabled) return;

  hideMessage();
  const loader = document.getElementById('loader');
  loader.style.display = 'flex';

  fetch(window.DJANGO_URLS.resendOtp, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({})
  })
  .then(response => response.json())
  .then(data => {
    loader.style.display = 'none';
    
    if (data.success) {
      showMessage('New verification code sent successfully!', 'success');
      startTimer();
      
      // Clear OTP inputs
      otpInputs.forEach(input => {
        input.value = '';
      });
      otpInputs[0].focus();
    } else {
      showMessage(data.error || 'Failed to resend code. Please try again.', 'error');
    }
  })
  .catch(error => {
    loader.style.display = 'none';
    showMessage('Network error. Please check your connection and try again.', 'error');
    console.error('Error:', error);
  });
}

/**
 * Initialize OTP input handlers
 */
function initOtpInputs() {
  // Auto-focus first input
  otpInputs[0].focus();

  otpInputs.forEach((input, index) => {
    // Handle input event
    input.addEventListener('input', (e) => {
      const value = e.target.value;
      
      // Only allow numbers
      if (value && !/^\d$/.test(value)) {
        e.target.value = '';
        return;
      }
      
      // Auto-focus next input
      if (value && index < otpInputs.length - 1) {
        otpInputs[index + 1].focus();
      }
      
      updateOtpCode();
    });

    // Handle backspace
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Backspace' && !e.target.value && index > 0) {
        otpInputs[index - 1].focus();
      }
    });

    // Handle paste
    input.addEventListener('paste', (e) => {
      e.preventDefault();
      const pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
      
      if (pastedData) {
        const digits = pastedData.split('').slice(0, 6);
        digits.forEach((digit, i) => {
          if (otpInputs[i]) {
            otpInputs[i].value = digit;
          }
        });
        
        // Focus last filled input or last input
        const lastFilledIndex = Math.min(digits.length - 1, otpInputs.length - 1);
        otpInputs[lastFilledIndex].focus();
      }
      
      updateOtpCode();
    });
  });
}

/**
 * Handle form submission
 */
function initFormSubmission() {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    updateOtpCode();
    
    if (otpCodeInput.value.length !== 6) {
      showMessage('Please enter a complete 6-digit code.', 'error');
      return;
    }

    hideMessage();
    const loader = document.getElementById('loader');
    loader.style.display = 'flex';

    // Get form data
    const formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      loader.style.display = 'none';
      
      if (data.success) {
        showMessage('Verification successful! Redirecting...', 'success');
        
        // Redirect after 1 second
        setTimeout(() => {
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            window.location.href = window.DJANGO_URLS.userDashboard;
          }
        }, 1000);
      } else {
        showMessage(data.error || 'Invalid verification code. Please try again.', 'error');
        
        // Clear inputs on error
        otpInputs.forEach(input => {
          input.value = '';
        });
        otpInputs[0].focus();
      }
    })
    .catch(error => {
      loader.style.display = 'none';
      showMessage('Network error. Please check your connection and try again.', 'error');
      console.error('Error:', error);
    });
  });
}

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
  initOtpInputs();
  initFormSubmission();
  startTimer();
});
