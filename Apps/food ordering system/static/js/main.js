/**
 * Enhanced Cart Management System
 * Handles cart operations with debouncing, optimistic UI, and comprehensive error handling
 */

// Cart management namespace
window.CartManager = (function() {
    'use strict';
    
    // Private variables
    let updateTimeout;
    let isUpdating = false;
    const DEBOUNCE_DELAY = 300; // milliseconds
    
    /**
     * Initialize cart functionality
     * Sets up event listeners for quantity controls and cart operations
     */
    function init() {
        setupQuantityControls();
        setupRemoveItemButtons();
        setupPromoCodeForm();
        setupQuickAddButtons();
        setupSaveForLaterButtons();
    }
    
    /**
     * Setup enhanced quantity controls with debouncing
     * Provides immediate visual feedback with delayed server updates
     */
    function setupQuantityControls() {
        document.querySelectorAll('.quantity-adjuster').forEach(adjuster => {
            const decreaseBtn = adjuster.querySelector('.quantity-btn.decrease');
            const increaseBtn = adjuster.querySelector('.quantity-btn.increase');
            const quantityInput = adjuster.querySelector('.quantity-input');
            const quantityDisplay = adjuster.querySelector('.quantity-display');
            
            const itemId = adjuster.dataset.itemId;
            const currentQuantity = parseInt(adjuster.dataset.currentQuantity);
            
            // Store original values for rollback on error
            adjuster.dataset.originalQuantity = currentQuantity;
            
            // Decrease button handler
            if (decreaseBtn) {
                decreaseBtn.addEventListener('click', function() {
                    if (isUpdating) return;
                    
                    const currentQty = parseInt(quantityDisplay.textContent);
                    if (currentQty > 1) {
                        updateQuantityOptimistic(itemId, currentQty - 1, adjuster);
                    }
                });
            }
            
            // Increase button handler
            if (increaseBtn) {
                increaseBtn.addEventListener('click', function() {
                    if (isUpdating) return;
                    
                    const currentQty = parseInt(quantityDisplay.textContent);
                    if (currentQty < 99) {
                        updateQuantityOptimistic(itemId, currentQty + 1, adjuster);
                    }
                });
            }
            
            // Direct input handler with debouncing
            if (quantityInput) {
                quantityInput.addEventListener('input', function() {
                    if (isUpdating) return;
                    
                    const newQty = parseInt(this.value);
                    if (isNaN(newQty) || newQty < 1) {
                        this.value = 1;
                        return;
                    }
                    if (newQty > 99) {
                        this.value = 99;
                        return;
                    }
                    
                    // Clear existing timeout
                    clearTimeout(updateTimeout);
                    
                    // Set new timeout for debounced update
                    updateTimeout = setTimeout(() => {
                        updateQuantityOptimistic(itemId, newQty, adjuster);
                    }, DEBOUNCE_DELAY);
                });
            }
        });
    }
    
    /**
     * Optimistic quantity update with rollback capability
     * Updates UI immediately, then syncs with server
     * 
     * @param {string} itemId - Menu item ID
     * @param {number} newQuantity - New quantity value
     * @param {HTMLElement} adjuster - Quantity adjuster element
     */
    function updateQuantityOptimistic(itemId, newQuantity, adjuster) {
        if (isUpdating) return;
        
        const quantityDisplay = adjuster.querySelector('.quantity-display');
        const quantityInput = adjuster.querySelector('.quantity-input');
        const originalQuantity = parseInt(adjuster.dataset.originalQuantity);
        
        // Show loading state
        setLoadingState(adjuster, true);
        
        // Update UI optimistically
        quantityDisplay.textContent = newQuantity;
        if (quantityInput) {
            quantityInput.value = newQuantity;
        }
        
        // Animate the change
        quantityDisplay.classList.add('scale-125', 'text-rose-600');
        setTimeout(() => {
            quantityDisplay.classList.remove('scale-125', 'text-rose-600');
        }, 200);
        
        // Send update to server
        updateQuantityOnServer(itemId, newQuantity, adjuster, originalQuantity);
    }
    
    /**
     * Send quantity update to server with error handling and version control
     * 
     * @param {string} itemId - Menu item ID
     * @param {number} newQuantity - New quantity value
     * @param {HTMLElement} adjuster - Quantity adjuster element
     * @param {number} originalQuantity - Original quantity for rollback
     */
    function updateQuantityOnServer(itemId, newQuantity, adjuster, originalQuantity) {
        const csrfToken = adjuster.querySelector('[name=csrfmiddlewaretoken]').value;
        const cartContainer = document.querySelector('.cart-container') || document.body;
        const cartVersion = cartContainer.dataset.cartVersion || 0;
        
        fetch(`/customer/cart/update/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `quantity=${newQuantity}&cart_version=${cartVersion}`
        })
        .then(response => {
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/accounts/login/';
                }, 2000);
                throw new Error('Authentication required');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update successful - update cart totals and version
                updateCartTotals(data.cart_totals);
                adjuster.dataset.originalQuantity = newQuantity;
                
                // Update cart version on client
                if (data.cart_totals.cart_version) {
                    cartContainer.dataset.cartVersion = data.cart_totals.cart_version;
                }
                
                showNotification('Cart updated successfully!', 'success');
            } else {
                // Handle stale cart scenario
                if (data.requires_refresh) {
                    showNotification(data.message, 'warning');
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    // Server rejected update - rollback
                    rollbackQuantityUpdate(adjuster, originalQuantity, data.message);
                }
            }
        })
        .catch(error => {
            if (error.message !== 'Authentication required') {
                console.error('Cart update error:', error);
                rollbackQuantityUpdate(adjuster, originalQuantity, 'Network error. Please try again.');
            }
        })
        .finally(() => {
            setLoadingState(adjuster, false);
        });
    }
    
    /**
     * Rollback quantity update on error
     * 
     * @param {HTMLElement} adjuster - Quantity adjuster element
     * @param {number} originalQuantity - Original quantity to restore
     * @param {string} errorMessage - Error message to display
     */
    function rollbackQuantityUpdate(adjuster, originalQuantity, errorMessage) {
        const quantityDisplay = adjuster.querySelector('.quantity-display');
        const quantityInput = adjuster.querySelector('.quantity-input');
        
        // Restore original values
        quantityDisplay.textContent = originalQuantity;
        if (quantityInput) {
            quantityInput.value = originalQuantity;
        }
        adjuster.dataset.originalQuantity = originalQuantity;
        
        // Show error animation
        quantityDisplay.classList.add('text-red-600', 'animate-pulse');
        setTimeout(() => {
            quantityDisplay.classList.remove('text-red-600', 'animate-pulse');
        }, 1000);
        
        showNotification(errorMessage, 'error');
    }
    
    /**
     * Set loading state for quantity controls
     * 
     * @param {HTMLElement} adjuster - Quantity adjuster element
     * @param {boolean} loading - Whether to show loading state
     */
    function setLoadingState(adjuster, loading) {
        isUpdating = loading;
        const buttons = adjuster.querySelectorAll('.quantity-btn');
        const input = adjuster.querySelector('.quantity-input');
        
        buttons.forEach(btn => {
            if (loading) {
                btn.disabled = true;
                btn.classList.add('opacity-50', 'cursor-not-allowed');
                // Show loading spinner
                const spinner = btn.querySelector('.animate-spin');
                if (spinner) spinner.classList.remove('hidden');
                // Hide icon
                const icon = btn.querySelector('svg:not(.animate-spin)');
                if (icon) icon.classList.add('hidden');
            } else {
                btn.disabled = false;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
                // Hide loading spinner
                const spinner = btn.querySelector('.animate-spin');
                if (spinner) spinner.classList.add('hidden');
                // Show icon
                const icon = btn.querySelector('svg:not(.animate-spin)');
                if (icon) icon.classList.remove('hidden');
            }
        });
        
        if (input) {
            input.disabled = loading;
            if (loading) {
                input.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                input.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    }
    
    /**
     * Update cart totals after successful operation
     * 
     * @param {Object} totals - Cart totals from server
     */
    function updateCartTotals(totals) {
        if (totals.subtotal) {
            document.getElementById('cart-subtotal').textContent = formatCurrency(totals.subtotal);
        }
        if (totals.total) {
            document.getElementById('cart-total').textContent = formatCurrency(totals.total);
        }
        if (totals.discount) {
            const discountRow = document.getElementById('discount-row');
            const discountAmount = document.getElementById('discount-amount');
            if (totals.discount > 0) {
                discountRow.classList.remove('hidden');
                discountAmount.textContent = '-' + formatCurrency(totals.discount);
            } else {
                discountRow.classList.add('hidden');
            }
        }
        
        // Update cart count badge in navigation
        updateCartCountBadge(totals.item_count || 0);
    }
    
    /**
     * Update cart count badge with animation
     * 
     * @param {number} count - New cart item count
     */
    function updateCartCountBadge(count) {
        const badge = document.querySelector('.cart-count-badge');
        if (badge) {
            const oldCount = parseInt(badge.textContent);
            if (oldCount !== count) {
                badge.textContent = count;
                badge.classList.add('animate-bounce');
                setTimeout(() => {
                    badge.classList.remove('animate-bounce');
                }, 500);
            }
        }
    }
    
    /**
     * Setup remove item buttons with confirmation
     */
    function setupRemoveItemButtons() {
        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const itemName = this.dataset.itemName;
                
                if (confirmAction(`Remove "${itemName}" from your cart?`)) {
                    removeItemFromCart(itemId, this);
                }
            });
        });
    }
    
    /**
     * Remove item from cart with animation and version control
     * 
     * @param {string} itemId - Menu item ID
     * @param {HTMLElement} button - Remove button element
     */
    function removeItemFromCart(itemId, button) {
        const cartItem = button.closest('.group');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const cartContainer = document.querySelector('.cart-container') || document.body;
        const cartVersion = cartContainer.dataset.cartVersion || 0;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<svg class="w-4 h-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Removing...';
        
        fetch(`/customer/cart/remove/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `cart_version=${cartVersion}`
        })
        .then(response => {
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                showNotification('Your session has expired. Please log in again.', 'error');
                setTimeout(() => {
                    window.location.href = '/accounts/login/';
                }, 2000);
                throw new Error('Authentication required');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update cart version on client
                if (data.cart_totals.cart_version) {
                    cartContainer.dataset.cartVersion = data.cart_totals.cart_version;
                }
                
                // Animate removal
                cartItem.style.transition = 'all 0.3s ease-out';
                cartItem.style.transform = 'translateX(-100%)';
                cartItem.style.opacity = '0';
                
                setTimeout(() => {
                    cartItem.remove();
                    updateCartTotals(data.cart_totals);
                    
                    // Check if cart is empty
                    if (data.cart_totals.item_count === 0) {
                        location.reload(); // Reload to show empty cart state
                    }
                }, 300);
                
                showNotification('Item removed from cart', 'info');
            } else {
                // Handle stale cart scenario
                if (data.requires_refresh) {
                    showNotification(data.message, 'warning');
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                } else {
                    showNotification(data.message || 'Failed to remove item', 'error');
                    button.disabled = false;
                    button.innerHTML = '<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>Remove';
                }
            }
        })
        .catch(error => {
            if (error.message !== 'Authentication required') {
                console.error('Remove item error:', error);
                showNotification('Network error. Please try again.', 'error');
                button.disabled = false;
                button.innerHTML = '<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>Remove';
            }
        });
    }
    
    /**
     * Setup promo code form with AJAX submission
     */
    function setupPromoCodeForm() {
        const form = document.getElementById('promo-code-form');
        if (!form) return;
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const input = document.getElementById('promo-code-input');
            const btn = document.getElementById('apply-promo-btn');
            const code = input.value.trim();
            
            if (!code) {
                showNotification('Please enter a promo code', 'warning');
                return;
            }
            
            // Show loading state
            btn.disabled = true;
            btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Applying...';
            
            const formData = new FormData(form);
            
            fetch('/customer/cart/apply-promo/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showPromoSuccess(data.promo_code);
                    updateCartTotals(data.cart_totals);
                    showNotification(data.message, 'success');
                } else {
                    showPromoError(data.message);
                }
            })
            .catch(error => {
                console.error('Promo code error:', error);
                showPromoError('Network error. Please try again.');
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = 'Apply';
            });
        });
    }
    
    /**
     * Show applied promo code success state
     * 
     * @param {Object} promoCode - Promo code data
     */
    function showPromoSuccess(promoCode) {
        const display = document.getElementById('applied-promo-display');
        const errorDisplay = document.getElementById('promo-error-display');
        const nameSpan = document.getElementById('applied-promo-name');
        
        errorDisplay.classList.add('hidden');
        display.classList.remove('hidden');
        nameSpan.textContent = promoCode.code;
        
        // Hide input form
        document.getElementById('promo-code-form').classList.add('hidden');
    }
    
    /**
     * Show promo code error message
     * 
     * @param {string} message - Error message
     */
    function showPromoError(message) {
        const display = document.getElementById('applied-promo-display');
        const errorDisplay = document.getElementById('promo-error-display');
        const messageSpan = document.getElementById('promo-error-message');
        
        display.classList.add('hidden');
        errorDisplay.classList.remove('hidden');
        messageSpan.textContent = message;
    }
    
    /**
     * Setup quick add buttons for popular items
     */
    function setupQuickAddButtons() {
        document.querySelectorAll('.quick-add-item').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const itemName = this.dataset.itemName;
                
                // Add loading state
                this.disabled = true;
                this.innerHTML = '<svg class="w-4 h-4 animate-spin inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Adding...';
                
                // Add to cart
                addToCart(itemId, 1, this, itemName);
            });
        });
    }
    
    /**
     * Add item to cart with animation
     * 
     * @param {string} itemId - Menu item ID
     * @param {number} quantity - Quantity to add
     * @param {HTMLElement} button - Button element
     * @param {string} itemName - Item name for notifications
     */
    function addToCart(itemId, quantity, button, itemName) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch(`/customer/cart/add/${itemId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `quantity=${quantity}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`${itemName} added to cart!`, 'success');
                updateCartCountBadge(data.cart_totals.item_count || 0);
                
                // Animate button success - button state now persists to prevent disappearing
                button.classList.add('bg-green-100', 'text-green-700', 'border-green-300');
                button.innerHTML = '✓ Added';
                button.disabled = false;
                
                /* Button states now persist - removed auto-reset to prevent disappearing effect */
            } else {
                showNotification(data.message || 'Failed to add item', 'error');
                button.disabled = false;
                button.innerHTML = button.dataset.originalText || 'Add to Cart';
            }
        })
        .catch(error => {
            console.error('Add to cart error:', error);
            showNotification('Network error. Please try again.', 'error');
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || 'Add to Cart';
        });
    }
    
    /**
     * Setup save for later functionality
     */
    function setupSaveForLaterButtons() {
        document.querySelectorAll('.save-for-later-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                const itemName = this.dataset.itemName;
                
                // Save to localStorage for now (can be enhanced with backend)
                const savedItems = JSON.parse(localStorage.getItem('savedForLater') || '[]');
                
                if (!savedItems.includes(itemId)) {
                    savedItems.push(itemId);
                    localStorage.setItem('savedForLater', JSON.stringify(savedItems));
                    
                    // Update button state
                    this.classList.add('text-blue-700', 'bg-blue-50');
                    this.innerHTML = '<svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24"><path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>Saved';
                    
                    showNotification(`${itemName} saved for later!`, 'success');
                } else {
                    showNotification('Item already saved for later', 'info');
                }
            });
        });
    }
    
    // Public API
    return {
        init: init,
        updateQuantityOptimistic: updateQuantityOptimistic,
        removeFromCart: removeItemFromCart,
        applyPromoCode: () => document.getElementById('promo-code-form').dispatchEvent(new Event('submit'))
    };
})();

