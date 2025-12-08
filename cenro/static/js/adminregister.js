/**
 * Admin Registration Page JavaScript
 * Handles form submission and loading states for admin registration
 */

/**
 * Initialize registration form handling
 */
document.addEventListener('DOMContentLoaded', function() {
  initRegistrationForm();
});

/**
 * Initialize form submission handling with loading states
 */
function initRegistrationForm() {
  const form = document.getElementById('registerForm');
  if (!form) return;

  form.addEventListener('submit', function() {
    const btn = form.querySelector('.register-btn');
    const btnText = btn.querySelector('.btn-text');
    const loading = btn.querySelector('.loading');
    
    if (btnText && loading) {
      btnText.classList.add('hidden');
      loading.classList.add('active');
    }
    
    btn.disabled = true;
  });
}
