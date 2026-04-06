/**
 * Nearby Destinations Feature
 * 
 * This module handles fetching and displaying nearby travel destinations
 * based on the user's current location. It uses the browser's Geolocation API
 * to get coordinates and calls the backend API to fetch destinations within
 * a specified radius.
 */

// Configuration options
const NEARBY_CONFIG = {
    radius: 10, // Search radius in kilometers
    limit: 6,   // Maximum number of destinations to show
    elementId: 'nearby-destinations-container', // Container for nearby destinations
    loaderElementId: 'nearby-destinations-loader', // Loading indicator element
    errorElementId: 'nearby-destinations-error', // Error message container
    apiEndpoint: '/destinations/api/nearby/', // Backend API endpoint
    fallbackLatitude: 51.5074, // London coordinates as fallback
    fallbackLongitude: -0.1278,
    enableHighAccuracy: true, // GPS vs. network-based geolocation
    locationTimeout: 10000, // Maximum time to wait for location (10 seconds)
}

/**
 * Initialize the nearby destinations feature
 * Detects user location and loads nearby destinations
 */
function initNearbyDestinations() {
    // Get container elements
    const container = document.getElementById(NEARBY_CONFIG.elementId);
    const loader = document.getElementById(NEARBY_CONFIG.loaderElementId);
    const errorContainer = document.getElementById(NEARBY_CONFIG.errorElementId);
    
    // Check if the necessary elements exist in the DOM
    if (!container) {
        console.error('Nearby destinations container not found');
        return;
    }
    
    // Show loader if it exists
    if (loader) {
        loader.style.display = 'block';
    }
    
    // Hide error container initially
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
    
    // Check if geolocation is available
    if (navigator.geolocation) {
        // Get user's current position
        navigator.geolocation.getCurrentPosition(
            // Success callback
            position => {
                const { latitude, longitude } = position.coords;
                fetchNearbyDestinations(latitude, longitude);
            },
            // Error callback
            error => {
                console.warn('Geolocation error:', error.message);
                handleLocationError(error);
            },
            // Options
            {
                enableHighAccuracy: NEARBY_CONFIG.enableHighAccuracy,
                timeout: NEARBY_CONFIG.locationTimeout,
                maximumAge: 0 // Always get a fresh position
            }
        );
    } else {
        // Geolocation not supported
        console.warn('Geolocation is not supported by this browser');
        handleLocationError({ code: 0, message: 'Geolocation not supported' });
    }
}

/**
 * Handle location errors by using fallback coordinates or showing an error message
 * @param {Error} error - The geolocation error
 */
function handleLocationError(error) {
    const errorContainer = document.getElementById(NEARBY_CONFIG.errorElementId);
    const loader = document.getElementById(NEARBY_CONFIG.loaderElementId);
    
    // Hide loader
    if (loader) {
        loader.style.display = 'none';
    }
    
    // Use fallback coordinates to still show some destinations
    fetchNearbyDestinations(
        NEARBY_CONFIG.fallbackLatitude, 
        NEARBY_CONFIG.fallbackLongitude
    );
    
    // Show appropriate error message if error container exists
    if (errorContainer) {
        let errorMessage = '';
        
        switch (error.code) {
            case 1: // PERMISSION_DENIED
                errorMessage = 'Location access was denied. Showing popular destinations instead.';
                break;
            case 2: // POSITION_UNAVAILABLE
                errorMessage = 'Location information is unavailable. Showing popular destinations instead.';
                break;
            case 3: // TIMEOUT
                errorMessage = 'Location request timed out. Showing popular destinations instead.';
                break;
            default:
                errorMessage = 'An unknown error occurred while trying to access your location. Showing popular destinations instead.';
        }
        
        errorContainer.textContent = errorMessage;
        errorContainer.style.display = 'block';
    }
}

/**
 * Fetch nearby destinations from the API using the provided coordinates
 * @param {number} latitude - The latitude coordinate
 * @param {number} longitude - The longitude coordinate
 */