/**
 * Utility functions for enhanced cart functionality
 * Provides notification system and helper functions used throughout the application
 */

// Wait for DOM to be fully loaded before executing scripts
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Initialize all interactive components on page load
     */
    initializeApp();
});

/**
 * Initialize application by setting up all interactive features
 */
function initializeApp() {
    setupMobileMenu();
    setupAutoHideMessages();
    setupFormValidation();
    setupImagePreview();
    
    // Initialize enhanced cart management if on cart page
    if (document.querySelector('.quantity-adjuster')) {
        CartManager.init();
    }
}

/**
 * Setup mobile menu toggle functionality
 * Handles opening and closing of mobile navigation menu
 */
function setupMobileMenu() {
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
            
            // Toggle icon between hamburger and close
            const icon = menuButton.querySelector('svg');
            if (icon) {
                icon.classList.toggle('rotate-90');
            }
        });
    }
}

/**
 * Auto-hide success/info messages - DISABLED to prevent disappearing elements
 * Messages now stay visible until manually closed by user
 */
function setupAutoHideMessages() {
    /* Auto-hide disabled - messages now persist to prevent disappearing effect */
    // const messages = document.querySelectorAll('[class*="bg-green"], [class*="bg-blue"]');
    // 
    // messages.forEach(function(message) {
    //     setTimeout(function() {
    //         message.style.transition = 'opacity 0.5s ease-out';
    //         message.style.opacity = '0';
    //         
    //         setTimeout(function() {
    //             message.remove();
    //         }, 500);
    //     }, 5000);
    // });
}

