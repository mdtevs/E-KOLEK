
    // Helper function to get CSRF token from cookie
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }

    function showLeaderboardTab(tab) {
      var userTab = document.getElementById('userLeaderboard');
      var barangayTab = document.getElementById('barangayLeaderboard');
      var userBtn = document.getElementById('userLeaderboardTab');
      var barangayBtn = document.getElementById('barangayLeaderboardTab');
      console.log('showLeaderboardTab called:', tab, {userTab, barangayTab, userBtn, barangayBtn});
      if (!userTab || !barangayTab || !userBtn || !barangayBtn) return;
      try {
        if (tab === 'user') {
          userTab.style.display = '';
          barangayTab.style.display = 'none';
          userBtn.classList.add('active-tab');
          barangayBtn.classList.remove('active-tab');
        } else if (tab === 'barangay') {
          userTab.style.display = 'none';
          barangayTab.style.display = '';
          userBtn.classList.remove('active-tab');
          barangayBtn.classList.add('active-tab');
        }
      } catch (e) {
        console.error('showLeaderboardTab error:', e);
      }
    }
    
function showTab(tabId, event) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(tab => {
    if(tab.id === tabId) {
      tab.style.display = '';
      tab.classList.add('active');
    } else {
      tab.style.display = 'none';
      tab.classList.remove('active');
    }
  });
  // Remove active class from all tab buttons
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active-tab'));
  // Add active class to clicked tab button
  if(event && event.currentTarget) {
    var button = event.currentTarget;
    button.classList.add('active-tab');
    setTimeout(function() {
      button.blur();
      setTimeout(function(){}, 50);
    }, 10);
  }
  // If switching to leaderboard, show user leaderboard by default
  if(tabId === 'leaderboard') {
    // Delay to ensure DOM is updated and elements are present
    setTimeout(function() { showLeaderboardTab('user'); }, 120);
  }
  
  // If switching to notifications tab, mark them as viewed
  if(tabId === 'notifications') {
    markNotificationsAsViewed();
  }
}
    
