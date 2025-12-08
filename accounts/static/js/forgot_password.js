/**
 * Forgot Password Page JavaScript
 * Handles method selection (SMS/Email)
 */

/**
 * Select OTP method
 * @param {string} method - 'sms' or 'email'
 */
function selectMethod(method) {
  const smsBtn = document.getElementById('smsMethod');
  const emailBtn = document.getElementById('emailMethod');
  const methodInput = document.getElementById('otp_method');

  if (method === 'sms') {
    smsBtn.classList.add('active');
    emailBtn.classList.remove('active');
    methodInput.value = 'sms';
  } else {
    emailBtn.classList.add('active');
    smsBtn.classList.remove('active');
    methodInput.value = 'email';
  }
}