/**
 * Show notification message to user with enhanced styling
 * @param {string} message - Message to display
 * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    
    if (!container) {
        // Create container if it doesn't exist
        const newContainer = document.createElement('div');
        newContainer.id = 'notification-container';
        newContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(newContainer);
    }
    
    // Create notification element with enhanced styling
    const notification = document.createElement('div');
    notification.className = `p-4 rounded-lg shadow-lg fade-in max-w-sm transform transition-all duration-300 ${getNotificationClass(type)}`;
    
    // Add icon based on type
    const icon = getNotificationIcon(type);
    notification.innerHTML = `
        <div class="flex items-center">
            <span class="flex-shrink-0 mr-3">${icon}</span>
            <span class="flex-1">${message}</span>
            <button class="ml-3 flex-shrink-0 text-white hover:text-gray-200 transition-colors" onclick="this.parentElement.parentElement.remove()">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Append and auto-remove with enhanced animation
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('scale-100', 'opacity-100');
        notification.classList.remove('scale-95', 'opacity-0');
    }, 10);
    
    // Notifications now stay visible - removed auto-hide to prevent disappearing effect
}

/**
 * Get notification icon based on type
 * @param {string} type - Notification type
 * @returns {string} SVG icon HTML
 */
function getNotificationIcon(type) {
    const icons = {
        'success': '<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>',
        'error': '<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>',
        'warning': '<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>',
        'info': '<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
    };
    return icons[type] || icons['info'];
}

/**
 * Get Tailwind CSS classes for notification type with enhanced styling
 * @param {string} type - Notification type
 * @returns {string} CSS classes
 */
function getNotificationClass(type) {
    const classes = {
        'success': 'bg-gradient-to-r from-green-500 to-green-600 text-white border-l-4 border-green-700 shadow-lg',
        'error': 'bg-gradient-to-r from-red-500 to-red-600 text-white border-l-4 border-red-700 shadow-lg',
        'warning': 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white border-l-4 border-yellow-700 shadow-lg',
        'info': 'bg-gradient-to-r from-blue-500 to-blue-600 text-white border-l-4 border-blue-700 shadow-lg'
    };
    return classes[type] || classes['info'];
}

/**
 * Format currency value for display with proper formatting
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Show confirmation dialog for user actions
 * @param {string} message - Confirmation message to display
 * @returns {boolean} True if user confirms, false otherwise
 */
function confirmAction(message) {
    return confirm(message);
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Export functions for use in other scripts
window.foodOrderingApp = {
    showNotification,
    formatCurrency,
    debounce,
    confirmAction
};
