// Notification helper functions
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3); z-index: 9999;
        display: flex; align-items: center; gap: 12px; font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `<i class='bx bx-check-circle' style="font-size: 1.5rem;"></i><span>${message}</span>`;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3); z-index: 9999;
        display: flex; align-items: center; gap: 12px; font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `<i class='bx bx-error-circle' style="font-size: 1.5rem;"></i><span>${message}</span>`;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

	function openAddRewardModal() {
		document.getElementById("addRewardModal").style.display = "flex";
	}

	function closeAddRewardModal() {
		document.getElementById("addRewardModal").style.display = "none";
	}

// Wait for DOM to be ready before attaching event listeners
window.addEventListener('DOMContentLoaded', function() {
	// Handle add reward form submission
	document.getElementById("addRewardForm").addEventListener("submit", function(e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'add', 'Reward', function() {
    const form = document.getElementById("addRewardForm");
    const submitBtn = document.getElementById('addRewardSubmitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const progress = document.getElementById('addRewardProgress');
    const progressBar = document.getElementById('addRewardProgressBar');
    const progressText = document.getElementById('addRewardProgressText');
    const fileInput = document.getElementById('rewardImage');
    
    // Check if image is selected
    const hasImage = fileInput.files.length > 0;
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline-block';
    submitBtn.disabled = true;
    
    // Show progress if uploading image
    if (hasImage) {
      progress.classList.add('active');
      progressText.style.display = 'block';
      progressText.textContent = 'Uploading to Google Drive...';
      progressText.style.color = '#6b7280';
      
      // Simulate progress for Google Drive upload
      let progressValue = 0;
      const progressInterval = setInterval(() => {
        progressValue += Math.random() * 15;
        if (progressValue > 90) progressValue = 90;
        progressBar.style.width = progressValue + '%';
      }, 200);
    }
    
    const data = new FormData(form);
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.addReward, {
      method: "POST",
      body: data
    })
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      if (hasImage) {
        progressBar.style.width = '100%';
        setTimeout(() => {
          clearInterval(progressInterval);
        }, 100);
      }
      
      if (data.success) {
        closeAddRewardModal();
        showSuccessNotification('Product added successfully!');
        setTimeout(() => location.reload(), 1500);
      } else {
        showErrorNotification('Error adding reward: ' + (data.error || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('Error adding reward:', error);
      showErrorNotification('Error adding reward: ' + error.message);
    })
    .finally(() => {
      // Reset button state
      btnText.style.display = 'inline-block';
      btnLoading.style.display = 'none';
      submitBtn.disabled = false;
      
      // Reset progress
      if (hasImage) {
        setTimeout(() => {
          progress.classList.remove('active');
          progressText.style.display = 'none';
          progressBar.style.width = '0%';
        }, 1000);
      }
    });
  });
});

// Add Stock Form Handler
document.getElementById("addStockForm").addEventListener("submit", function(e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'stock-add', 'Stock', function() {
    const form = document.getElementById("addStockForm");
    const data = new FormData(form);
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.addStock, {
      method: "POST",
      body: data
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        closeAddStockModal();
        showSuccessNotification('Stock added successfully!');
        setTimeout(() => location.reload(), 1500);
      } else {
        showErrorNotification(data.error || 'Failed to add stock');
      }
    });
  });
});

