/**
 * TravelGuide - Notifications JavaScript Module
 * ==========================================================================
 * Handles real-time notification updates, AJAX interactions, and UI enhancements
 * for the notification system across the TravelGuide application.
 * 
 * This module manages fetching unread notification counts, displaying notification
 * badges, handling notification actions like mark as read/unread, and integrating
 * with the destination approval workflow.
 * 
 * @author TravelGuide Team
 */

/**
 * Initialize the notification system when the DOM is fully loaded
 * Sets up event listeners and begins polling for notification updates
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize notification system
    initNotifications();
});

/**
 * Sets up the notification system with event listeners and polling
 * This is the main entry point for notification functionality
 */
function initNotifications() {
    // Initialize the notification badge in the navbar
    updateNotificationBadge();
    
    // Set up polling for notification updates (every 60 seconds)
    setInterval(updateNotificationBadge, 60000);
    
    // Add event listeners to notification action buttons
    setupNotificationActionListeners();
    
    // Initialize destination-specific notification handlers if on relevant pages
    const destinationApprovalElements = document.querySelectorAll('.destination-approval-section');
    if (destinationApprovalElements.length > 0) {
        setupDestinationApprovalNotifications();
    }
}

/**
 * Updates the notification badges throughout the interface with the current unread count
 * Fetches the count via AJAX and updates UI elements across both desktop and mobile views
 * 
 * @returns {Promise} - A promise that resolves when badges are updated
 */
function updateNotificationBadge() {
    // Get CSRF token for the AJAX request
    const csrftoken = getCookie('csrftoken');
    
    /**
     * Make AJAX request to get unread notification count
     * Uses the correct endpoint path defined in notifications/urls.py
     */
    return fetch('/notifications/count/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        // Update all desktop notification badges on the page
        updateBadges('.notification-badge', data.unread_count);
        
        // Update all mobile notification badges
        updateBadges('.mobile-notification-badge', data.unread_count);
        
        // Update desktop notification icon color if there are unread notifications
        updateNotificationIconColor('notification-icon', data.unread_count);
        
        // Update mobile notification icon color
        updateNotificationIconColor('mobile-notification-icon', data.unread_count, 'text-indigo-500');
        
        return data; // Return data for potential chaining
    })
    .catch(error => {
        console.error('Error updating notification badges:', error);
    });
}

/**
 * Helper function to update badge elements with proper styling
 * 
 * @param {string} selector - CSS selector for the badge elements
 * @param {number} count - Number of unread notifications
 */
function updateBadges(selector, count) {
    const badges = document.querySelectorAll(selector);
    badges.forEach(badge => {
        // If there are unread notifications, show the badge with count
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
            
            // Apply our indigo/violet gradient styling
            badge.classList.add('bg-gradient-to-r', 'from-indigo-600', 'to-violet-600');
        } else {
            // Otherwise hide the badge
            badge.classList.add('hidden');
        }
    });
}

/**
 * Helper function to update notification icon color
 * 
 * @param {string} iconId - ID of the notification icon element
 * @param {number} count - Number of unread notifications
 * @param {string} colorClass - CSS class to apply for highlighted state
 */
function updateNotificationIconColor(iconId, count, colorClass = 'text-indigo-500') {
    const icon = document.getElementById(iconId) || document.querySelector('.' + iconId);
    if (icon) {
        if (count > 0) {
            icon.classList.add(colorClass);
        } else {
            icon.classList.remove(colorClass);
        }
    }
}

/**
 * Sets up event listeners for notification action buttons
 * Handles mark as read/unread and delete actions with AJAX
 */
