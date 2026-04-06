"""
Rewards App Forms.

This module contains forms used in the rewards app for point redemption
and other user interactions with the reward system.

The forms in this module handle the user-facing aspects of the rewards system,
particularly the redemption of points for various rewards. They include validation
logic to ensure users have sufficient points, appropriate redemption values,
and follow the program's exchange rate policies.

The forms maintain the TravelGuide platform's indigo/violet color scheme through
appropriate CSS classes and styling, ensuring visual consistency with the rest
of the application.

Key components:
- RedemptionForm: Handles the validation and processing of reward point redemptions
- Preset redemption options with predefined point values and rewards
- Custom redemption options with user-defined point values
- Validation to ensure program policies are followed
"""

from django import forms
from django.core.exceptions import ValidationError

from .models import RewardPoints, RewardRedemption, RewardRedemptionType


class RedemptionForm(forms.ModelForm):
    """
    Form for redeeming reward points.
    
    This form handles the validation and processing of reward point redemptions,
    ensuring users have sufficient points and selecting appropriate redemption options.
    
    The form provides both preset redemption options (with predefined point values and
    rewards) and custom redemption options where users can specify their desired
    point amount and redemption type. The preset options are only shown if the user
    has sufficient points for at least one option.
    
    The form integrates with the TravelGuide platform's indigo/violet color scheme
    through appropriate CSS classes and styling on form widgets. It also provides
    helpful context to users about their current point balance and available options.
    
    Key features:
    - Dynamic preset options based on user's current point balance
    - Custom redemption option for flexibility
    - Validation to ensure users have sufficient points
    - Validation to ensure redemption values follow program policies
    - Clear error messages and help text
    - Consistent styling with the platform's indigo/violet theme
    """
    # Preset redemption options field
    # This field provides users with pre-configured redemption choices based on their point balance
    # The choices are dynamically populated in __init__ based on the user's available points
    # Using RadioSelect widget for better UX with clear visual distinction between options
    # The field is not required as users can opt for a custom redemption instead
    preset_option = forms.ChoiceField(
        choices=[], 
        required=False,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input me-2',  # Tailwind classes for proper spacing and styling
            'style': 'accent-color: rgb(124, 58, 237);'  # violet-600 color for selected radio buttons
        }),
        label="Select a redemption option",
        help_text="Choose one of our preset redemption options or customize your own below."
    )
    
    class Meta:
        """
        Meta configuration for the RedemptionForm.
        
        This inner class defines the model association, fields to include in the form,
        and widget customizations for improved user experience and visual consistency.
        
        The widgets are styled to match the TravelGuide platform's indigo/violet color scheme
        and follow modern form design practices for better usability.
        """
        # Associate this form with the RewardRedemption model
        # This enables automatic form field generation and model instance creation
        model = RewardRedemption
        
        # Only include these specific fields from the model
        # Other fields like user, status, and created_at are handled automatically
        # or set during form processing
        fields = ['redemption_type', 'points_used', 'redemption_value']
        
        # Custom widget definitions for better styling and user experience
        # Each widget includes appropriate CSS classes and attributes
        widgets = {
            # Dropdown for selecting redemption type (e.g., COUPON, TRAVEL_CREDIT)
            # Uses form-select class for consistent styling
            'redemption_type': forms.Select(attrs={
                'class': 'form-select border-indigo-300 focus:border-violet-500 focus:ring focus:ring-violet-200',
                'aria-label': 'Select redemption type'
            }),
            
            # Number input for points with minimum value constraint
            # Prevents users from entering invalid point amounts
            'points_used': forms.NumberInput(attrs={
                'class': 'form-control border-indigo-300 focus:border-violet-500 focus:ring focus:ring-violet-200',
                'min': '100',  # Minimum points for any redemption
                'aria-label': 'Points to redeem'
            }),
            
            # Decimal input for redemption value with step size for currency
            # Allows precise value entry for monetary redemptions
            'redemption_value': forms.NumberInput(attrs={
                'class': 'form-control border-indigo-300 focus:border-violet-500 focus:ring focus:ring-violet-200',
                'step': '0.01',  # For currency precision
                'aria-label': 'Redemption value'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with user data for validation.
        
        This method customizes the form based on the current user's point balance
        and available redemption options.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments including 'user'
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Get user's current point balance
        if self.user:
            self.point_balance = RewardPoints.get_user_point_balance(self.user)
            self.fields['points_used'].help_text = f"You have {self.point_balance} points available"
            
            # Generate preset options based on point balance
            preset_choices = []
            
            # Only add options the user has enough points for
            if self.point_balance >= 500:
                preset_choices.append(
                    ('option1', f'10% Discount Coupon (500 points)')
                )
            if self.point_balance >= 1000:
                preset_choices.append(
                    ('option2', f'25% Discount Coupon (1000 points)')
                )
            if self.point_balance >= 2500:
                preset_choices.append(
                    ('option3', f'$50 Travel Credit (2500 points)')
                )
            if self.point_balance >= 5000:
                preset_choices.append(
                    ('option4', f'$100 Cash Transfer (5000 points)')
                )
                
            if preset_choices:
                preset_choices.append(('custom', 'Custom Redemption'))
                self.fields['preset_option'].choices = preset_choices
                self.fields['preset_option'].initial = 'custom'
            else:
                # If user doesn't have enough points for any preset option
                self.fields['preset_option'].widget = forms.HiddenInput()
    
    def clean(self):
        """
        Validate the form data.
        
        This method ensures the user has enough points for the redemption
        and handles preset option selection.
        
        Returns:
            dict: Cleaned form data
            
        Raises:
            ValidationError: If user doesn't have enough points or other validation fails
        """
        cleaned_data = super().clean()
        preset_option = cleaned_data.get('preset_option')
        points_used = cleaned_data.get('points_used')
        redemption_type = cleaned_data.get('redemption_type')
        redemption_value = cleaned_data.get('redemption_value')
        
        # Handle preset options if a non-custom option was selected
        # Each preset option has predefined values for redemption_type, points_used, and redemption_value
        # This simplifies the redemption process for users while ensuring consistent point values
        if preset_option and preset_option != 'custom':
            # Option 1: 10% discount coupon for 500 points
            # Uses the COUPON redemption type with a value of 10 (percent)
            if preset_option == 'option1':
                cleaned_data['redemption_type'] = RewardRedemptionType.COUPON
                cleaned_data['points_used'] = 500
                cleaned_data['redemption_value'] = 10
            # Option 2: 25% discount coupon for 1000 points
            # Uses the COUPON redemption type with a value of 25 (percent)
            elif preset_option == 'option2':
                cleaned_data['redemption_type'] = RewardRedemptionType.COUPON
                cleaned_data['points_used'] = 1000
                cleaned_data['redemption_value'] = 25
            # Option 3: $50 travel credit for 2500 points
            # Uses the TRAVEL_CREDIT redemption type with a value of 50 (dollars)
            elif preset_option == 'option3':
                cleaned_data['redemption_type'] = RewardRedemptionType.TRAVEL_CREDIT
                cleaned_data['points_used'] = 2500
                cleaned_data['redemption_value'] = 50
            # Option 4: $100 cash transfer for 5000 points
            # Uses the CASH_TRANSFER redemption type with a value of 100 (dollars)
            elif preset_option == 'option4':
                cleaned_data['redemption_type'] = RewardRedemptionType.CASH_TRANSFER
                cleaned_data['points_used'] = 5000
                cleaned_data['redemption_value'] = 100
        
        # Ensure user has enough points for the requested redemption
        # This validation prevents users from redeeming more points than they have available
        # and provides a clear error message with their current balance
        if self.user and points_used:
            if points_used > self.point_balance:
                raise ValidationError(f"You only have {self.point_balance} points available")
        
        # Ensure points and value are reasonable based on the program's exchange rate policy
        # This validation prevents abuse of the rewards system by ensuring users can't
        # get disproportionately high value for their points
        if points_used and redemption_value:
            # Calculate points-to-value ratio (points needed per $1 of redemption value)
            # Higher ratio means better value for the program, lower ratio means better value for the user
            pts_value_ratio = points_used / float(redemption_value)
            
            # Minimum points per $1 of value (program policy)
            # This ensures consistent value across all redemption types
            # and maintains the financial sustainability of the rewards program
            min_ratio = 25  # Minimum points per $1 of value
            
            # If the ratio is too low (user getting too much value), reject the redemption
            if pts_value_ratio < min_ratio:
                raise ValidationError(
                    f"The redemption value is too high for the points used. " 
                    f"You need at least {min_ratio} points per $1 of value."
                )
        
        # Return the cleaned data for further processing
        return cleaned_data
