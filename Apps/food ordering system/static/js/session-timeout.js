/**
 * Session Timeout Manager for Food Ordering System
 * 
 * Handles automatic logout warnings and session management with countdown timer.
 * Provides user-friendly warnings before session expires and allows session extension.
 * 
 * Features:
 * - Countdown timer with visual warning
 * - Session extension functionality
 * - AJAX session status checking
 * - Responsive modal design
 * - Activity tracking to reset timeout
 */

class SessionTimeoutManager {
    constructor() {
        // Configuration from Django response headers
        this.sessionTimeout = parseInt(document.querySelector('meta[name="session-timeout"]')?.content || '1200'); // 20 minutes default
        this.warningTime = parseInt(document.querySelector('meta[name="warning-time"]')?.content || '120'); // 2 minutes default
        this.checkInterval = 30000; // Check every 30 seconds
        this.warningShown = false;
        this.countdownInterval = null;
        this.sessionCheckInterval = null;
        this.timeRemaining = 0;
        
        // DOM elements
        this.warningModal = null;
        this.countdownElement = null;
        this.extendButton = null;
        this.logoutButton = null;
        
        // Navbar timer elements
        this.navbarTimer = null;
        this.navbarCountdown = null;
        this.timerStatus = null;
        
        // DEBUG: Log initialization
        console.log('DEBUG: SessionTimeoutManager constructor called');
        console.log('DEBUG: Body data-user-authenticated:', document.body.getAttribute('data-user-authenticated'));
        console.log('DEBUG: Body classes:', document.body.className);
        
        this.init();
    }
    
    /**
     * Check if user is authenticated by reading meta tag
     * @returns {boolean} True if user is authenticated
     */
    isUserAuthenticated() {
        const userAuthMeta = document.querySelector('meta[name="user-authenticated"]');
        return userAuthMeta && userAuthMeta.content === 'true';
    }
    
    /**
     * Initialize the session timeout manager
     * Sets up event listeners and starts monitoring
     */
    init() {
        // Only initialize for authenticated users
        console.log('DEBUG: init() called, checking authentication...');
        if (!this.isUserAuthenticated()) {
            console.log('DEBUG: User not authenticated, aborting initialization');
            return;
        }
        
        console.log('Session timeout manager initialized');
        console.log(`Session timeout: ${this.sessionTimeout}s, Warning time: ${this.warningTime}s`);
        
        this.createWarningModal();
        this.setupEventListeners();
        this.startSessionMonitoring();
        this.resetTimer();
        this.initializeNavbarTimer();
    }
    
    /**
     * Check if current URL is exempt from session timeout
     * 
     * @returns {boolean} True if URL is exempt, False otherwise
     */
    isExemptUrl() {
        const exemptUrls = ['/checkout/', '/payment/', '/order/confirm/', '/api/payment/', '/api/checkout/'];
        return exemptUrls.some(url => window.location.pathname.startsWith(url));
    }
    
    /**
     * Initialize the navbar countdown timer
     * Sets up the navbar timer element and click handler
     */
    initializeNavbarTimer() {
        console.log('DEBUG: initializeNavbarTimer() called');
        
        // Cache navbar timer elements
        this.navbarTimer = document.getElementById('navbarSessionTimer');
        this.navbarCountdown = document.getElementById('navbarCountdown');
        this.timerStatus = document.getElementById('timerStatus');
        
        console.log('DEBUG: Navbar timer elements found:');
        console.log('  - navbarTimer:', this.navbarTimer);
        console.log('  - navbarCountdown:', this.navbarCountdown);
        console.log('  - timerStatus:', this.timerStatus);
        
        if (this.navbarTimer && this.navbarCountdown) {
            // Add click handler for quick extend session or open modal
            this.navbarTimer.addEventListener('click', () => {
                if (this.timeRemaining <= 120) {
                    // Critical time - extend session immediately
                    this.extendSession();
                } else if (this.warningShown) {
                    // Warning shown - open modal for full options
                    this.warningModal.classList.remove('hidden');
                } else {
                    // Extend session directly for convenience
                    this.extendSession();
                }
            });
            
            // Add tooltip for better UX
            this.navbarTimer.setAttribute('title', 'Click to extend session');
            
            console.log('DEBUG: Navbar session timer initialized successfully');
        } else {
            console.log('DEBUG: ERROR - Navbar timer elements not found!');
        }
    }
    
