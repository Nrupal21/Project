/**
 * Account Management Form Validation and Enhancement Scripts
 * 
 * This file contains client-side validation and UX enhancement functions
 * for TravelGuide account management features including registration, login,
 * profile updates, password changes, and email verification.
 * 
 * @author TravelGuide Team
 * @version 1.0.0
 */

/**
 * Initialize all account-related validation and enhancement functionality
 * 
 * This is the main entry point that sets up all event listeners and
 * initializes validation for account forms when the DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form validation for all account forms
    initLoginValidation();
    initRegistrationValidation();
    initProfileValidation();
    initPasswordValidation();
    initEmailVerificationHandler();
    
    // Initialize additional UI enhancements
    setupPasswordToggle();
    setupAvatarPreview();
});

/**
 * Set up login form validation
 * 
 * Validates username/email and password fields on the login form
 * before submission to provide immediate feedback to users
 */
function initLoginValidation() {
    // Get login form if it exists on the page
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;
    
    // Add submit event listener
    loginForm.addEventListener('submit', function(event) {
        // Reset previous error messages
        clearErrorMessages(loginForm);
        
        // Get form input values
        const username = loginForm.querySelector('input[name="username"]').value.trim();
        const password = loginForm.querySelector('input[name="password"]').value;
        
        // Validate username
        if (!username) {
            event.preventDefault();
            displayErrorMessage(loginForm.querySelector('input[name="username"]'), 'Username or email is required');
        }
        
        // Validate password
        if (!password) {
            event.preventDefault();
            displayErrorMessage(loginForm.querySelector('input[name="password"]'), 'Password is required');
        }
    });
}

/**
 * Set up registration form validation
 * 
 * Performs comprehensive client-side validation of the registration form
 * including username, email, and password strength checks
 */
function initRegistrationValidation() {
    // Get registration form if it exists on the page
    const regForm = document.getElementById('register-form');
    if (!regForm) return;
    
    // Add submit event listener
    regForm.addEventListener('submit', function(event) {
        // Reset previous error messages
        clearErrorMessages(regForm);
        
        // Get form input values
        const username = regForm.querySelector('input[name="username"]').value.trim();
        const email = regForm.querySelector('input[name="email"]').value.trim();
        const password1 = regForm.querySelector('input[name="password1"]').value;
        const password2 = regForm.querySelector('input[name="password2"]').value;
        
        let isValid = true;
        
        // Validate username (at least 3 characters, alphanumeric)
        if (!username || username.length < 3) {
            displayErrorMessage(regForm.querySelector('input[name="username"]'), 'Username must be at least 3 characters');
            isValid = false;
        } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            displayErrorMessage(regForm.querySelector('input[name="username"]'), 'Username can only contain letters, numbers and underscores');
            isValid = false;
        }
        
        // Validate email format
        if (!email || !validateEmail(email)) {
            displayErrorMessage(regForm.querySelector('input[name="email"]'), 'Please enter a valid email address');
            isValid = false;
        }
        
        // Validate password strength
        if (!password1 || password1.length < 8) {
            displayErrorMessage(regForm.querySelector('input[name="password1"]'), 'Password must be at least 8 characters');
            isValid = false;
        } else if (!validatePasswordStrength(password1)) {
            displayErrorMessage(regForm.querySelector('input[name="password1"]'), 
                'Password must include at least one uppercase letter, one lowercase letter, and one number or special character');
            isValid = false;
        }
        
        // Check if passwords match
        if (password1 !== password2) {
            displayErrorMessage(regForm.querySelector('input[name="password2"]'), 'Passwords do not match');
            isValid = false;
        }
        
        // Prevent form submission if validation fails
        if (!isValid) {
            event.preventDefault();
        }
    });
}

/**
 * Set up profile form validation
 * 
 * Validates user profile information including name fields,
 * email format, and avatar file size and type
 */
function initProfileValidation() {
    // Get profile form if it exists on the page
    const profileForm = document.getElementById('profile-form');
    if (!profileForm) return;
    
    // Add submit event listener
    profileForm.addEventListener('submit', function(event) {
        // Reset previous error messages
        clearErrorMessages(profileForm);
        
        let isValid = true;
        
        // Validate email if present
        const emailInput = profileForm.querySelector('input[name="email"]');
        if (emailInput) {
            const email = emailInput.value.trim();
            if (email && !validateEmail(email)) {
                displayErrorMessage(emailInput, 'Please enter a valid email address');
                isValid = false;
            }
        }
        
        // Validate avatar file if one is selected
        const avatarInput = profileForm.querySelector('input[name="avatar"]');
        if (avatarInput && avatarInput.files.length > 0) {
            const file = avatarInput.files[0];
            
            // Check file type
            const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
            if (!validTypes.includes(file.type)) {
                displayErrorMessage(avatarInput, 'Only JPEG, PNG, and GIF images are allowed');
                isValid = false;
            }
            
            // Check file size (max 5MB)
            if (file.size > 5 * 1024 * 1024) {
                displayErrorMessage(avatarInput, 'File size must be less than 5MB');
                isValid = false;
            }
        }
        
        // Prevent form submission if validation fails
        if (!isValid) {
            event.preventDefault();
        }
    });
}

