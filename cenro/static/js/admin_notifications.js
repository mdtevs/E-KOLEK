/**
 * Admin Notification System JavaScript
 * Handles notification bell functionality, dropdown, badge updates, and marking notifications as read
 */

(function() {
    'use strict';

    // Configuration
    const REFRESH_INTERVAL = 30000; // Refresh notifications every 30 seconds
    let refreshTimer = null;

    // DOM Elements
    let bellBtn, badge, dropdown, notificationList, loading, empty, markAllReadBtn;

    // State
    let isDropdownOpen = false;
    let currentNotifications = [];

    /**
     * Initialize notification system when DOM is ready
     */
    function init() {
        // Get DOM elements
        bellBtn = document.getElementById('adminNotificationBell');
        badge = document.getElementById('adminNotificationBadge');
        dropdown = document.getElementById('adminNotificationDropdown');
        notificationList = document.getElementById('adminNotificationList');
        loading = document.getElementById('notificationLoading');
        empty = document.getElementById('notificationEmpty');
        markAllReadBtn = document.getElementById('markAllReadBtn');

        if (!bellBtn || !badge || !dropdown) {
            console.warn('Admin notification elements not found');
            return;
        }

        // Attach event listeners
        bellBtn.addEventListener('click', toggleDropdown);
        markAllReadBtn.addEventListener('click', markAllAsRead);
        
        // Close dropdown when clicking outside
        document.addEventListener('click', handleOutsideClick);

        // Initial load
        loadNotifications();
        updateUnreadCount();

        // Set up auto-refresh
        startAutoRefresh();
    }

    /**
     * Toggle notification dropdown visibility
     */
    function toggleDropdown(e) {
        e.stopPropagation();
        
        if (isDropdownOpen) {
            closeDropdown();
        } else {
            openDropdown();
        }
    }

    /**
     * Open notification dropdown
     */
    async function openDropdown() {
        dropdown.style.display = 'block';
        isDropdownOpen = true;
        loadNotifications(); // Refresh when opening
        
        // Mark all notifications as read when dropdown is opened
        await markAllAsReadOnView();
    }

    /**
     * Close notification dropdown
     */
    function closeDropdown() {
        dropdown.style.display = 'none';
        isDropdownOpen = false;
    }

    /**
     * Handle clicks outside dropdown to close it
     */
    function handleOutsideClick(e) {
        if (isDropdownOpen && !dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
            closeDropdown();
        }
    }

    /**
     * Load notifications from API
     */
    async function loadNotifications() {
        try {
            // Show loading state
            if (loading) loading.style.display = 'block';
            if (empty) empty.style.display = 'none';
            
            const response = await fetch('/cenro/api/notifications/list/', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // Handle 401 - admin logged out or session expired
            if (response.status === 401) {
                console.log('Admin session expired - stopping notification polling');
                stopAutoRefresh(); // Stop polling
                closeDropdown(); // Close dropdown if open
                // Silently fail - admin will be redirected by other mechanisms
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (loading) loading.style.display = 'none';
            
            if (data.notifications && data.notifications.length > 0) {
                currentNotifications = data.notifications;
                renderNotifications(data.notifications);
            } else {
                // Show empty state
                if (empty) empty.style.display = 'block';
                // Clear notification list content except loading and empty divs
                const items = notificationList.querySelectorAll('.notification-item');
                items.forEach(item => item.remove());
            }

        } catch (error) {
            console.error('Error loading notifications:', error);
            if (loading) loading.style.display = 'none';
            if (empty) {
                empty.style.display = 'block';
                empty.innerHTML = `
                    <i class='bx bx-error-circle' style="font-size: 3rem; color: #ef4444;"></i>
                    <p style="margin: 10px 0 0 0; font-size: 0.95rem; font-weight: 500; color: #ef4444;">Failed to load notifications</p>
                `;
            }
        }
    }

    /**
     * Render notifications in the dropdown
     */
    function renderNotifications(notifications) {
        // Remove existing notification items
        const existingItems = notificationList.querySelectorAll('.notification-item');
        existingItems.forEach(item => item.remove());

        // Create and append new notification items
        notifications.forEach(notification => {
            const item = createNotificationElement(notification);
            notificationList.appendChild(item);
        });
    }

    /**
     * Create a notification element
     */
    function createNotificationElement(notification) {
        const item = document.createElement('div');
        item.className = `notification-item ${!notification.is_read ? 'unread' : ''}`;
        item.dataset.id = notification.id;
        
        // Determine icon based on notification type
        let iconClass = 'bx-info-circle';
        let iconType = notification.type;
        
        switch(notification.type) {
            case 'new_registration':
                iconClass = 'bx-user-plus';
                break;
            case 'user_approved':
                iconClass = 'bx-user-check';
                break;
            case 'user_rejected':
                iconClass = 'bx-user-x';
                break;
            case 'system_alert':
                iconClass = 'bx-bell';
                break;
            case 'admin_account_locked':
                iconClass = 'bx-lock';
                break;
            case 'admin_account_suspended':
                iconClass = 'bx-user-x';
                break;
            case 'admin_account_unlocked':
                iconClass = 'bx-lock-open';
                break;
            case 'admin_account_reactivated':
                iconClass = 'bx-user-check';
                break;
            case 'barangay_assignment_changed':
                iconClass = 'bx-map';
                break;
        }

        item.innerHTML = `
            <div class="notification-icon ${iconType}">
                <i class='bx ${iconClass}'></i>
            </div>
            <div class="notification-content">
                <p class="notification-message">${escapeHtml(notification.message)}</p>
                <p class="notification-time">${notification.time_ago}</p>
            </div>
            ${!notification.is_read ? '<div class="notification-unread-dot"></div>' : ''}
        `;

        // Add click handler
        item.addEventListener('click', () => handleNotificationClick(notification));

        return item;
    }

    /**
     * Handle notification click - mark as read and navigate
     */
    async function handleNotificationClick(notification) {
        try {
            // Mark as read if unread
            if (!notification.is_read) {
                await markNotificationAsRead(notification.id);
            }

            // Close dropdown
            closeDropdown();

            // Navigate to link if provided
            if (notification.link_url) {
                window.location.href = notification.link_url;
            }

        } catch (error) {
            console.error('Error handling notification click:', error);
        }
    }

    /**
     * Mark a single notification as read
     */
    async function markNotificationAsRead(notificationId) {
        try {
            const csrfToken = getCSRFToken();
            
            const response = await fetch(`/cenro/api/notifications/mark-read/${notificationId}/`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-Csrftoken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Update UI
                updateNotificationItemUI(notificationId);
                updateUnreadCount();
            }

        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    /**
     * Mark all notifications as read when dropdown is viewed
     */
    async function markAllAsReadOnView() {
        try {
            const csrfToken = getCSRFToken();
            
            const response = await fetch('/cenro/api/notifications/mark-all-read/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-Csrftoken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Update all notification items UI
                const items = notificationList.querySelectorAll('.notification-item.unread');
                items.forEach(item => {
                    item.classList.remove('unread');
                    const dot = item.querySelector('.notification-unread-dot');
                    if (dot) dot.remove();
                });

                // Update badge - hide it immediately
                badge.style.display = 'none';
            }

        } catch (error) {
            console.error('Error marking all notifications as read on view:', error);
        }
    }

    /**
     * Mark all notifications as read (manual button click)
     */
    async function markAllAsRead(e) {
        e.stopPropagation();
        
        try {
            const csrfToken = getCSRFToken();
            
            const response = await fetch('/cenro/api/notifications/mark-all-read/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'X-Csrftoken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // Update all notification items UI
                const items = notificationList.querySelectorAll('.notification-item.unread');
                items.forEach(item => {
                    item.classList.remove('unread');
                    const dot = item.querySelector('.notification-unread-dot');
                    if (dot) dot.remove();
                });

                // Update badge
                updateUnreadCount();
                
                // Show success feedback
                showToast('All notifications marked as read', 'success');
            }

        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            showToast('Failed to mark notifications as read', 'error');
        }
    }

    /**
     * Update notification item UI to mark as read
     */
    function updateNotificationItemUI(notificationId) {
        const item = notificationList.querySelector(`.notification-item[data-id="${notificationId}"]`);
        if (item) {
            item.classList.remove('unread');
            const dot = item.querySelector('.notification-unread-dot');
            if (dot) dot.remove();
        }
    }

    /**
     * Update unread notification count badge
     */
    async function updateUnreadCount() {
        try {
            const response = await fetch('/cenro/api/notifications/unread-count/', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // Handle 401 - admin logged out or session expired
            if (response.status === 401) {
                console.log('Admin session expired - stopping notification polling');
                stopAutoRefresh(); // Stop polling immediately
                // Hide badge
                if (badge) badge.style.display = 'none';
                return; // Silently fail
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const count = data.count || 0;

            // Update badge
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }

        } catch (error) {
            console.error('Error updating unread count:', error);
            // Stop polling on any error to prevent console spam
            stopAutoRefresh();
        }
    }

    /**
     * Start auto-refresh timer
     */
    function startAutoRefresh() {
        refreshTimer = setInterval(() => {
            updateUnreadCount();
            if (isDropdownOpen) {
                loadNotifications();
            }
        }, REFRESH_INTERVAL);
    }

    /**
     * Stop auto-refresh timer
     */
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    /**
     * Get CSRF token from cookie or meta tag
     */
    function getCSRFToken() {
        // Try to get from meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Fallback to cookie
        const name = 'csrftoken';
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

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        // Simple toast implementation (you can replace with your preferred toast library)
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            animation: slideInUp 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutDown 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Clean up on page unload
    window.addEventListener('beforeunload', stopAutoRefresh);

    // Expose cleanup function globally for logout handlers
    window.stopAdminNotificationPolling = stopAutoRefresh;

})();
