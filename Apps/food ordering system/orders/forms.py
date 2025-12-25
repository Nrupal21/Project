"""
Forms for promo code management and order processing.
"""
from django import forms
from django.utils import timezone
from .models import PromoCode, SeasonalPromotion


class PromoCodeForm(forms.ModelForm):
    """
    Form for creating and editing promo codes.
    Includes validation for discount types and constraints.
    """
    
    class Meta:
        model = PromoCode
        fields = [
            'code', 'name', 'description', 'discount_type', 'discount_value',
            'minimum_order_amount', 'max_discount_amount', 'usage_limit',
            'usage_limit_per_user', 'start_date', 'end_date', 'first_time_only',
            'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Enter promo code (e.g., SAVE20)',
                'uppercase': 'true'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Promo code display name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Describe the promo code for customers'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_order_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'max_discount_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Optional - leave empty for no limit'
            }),
            'usage_limit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'min': '1',
                'placeholder': 'Optional - leave empty for unlimited'
            }),
            'usage_limit_per_user': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'min': '1',
                'placeholder': 'Optional - leave empty for unlimited'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
            'first_time_only': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default values for new instances
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now()
            self.fields['end_date'].initial = timezone.now() + timezone.timedelta(days=30)
            self.fields['is_active'].initial = True
        
        # Make code uppercase and remove spaces
        if self.data.get('code'):
            self.data = self.data.copy()
            self.data['code'] = self.data['code'].upper().replace(' ', '')
    
    def clean_code(self):
        """Convert code to uppercase and remove spaces."""
        code = self.cleaned_data.get('code')
        if code:
            return code.upper().replace(' ', '')
        return code
    
    def clean(self):
        """Validate form data for consistency."""
        cleaned_data = super().clean()
        
        discount_type = cleaned_data.get('discount_type')
        discount_value = cleaned_data.get('discount_value')
        max_discount_amount = cleaned_data.get('max_discount_amount')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate discount values based on type
        if discount_type == 'percentage':
            if discount_value and (discount_value < 0 or discount_value > 100):
                raise forms.ValidationError('Percentage discount must be between 0 and 100.')
        elif discount_type == 'fixed':
            if discount_value and discount_value <= 0:
                raise forms.ValidationError('Fixed discount amount must be greater than 0.')
        elif discount_type == 'free_delivery':
            if discount_value and discount_value != 0:
                raise forms.ValidationError('Free delivery discount value must be 0.')
        
        # Validate date range
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End date must be after start date.')
        
        # Validate max discount amount for percentage discounts
        if discount_type == 'percentage' and max_discount_amount and max_discount_amount <= 0:
            raise forms.ValidationError('Maximum discount amount must be greater than 0.')
        
        return cleaned_data


class SeasonalPromotionForm(forms.ModelForm):
    """
    Form for creating and editing seasonal promotions.
    """
    
    class Meta:
        model = SeasonalPromotion
        fields = [
            'name', 'description', 'promotion_type', 'start_date', 'end_date',
            'code_prefix', 'discount_type', 'discount_value', 'minimum_order_amount',
            'usage_limit_per_code', 'restaurants', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Promotion name (e.g., Summer Sale 2024)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Describe the promotion'
            }),
            'promotion_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'type': 'datetime-local'
            }),
            'code_prefix': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Code prefix (e.g., SUMMER)',
                'uppercase': 'true'
            }),
            'discount_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_order_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'usage_limit_per_code': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'min': '1',
                'value': '100'
            }),
            'restaurants': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter restaurants based on user (for restaurant owners)
        if user and hasattr(user, 'restaurants'):
            self.fields['restaurants'].queryset = user.restaurants.all()
        
        # Set default values for new instances
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now()
            self.fields['end_date'].initial = timezone.now() + timezone.timedelta(days=7)
            self.fields['is_active'].initial = True
    
    def clean_code_prefix(self):
        """Convert code prefix to uppercase and remove spaces."""
        prefix = self.cleaned_data.get('code_prefix')
        if prefix:
            return prefix.upper().replace(' ', '')
        return prefix


class ApplyPromoCodeForm(forms.Form):
    """
    Form for customers to apply promo codes in cart.
    """
    
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Enter promo code',
            'uppercase': 'true'
        })
    )
    
    def clean_code(self):
        """Convert code to uppercase and remove spaces."""
        code = self.cleaned_data.get('code')
        if code:
            return code.upper().replace(' ', '')
        return code