/**
 * Set up password change form validation
 * 
 * Validates password strength and confirms that new password
 * and confirmation fields match before submission
 */
function initPasswordValidation() {
    // Get password form if it exists on the page
    const passwordForm = document.getElementById('password-form');
    if (!passwordForm) return;
    
    // Add submit event listener
    passwordForm.addEventListener('submit', function(event) {
        // Reset previous error messages
        clearErrorMessages(passwordForm);
        
        let isValid = true;
        
        // Get password fields
        const oldPassword = passwordForm.querySelector('input[name="old_password"]')?.value;
        const newPassword1 = passwordForm.querySelector('input[name="new_password1"]')?.value;
        const newPassword2 = passwordForm.querySelector('input[name="new_password2"]')?.value;
        
        // Validate old password if field exists
        if (oldPassword !== undefined && !oldPassword) {
            displayErrorMessage(passwordForm.querySelector('input[name="old_password"]'), 'Current password is required');
            isValid = false;
        }
        
        // Validate new password strength
        if (newPassword1 !== undefined) {
            if (!newPassword1 || newPassword1.length < 8) {
                displayErrorMessage(passwordForm.querySelector('input[name="new_password1"]'), 'Password must be at least 8 characters');
                isValid = false;
            } else if (!validatePasswordStrength(newPassword1)) {
                displayErrorMessage(passwordForm.querySelector('input[name="new_password1"]'), 
                    'Password must include at least one uppercase letter, one lowercase letter, and one number or special character');
                isValid = false;
            }
            
            // Check if passwords match
            if (newPassword1 !== newPassword2) {
                displayErrorMessage(passwordForm.querySelector('input[name="new_password2"]'), 'Passwords do not match');
                isValid = false;
            }
        }
        
        // Prevent form submission if validation fails
        if (!isValid) {
            event.preventDefault();
        }
    });
}

/**
 * Initialize email verification resend functionality
 * 
 * Sets up click handler for the resend verification email button
 * with rate limiting to prevent abuse. Includes countdown timer
 * for the cooldown period and visual feedback for the user.
 */
