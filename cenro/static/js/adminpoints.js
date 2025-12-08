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

let html5QrCode;

// ✅ Start QR Scanner
function startQrScanner() {
  const scannerBox = document.getElementById('scanner-box');
  scannerBox.innerHTML = "";

  if (html5QrCode) {
    html5QrCode.stop().catch(() => {});
  }

  html5QrCode = new Html5Qrcode("scanner-box");
  html5QrCode.start(
    { facingMode: "environment" },
    { fps: 10, qrbox: 200 },
    qrCodeMessage => {
      html5QrCode.stop();
      fetchUserDetails(qrCodeMessage); // Now expecting user ID instead of family code
    }
  ).catch(err => {
    scannerBox.innerHTML = "Unable to start scanner: " + err;
  });
}

function openTab(evt, tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

  document.getElementById(tabId).style.display = 'block';
  evt.currentTarget.classList.add('active');
  
  // Save tab state for persistence
  if (window.TabPersistence) {
    window.TabPersistence.saveTabState(tabId);
  }
}

// Initialize tab persistence on page load
document.addEventListener('DOMContentLoaded', function() {
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-btn',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
});

// Auto-update points for redeem rewards
document.getElementById('rewardSelect')?.addEventListener('change', function(){
  document.getElementById('requiredPoints').value = this.options[this.selectedIndex].dataset.points;
});

// ✅ Fetch User Details by User ID
function fetchUserDetails(userId) {
  fetch(window.DJANGO_URLS.getUserById + `?id=${userId}`)
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        showErrorNotification("User not found!");
      } else {
        // Populate waste transaction form
        document.getElementById('userName').value = data.name || '';
        document.getElementById('familyCode').value = data.family_code || '';
        document.getElementById('userId').value = data.user_id || '';

        // Populate reward redemption form
        document.getElementById('redeemUserName').value = data.name || '';
        document.getElementById('redeemFamilyCode').value = data.family_code || '';
        document.getElementById('redeemUserId').value = data.user_id || '';
      }
    })
    .catch(err => console.error("Fetch error:", err));
}

// ✅ Auto Compute Points
function computePoints() {
  const wasteTypeSelect = document.getElementById('wasteType');
  const wasteKg = parseFloat(document.getElementById('wasteKg').value) || 0;
  const pointsPerKg = parseInt(
    wasteTypeSelect.selectedOptions[0]?.getAttribute('data-points')
  ) || 0;
  document.getElementById('totalPoints').value = wasteKg * pointsPerKg;
}
document.getElementById('wasteType').addEventListener('change', computePoints);
document.getElementById('wasteKg').addEventListener('input', computePoints);

// ✅ Save Waste Transaction
document.getElementById('wasteForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  showConfirmation(e, 'add', 'Waste Transaction', () => {
    const formData = new FormData(document.getElementById('wasteForm'));
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.saveWasteTransaction, {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      showSuccessNotification(data.message || 'Transaction saved!');
      document.getElementById('wasteForm').reset();
      document.getElementById('totalPoints').value = '';
    })
    .catch(err => {
      console.error("Error saving transaction:", err);
      showErrorNotification('Failed to save transaction');
    });
  });
});

// ✅ Auto Update Points Required (already included but keeping for safety)
document.getElementById('rewardSelect')?.addEventListener('change', function(){
  document.getElementById('requiredPoints').value = this.options[this.selectedIndex].dataset.points;
});

// ✅ Redeem Rewards Submit
document.getElementById('redeemForm').addEventListener('submit', function(e) {
  e.preventDefault();
  
  showConfirmation(e, 'add', 'Reward Redemption', () => {
    const formData = new FormData(document.getElementById('redeemForm'));
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.redeemReward, {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        showErrorNotification(data.error);
      } else {
        showSuccessNotification(data.message);
        document.getElementById('redeemForm').reset();
        document.getElementById('requiredPoints').value = '';
      }
    })
    .catch(err => {
      console.error("Error redeeming reward:", err);
      showErrorNotification('Failed to redeem reward');
    });
  });
});