    /**
     * Update the navbar countdown timer
     * Shows/hides timer based on remaining time and updates display
     */
    updateNavbarTimer() {
        if (!this.navbarTimer || !this.navbarCountdown) {
            return;
        }
        
        // Hide timer during checkout/payment flows (exempt URLs)
        if (this.isExemptUrl()) {
            this.navbarTimer.classList.add('hidden');
            this.navbarTimer.classList.remove('flex', 'bg-orange-50', 'bg-red-50', 'border', 'border-orange-200', 'border-red-200', 'animate-pulse');
            this.navbarCountdown.classList.remove('text-orange-600', 'text-red-600');
            return;
        }
        
        // Hide timer when warning modal is open (avoid redundancy)
        if (this.warningShown && this.warningModal && !this.warningModal.classList.contains('hidden')) {
            this.navbarTimer.classList.add('hidden');
            this.navbarTimer.classList.remove('flex');
            return;
        }
        
        // Show timer when less than 30 minutes remaining (temporarily for testing)
        const showThreshold = 1800; // 30 minutes in seconds - changed for debugging
        
        if (this.timeRemaining <= showThreshold) {
            // Show the timer
            this.navbarTimer.classList.remove('hidden');
            this.navbarTimer.classList.add('flex');
            
            // Update countdown display
            const minutes = Math.floor(this.timeRemaining / 60);
            const seconds = this.timeRemaining % 60;
            const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            this.navbarCountdown.textContent = timeString;
            
            // Update colors based on urgency
            if (this.timeRemaining <= 120) { // Less than 2 minutes - red
                this.navbarTimer.classList.add('bg-red-50', 'border', 'border-red-200');
                this.navbarTimer.classList.remove('bg-orange-50', 'border-orange-200');
                this.navbarCountdown.classList.add('text-red-600');
                this.navbarCountdown.classList.remove('text-orange-600', 'text-gray-700');
                
                // Add pulse animation for urgency
                this.navbarTimer.classList.add('animate-pulse');
            } else if (this.timeRemaining <= 300) { // Less than 5 minutes - orange
                this.navbarTimer.classList.add('bg-orange-50', 'border', 'border-orange-200');
                this.navbarTimer.classList.remove('bg-red-50', 'border-red-200');
                this.navbarCountdown.classList.add('text-orange-600');
                this.navbarCountdown.classList.remove('text-red-600', 'text-gray-700');
                
                // Remove pulse if not urgent
                this.navbarTimer.classList.remove('animate-pulse');
            }
        } else {
            // Hide the timer when plenty of time remains
            this.navbarTimer.classList.add('hidden');
            this.navbarTimer.classList.remove('flex', 'bg-orange-50', 'bg-red-50', 'border', 'border-orange-200', 'border-red-200', 'animate-pulse');
            this.navbarCountdown.classList.remove('text-orange-600', 'text-red-600');
        }
    }
    