function initEmailVerificationHandler() {
    // Get resend verification button if it exists on the page
    const resendButton = document.getElementById('resend-verification-btn');
    if (!resendButton) return;
    
    // Track the cooldown state
    let isInCooldown = false;
    let cooldownTimer = null;
    let remainingSeconds = 0;
    let originalButtonText = resendButton.textContent; // Store original button text
    
    /**
     * Start cooldown timer to prevent frequent resend requests
     * 
     * Implements a 5-minute (300 seconds) cooldown period during which
     * the button is disabled and displays a countdown timer
     */
    function startCooldown() {
        // Set initial state
        isInCooldown = true;
        remainingSeconds = 300; // 5 minutes in seconds
        
        // Disable the button and update its appearance
        resendButton.disabled = true;
        resendButton.classList.add('bg-gray-400', 'cursor-not-allowed');
        resendButton.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
        
        // Update button text with initial countdown
        resendButton.textContent = `Wait ${formatCountdown(remainingSeconds)}`;

        // Store cooldown end time in localStorage to persist across page refreshes
        const cooldownEndTime = Date.now() + (remainingSeconds * 1000);
        localStorage.setItem('verification_cooldown_end', cooldownEndTime.toString());
        
        // Set up countdown interval
        cooldownTimer = setInterval(() => {
            // Decrement remaining time
            remainingSeconds--;
            
            // Update button text
            if (remainingSeconds > 0) {
                resendButton.textContent = `Wait ${formatCountdown(remainingSeconds)}`;
            } else {
                // Reset when countdown finishes
                clearInterval(cooldownTimer);
                cooldownTimer = null;
                isInCooldown = false;
                
                // Remove stored cooldown timestamp
                localStorage.removeItem('verification_cooldown_end');
                
                // Re-enable button
                resendButton.disabled = false;
                resendButton.textContent = originalButtonText;
                resendButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
                resendButton.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
            }
        }, 1000);
    }
    
    /**
     * Send verification email request to the server
     * 
     * Makes an AJAX POST request to the resend verification endpoint
     * and handles the response
     */
    function sendVerificationRequest() {
        // Show loading state
        resendButton.textContent = 'Sending...';
        resendButton.disabled = true;
        
        // Get CSRF token for the request
        const csrfToken = getCsrfToken();
        
        // Make AJAX request to resend verification endpoint
        fetch('/accounts/api/resend_verification_email/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            // Check if request was successful
            if (data.success) {
                // Show success notification
                showNotification(data.message || 'Verification email sent successfully!', 'success');
                
                // Start cooldown timer to prevent abuse
                startCooldown();
            } else {
                // Show error notification
                showNotification(data.message || 'Failed to send verification email', 'error');
                
                // Re-enable button after short delay
                setTimeout(() => {
                    resendButton.textContent = originalButtonText;
                    resendButton.disabled = false;
                    resendButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
                    resendButton.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
                }, 3000);
            }
        })
        .catch(error => {
            console.error('Error sending verification email:', error);
            showNotification('An error occurred while sending the verification email', 'error');
            
            // Re-enable button after short delay
            setTimeout(() => {
                resendButton.textContent = originalButtonText;
                resendButton.disabled = false;
                resendButton.classList.remove('bg-gray-400', 'cursor-not-allowed');
                resendButton.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
            }, 3000);
        });
    }
    
    // Add click event listener to the resend button
    resendButton.addEventListener('click', function(event) {
        // Prevent default button action
        event.preventDefault();
        
        // Check if button is in cooldown
        if (isInCooldown) return;
        
        // Send verification request
        sendVerificationRequest();
    });
    
    // Check if there's a stored cooldown timestamp from a previous session
    const storedCooldownEnd = localStorage.getItem('verification_cooldown_end');
    if (storedCooldownEnd) {
        const cooldownEndTime = parseInt(storedCooldownEnd, 10);
        const currentTime = Date.now();
        
        // If cooldown period is still active
        if (cooldownEndTime > currentTime) {
            // Calculate remaining seconds
            remainingSeconds = Math.ceil((cooldownEndTime - currentTime) / 1000);
            
            // Start the cooldown with the remaining time
            if (remainingSeconds > 0) {
                startCooldown();
            } else {
                // Clear expired cooldown
                localStorage.removeItem('verification_cooldown_end');
            }
        } else {
            // Clear expired cooldown
            localStorage.removeItem('verification_cooldown_end');
        }
    }
}

/**
 * Set up password visibility toggle functionality
 * 
 * Adds a toggle button next to password fields to show/hide
 * the password contents for better user experience
 */
function setupPasswordToggle() {
    // Find all password fields
    const passwordFields = document.querySelectorAll('input[type="password"]');
    
    passwordFields.forEach(field => {
        // Create toggle button
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'absolute right-0 top-0 mt-2 mr-3 text-gray-500 hover:text-gray-700';
        toggleButton.innerHTML = '<svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M10 3C5.5 3 2 7.5 2 10s3.5 7 8 7 8-3.5 8-7-3.5-7-8-7zm0 12c-3.866 0-7-2.582-7-5s3.134-5 7-5 7 2.582 7 5-3.134 5-7 5z" clip-rule="evenodd"/></svg>';
        
        // Set up wrapper for positioning
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(field);
        wrapper.appendChild(toggleButton);
        
        // Add click event to toggle password visibility
        toggleButton.addEventListener('click', function() {
            if (field.type === 'password') {
                field.type = 'text';
                this.innerHTML = '<svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.28 2.22a.75.75 0 00-1.06 1.06l14.5 14.5a.75.75 0 001.06-1.06l-1.745-1.745C17.023 13.499 18 11.792 18 10c0-2.418-3.328-5-8-5-1.216 0-2.36.254-3.394.706L3.28 2.22zm10.073 10.073L9.736 8.676A2.5 2.5 0 0112.5 11c0 .448-.12.867-.326 1.23l-1.18-1.18a.75.75 0 00-1.06 1.06l2.037 2.036a.75.75 0 001.06-1.06l-.977-.977zM7.5 9.5c0-.312.06-.61.169-.876L5.98 6.935A5.715 5.715 0 005 10c0 2.418 3.328 5 8 5 .996 0 1.94-.183 2.802-.496l-1.64-1.64A2.5 2.5 0 017.5 9.5z" clip-rule="evenodd" /></svg>';
            } else {
                field.type = 'password';
                this.innerHTML = '<svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M10 3C5.5 3 2 7.5 2 10s3.5 7 8 7 8-3.5 8-7-3.5-7-8-7zm0 12c-3.866 0-7-2.582-7-5s3.134-5 7-5 7 2.582 7 5-3.134 5-7 5z" clip-rule="evenodd"/></svg>';
            }
        });
    });
}

