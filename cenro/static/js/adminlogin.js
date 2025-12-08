/**
 * Admin Login Page JavaScript
 * Handles message deduplication, auto-dismissal, and form submission states
 */

/**
 * Remove duplicate admin management messages and handle message cleanup
 */
document.addEventListener('DOMContentLoaded', function() {
  removeDuplicateMessages();
  initLoginForm();
  autoDismissMessages();
});

/**
 * Auto-dismiss messages after they're shown once
 * This prevents confusion where old messages persist on page refresh
 */
function autoDismissMessages() {
  const alerts = document.querySelectorAll('.alert');
  
  alerts.forEach((alert) => {
    // Auto-remove after 5 seconds to prevent confusion on refresh
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s ease-out';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
}

/**
 * Remove duplicate alert messages and admin management messages
 */
function removeDuplicateMessages() {
  const alerts = document.querySelectorAll('.alert');
  const seenMessages = new Set();
  
  alerts.forEach((alert) => {
    const messageText = (alert.textContent || alert.innerText).trim();
    
    // Remove duplicate messages
    if (seenMessages.has(messageText)) {
      alert.remove();
      return;
    }
    seenMessages.add(messageText);
    
    // Remove messages that are admin management related (not login-specific)
    // These should never appear on the login page
    const adminPanelKeywords = [
      'Admin account "',              // "Admin account 'X' has been created/unlocked"
      'created successfully',          // Account creation success
      'Password reset email sent',     // Admin panel password reset action
      'has been unlocked',            // Admin unlocking another admin
      'has been reactivated',         // Admin reactivating another admin  
      'Updated barangay',             // Barangay assignment changes
      'barangay assignments for',     // Specific barangay assignment messages
      'now has access to all barangays', // Barangay access message
      'Barangay assignments updated',  // Generic barangay update
      'Family verified',              // Family verification action
      'User approved',                // User approval action
      'User rejected',                // User rejection action
      'Schedule notification',        // Schedule-related admin actions
      'Reward has been',              // Reward management actions
      'Content has been',             // Content management actions
      'Quiz has been',                // Quiz management actions
      'Notification sent to'          // Manual notification sending
    ];
    
    const isAdminPanelMessage = adminPanelKeywords.some(keyword => 
      messageText.includes(keyword)
    );
    
    if (isAdminPanelMessage) {
      alert.remove();
      return;
    }
  });
}

/**
 * Initialize login form submission handling
 */
function initLoginForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', function() {
    const btn = document.getElementById('loginBtn');
    const btnText = btn.querySelector('.btn-text');
    const loading = btn.querySelector('.loading');
    
    if (btnText && loading) {
      btnText.classList.add('hidden');
      loading.classList.add('active');
    }
    
    btn.disabled = true;
  });
  
  // Initialize password toggle
  initPasswordToggle();
}

/**
 * Initialize password visibility toggle
 */
function initPasswordToggle() {
  const passwordToggle = document.getElementById('passwordToggle');
  const passwordInput = document.getElementById('password');
  const toggleIcon = document.getElementById('toggleIcon');
  
  if (!passwordToggle || !passwordInput || !toggleIcon) return;
  
  passwordToggle.addEventListener('click', function() {
    const isPassword = passwordInput.type === 'password';
    
    // Toggle input type
    passwordInput.type = isPassword ? 'text' : 'password';
    
    // Toggle icon
    toggleIcon.classList.remove(isPassword ? 'bx-show' : 'bx-hide');
    toggleIcon.classList.add(isPassword ? 'bx-hide' : 'bx-show');
    
    // Update aria-label for accessibility
    passwordToggle.setAttribute('aria-label', 
      isPassword ? 'Hide password' : 'Show password'
    );
  });
}