// Remove Stock Form Handler
document.getElementById("removeStockForm").addEventListener("submit", function(e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'stock-remove', 'Stock', function() {
    const form = document.getElementById("removeStockForm");
    const data = new FormData(form);
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.removeStock, {
      method: "POST",
      body: data
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        closeRemoveStockModal();
        showSuccessNotification('Stock removed successfully!');
        setTimeout(() => location.reload(), 1500);
      } else {
        showErrorNotification(data.error || 'Failed to remove stock');
      }
    });
  });
});

  // Handle edit reward form submission
  document.getElementById("editRewardForm").addEventListener("submit", function(e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'update', 'Reward', function() {
    const form = document.getElementById("editRewardForm");
    const submitBtn = document.getElementById('editRewardSubmitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const progress = document.getElementById('editRewardProgress');
    const progressBar = document.getElementById('editRewardProgressBar');
    const progressText = document.getElementById('editRewardProgressText');
    const fileInput = document.getElementById('editRewardImage');
    
    // Check if new image is selected
    const hasNewImage = fileInput.files.length > 0;
  
  // Show loading state
  btnText.style.display = 'none';
  btnLoading.style.display = 'inline-block';
  submitBtn.disabled = true;
  
  // Show progress if uploading new image
  if (hasNewImage) {
    progress.classList.add('active');
    progressText.style.display = 'block';
    progressText.textContent = 'Uploading to Google Drive...';
    progressText.style.color = '#6b7280';
    
    // Simulate progress for Google Drive upload
    let progressValue = 0;
    const progressInterval = setInterval(() => {
      progressValue += Math.random() * 15;
      if (progressValue > 90) progressValue = 90;
      progressBar.style.width = progressValue + '%';
    }, 200);
  }
  
  const data = new FormData(form);
  data.append('id', document.getElementById("editRewardId").value);
  
  AdminUtils.fetchWithCSRF(window.DJANGO_URLS.editReward, {
    method: "POST",
    body: data
  })
  .then(res => res.json())
  .then(data => {
    if (hasNewImage) {
      progressBar.style.width = '100%';
      setTimeout(() => {
        clearInterval(progressInterval);
      }, 100);
    }
    
    if (data.success) {
      closeEditRewardModal();
      showSuccessNotification('Product updated successfully!');
      setTimeout(() => location.reload(), 1500);
    } else {
      showErrorNotification('Error updating reward: ' + (data.error || 'Unknown error'));
    }
  })
  .catch(error => {
    showErrorNotification('Error updating reward. Please try again.');
  })
  .finally(() => {
    // Reset button state
    btnText.style.display = 'inline-block';
    btnLoading.style.display = 'none';
    submitBtn.disabled = false;
    
    // Reset progress
    if (hasNewImage) {
      setTimeout(() => {
        progress.classList.remove('active');
        progressText.style.display = 'none';
        progressBar.style.width = '0%';
      }, 1000);
    }
  });
  });
});

  // Check for success message from localStorage
  const msg = localStorage.getItem('successMessage');
  if (msg) {
    showSuccessMessage(msg);
    localStorage.removeItem('successMessage');
  }
  
  // Add file input change listeners for better UX
  document.getElementById('rewardImage').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const progressText = document.getElementById('addRewardProgressText');
    if (file) {
      progressText.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
      progressText.style.display = 'block';
      progressText.style.color = '#10b981';
    } else {
      progressText.style.display = 'none';
    }
  });
  
  document.getElementById('editRewardImage').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const progressText = document.getElementById('editRewardProgressText');
    if (file) {
      progressText.textContent = `Selected: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
      progressText.style.display = 'block';
      progressText.style.color = '#10b981';
    } else {
      progressText.style.display = 'none';
    }
  });
}); // End DOMContentLoaded

// Global helper functions - must be outside DOMContentLoaded to be called from HTML
let rewardToDelete = null;

function openEditRewardModal(id, name, category, points, description, image_url) {
  document.getElementById('editRewardId').value = id;
  document.getElementById('editRewardName').value = name;
  document.getElementById('editRewardCategory').value = category;
  
  // Format points to remove unnecessary decimals (e.g., 3.00 → 3, 3.50 → 3.5)
  const formattedPoints = window.formatPointsDisplay ? window.formatPointsDisplay(points) : points;
  document.getElementById('editRewardPoints').value = formattedPoints;
  
  document.getElementById('editRewardDescription').value = description;
  
  // Show current image preview if image exists
  const imagePreview = document.getElementById('editCurrentImagePreview');
  const currentImage = document.getElementById('editCurrentImage');
  
  if (image_url && image_url !== 'None' && image_url !== '') {
    currentImage.src = image_url;
    imagePreview.style.display = 'block';
  } else {
    imagePreview.style.display = 'none';
  }
  
  // Reset the file input and progress indicators
  document.getElementById('editRewardImage').value = '';
  const progressText = document.getElementById('editRewardProgressText');
  const progress = document.getElementById('editRewardProgress');
  if (progressText) progressText.style.display = 'none';
  if (progress) progress.classList.remove('active');
  
  document.getElementById('editRewardModal').style.display = 'flex';
}

function closeEditRewardModal() {
  document.getElementById('editRewardModal').style.display = 'none';
}

function openAddStockModal() {
  document.getElementById('addStockModal').style.display = 'flex';
}

function closeAddStockModal() {
  document.getElementById('addStockModal').style.display = 'none';
}

function openRemoveStockModal() {
  document.getElementById('removeStockModal').style.display = 'flex';
}

function closeRemoveStockModal() {
  document.getElementById('removeStockModal').style.display = 'none';
}

function openDeleteRewardModal(id) {
  rewardToDelete = id;
  document.getElementById("deleteRewardModal").style.display = "flex";
}

function closeDeleteRewardModal() {
  document.getElementById("deleteRewardModal").style.display = "none";
}

function confirmDeleteReward() {
  AdminUtils.fetchWithCSRF(window.DJANGO_URLS.deleteReward, {
    method: "POST",
    body: new URLSearchParams({id: rewardToDelete})
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      closeDeleteRewardModal();
      showSuccessNotification('Product deleted successfully!');
      setTimeout(() => location.reload(), 1500);
    } else {
      showErrorNotification(data.error || 'Failed to delete reward');
    }
  });
}

function showSuccessMessage(msg) {
  const box = document.getElementById('successMessage');
  box.textContent = msg;
  box.style.display = 'block';
  setTimeout(() => {
    box.style.display = 'none';
  }, 1000);
}
	