/**
 * Set up avatar image preview functionality
 * 
 * Shows a preview of selected avatar images before form submission
 * to help users confirm their selection
 */
function setupAvatarPreview() {
    // Find avatar file input if it exists
    const avatarInput = document.querySelector('input[name="avatar"][type="file"]');
    if (!avatarInput) return;
    
    // Find or create preview image element
    let previewContainer = document.querySelector('.avatar-preview');
    if (!previewContainer) {
        previewContainer = document.createElement('div');
        previewContainer.className = 'avatar-preview mt-2';
        avatarInput.parentNode.appendChild(previewContainer);
    }
    
    // Add change event listener to file input
    avatarInput.addEventListener('change', function(event) {
        // Clear previous preview
        previewContainer.innerHTML = '';
        
        // Get selected file
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            previewContainer.innerHTML = '<p class="text-red-500 text-xs">Invalid file type. Please select a JPEG, PNG, or GIF image.</p>';
            return;
        }
        
        // Create preview
        const img = document.createElement('img');
        img.className = 'h-24 w-24 object-cover rounded-full border-2 border-indigo-500';
        img.file = file;
        previewContainer.appendChild(img);
        
        // Create file reader to load image
        const reader = new FileReader();
        reader.onload = (function(aImg) {
            return function(e) {
                aImg.src = e.target.result;
            };
        })(img);
        
        reader.readAsDataURL(file);
    });
}

/* -------- HELPER FUNCTIONS -------- */

/**
 * Display an error message for a form field
 * 
 * Creates and inserts an error message element below the specified input
 * 
 * @param {HTMLElement} inputElement - The input element with an error
 * @param {string} message - The error message to display
 */
function displayErrorMessage(inputElement, message) {
    // Create error message element
    const errorElement = document.createElement('p');
    errorElement.className = 'text-red-500 text-xs italic mt-1 error-message';
    errorElement.textContent = message;
    
    // Insert after input element
    if (inputElement.parentNode) {
        inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
    }
    
    // Highlight input
    inputElement.classList.add('border-red-500');
}

/**
 * Clear all error messages from a form
 * 
 * Removes all error message elements and styling from the specified form
 * 
 * @param {HTMLFormElement} formElement - The form to clear errors from
 */
function clearErrorMessages(formElement) {
    // Remove error message elements
    const errorMessages = formElement.querySelectorAll('.error-message');
    errorMessages.forEach(el => el.remove());
    
    // Remove error styling from inputs
    const inputs = formElement.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.classList.remove('border-red-500');
    });
}

/**
 * Validate email format
 * 
 * Checks if an email address follows a valid format
 * 
 * @param {string} email - The email address to validate
 * @returns {boolean} True if email format is valid, false otherwise
 */
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Validate password strength
 * 
 * Checks if a password meets minimum security requirements
 * 
 * @param {string} password - The password to validate
 * @returns {boolean} True if password meets requirements, false otherwise
 */
function validatePasswordStrength(password) {
    // Password should have at least one uppercase letter, one lowercase letter,
    // and one number or special character
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumberOrSpecial = /[0-9!@#$%^&*(),.?":{}|<>]/.test(password);
    
    return hasUpperCase && hasLowerCase && hasNumberOrSpecial;
}

/**
 * Get CSRF token from cookies
 * 
 * Extracts Django's CSRF token from page cookies for AJAX requests
 * 
 * @returns {string} The CSRF token value
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
        
    return cookieValue || '';
}

/**
 * Display notification message to the user
 * 
 * Creates and shows a temporary notification with the specified message and type
 * 
 * @param {string} message - The message to display
 * @param {string} type - The type of notification ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    
    // Set appropriate styling based on type
    let bgColor, textColor, borderColor;
    
    switch (type) {
        case 'success':
            bgColor = 'bg-green-100';
            textColor = 'text-green-700';
            borderColor = 'border-green-400';
            break;
        case 'error':
            bgColor = 'bg-red-100';
            textColor = 'text-red-700';
            borderColor = 'border-red-400';
            break;
        default: // info
            bgColor = 'bg-blue-100';
            textColor = 'text-blue-700';
            borderColor = 'border-blue-400';
    }
    
    // Set notification styles
    notification.className = `fixed top-4 right-4 px-4 py-3 rounded ${bgColor} ${textColor} ${borderColor} border shadow-lg max-w-md z-50`;
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span class="block">${message}</span>
            <button class="ml-4 text-${textColor.split('-')[1]}-900" onclick="this.parentNode.parentNode.remove()">×</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

/**
 * Format countdown time in MM:SS format
 * 
 * Converts seconds into a formatted time string
 * 
 * @param {number} seconds - The number of seconds
 * @returns {string} Formatted time string (MM:SS)
 */
function formatCountdown(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
