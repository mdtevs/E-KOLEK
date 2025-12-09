/**
 * Email OTP Verification JavaScript
 * Version 1.0
 * Handles email verification with OTP similar to phone verification
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Email OTP Verification System
  let emailOtpTimer = null;
  let emailOtpExpiryTime = null;

  // Send Email OTP Button
  const sendEmailOtpBtn = document.getElementById('sendEmailOtpBtn');

  if (sendEmailOtpBtn) {
    sendEmailOtpBtn.addEventListener('click', function() {
      const emailInput = document.getElementById('id_email');
      const email = emailInput.value.trim();
      const sendBtn = this;
    
      // Validate email
      if (!email) {
        showEmailMessage('Please enter your email address first', 'error');
        emailInput.focus();
        return;
      }
    
      // Basic email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showEmailMessage('Please enter a valid email address', 'error');
        emailInput.focus();
        return;
      }
    
      // Disable button and show loading
      sendBtn.disabled = true;
      sendBtn.textContent = 'Sending...';
    
      // Send email OTP via AJAX
      fetch('/email-otp/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: `email=${encodeURIComponent(email)}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Show OTP verification section
          document.getElementById('emailOtpVerificationSection').style.display = 'block';
          sendBtn.textContent = 'OTP Sent';
          sendBtn.style.background = '#059669';
        
          // Keep email input editable - add warning styling
          emailInput.style.background = '#fef3c7'; // Light yellow background
          emailInput.style.borderColor = '#f59e0b';
        
          // Add change listener to reset OTP state if email is modified
          emailInput.addEventListener('input', function resetEmailOtpState() {
            // Reset verification state
            document.getElementById('email_otp_verified').value = 'false';
            document.getElementById('emailOtpVerificationSection').style.display = 'none';
            document.getElementById('id_email_otp_code').value = '';
            sendBtn.textContent = 'Send OTP';
            sendBtn.style.background = '#6366f1';
            sendBtn.disabled = false;
            emailInput.style.background = '';
            emailInput.style.borderColor = '#e5e7eb';
            updateSubmitButtonState();
            showEmailMessage('Email address changed. Please send OTP again.', 'warning');
            // Remove this listener after first trigger
            emailInput.removeEventListener('input', resetEmailOtpState);
          }, { once: true });
        
          // Start countdown timer
          startEmailOtpTimer();
        
          showEmailMessage('OTP sent to your email! Check your inbox.', 'success');
        
          // Focus on OTP input
          document.getElementById('id_email_otp_code').focus();
        } else {
          sendBtn.disabled = false;
          sendBtn.textContent = 'Send OTP';
          showEmailMessage(data.error || 'Failed to send OTP. Please try again.', 'error');
        }
      })
      .catch(error => {
        console.error('Email OTP send error:', error);
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send OTP';
        showEmailMessage('Network error. Please check your connection.', 'error');
      });
    });
  }

  // Verify Email OTP Button
  const verifyEmailOtpBtn = document.getElementById('verifyEmailOtpBtn');
  if (verifyEmailOtpBtn) {
    verifyEmailOtpBtn.addEventListener('click', function() {
      const otpInput = document.getElementById('id_email_otp_code');
      const otpCode = otpInput.value.trim();
      const email = document.getElementById('id_email').value.trim();
      const verifyBtn = this;
    
      // Validate OTP code
      if (!otpCode || otpCode.length !== 6) {
        showEmailMessage('Please enter the 6-digit OTP code', 'error');
        otpInput.focus();
        return;
      }
    
      // Disable button and show loading
      verifyBtn.disabled = true;
      verifyBtn.textContent = 'Verifying...';
    
      // Verify OTP via AJAX
      fetch('/email-otp/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: `email=${encodeURIComponent(email)}&otp=${encodeURIComponent(otpCode)}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Mark as verified
          document.getElementById('email_otp_verified').value = 'true';
        
          // Hide the entire email OTP verification section
          document.getElementById('emailOtpVerificationSection').style.display = 'none';
        
          // Update the Send OTP button to show "Verified" with checkmark
          const sendEmailOtpBtn = document.getElementById('sendEmailOtpBtn');
          sendEmailOtpBtn.textContent = '✓ Verified';
          sendEmailOtpBtn.style.background = '#059669';
          sendEmailOtpBtn.disabled = true;
        
          // Add verified indicator to email input
          const emailInput = document.getElementById('id_email');
          emailInput.style.borderColor = '#059669';
          emailInput.style.borderWidth = '2px';
        
          // Check if both phone and email are verified before enabling submit
          checkBothVerifications();
        
          // Clear timer
          if (emailOtpTimer) {
            clearInterval(emailOtpTimer);
          }
        
          showEmailMessage('Email verified successfully!', 'success');
        } else {
          verifyBtn.disabled = false;
          verifyBtn.textContent = 'Verify OTP';
          showEmailMessage(data.error || 'Invalid OTP code. Please try again.', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verify OTP';
        showEmailMessage('Network error. Please check your connection.', 'error');
      });
    });
  } else {
    console.error('Verify Email OTP button not found!');
  }

  // Resend Email OTP Button
  const resendEmailOtpBtn = document.getElementById('resendEmailOtpBtn');
  if (resendEmailOtpBtn) {
    resendEmailOtpBtn.addEventListener('click', function() {
      const email = document.getElementById('id_email').value.trim();
      const resendBtn = this;
    
      resendBtn.disabled = true;
      resendBtn.textContent = 'Resending...';
    
      fetch('/email-otp/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': window.CSRF_TOKEN
        },
        body: `email=${encodeURIComponent(email)}`
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          resendBtn.disabled = false;
          resendBtn.textContent = 'Resend OTP';
          startEmailOtpTimer();
          showEmailMessage('OTP resent successfully!', 'success');
        } else {
          resendBtn.disabled = false;
          resendBtn.textContent = 'Resend OTP';
          showEmailMessage(data.error || 'Failed to resend OTP.', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        resendBtn.disabled = false;
        resendBtn.textContent = 'Resend OTP';
        showEmailMessage('Network error. Please check your connection.', 'error');
      });
    });
  } else {
    console.error('Resend Email OTP button not found!');
  }

  // Start email OTP expiry timer (5 minutes)
  function startEmailOtpTimer() {
    emailOtpExpiryTime = Date.now() + (5 * 60 * 1000); // 5 minutes from now
  
    if (emailOtpTimer) {
      clearInterval(emailOtpTimer);
    }
  
    emailOtpTimer = setInterval(function() {
      const remaining = emailOtpExpiryTime - Date.now();
    
      if (remaining <= 0) {
        clearInterval(emailOtpTimer);
        document.getElementById('emailOtpTimer').textContent = 'OTP expired. Please resend.';
        document.getElementById('emailOtpTimer').style.color = '#dc2626';
      } else {
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        document.getElementById('emailOtpTimer').textContent = `OTP expires in ${minutes}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('emailOtpTimer').style.color = '#059669';
      }
    }, 1000);
  }

  // Show email message helper
  function showEmailMessage(message, type) {
    const statusDiv = document.getElementById('emailOtpStatusMessage');
    const colors = {
      success: '#059669',
      error: '#dc2626',
      warning: '#f59e0b'
    };
    statusDiv.innerHTML = `<p style="color: ${colors[type] || colors.error}; font-weight: 600; font-size: 0.9rem;">${message}</p>`;
    
    // Clear message after 5 seconds
    setTimeout(() => {
      statusDiv.innerHTML = '';
    }, 5000);
  }  // Check if both phone and email are verified
  function checkBothVerifications() {
    const phoneVerified = document.getElementById('otp_verified').value === 'true';
    const emailVerified = document.getElementById('email_otp_verified').value === 'true';
  
    const submitBtn = document.getElementById('submitBtn');
    if (phoneVerified && emailVerified) {
      submitBtn.disabled = false;
      submitBtn.style.opacity = '1';
      submitBtn.style.cursor = 'pointer';
      submitBtn.textContent = submitBtn.getAttribute('data-original-text') || 'Register';
    }
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
      const phoneVerified = document.getElementById('otp_verified').value;
      const emailVerified = document.getElementById('email_otp_verified').value;
    
      if (phoneVerified !== 'true') {
        e.preventDefault();
        showEmailMessage('Please verify your phone number before registering.', 'error');
        document.getElementById('id_phone').scrollIntoView({ behavior: 'smooth' });
        return false;
      }
    
      if (emailVerified !== 'true') {
        e.preventDefault();
        showEmailMessage('Please verify your email address before registering.', 'error');
        document.getElementById('id_email').scrollIntoView({ behavior: 'smooth' });
        return false;
      }
    });
  }

}); // End DOMContentLoaded
