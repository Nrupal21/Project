/**
 * TravelGuide Modern Interactions
 * @description Enhanced JavaScript for modern UI/UX interactions
 * @version 2.0
 * @author TravelGuide Team
 * 
 * This file contains:
 * - Smooth scroll behaviors
 * - Intersection Observer animations
 * - Modern navigation interactions
 * - Form enhancements
 * - Image lazy loading
 * - Parallax effects
 * - Toast notifications
 * - Modal management
 */

/**
 * Initialize all modern interactions when DOM is ready
 * @description Main initialization function that sets up all interactive features
 */
document.addEventListener('DOMContentLoaded', function() {
    initSmoothScroll();
    initScrollAnimations();
    initLazyLoading();
    initParallax();
    initNavbar();
    initTooltips();
    initModals();
    initFormEnhancements();
    initCardHoverEffects();
    initImageGallery();
});

/**
 * Smooth Scroll Implementation
 * @description Enables smooth scrolling for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            
            // Skip if href is just "#"
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Scroll Animations with Intersection Observer
 * @description Animates elements as they enter the viewport
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                
                // Add stagger delay for children
                const children = entry.target.querySelectorAll('[data-stagger]');
                children.forEach((child, index) => {
                    child.style.animationDelay = `${index * 0.1}s`;
                });
                
                // Unobserve after animation
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all elements with data-animate attribute
    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Lazy Loading for Images
 * @description Implements lazy loading for better performance
 */
function initLazyLoading() {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.getAttribute('data-src');
                
                if (src) {
                    img.src = src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

/**
 * Parallax Scrolling Effect
 * @description Creates depth with parallax scrolling
 */
function initParallax() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');
    
    if (parallaxElements.length === 0) return;
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(el => {
            const speed = el.getAttribute('data-parallax-speed') || 0.5;
            const yPos = -(scrolled * speed);
            el.style.transform = `translateY(${yPos}px)`;
        });
    });
}

/**
 * Enhanced Navbar Behavior
 * @description Adds scroll-based navbar styling and mobile menu
 */
function initNavbar() {
    const navbar = document.getElementById('main-header');
    if (!navbar) return;
    
    let lastScroll = 0;
    const scrollThreshold = 100;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Add/remove scrolled class
        if (currentScroll > scrollThreshold) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
        
        // Hide/show navbar on scroll
        if (currentScroll > lastScroll && currentScroll > scrollThreshold) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
    
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('[data-mobile-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('open');
            document.body.classList.toggle('menu-open');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                mobileMenu.classList.remove('open');
                document.body.classList.remove('menu-open');
            }
        });
    }
}

/**
 * Tooltip Implementation
 * @description Shows tooltips on hover
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(el => {
        const tooltipText = el.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 9999;
            white-space: nowrap;
        `;
        
        el.style.position = 'relative';
        
        el.addEventListener('mouseenter', (e) => {
            document.body.appendChild(tooltip);
            const rect = el.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
            setTimeout(() => tooltip.style.opacity = '1', 10);
        });
        
        el.addEventListener('mouseleave', () => {
            tooltip.style.opacity = '0';
            setTimeout(() => tooltip.remove(), 300);
        });
    });
}

/**
 * Modal Management
 * @description Handles modal open/close with animations
 */
function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal-trigger]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = trigger.getAttribute('data-modal-trigger');
            const modal = document.getElementById(modalId);
            
            if (modal) {
                openModal(modal);
            }
        });
    });
    
    // Close modal buttons
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            if (modal) {
                closeModal(modal);
            }
        });
    });
    
    // Close on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                const modal = backdrop.closest('.modal');
                if (modal) {
                    closeModal(modal);
                }
            }
        });
    });
}

/**
 * Open Modal
 * @param {HTMLElement} modal - Modal element to open
 */
function openModal(modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Trap focus within modal
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    firstElement?.focus();
    
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal(modal);
        }
        
        if (e.key === 'Tab') {
            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement?.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement?.focus();
            }
        }
    });
}

/**
 * Close Modal
 * @param {HTMLElement} modal - Modal element to close
 */