    /**
     * Create the session timeout warning modal
     * Uses Tailwind CSS for styling with responsive design
     */
    createWarningModal() {
        const modalHTML = `
            <!-- Session Timeout Warning Modal -->
            <div id="sessionTimeoutModal" class="fixed inset-0 z-50 hidden">
                <!-- Backdrop -->
                <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
                
                <!-- Modal Content -->
                <div class="fixed inset-0 flex items-center justify-center p-4">
                    <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 transform transition-all">
                        <!-- Modal Header -->
                        <div class="p-6 border-b border-gray-100">
                            <div class="flex items-center space-x-3">
                                <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                                    <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-900">Session Timeout Warning</h3>
                                    <p class="text-sm text-gray-600">Your session is about to expire</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Modal Body -->
                        <div class="p-6">
                            <p class="text-gray-700 mb-4">
                                For your security, your session will automatically expire due to inactivity. 
                                Please choose an option below:
                            </p>
                            
                            <!-- Countdown Timer -->
                            <div class="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-orange-800">Time remaining:</span>
                                    <div class="flex items-center space-x-2">
                                        <svg class="w-5 h-5 text-orange-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <span id="sessionCountdown" class="text-lg font-bold text-orange-900">2:00</span>
                                    </div>
                                </div>
                                
                                <!-- Progress Bar -->
                                <div class="mt-3 bg-orange-200 rounded-full h-2">
                                    <div id="sessionProgress" class="bg-orange-600 h-2 rounded-full transition-all duration-1000" style="width: 100%"></div>
                                </div>
                            </div>
                            
                            <!-- Action Buttons -->
                            <div class="flex space-x-3">
                                <button id="extendSessionBtn" class="flex-1 bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                                    </svg>
                                    <span>Extend Session</span>
                                </button>
                                <button id="logoutNowBtn" class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                                    </svg>
                                    <span>Logout Now</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Cache DOM elements
        this.warningModal = document.getElementById('sessionTimeoutModal');
        this.countdownElement = document.getElementById('sessionCountdown');
        this.extendButton = document.getElementById('extendSessionBtn');
        this.logoutButton = document.getElementById('logoutNowBtn');
    }
    
    /**
     * Setup event listeners for user activity and modal buttons
     */
    setupEventListeners() {
        // User activity events to reset timer
        const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        activityEvents.forEach(event => {
            document.addEventListener(event, () => this.handleUserActivity(), true);
        });
        
        // Modal button events
        if (this.extendButton) {
            this.extendButton.addEventListener('click', () => this.extendSession());
        }
        
        if (this.logoutButton) {
            this.logoutButton.addEventListener('click', () => this.logoutNow());
        }
        
        // Handle page visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkSessionStatus();
            }
        });
    }
    
    /**
     * Start monitoring session status
     * Periodically checks server for session validity
     */
    startSessionMonitoring() {
        this.sessionCheckInterval = setInterval(() => {
            this.checkSessionStatus();
        }, this.checkInterval);
    }
    
    /**
     * Check session status with server
     * Verifies if session is still valid on server side
     */
    async checkSessionStatus() {
        try {
            const response = await fetch('/auth/session-status/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
            });
            
            if (response.status === 401) {
                // Session has expired on server
                this.handleSessionExpired();
            } else if (response.ok) {
                const data = await response.json();
                if (data.status === 'timeout') {
                    this.handleSessionExpired();
                } else {
                    // Session is valid, update timeout info
                    this.updateTimeoutInfo(data);
                }
            }
        } catch (error) {
            console.error('Error checking session status:', error);
        }
    }
    
    /**
     * Update timeout information from server response
     * 
     * @param {Object} data - Server response data
     */
    updateTimeoutInfo(data) {
        if (data.session_timeout) {
            this.sessionTimeout = data.session_timeout;
        }
        if (data.warning_time) {
            this.warningTime = data.warning_time;
        }
    }
    
    /**
     * Handle user activity to reset session timer
     * Resets countdown and hides warning if shown
     */
    handleUserActivity() {
        if (this.warningShown) {
            // Don't reset if warning is already shown (user needs to take action)
            return;
        }
        
        this.resetTimer();
    }
    
    /**
     * Reset the session timeout timer
     * Clears existing intervals and starts fresh countdown
     */
    resetTimer() {
        // Clear existing intervals
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        
        // Reset state
        this.warningShown = false;
        this.timeRemaining = this.sessionTimeout;
        
        // Hide warning modal if visible
        if (this.warningModal) {
            this.warningModal.classList.add('hidden');
        }
        
        // Start new countdown
        this.startCountdown();
    }
    
    /**
     * Start the countdown timer
     * Shows warning when time reaches warning threshold
     */
    startCountdown() {
        this.countdownInterval = setInterval(() => {
            this.timeRemaining--;
            
            // Update navbar timer on every tick
            this.updateNavbarTimer();
            
            // Show warning when approaching timeout
            if (this.timeRemaining <= this.warningTime && !this.warningShown) {
                this.showWarning();
            }
            
            // Auto logout when time expires
            if (this.timeRemaining <= 0) {
                this.handleSessionExpired();
            }
        }, 1000);
    }
    
    /**
     * Show the session timeout warning modal
     * Displays countdown timer and action buttons
     */
    showWarning() {
        this.warningShown = true;
        
        if (this.warningModal) {
            this.warningModal.classList.remove('hidden');
            this.updateCountdownDisplay();
        }
        
        console.log('Session timeout warning shown');
    }
    
    /**
     * Update the countdown display in the modal
     * Shows remaining time in MM:SS format with progress bar
     */
    updateCountdownDisplay() {
        if (!this.countdownElement) return;
        
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        this.countdownElement.textContent = timeString;
        
        // Update progress bar
        const progressBar = document.getElementById('sessionProgress');
        if (progressBar) {
            const progressPercentage = (this.timeRemaining / this.warningTime) * 100;
            progressBar.style.width = `${Math.max(0, progressPercentage)}%`;
        }
        
        // Change color as time runs out
        if (this.timeRemaining <= 30) {
            this.countdownElement.classList.add('text-red-600');
            this.countdownElement.classList.remove('text-orange-900');
        }
    }
    
    /**
     * Extend the current session
     * Makes server request to refresh session and resets timer
     */
    async extendSession() {
        try {
            // Show visual feedback that extension is in progress
            this.showExtensionFeedback();
            
            const response = await fetch('/auth/extend-session/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                credentials: 'same-origin',
            });
            
            if (response.ok) {
                // Session extended successfully
                this.resetTimer();
                this.announceToScreenReader('Session extended successfully');
                console.log('Session extended successfully');
            } else {
                console.error('Failed to extend session');
                this.announceToScreenReader('Failed to extend session');
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Error extending session:', error);
            this.announceToScreenReader('Error extending session');
            this.handleSessionExpired();
        }
    }
    
    /**
     * Handle session expiration
     * Shows message and redirects to login page
     */
    handleSessionExpired() {
        // Clear all intervals
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
        }
        
        // Show expired message
        this.showSessionExpiredMessage();
        
        /* Removed auto-redirect to prevent buttons disappearing after 2 seconds */
        // User can manually navigate to login when ready
    }
    
    /**
     * Show session expired message
     * Displays a temporary message before redirect
     */
    showSessionExpiredMessage() {
        const messageHTML = `
            <div id="sessionExpiredMessage" class="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg max-w-sm">
                <div class="flex items-center space-x-3">
                    <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                        <p class="text-sm font-medium text-red-800">Session Expired</p>
                        <p class="text-xs text-red-600">Redirecting to login page...</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', messageHTML);
        
        // Remove message after redirect
        setTimeout(() => {
            const message = document.getElementById('sessionExpiredMessage');
            if (message) {
                message.remove();
            }
        }, 3000);
    }
    
