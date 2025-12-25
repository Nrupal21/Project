"""
Simple test to verify wizard backend validation works correctly.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.registration_wizard import RegistrationWizardMixin
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


def test_validation_only():
    """Test just the validation logic without step progression."""
    
    print('🔍 Testing Wizard Validation Logic')
    print('=' * 40)
    
    factory = RequestFactory()
    request = factory.post('/restaurant/register/wizard/')
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    wizard = RegistrationWizardMixin()
    
    # Test valid data for each step
    test_cases = [
        {
            'step': 1,
            'data': {
                'username': 'testrestaurant2025',
                'email': 'test@restaurant.com',
                'password': 'TestPass123!',
                'password_confirm': 'TestPass123!'
            },
            'name': 'Account Info'
        },
        {
            'step': 2,
            'data': {
                'restaurant_name': 'Test Restaurant',
                'description': 'A wonderful place with great food',
                'cuisine_type': 'italian'
            },
            'name': 'Restaurant Details'
        },
        {
            'step': 3,
            'data': {
                'phone': '(555) 123-4567',
                'email': 'contact@test.com',
                'address': '123 Main Street, City, State 12345'
            },
            'name': 'Location & Contact'
        },
        {
            'step': 4,
            'data': {
                'opening_time': '09:00',
                'closing_time': '22:00',
                'minimum_order': '15.00',
                'delivery_fee': '3.99'
            },
            'name': 'Business Hours & Pricing'
        }
    ]
    
    all_valid = True
    
    for case in test_cases:
        step = case['step']
        data = case['data']
        name = case['name']
        
        is_valid, errors = wizard.validate_step_data(request, step, data)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f'Step {step} ({name}): {status}')
        
        if not is_valid:
            all_valid = False
            for field, error in errors.items():
                print(f'  Error - {field}: {error}')
    
    print('\n' + '=' * 40)
    if all_valid:
        print('✅ All validation tests passed!')
        print('Backend logic is working correctly.')
        print('The issue is likely in the JavaScript validation.')
    else:
        print('❌ Backend validation has issues.')
    
    return all_valid


if __name__ == '__main__':
    test_validation_only()