function closeModal(modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

/**
 * Form Enhancements
 * @description Adds modern form behaviors and validation
 */
function initFormEnhancements() {
    // Floating labels
    const floatingInputs = document.querySelectorAll('.floating-label-group input');
    
    floatingInputs.forEach(input => {
        // Check if input has value on load
        if (input.value) {
            input.classList.add('has-value');
        }
        
        input.addEventListener('blur', () => {
            if (input.value) {
                input.classList.add('has-value');
            } else {
                input.classList.remove('has-value');
            }
        });
    });
    
    // Real-time validation
    const validatableInputs = document.querySelectorAll('input[data-validate]');
    
    validatableInputs.forEach(input => {
        input.addEventListener('blur', () => {
            validateInput(input);
        });
        
        input.addEventListener('input', () => {
            if (input.classList.contains('invalid')) {
                validateInput(input);
            }
        });
    });
}

/**
 * Validate Input Field
 * @param {HTMLInputElement} input - Input element to validate
 */
function validateInput(input) {
    const validationType = input.getAttribute('data-validate');
    let isValid = true;
    let errorMessage = '';
    
    switch (validationType) {
        case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            isValid = emailRegex.test(input.value);
            errorMessage = 'Please enter a valid email address';
            break;
        case 'required':
            isValid = input.value.trim() !== '';
            errorMessage = 'This field is required';
            break;
        case 'phone':
            const phoneRegex = /^[\d\s\-\+\(\)]+$/;
            isValid = phoneRegex.test(input.value) && input.value.length >= 10;
            errorMessage = 'Please enter a valid phone number';
            break;
    }
    
    if (isValid) {
        input.classList.remove('invalid');
        input.classList.add('valid');
        removeErrorMessage(input);
    } else {
        input.classList.remove('valid');
        input.classList.add('invalid');
        showErrorMessage(input, errorMessage);
    }
    
    return isValid;
}

/**
 * Show Error Message
 * @param {HTMLInputElement} input - Input element
 * @param {string} message - Error message to display
 */
function showErrorMessage(input, message) {
    removeErrorMessage(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 0.875rem;
        margin-top: 0.25rem;
        animation: fadeInUp 0.3s ease;
    `;
    
    input.parentNode.appendChild(errorDiv);
}

/**
 * Remove Error Message
 * @param {HTMLInputElement} input - Input element
 */
function removeErrorMessage(input) {
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Card Hover Effects
 * @description Adds 3D tilt effect to cards
 */
function initCardHoverEffects() {
    const cards = document.querySelectorAll('[data-tilt]');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        });
    });
}

/**
 * Image Gallery
 * @description Creates lightbox for image galleries
 */
function initImageGallery() {
    const galleryImages = document.querySelectorAll('[data-gallery]');
    
    if (galleryImages.length === 0) return;
    
    galleryImages.forEach(img => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => {
            openLightbox(img.src, img.alt);
        });
    });
}

/**
 * Open Lightbox
 * @param {string} src - Image source URL
 * @param {string} alt - Image alt text
 */
function openLightbox(src, alt) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;
    
    const img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        animation: scaleIn 0.3s ease;
    `;
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        position: absolute;
        top: 2rem;
        right: 2rem;
        background: white;
        border: none;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        font-size: 2rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s;
    `;
    
    closeBtn.addEventListener('click', () => {
        lightbox.style.opacity = '0';
        setTimeout(() => lightbox.remove(), 300);
    });
    
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            lightbox.style.opacity = '0';
            setTimeout(() => lightbox.remove(), 300);
        }
    });
    
    lightbox.appendChild(img);
    lightbox.appendChild(closeBtn);
    document.body.appendChild(lightbox);
}

/**
 * Toast Notification System
 * @description Shows toast notifications
 */
const Toast = {
    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type of toast (success, error, info, warning)
     * @param {number} duration - Duration in milliseconds
     */
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        
        toast.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: ${colors[type]};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            animation: slideInUp 0.3s ease;
            max-width: 400px;
        `;
        
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

/**
 * Debounce Function
 * @description Limits function execution rate
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle Function
 * @description Limits function execution frequency
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other scripts
window.TravelGuide = {
    Toast,
    debounce,
    throttle,
    openModal,
    closeModal
};