    /**
     * Logout immediately
     * Redirects user to login page
     */
    logoutNow() {
        window.location.href = '/auth/logout/';
    }
    
    /**
     * Get CSRF token from cookies
     * 
     * @returns {string} CSRF token value
     */
    getCSRFToken() {
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
     * Show visual feedback when session is extended
     * Displays a brief checkmark animation to confirm action
     */
    showExtensionFeedback() {
        if (!this.navbarTimer) return;
        
        // Add temporary success styling
        this.navbarTimer.classList.add('bg-green-50', 'border', 'border-green-200');
        
        // Create checkmark overlay
        const checkmark = document.createElement('div');
        checkmark.className = 'absolute inset-0 flex items-center justify-center bg-green-50 rounded-lg';
        checkmark.innerHTML = `
            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
        `;
        
        this.navbarTimer.style.position = 'relative';
        this.navbarTimer.appendChild(checkmark);
        
        // Remove feedback after 1.5 seconds
        setTimeout(() => {
            if (checkmark.parentNode) {
                checkmark.remove();
            }
            this.navbarTimer.classList.remove('bg-green-50', 'border', 'border-green-200');
        }, 1500);
    }
    
    /**
     * Announce messages to screen readers for accessibility
     * 
     * @param {string} message - Message to announce to screen readers
     */
    announceToScreenReader(message) {
        if (this.timerStatus) {
            this.timerStatus.textContent = message;
            
            // Clear the message after 3 seconds to avoid stale announcements
            setTimeout(() => {
                this.timerStatus.textContent = 'Session timer active';
            }, 3000);
        }
    }
    
    /**
     * Cleanup method to remove event listeners and intervals
     * Call this when page is unloading
     */
    cleanup() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        if (this.sessionCheckInterval) {
            clearInterval(this.sessionCheckInterval);
        }
        
        // Remove modal if it exists
        if (this.warningModal) {
            this.warningModal.remove();
        }
    }
}

// Initialize session timeout manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user is authenticated
    const isAuthenticated = document.body.getAttribute('data-user-authenticated') === 'true' || 
                           document.body.classList.contains('user-authenticated');
    
    console.log('DEBUG: DOMContentLoaded - isAuthenticated:', isAuthenticated);
    
    if (isAuthenticated) {
        window.sessionTimeoutManager = new SessionTimeoutManager();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (window.sessionTimeoutManager) {
                window.sessionTimeoutManager.cleanup();
            }
        });
    }
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionTimeoutManager;
}
