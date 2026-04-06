# Guides Travel Management Platform - Development Guidelines

## Introduction

This document outlines the development guidelines and standards for the Guides travel management platform. Following these guidelines will ensure consistency, maintainability, and high quality across the codebase. All developers working on this project must adhere to these standards.

## Project Structure

The Guides project is organized as a Django-based application with the following structure:

```
Guides/
├── accounts/         # User authentication and profile management
├── bookings/         # Booking system for tours and accommodations
├── core/             # Core functionality and shared components
├── destinations/     # Destination information and management
├── Doc/              # Project documentation
├── emergency/        # Emergency services and safety information
├── guides/           # Main project configuration and settings
├── itineraries/      # Itinerary planning and management
├── notifications/    # User notification system
├── reviews/          # Review system and ratings
├── rewards/          # User loyalty and rewards program
├── security/         # Security features including 2FA
├── static/           # Static assets (CSS, JS, images)
├── templates/        # HTML templates
├── tours/            # Tour package management
├── transportation/   # Transportation services and booking
├── media/            # User-uploaded content
└── scripts/          # Utility scripts
```

## Coding Standards

### General Standards

1. Follow PEP 8 guidelines for Python code
2. Use 4 spaces for indentation (not tabs)
3. Maximum line length: 88 characters
4. Use descriptive variable and function names
5. Keep functions and methods small and focused on a single task
6. Write tests for all new functionality

### Documentation Standards

#### Function Comments

**EVERY** function must have comprehensive comments that include:

```python
def calculate_reward_points(user_id, transaction_amount, promotion_code=None):
    """
    Calculate reward points for a user based on transaction amount and optional promotion.
    
    Args:
        user_id (int): The unique identifier of the user
        transaction_amount (Decimal): The amount of the transaction in default currency
        promotion_code (str, optional): Promotion code for bonus points
        
    Returns:
        int: The number of points earned from this transaction
        
    Raises:
        UserNotFoundError: If user_id doesn't exist
        InvalidPromotionError: If promotion_code is invalid
        
    Example:
        >>> calculate_reward_points(42, Decimal('100.00'), 'SUMMER2025')
        150
    """
    # Implementation here
```

#### Class Comments

All classes must include:

```python
class RewardCalculator:
    """
    Handles calculation of reward points for user transactions.
    
    This class manages the logic for determining point values based on 
    transaction amounts, user tier status, and active promotions.
    
    Attributes:
        point_multiplier (float): Base multiplier for point calculation
        tier_bonuses (dict): Point bonuses based on user tier level
        
    Usage:
        calculator = RewardCalculator()
        points = calculator.calculate(user, amount)
    """
```

#### Model Comments

All models must include field descriptions:

```python
class Destination(models.Model):
    """
    Represents a travel destination in the system.
    
    This model stores comprehensive information about destinations including
    geographic data, descriptive content, and relationship to regions.
    """
    
    name = models.CharField(
        max_length=100,
        help_text="The display name of the destination"
    )
    # More fields with comments
```

### Template Organization

1. **All HTML files must be stored in the templates folder**
2. Templates should follow a nested structure based on the app:

```
templates/
├── accounts/
│   ├── login.html
│   ├── profile.html
│   └── register.html
├── base.html
├── destinations/
│   ├── destination_detail.html
│   └── destination_list.html
└── tours/
    ├── tour_detail.html
    └── tour_list.html
```

3. Each template file must include header comments:

```html
{# 
   Template: destination_detail.html
   Purpose: Displays detailed information about a single destination
   Context variables:
     - destination: Destination object with all related data
     - attractions: QuerySet of related Attraction objects
     - reviews: QuerySet of destination reviews
   
   Extends: base.html
   Blocks: content, sidebar, scripts
#}
```

4. Document template blocks and include files:

```html
{% extends "base.html" %}

{# Main content block containing destination information #}
{% block content %}
    <div class="destination-detail">
        {# Include the destination header with image gallery #}
        {% include "destinations/partials/destination_header.html" %}
        
        {# Description section with expandable content #}
        <section class="destination-description">
            <!-- Content here -->
        </section>
    </div>
{% endblock %}
```

### Styling Guidelines

1. **Use Tailwind CSS for styling whenever possible**
2. Minimize custom CSS and prefer Tailwind utility classes
3. When custom CSS is necessary, document it extensively

```html
<!-- Preferred approach using Tailwind CSS -->
<div class="p-4 bg-indigo-100 rounded-lg shadow-md hover:bg-indigo-200 transition-colors duration-300">
    <h2 class="text-xl font-semibold text-indigo-800">Destination Name</h2>
    <p class="text-gray-700 mt-2">Destination description goes here...</p>
</div>

<!-- When custom CSS is necessary, document it -->
<div class="destination-card">
    <h2>Destination Name</h2>
    <p>Destination description goes here...</p>
</div>

<!-- Custom CSS should be documented -->
<style>
/* 
 * Destination card component
 * Used for displaying destination previews in lists and search results
 * Implements hover effects and consistent spacing
 */
.destination-card {
    padding: 1rem;
    background-color: theme('colors.indigo.100');
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: background-color 0.3s ease;
}
</style>
```

## Version Control Guidelines

1. Use feature branches for development
2. Branch naming convention: `feature/feature-name`, `bugfix/issue-description`
3. Write descriptive commit messages
4. Reference issue numbers in commit messages
5. Create pull requests for code review before merging

## Database Guidelines

1. Create migrations for all model changes
2. Add appropriate indexes for frequently queried fields
3. Use Django ORM features instead of raw SQL when possible
4. Document complex queries with comments explaining their purpose

## API Guidelines

1. Follow REST principles for API design
2. Document all API endpoints with:
   - URL pattern
   - HTTP methods
   - Request parameters
   - Response format
   - Authentication requirements
   - Error responses
3. Version the API appropriately
4. Use JWT for authentication

## Testing Guidelines

1. Write tests for all new features and bug fixes
2. Follow the testing structure:
   - Unit tests for individual functions
   - Integration tests for API endpoints
   - End-to-end tests for critical user flows
3. Run tests before committing changes

## Performance Guidelines

1. Optimize database queries (use `select_related` and `prefetch_related`)
2. Use caching where appropriate
3. Optimize frontend assets (minify, compress)
4. Document performance considerations in function comments

## Security Guidelines

1. Validate all user input
2. Protect against common vulnerabilities (XSS, CSRF, SQL injection)
3. Use HTTPS for all communication
4. Follow the principle of least privilege

## Deployment Process

1. Staging environment deployment for testing
2. Production deployment only after QA approval
3. Use CI/CD for automated testing and deployment
4. Monitor application performance and errors

## Timeline

Please refer to the [project_timeline.md](project_timeline.md) document for the detailed project timeline with milestones and target dates.

## Conclusion

Following these guidelines will ensure a consistent, maintainable, and high-quality codebase for the Guides travel management platform. All developers are expected to adhere to these standards and actively contribute to improving them as needed.
