# Code Commenting Checklist

## Overview
This document provides a comprehensive checklist for ensuring that **every function in all files** is properly commented and easy to understand. Proper code documentation is a critical requirement for the Guides project to ensure maintainability, knowledge transfer, and efficient collaboration.

## Function Comment Checklist

### Essential Elements
Each function comment must include:

- [ ] **Purpose description**: Clear explanation of what the function does
- [ ] **Parameter descriptions**: For each parameter, explain its purpose, type, and any constraints
- [ ] **Return value description**: What the function returns and its meaning
- [ ] **Exception information**: Any exceptions that might be raised
- [ ] **Usage examples**: For complex functions, include example usage

### Comment Format

```python
def calculate_distance(origin, destination):
    """
    Calculate the Haversine distance between two geographic points.
    
    Args:
        origin (tuple): A tuple containing the latitude and longitude of the origin point (lat, lng)
        destination (tuple): A tuple containing the latitude and longitude of the destination point (lat, lng)
    
    Returns:
        float: Distance between the points in kilometers
    
    Raises:
        ValueError: If coordinates are not within valid ranges
    
    Example:
        >>> calculate_distance((40.7128, -74.0060), (34.0522, -118.2437))
        3935.9547505083156
    """
    # Implementation here
```

## Class Comment Checklist

### Essential Elements
Each class comment must include:

- [ ] **Class purpose**: What the class represents or does
- [ ] **Attributes**: Description of class attributes
- [ ] **Usage information**: How the class should be used
- [ ] **Related classes**: Mention related classes if applicable

### Comment Format

```python
class Destination(models.Model):
    """
    Represents a travel destination with detailed information.
    
    This model stores comprehensive information about travel destinations
    including geographic data, descriptions, and metadata for search optimization.
    
    Attributes:
        name (str): Name of the destination
        description (str): Detailed description
        latitude (Decimal): Geographic latitude coordinate
        longitude (Decimal): Geographic longitude coordinate
        region (ForeignKey): Reference to the Region model
        slug (str): URL-friendly identifier
    
    Related:
        Region: Each destination belongs to a region
        Attraction: Destinations contain multiple attractions
    """
    # Implementation here
```

## Inline Comment Checklist

For complex code blocks within functions:

- [ ] **Algorithm explanation**: Explain complex algorithms or logic
- [ ] **Decision reasoning**: Explain why certain approaches were chosen
- [ ] **Formula explanation**: Document any mathematical or business formulas
- [ ] **Workaround notes**: Explain any non-obvious solutions or workarounds

### Comment Format

```python
def calculate_price(base_price, season_factor, promotion_code=None):
    """
    Calculate the final price based on base price, season, and promotions.
    
    Args:
        base_price (float): Base price of the tour/accommodation
        season_factor (float): Seasonal pricing multiplier
        promotion_code (str, optional): Promotion code for discounts
    
    Returns:
        float: Final calculated price
    """
    # Apply seasonal adjustment
    adjusted_price = base_price * season_factor
    
    # Apply promotion if valid
    if promotion_code:
        # Check if promotion exists and is valid
        promotion = Promotion.objects.filter(
            code=promotion_code,
            is_active=True,
            valid_from__lte=datetime.now(),
            valid_to__gte=datetime.now()
        ).first()
        
        if promotion:
            # Percentage-based discounts are applied after seasonal adjustments
            # to ensure consistent discount behavior across seasons
            if promotion.discount_type == 'PERCENTAGE':
                adjusted_price *= (1 - promotion.discount_value / 100)
            # Fixed amount discounts are applied directly
            elif promotion.discount_type == 'FIXED':
                adjusted_price -= promotion.discount_value
    
    # Ensure price never goes below minimum threshold (cost price)
    # This prevents selling at a loss even with heavy discounts
    if adjusted_price < base_price * 0.7:  # 70% of base is our cost floor
        adjusted_price = base_price * 0.7
    
    return round(adjusted_price, 2)  # Round to 2 decimal places for currency
```