function fetchNearbyDestinations(latitude, longitude) {
    const apiUrl = `${NEARBY_CONFIG.apiEndpoint}?lat=${latitude}&lng=${longitude}&radius=${NEARBY_CONFIG.radius}&limit=${NEARBY_CONFIG.limit}`;
    const container = document.getElementById(NEARBY_CONFIG.elementId);
    const loader = document.getElementById(NEARBY_CONFIG.loaderElementId);
    const errorContainer = document.getElementById(NEARBY_CONFIG.errorElementId);
    
    // Make the API request
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide loader
            if (loader) {
                loader.style.display = 'none';
            }
            
            // Process and display the destinations
            if (data.success && data.destinations && data.destinations.length > 0) {
                renderNearbyDestinations(data.destinations);
            } else {
                throw new Error('No nearby destinations found');
            }
        })
        .catch(error => {
            console.error('Error fetching nearby destinations:', error);
            
            // Hide loader
            if (loader) {
                loader.style.display = 'none';
            }
            
            // Show error message
            if (errorContainer) {
                errorContainer.textContent = 'Unable to find destinations near you. Please try again later.';
                errorContainer.style.display = 'block';
            }
            
            // Show empty state or fallback content in container
            container.innerHTML = `
                <div class="text-center py-10">
                    <p class="text-gray-500">No destinations found nearby.</p>
                </div>
            `;
        });
}

/**
 * Render the nearby destinations in the container
 * @param {Array} destinations - Array of destination objects from the API
 */
function renderNearbyDestinations(destinations) {
    const container = document.getElementById(NEARBY_CONFIG.elementId);
    
    // Clear the container
    container.innerHTML = '';
    
    // Create HTML for each destination
    destinations.forEach((destination, index) => {
        // Create the destination card with proper styling and animation
        const card = document.createElement('div');
        card.className = 'group relative overflow-hidden rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2';
        card.setAttribute('data-aos', 'fade-up');
        card.setAttribute('data-aos-delay', (index * 100).toString());
        
        // Calculate badge color using modulo for cycling through colors
        const badgeColors = [
            'bg-green-100 text-green-800', 
            'bg-blue-100 text-blue-800', 
            'bg-purple-100 text-purple-800', 
            'bg-yellow-100 text-yellow-800'
        ];
        const badgeColor = badgeColors[index % badgeColors.length];
        
        // Calculate button gradient using modulo for cycling through gradients
        const buttonGradients = [
            'from-blue-500 to-indigo-600',
            'from-purple-500 to-pink-500',
            'from-green-500 to-teal-500',
            'from-yellow-500 to-orange-500'
        ];
        const buttonGradient = buttonGradients[index % buttonGradients.length];
        
        // Format the distance for display
        const distanceText = destination.distance === 1 
            ? '1 km away' 
            : `${destination.distance} km away`;
        
        // Build card HTML with image, details, and action button
        card.innerHTML = `
            <div class="relative h-72 overflow-hidden">
                <img src="${destination.image_url || 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80'}" 
                     alt="${destination.name}" 
                     class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                <div class="absolute bottom-0 left-0 p-6 w-full">
                    <div class="flex justify-between items-center">
                        <span class="px-3 py-1 rounded-full text-xs font-medium ${badgeColor}">
                            ${distanceText}
                        </span>
                        ${destination.rating ? `
                            <div class="flex items-center bg-white/20 backdrop-blur-sm px-2 py-1 rounded-full">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118l-2.8-2.034c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                <span class="text-white text-xs ml-1">${destination.rating}</span>
                            </div>
                        ` : ''}
                    </div>
                    <h3 class="text-xl font-bold text-white mt-2">${destination.name}</h3>
                    <p class="text-sm text-white/80">${destination.city}${destination.country ? `, ${destination.country}` : ''}</p>
                </div>
            </div>
            <div class="p-6 bg-white">
                <p class="text-sm text-gray-600 mb-4">${destination.short_description || 'Discover this amazing destination near you.'}</p>
                <div class="flex justify-between items-center">
                    ${destination.price ? `
                        <p class="text-lg font-bold text-gray-900">$${destination.price}</p>
                    ` : `
                        <div></div>
                    `}
                    <a href="/destinations/${destination.slug}/" class="inline-block px-4 py-2 bg-gradient-to-r ${buttonGradient} text-white font-medium rounded-lg text-sm transition-transform hover:scale-105">
                        Explore
                    </a>
                </div>
            </div>
        `;
        
        // Add the card to the container
        container.appendChild(card);
    });
    
    // Initialize AOS animations if AOS is available
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initNearbyDestinations);
