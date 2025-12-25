"""
Debug script to test wizard step progression.
Tests the backend logic for step validation and progression.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from restaurant.registration_wizard import RegistrationWizardMixin
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


def test_step_progression():
    """Test that wizard can progress through steps with valid data."""
    
    print('🔍 Testing Wizard Step Progression')
    print('=' * 50)
    
    factory = RequestFactory()
    request = factory.post('/restaurant/register/wizard/')
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    wizard = RegistrationWizardMixin()
    
    # Test Step 1: Account Info
    print('\n📝 Step 1: Account Information')
    step1_data = {
        'username': 'testrestaurant2025',
        'email': 'test@restaurant.com',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!',
        'action': 'next',
        'current_step': '1'
    }
    
    is_valid, errors = wizard.validate_step_data(request, 1, step1_data)
    print(f'   Validation: {"✅ PASS" if is_valid else "❌ FAIL"}')
    if errors:
        for field, error in errors.items():
            print(f'   Error - {field}: {error}')
    
    if is_valid:
        wizard._save_step_data(request, 1, step1_data, {})
        wizard.mark_step_complete(request, 1)
        wizard.set_current_step(request, 2)
        print('   ✅ Progressed to Step 2')
    
    # Test Step 2: Restaurant Details
    print('\n📝 Step 2: Restaurant Details')
    step2_data = {
        'restaurant_name': 'Test Restaurant',
        'description': 'A wonderful place with great food and amazing atmosphere',
        'cuisine_type': 'Italian',
        'action': 'next',
        'current_step': '2'
    }
    
    is_valid, errors = wizard.validate_step_data(request, 2, step2_data)
    print(f'   Validation: {"✅ PASS" if is_valid else "❌ FAIL"}')
    if errors:
        for field, error in errors.items():
            print(f'   Error - {field}: {error}')
    
    if is_valid:
        wizard._save_step_data(request, 2, step2_data, {})
        wizard.mark_step_complete(request, 2)
        wizard.set_current_step(request, 3)
        print('   ✅ Progressed to Step 3')
    
    # Test Step 3: Location & Contact
    print('\n📝 Step 3: Location & Contact')
    step3_data = {
        'phone': '(555) 123-4567',
        'email': 'contact@testrestaurant.com',
        'address': '123 Main Street, City, State 12345',
        'action': 'next',
        'current_step': '3'
    }
    
    is_valid, errors = wizard.validate_step_data(request, 3, step3_data)
    print(f'   Validation: {"✅ PASS" if is_valid else "❌ FAIL"}')
    if errors:
        for field, error in errors.items():
            print(f'   Error - {field}: {error}')
    
    if is_valid:
        wizard._save_step_data(request, 3, step3_data, {})
        wizard.mark_step_complete(request, 3)
        wizard.set_current_step(request, 4)
        print('   ✅ Progressed to Step 4')
    
    # Test Step 4: Business Hours & Pricing
    print('\n📝 Step 4: Business Hours & Pricing')
    step4_data = {
        'opening_time': '09:00',
        'closing_time': '22:00',
        'minimum_order': '15.00',
        'delivery_fee': '3.99',
        'action': 'next',
        'current_step': '4'
    }
    
    is_valid, errors = wizard.validate_step_data(request, 4, step4_data)
    print(f'   Validation: {"✅ PASS" if is_valid else "❌ FAIL"}')
    if errors:
        for field, error in errors.items():
            print(f'   Error - {field}: {error}')
    
    if is_valid:
        wizard._save_step_data(request, 4, step4_data, {})
        wizard.mark_step_complete(request, 4)
        wizard.set_current_step(request, 5)
        print('   ✅ Progressed to Step 5')
    
    # Check final state
    current_step = wizard.get_current_step(request)
    completed_steps = wizard.get_completed_steps(request)
    
    print('\n📊 Final State:')
    print(f'   Current Step: {current_step}')
    print(f'   Completed Steps: {completed_steps}')
    print(f'   Total Progress: {len(completed_steps)}/5 steps')
    
    if current_step == 5 and len(completed_steps) == 4:
        print('\n🎉 SUCCESS: Wizard can progress through all steps!')
    else:
        print('\n❌ ISSUE: Wizard progression failed')
    
    print('\n' + '=' * 50)
    print('Debug test completed.')


if __name__ == '__main__':
    test_step_progression()