document.addEventListener('DOMContentLoaded', function() {
  showTab('rewards', {currentTarget: document.querySelector('.tab-button')});
  // Add event listeners for leaderboard sub-tabs only after DOM is ready
  var userBtn = document.getElementById('userLeaderboardTab');
  var barangayBtn = document.getElementById('barangayLeaderboardTab');
  if (userBtn) userBtn.addEventListener('click', function() { showLeaderboardTab('user'); });
  if (barangayBtn) barangayBtn.addEventListener('click', function() { showLeaderboardTab('barangay'); });
});

    // Referral functionality
    function copyReferralCode() {
      const codeInput = document.getElementById('referralCodeDisplay');
      const copyBtn = document.querySelector('.copy-btn');
      
      codeInput.select();
      codeInput.setSelectionRange(0, 99999); // For mobile devices
      
      try {
        document.execCommand('copy');
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="bx bx-check"></i> Copied!';
        copyBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        
        setTimeout(() => {
          copyBtn.innerHTML = originalText;
          copyBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        }, 2000);
        
      } catch (err) {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy referral code. Please copy it manually.');
      }
    }

    function shareOnWhatsApp() {
      const referralCode = document.getElementById('referralCodeDisplay').value;
      const message = encodeURIComponent(`Hey! Join me on E-KOLEK, the waste management rewards platform! Use my referral code "${referralCode}" when you sign up and we both get 10 bonus points! 🌱♻️`);
      const whatsappUrl = `https://wa.me/?text=${message}`;
      window.open(whatsappUrl, '_blank');
    }

    function shareOnFacebook() {
      const referralCode = document.getElementById('referralCodeDisplay').value;
      const message = encodeURIComponent(`Join me on E-KOLEK! Use referral code: ${referralCode}`);
      const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.origin)}&quote=${message}`;
      window.open(facebookUrl, '_blank');
    }

    function shareGeneral() {
      const referralCode = document.getElementById('referralCodeDisplay').value;
      const shareText = `Hey! Join me on E-KOLEK, the waste management rewards platform! Use my referral code "${referralCode}" when you sign up and we both get 10 bonus points! 🌱♻️`;
      
      if (navigator.share) {
        navigator.share({
          title: 'Join E-KOLEK',
          text: shareText,
          url: window.location.origin
        }).catch(console.error);
      } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(shareText).then(() => {
          alert('Referral message copied to clipboard!');
        }).catch(() => {
          alert(`Share this message: ${shareText}`);
        });
      }
    }

    // Redemption Modal Functions
    function openRedeemModal(rewardName, rewardPoints) {
      const modal = document.getElementById('redeemModal');
      const modalRewardName = document.getElementById('modalRewardName');
      const modalRewardPoints = document.getElementById('modalRewardPoints');
      
      // Update modal content with reward details
      if (modalRewardName) modalRewardName.textContent = rewardName;
      if (modalRewardPoints) modalRewardPoints.textContent = `${rewardPoints} points required`;
      
      // Show modal with animation
      if (modal) {
        modal.style.display = 'flex';
        // Force reflow for animation
        modal.offsetHeight;
        modal.classList.add('show');
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
      }
    }

    function closeRedeemModal() {
      const modal = document.getElementById('redeemModal');
      
      if (modal) {
        modal.classList.remove('show');
        // Wait for fade out animation before hiding
        setTimeout(() => {
          modal.style.display = 'none';
          document.body.style.overflow = '';
        }, 300);
      }
    }

    // Close modal when clicking outside
    document.addEventListener('click', function(event) {
      const modal = document.getElementById('redeemModal');
      if (event.target === modal) {
        closeRedeemModal();
      }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        closeRedeemModal();
      }
    });

    // ========================================
    // NOTIFICATION SYSTEM
    // ========================================

    /**
     * Mark all unviewed notifications as viewed when user opens the notifications tab
     */
    function markNotificationsAsViewed() {
      // Check if there are any new notifications
      const newNotifications = document.querySelectorAll('.notification-card.notification-new');
      
      if (newNotifications.length === 0) {
        return; // No new notifications to mark
      }

      // Get CSRF token from cookie
      const csrfToken = getCookie('csrftoken');

      // Send API request to mark notifications as viewed
      fetch('/api/notifications/mark-viewed/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin'
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Remove "new" styling from all notification cards
          newNotifications.forEach(card => {
            card.classList.remove('notification-new');
            
            // Remove the "New" label
            const newLabel = card.querySelector('.new-label');
            if (newLabel) {
              newLabel.style.animation = 'fadeOut 0.3s ease';
              setTimeout(() => newLabel.remove(), 300);
            }
          });

          // Update the notification badge on the tab
          const notificationBadge = document.getElementById('notificationBadge');
          if (notificationBadge) {
            notificationBadge.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notificationBadge.remove(), 300);
          }

          // Update the badge text in the section header
          const badgeText = document.getElementById('notificationsBadgeText');
          if (badgeText) {
            badgeText.textContent = 'No New';
          }

          console.log(`${data.updated_count} notifications marked as viewed`);
        }
      })
      .catch(error => {
        console.error('Error marking notifications as viewed:', error);
      });
    }

    /**
     * Periodically check for new notifications (optional - for real-time updates)
     */
    function checkForNewNotifications() {
      fetch('/api/notifications/unread-count/', {
        method: 'GET',
        credentials: 'same-origin'
      })
      .then(response => response.json())
      .then(data => {
        if (data.success && data.unread_count > 0) {
          // Update badge if it doesn't exist
          let badge = document.getElementById('notificationBadge');
          if (!badge && data.unread_count > 0) {
            const notificationTab = document.querySelector('[onclick*="notifications"]');
            if (notificationTab) {
              const iconText = notificationTab.querySelector('.tab-icon-text');
              if (iconText) {
                badge = document.createElement('span');
                badge.id = 'notificationBadge';
                badge.className = 'notification-badge';
                badge.textContent = data.unread_count;
                iconText.appendChild(badge);
              }
            }
          } else if (badge) {
            badge.textContent = data.unread_count;
          }
        }
      })
      .catch(error => {
        console.error('Error checking for new notifications:', error);
      });
    }

    // Store notification check interval ID if enabled
    let notificationCheckInterval = null;
    
    // Check for new notifications every 60 seconds (optional)
    // Uncomment the line below if you want real-time notification updates
    // notificationCheckInterval = setInterval(checkForNewNotifications, 60000);

    /**
     * Prepare for logout - stop all background tasks
     * This prevents 401 errors after logout
     */
    window.prepareLogout = function(event) {
      // Clear notification polling interval if active
      if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
        notificationCheckInterval = null;
        console.log('Stopped notification polling before logout');
      }
      
      // Clear any other intervals or pending requests
      // This prevents API calls after logout
      
      // Let the form submit naturally
      return true;
    };

    // Add fadeOut animation to CSS dynamically
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.8); }
      }
    `;
    document.head.appendChild(style);
