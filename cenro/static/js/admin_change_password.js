/**
 * Admin Change Password Page JavaScript
 * Handles password validation and strength indicator for admin password changes
 */

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

/**
 * Initialize password form validation
 */
document.addEventListener('DOMContentLoaded', function() {
  initPasswordForm();
  initPasswordStrength();
});

/**
 * Initialize form submission validation
 */
function initPasswordForm() {
  const form = document.getElementById('passwordForm');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const currentPassword = document.getElementById('current_password').value;

    // Check if passwords match
    if (newPassword !== confirmPassword) {
      e.preventDefault();
      showErrorNotification('New passwords do not match!');
      return false;
    }

    // Check if new password is different from current
    if (newPassword === currentPassword) {
      e.preventDefault();
      showErrorNotification('New password must be different from current password!');
      return false;
    }

    // Check minimum length
    if (newPassword.length < 8) {
      e.preventDefault();
      showErrorNotification('Password must be at least 8 characters long!');
      return false;
    }
  });
}

/**
 * Initialize password strength indicator
 */
function initPasswordStrength() {
  const newPasswordInput = document.getElementById('new_password');
  if (!newPasswordInput) return;

  newPasswordInput.addEventListener('input', function() {
    const password = this.value;
    const strength = calculatePasswordStrength(password);
    
    // Can be extended to show visual strength indicator
    // For example: updateStrengthIndicator(strength);
  });
}

/**
 * Calculate password strength
 * @param {string} password - The password to evaluate
 * @returns {number} - Strength score (0-5)
 */
function calculatePasswordStrength(password) {
  let strength = 0;
  
  if (password.length >= 8) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[a-z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;
  
  return strength;
}

/**
 * Optional: Update visual strength indicator
 * @param {number} strength - Strength score (0-5)
 */
function updateStrengthIndicator(strength) {
  // Can be implemented to show visual feedback
  // Example: change color of a progress bar or text
  const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#20c997'];
  
  // Use these to update UI if needed
}