## Module/File Comment Checklist

At the top of each file:

- [ ] **Module purpose**: Brief description of the file's purpose
- [ ] **Author information**: Who created/maintains the file
- [ ] **Module-level dependencies**: Important imports and their purpose
- [ ] **Module usage**: How this module fits into the larger system

### Comment Format

```python
"""
Destination management module for the Guides platform.

This module handles the creation, retrieval, updating, and deletion of
travel destinations. It includes models, views, serializers, and utility
functions for managing destination data.

Author: [Developer Name]
Created: 2025-07-15
"""
```

## Django-Specific Comment Checklist

### Models
- [ ] **Field purpose**: Comment on each model field
- [ ] **Validation logic**: Explain any custom validation
- [ ] **Index rationale**: Explain why indexes were added
- [ ] **Meta options**: Explain any custom Meta options

### Views
- [ ] **View purpose**: What the view displays or processes
- [ ] **Permission requirements**: What permissions are needed
- [ ] **Form handling**: How form data is processed
- [ ] **Context data**: Explain additional context variables

### Forms
- [ ] **Form purpose**: What data the form collects
- [ ] **Validation rules**: Custom validation explanation
- [ ] **Widget choices**: Why specific widgets were chosen

### Templates
- [ ] **Template purpose**: What the template displays
- [ ] **Block structure**: Explain template inheritance structure
- [ ] **Context requirements**: What context variables are required

## REST API Comment Checklist

### Serializers
- [ ] **Serializer purpose**: What data is serialized/deserialized
- [ ] **Field transformations**: Any special field handling
- [ ] **Validation logic**: Custom validation rules

### ViewSets
- [ ] **Endpoint purpose**: What the endpoint provides
- [ ] **Query parameters**: Available query parameters and their effects
- [ ] **Permission requirements**: Required permissions
- [ ] **Pagination**: Pagination behavior if applicable

## Comment Review Process

### Self-Review
Before submitting code for review:

- [ ] Every function has a docstring comment
- [ ] All parameters are documented
- [ ] Return values are documented
- [ ] Complex logic has inline comments
- [ ] Classes have descriptive docstrings
- [ ] File has a module-level docstring

### Peer Review
When reviewing others' code:

- [ ] All new functions have comprehensive comments
- [ ] Existing function comments are updated when functionality changes
- [ ] Comments are clear and accurate
- [ ] Comments provide value beyond just restating the code
- [ ] Examples are provided for complex functions

## Comment Style Guidelines

### Do's
- Keep comments up-to-date when code changes
- Explain "why" not just "what" the code does
- Use consistent formatting and style
- Comment complex algorithms step by step
- Document assumptions and preconditions

### Don'ts
- Write comments that merely repeat the code
- Leave outdated comments
- Use excessive comments for simple code
- Include TODOs without tickets/issues
- Use comments for code versioning

## Automated Documentation Tools

### Docstring Coverage
Use docstring-coverage to check for missing function comments:

```bash
pip install docstring-coverage
docstr-coverage --verbose path/to/module
```

### Sphinx Documentation
Generate HTML documentation from docstrings:

```bash
pip install sphinx
cd docs
sphinx-quickstart
make html
```

## Documentation Maintenance

### Regular Reviews
- Schedule regular documentation reviews
- Update comments when functionality changes
- Remove comments for deleted code
- Keep examples up-to-date

### Documentation Debt
- Track "documentation debt" for under-commented code
- Prioritize documentation improvements in sprints
- Set targets for documentation coverage

## Conclusion

Thorough code commenting is not optional—it's a mandatory requirement for the Guides project. All team members must ensure every function in all files is properly documented. This makes the codebase more maintainable, facilitates knowledge transfer, and improves collaboration efficiency.

Remember: A well-commented function today saves hours of confusion tomorrow. Your future self (and colleagues) will thank you for the comprehensive documentation.
