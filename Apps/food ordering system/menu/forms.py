"""
Menu app forms.
Contains forms for creating and updating menu items and categories.
"""
from django import forms
from .models import MenuItem, Category


class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating food categories.
    
    Handles category name, description, and display order.
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Enter category description (optional)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'min': 0,
                'placeholder': 'Display order (0 = first)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with proper field labels and help text.
        """
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Category Name'
        self.fields['description'].label = 'Description'
        self.fields['description'].required = False
        self.fields['is_active'].label = 'Active'
        self.fields['display_order'].label = 'Display Order'
        self.fields['display_order'].help_text = 'Lower numbers appear first in the menu'


class MenuItemForm(forms.ModelForm):
    """
    Form for creating and updating menu items.
    
    Handles all menu item fields including image upload with validation.
    """
    
    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'description', 'price', 'image', 
            'is_available', 'dietary_type', 'preparation_time'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'placeholder': 'Enter menu item name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Enter detailed description of the menu item'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Enter price (e.g., 12.99)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'accept': 'image/*'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
            }),
            'dietary_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent'
            }),
            'preparation_time': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent',
                'min': 1,
                'max': 120,
                'placeholder': 'Minutes'
            })
        }
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the form with proper field labels, help text, and category filtering.
        """
        super().__init__(*args, **kwargs)
        
        # Set field labels and help text
        self.fields['category'].label = 'Category'
        self.fields['category'].empty_label = 'Select a category'
        self.fields['name'].label = 'Item Name'
        self.fields['description'].label = 'Description'
        self.fields['price'].label = 'Price ($)'
        self.fields['price'].help_text = 'Enter the price in dollars'
        self.fields['image'].label = 'Image'
        self.fields['image'].help_text = 'Upload a photo of the menu item (recommended size: 800x600px)'
        self.fields['is_available'].label = 'Available'
        self.fields['is_available'].help_text = 'Uncheck to temporarily remove from menu'
        self.fields['dietary_type'].label = 'Dietary Type'
        self.fields['preparation_time'].label = 'Preparation Time'
        self.fields['preparation_time'].help_text = 'Estimated time in minutes to prepare'
        
        # Filter categories to only show active ones
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    
    def clean_image(self):
        """
        Validate the uploaded image file.
        
        Returns:
            ImageField: The validated image file
            
        Raises:
            ValidationError: If image format or size is invalid
        """
        image = self.cleaned_data.get('image')
        
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file size must be less than 5MB.')
            
            # Check file extension
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = image.name.lower().split('.')[-1]
            if file_extension not in valid_extensions:
                raise forms.ValidationError(
                    f'Invalid image format. Please upload a {", ".join(valid_extensions)} file.'
                )
        
        return image
    
    def clean_price(self):
        """
        Validate the price field.
        
        Returns:
            Decimal: The validated price
            
        Raises:
            ValidationError: If price is negative or too high
        """
        price = self.cleaned_data.get('price')
        
        if price is not None:
            if price < 0:
                raise forms.ValidationError('Price cannot be negative.')
            if price > 9999.99:
                raise forms.ValidationError('Price cannot exceed $9,999.99.')
        
        return price
    
    def clean_name(self):
        """
        Validate the menu item name.
        
        Returns:
            str: The validated name
            
        Raises:
            ValidationError: If name is too short or contains invalid characters
        """
        name = self.cleaned_data.get('name')
        
        if name:
            if len(name.strip()) < 2:
                raise forms.ValidationError('Menu item name must be at least 2 characters long.')
            if len(name) > 200:
                raise forms.ValidationError('Menu item name cannot exceed 200 characters.')
        
        return name.strip()


class MenuItemBulkUpdateForm(forms.Form):
    """
    Form for bulk updating menu item availability.
    
    Allows restaurant owners to toggle availability for multiple items at once.
    """
    
    def __init__(self, menu_items, *args, **kwargs):
        """
        Initialize the form with dynamic fields for each menu item.
        
        Args:
            menu_items: QuerySet of MenuItem objects to include in the form
        """
        super().__init__(*args, **kwargs)
        
        for item in menu_items:
            field_name = f'item_{item.id}'
            self.fields[field_name] = forms.BooleanField(
                required=False,
                initial=item.is_available,
                label=item.name,
                widget=forms.CheckboxInput(attrs={
                    'class': 'w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500'
                })
            )
