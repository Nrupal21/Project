/**
 * JavaScript for handling the AI Itinerary Form interactions
 * 
 * This script handles:
 * - Interest checkbox selection and styling
 * - Destination search functionality
 * - Form validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize interest checkboxes
    initInterestCheckboxes();
    
    // Handle destination search functionality
    initDestinationSearch();
    
    // Form validation
    initFormValidation();
});

/**
 * Initialize interest checkboxes with click handlers
 */
function initInterestCheckboxes() {
    const interestCheckboxes = document.querySelectorAll('input[name="interests"]');
    
    interestCheckboxes.forEach(checkbox => {
        // Add click handler to the label
        const label = document.querySelector(`label[for="${checkbox.id}"]`);
        
        if (label) {
            label.addEventListener('click', function(e) {
                // Toggle the checkbox state
                checkbox.checked = !checkbox.checked;
                // Update the UI
                updateCheckboxStyle(checkbox);
            });
        }
        
        // Update UI when checkbox state changes
        checkbox.addEventListener('change', function() {
            updateCheckboxStyle(this);
        });
        
        // Set initial state
        updateCheckboxStyle(checkbox);
    });
}

/**
 * Update the visual style of a checkbox based on its state
 * @param {HTMLInputElement} checkbox - The checkbox element to update
 */
function updateCheckboxStyle(checkbox) {
    const label = document.querySelector(`label[for="${checkbox.id}"]`);
    if (!label) return;
    
    if (checkbox.checked) {
        // Add checked styles
        label.classList.add(
            'bg-indigo-100', 'dark:bg-indigo-900/50', 
            'border-indigo-500', 'dark:border-indigo-400', 
            'text-indigo-700', 'dark:text-indigo-200'
        );
        label.classList.remove(
            'bg-white', 'dark:bg-gray-700', 
            'text-gray-700', 'dark:text-gray-300'
        );
    } else {
        // Add unchecked styles
        label.classList.remove(
            'bg-indigo-100', 'dark:bg-indigo-900/50', 
            'border-indigo-500', 'dark:border-indigo-400', 
            'text-indigo-700', 'dark:text-indigo-200'
        );
        label.classList.add(
            'bg-white', 'dark:bg-gray-700', 
            'text-gray-700', 'dark:text-gray-300'
        );
    }
}

/**
 * Initialize destination search functionality
 */
function initDestinationSearch() {
    const cityInput = document.getElementById('city');
    const destinationIdInput = document.getElementById('destination_id');
    const suggestionsContainer = document.getElementById('destination-suggestions');
    
    if (!cityInput || !suggestionsContainer) return;
    
    // Handle clicks on suggestion items
    suggestionsContainer.addEventListener('click', function(e) {
        if (e.target && e.target.matches('.suggestion-item')) {
            e.preventDefault();
            const destinationId = e.target.dataset.id;
            const destinationName = e.target.textContent.trim();
            
            // Update the city input and set the hidden destination_id
            if (cityInput) cityInput.value = destinationName;
            if (destinationIdInput) destinationIdInput.value = destinationId;
            
            // Clear the suggestions
            suggestionsContainer.innerHTML = '';
        }
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        // Check if at least one interest is selected
        const checkedInterests = form.querySelectorAll('input[name="interests"]:checked');
        if (checkedInterests.length === 0) {
            e.preventDefault();
            alert('Please select at least one interest.');
            return false;
        }
        
        // Check if destination is selected
        const destinationId = document.getElementById('destination_id');
        if (destinationId && !destinationId.value) {
            e.preventDefault();
            alert('Please select a destination from the suggestions.');
            return false;
        }
        
        return true;
    });
}