function setupNotificationActionListeners() {
    // Add event listeners to mark as read/unread buttons
    document.querySelectorAll('.mark-read-btn, .mark-unread-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const url = this.getAttribute('data-url');
            const notificationId = this.getAttribute('data-id');
            const notificationCard = document.getElementById(`notification-${notificationId}`);
            
            // Get CSRF token for the AJAX request
            const csrftoken = getCookie('csrftoken');
            
            // Make AJAX request to mark notification as read/unread
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI based on the new read status
                    if (data.is_read) {
                        notificationCard.classList.remove('bg-indigo-50', 'dark:bg-indigo-900/20');
                        notificationCard.classList.add('bg-white', 'dark:bg-gray-800');
                        
                        // Update button text and data-url for toggling
                        this.textContent = 'Mark as unread';
                        this.classList.remove('mark-read-btn');
                        this.classList.add('mark-unread-btn');
                        this.setAttribute('data-url', `/notifications/${notificationId}/mark-unread/`);
                    } else {
                        notificationCard.classList.remove('bg-white', 'dark:bg-gray-800');
                        notificationCard.classList.add('bg-indigo-50', 'dark:bg-indigo-900/20');
                        
                        // Update button text and data-url for toggling
                        this.textContent = 'Mark as read';
                        this.classList.remove('mark-unread-btn');
                        this.classList.add('mark-read-btn');
                        this.setAttribute('data-url', `/notifications/${notificationId}/mark-read/`);
                    }
                    
                    // Update the badge count
                    updateNotificationBadge();
                    
                    // Show success notification
                    showNotification(data.is_read ? 'Notification marked as read' : 'Notification marked as unread', 'success');
                }
            })
            .catch(error => {
                console.error('Error updating notification:', error);
                showNotification('Failed to update notification', 'error');
            });
        });
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-notification-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Confirm deletion
            if (!confirm('Are you sure you want to delete this notification?')) {
                return;
            }
            
            const url = this.getAttribute('data-url');
            const notificationId = this.getAttribute('data-id');
            const notificationCard = document.getElementById(`notification-${notificationId}`);
            
            // Get CSRF token for the AJAX request
            const csrftoken = getCookie('csrftoken');
            
            // Make AJAX request to delete notification
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Animate card removal
                    notificationCard.style.transition = 'opacity 0.3s, transform 0.3s';
                    notificationCard.style.opacity = '0';
                    notificationCard.style.transform = 'translateX(100px)';
                    
                    // Remove card from DOM after animation
                    setTimeout(() => {
                        notificationCard.remove();
                        
                        // Show empty state if no notifications left
                        const notificationCards = document.querySelectorAll('.notification-card');
                        if (notificationCards.length === 0) {
                            const notificationsList = document.getElementById('notifications-list');
                            if (notificationsList) {
                                notificationsList.innerHTML = `
                                    <div class="text-center p-8 bg-white dark:bg-gray-800 rounded-lg shadow">
                                        <svg class="mx-auto h-12 w-12 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                                        </svg>
                                        <h3 class="mt-2 text-lg font-medium text-gray-900 dark:text-white">No notifications</h3>
                                        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">You don't have any notifications at the moment.</p>
                                    </div>
                                `;
                            }
                        }
                    }, 300);
                    
                    // Update the badge count
                    updateNotificationBadge();
                    
                    // Show success notification
                    showNotification('Notification deleted', 'success');
                }
            })
            .catch(error => {
                console.error('Error deleting notification:', error);
                showNotification('Failed to delete notification', 'error');
            });
        });
    });
}

/**
 * Sets up special notification handlers for destination approval pages
 * Integrates with the destination approval workflow
 */
function setupDestinationApprovalNotifications() {
    // Add event listeners to approval form submit buttons
    document.querySelectorAll('.approval-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            // Form will be submitted normally, but add extra handling
            localStorage.setItem('lastAction', 'destination_approved');
        });
    });
    
    // Add event listeners to rejection form submit buttons
    document.querySelectorAll('.rejection-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            // Form will be submitted normally, but add extra handling
            localStorage.setItem('lastAction', 'destination_rejected');
        });
    });
    
    // Check if we need to show a notification based on previous action
    const lastAction = localStorage.getItem('lastAction');
    if (lastAction) {
        // Show appropriate notification
        if (lastAction === 'destination_approved') {
            showNotification('Destination approved! The creator has been notified.', 'success', 8000);
        } else if (lastAction === 'destination_rejected') {
            showNotification('Destination rejected. The creator has been sent an email with the rejection reason.', 'info', 8000);
        }
        
        // Clear the stored action
        localStorage.removeItem('lastAction');
    }
}

/**
 * Helper function to get a cookie by name (used for CSRF token)
 * Required for all AJAX requests to Django
 * 
 * @param {string} name - The name of the cookie to retrieve
 * @returns {string|null} The cookie value or null if not found
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}
