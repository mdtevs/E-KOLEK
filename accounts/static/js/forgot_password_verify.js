/**
 * Forgot Password Verify OTP JavaScript
 * Handles OTP input, validation, resend functionality
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
 * Update hidden OTP code input
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

  const loader = document.getElementById('loader');
  loader.style.display = 'flex';

  fetch(window.DJANGO_URLS.forgotPasswordResend, {
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
      alert('New verification code sent!');
      startTimer();
      
      // Clear inputs
      otpInputs.forEach(input => {
        input.value = '';
      });
      otpInputs[0].focus();
    } else {
      alert(data.error || 'Failed to resend code');
    }
  })
  .catch(error => {
    loader.style.display = 'none';
    alert('Error: Could not resend code');
    console.error('Error:', error);
  });
}

/**
 * Initialize OTP inputs
 */
function initOtpInputs() {
  // Auto-focus first input
  otpInputs[0].focus();

  otpInputs.forEach((input, index) => {
    // Handle input
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
        
        const lastFilledIndex = Math.min(digits.length - 1, otpInputs.length - 1);
        otpInputs[lastFilledIndex].focus();
      }
      
      updateOtpCode();
    });
  });
}

/**
 * Initialize form submission
 */
function initFormSubmission() {
  form.addEventListener('submit', (e) => {
    updateOtpCode();
    if (otpCodeInput.value.length !== 6) {
      e.preventDefault();
      alert('Please enter the complete 6-digit code');
    }
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
