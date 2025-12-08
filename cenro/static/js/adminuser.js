
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
