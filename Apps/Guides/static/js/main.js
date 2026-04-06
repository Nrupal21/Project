/**
 * TravelGuide - Main JavaScript file
 * ==========================================================================
 * This file contains common functionality used across the TravelGuide application
 * including notification handling, CSRF token management, form validation,
 * date formatting, and UI interaction helpers.
 *
 * The code follows a functional programming approach with each function handling
 * a specific task. Every function is thoroughly documented with JSDoc comments
 * explaining purpose, parameters, return values, and examples where helpful.
 */


/**
 * Handles showing a notification to the user with automatic dismissal
 * 
 * Creates a toast notification that appears in the top right corner of the screen
 * with styling based on the notification type. The notification slides in from
 * the right, remains visible for the specified duration, then slides out and
 * is removed from the DOM.
 * 
 * @param {string} message - The notification message to display (can include HTML)
 * @param {string} type - The type of notification ('success', 'error', 'info', 'warning')
 * @param {number} duration - How long to show the notification in milliseconds
 * 
 * @example
 * // Show a success notification for 3 seconds
 * showNotification('Your profile has been updated!', 'success', 3000);
 */

function showNotification(message, type = 'info', duration = 5000) {
    // Get the notification container
    const container = document.getElementById('notification-container');
    
    // If container doesn't exist, create one
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'notification-container';
        newContainer.className = 'fixed top-5 right-5 z-50 w-72 transform transition-all duration-300';
        document.body.appendChild(newContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    
    // Set appropriate styling based on notification type using our color palette
    let bgColor, textColor, borderColor;
    switch(type) {
        case 'success':
            bgColor = 'bg-green-100';
            textColor = 'text-green-700';
            borderColor = 'border-green-500';
            break;
        case 'error':
            bgColor = 'bg-red-100';
            textColor = 'text-red-700';
            borderColor = 'border-red-500';
            break;
        case 'warning':
            bgColor = 'bg-yellow-100';
            textColor = 'text-yellow-700';
            borderColor = 'border-yellow-500';
            break;
        case 'info':
        default:
            bgColor = 'bg-indigo-100'; // Updated to use indigo instead of blue
            textColor = 'text-indigo-700';
            borderColor = 'border-indigo-500';
            break;
    }
    
    // Apply styles to notification
    notification.className = `notification mb-3 p-4 rounded shadow-md ${bgColor} ${textColor} ${borderColor} opacity-0 transform translate-x-3`;
    notification.innerHTML = message;
    
    // Add to container
    const notificationContainer = container || newContainer;
    notificationContainer.appendChild(notification);
    
    // Trigger animation to show notification
    setTimeout(() => {
        notification.classList.remove('opacity-0', 'translate-x-3');
    }, 10);
    
    // Set timeout to remove notification
    setTimeout(() => {
        notification.classList.add('opacity-0', 'translate-x-3');
        
        // Remove from DOM after animation completes
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

/**
 * Gets a cookie value by its name - essential for CSRF token handling
 * 
 * This function parses the document.cookie string to find a specific cookie
 * by name and return its value. It's particularly important for AJAX requests
 * that require CSRF token validation in Django.
 * 
 * @param {string} name - The name of the cookie to retrieve
 * @returns {string|null} The cookie value or null if not found
 * 
 * @example
 * // Get the CSRF token for an AJAX request
 * const csrftoken = getCookie('csrftoken');
 * 
 * // Use it in fetch headers
 * fetch('/api/endpoint/', {
 *     method: 'POST',
 *     headers: {
 *         'X-CSRFToken': csrftoken,
 *         'Content-Type': 'application/json'
 *     },
 *     body: JSON.stringify(data)
 * });
 */

function getCookie(name) {
    // Split document.cookie on semicolons
    const value = `; ${document.cookie}`;
    // Find the part that starts with the name we want
    const parts = value.split(`; ${name}=`);
    
    // If we found the cookie, return its value
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
    return null;
}

/**
 * Handles form validation errors and displays them on the form
 * 
 * This function processes a JSON object of validation errors returned from the server
 * and displays them next to the corresponding form fields. It adds error styling to
 * form inputs and creates error message elements.
 * 
 * The errors object should be structured with field names as keys and error messages as values.
 * 
 * @param {Object} errors - Object containing field names as keys and error messages as values
 * @param {string} formId - ID of the form to display errors on
 * 
 * @example
 * // Server response with validation errors
 * const response = {
 *     errors: {
 *         email: 'Please enter a valid email address',
 *         password: 'Password must be at least 8 characters'
 *     }
 * };
 * 
 * // Display these errors on the login form
 * displayFormErrors(response.errors, 'login-form');
 */

function displayFormErrors(errors, formId) {
    // Get the form element
    const form = document.getElementById(formId);
    
    if (!form) return;
    
    // Clear any existing error messages
    const existingErrors = form.querySelectorAll('.error-message');
    existingErrors.forEach(el => el.remove());
    
    // Remove existing error styling
    form.querySelectorAll('.error-border').forEach(input => {
        input.classList.remove('error-border', 'border-red-500');
    });
    
    // Display new error messages
    for (const field in errors) {
        // Find the input with this name
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            // Add error styling to input
            input.classList.add('error-border', 'border-red-500');
            
            // Create error message element
            const errorMessage = document.createElement('p');
            errorMessage.className = 'error-message text-red-500 text-xs mt-1';
            errorMessage.textContent = errors[field];
            
            // Insert after the input
            input.parentNode.insertBefore(errorMessage, input.nextSibling);
        }
    }
}

/**
 * Format a date to a human-readable string
 * @param {Date|string} date - Date object or ISO date string
 * @param {boolean} includeTime - Whether to include the time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = false) {
    const d = new Date(date);
    
    // Check if date is valid
    if (isNaN(d.getTime())) {
        return 'Invalid date';
    }
    
    // Options for date formatting
    const options = {
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
    };
    
    // Add time options if requested
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return d.toLocaleDateString(undefined, options);
}

/**
 * Format a time string in MM:SS format
 * @param {number} seconds - Time in seconds
 * @returns {string} Time formatted as MM:SS
 */
function formatCountdown(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    // Pad with leading zeros if needed
    const formattedMinutes = String(minutes).padStart(2, '0');
    const formattedSeconds = String(remainingSeconds).padStart(2, '0');
    
    return `${formattedMinutes}:${formattedSeconds}`;
}

/**
 * Handle mobile menu toggle
 * Initialize when DOM content is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Auto-dismiss notifications
    const dismissNotifications = () => {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach((notification, index) => {
            setTimeout(() => {
                notification.classList.add('opacity-0');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }, 5000 + (index * 300)); // Stagger removal by 300ms per notification
        });
    };
    
    dismissNotifications();
});
