/**
 * Google AdSense Configuration File
 * 
 * This file centralizes all Google AdSense configurations for the TravelGuide website.
 * Using a separate file for ad configuration makes it easier to manage and update ad settings.
 * 
 * @author TravelGuide Development Team
 * @version 1.0.0
 */

/**
 * Publisher ID for Google AdSense
 * Replace with your actual Google AdSense publisher ID
 * Format: ca-pub-XXXXXXXXXXXXXXXX
 */
const ADSENSE_PUBLISHER_ID = 'ca-pub-YOUR_PUBLISHER_ID';

/**
 * Ad slot IDs for different ad units
 * Each ad placement needs its unique slot ID from Google AdSense dashboard
 */
const AD_SLOTS = {
    /**
     * Top banner ad slot - appears below navigation
     * This is typically the first ad users see when visiting a page
     */
    topBanner: 'YOUR_AD_SLOT_ID',
    
    /**
     * Bottom banner ad slot - appears above footer
     * Positioned for visibility as users reach the end of content
     */
    bottomBanner: 'YOUR_AD_SLOT_ID_BOTTOM',
    
    /**
     * Sidebar ad slot - appears in sidebar (if implemented)
     * Good for sticky ads that stay visible while scrolling
     */
    sidebar: 'YOUR_SIDEBAR_AD_SLOT_ID'
};

/**
 * Initialize all ad units on the page
 * This function should be called after the DOM is fully loaded
 * It finds all adsbygoogle elements and initializes them
 */
function initializeAds() {
    console.log('Initializing Google AdSense ads...');
    
    // Initialize each ad unit individually or use the push method for all
    document.querySelectorAll('.adsbygoogle').forEach((adElement, index) => {
        try {
            // Push to adsbygoogle to initialize this specific ad
            (adsbygoogle = window.adsbygoogle || []).push({});
            console.log(`Ad unit ${index + 1} initialized`);
        } catch (error) {
            console.error(`Error initializing ad unit ${index + 1}:`, error);
        }
    });
}

/**
 * Checks if AdBlocker is potentially active
 * This can help show alternative content if ads are being blocked
 * @returns {Promise<boolean>} True if AdBlocker is likely active
 */
function checkAdBlocker() {
    return new Promise((resolve) => {
        // Create a test ad element
        const testAd = document.createElement('div');
        testAd.innerHTML = '&nbsp;';
        testAd.className = 'adsbox';
        document.body.appendChild(testAd);
        
        // Wait a moment for AdBlocker to hide the element if active
        setTimeout(() => {
            const isBlocked = testAd.offsetHeight === 0;
            testAd.remove();
            resolve(isBlocked);
        }, 100);
    });
}

/**
 * Shows alternative content if ads are blocked
 * This provides a better user experience than empty ad containers
 */
async function handleAdBlocker() {
    const isBlocked = await checkAdBlocker();
    
    if (isBlocked) {
        console.log('Ad blocker detected');
        document.querySelectorAll('.ad-container').forEach(container => {
            // Replace ad containers with alternative content
            container.innerHTML = `
                <div class="ad-alternative p-4 text-center text-gray-600 bg-gray-100 rounded-lg">
                    <p>Support our site by disabling your ad blocker</p>
                    <p class="text-sm mt-2">We use non-intrusive ads to keep our content free</p>
                </div>
            `;
        });
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ADSENSE_PUBLISHER_ID,
        AD_SLOTS,
        initializeAds,
        checkAdBlocker,
        handleAdBlocker
    };
}
