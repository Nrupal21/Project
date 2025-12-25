"""
Test script to simulate form submission and debug the wizard.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User


def test_wizard_submission():
    """Test wizard form submission with different actions."""
    
    print('🧪 Testing Wizard Form Submission')
    print('=' * 40)
    
    client = Client()
    
    # Test 1: GET the wizard page
    print('\n1️⃣ Testing GET request to wizard...')
    response = client.get(reverse('restaurant:registration_wizard'))
    print(f'   Status: {response.status_code} {"✅" if response.status_code == 200 else "❌"}')
    
    # Test 2: POST with 'next' action
    print('\n2️⃣ Testing POST with "next" action...')
    form_data = {
        'action': 'next',
        'current_step': '1',
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'password_confirm': 'TestPass123!'
    }
    
    response = client.post(reverse('restaurant:registration_wizard'), data=form_data)
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 302:
        print('   ✅ Redirect received (step progression working)')
        print(f'   Redirect to: {response.url}")
    elif response.status_code == 200:
        print('   ❌ Form returned to same page (validation likely failed)')
        # Check for form errors in context
        if hasattr(response, 'context') and response.context:
            messages = list(response.context.get('messages', []))
            if messages:
                for msg in messages:
                    print(f'   Message: {msg}')
    else:
        print(f'   ❌ Unexpected status code: {response.status_code}')
    
    # Test 3: POST with 'save_draft' action
    print('\n3️⃣ Testing POST with "save_draft" action...')
    draft_data = {
        'action': 'save_draft',
        'current_step': '1',
        'username': 'testuser456',
        'email': 'draft@example.com'
    }
    
    response = client.post(reverse('restaurant:registration_wizard'), data=draft_data)
    print(f'   Status: {response.status_code}')
    
    if response.status_code == 200:
        print('   ✅ Save draft returned to form (expected behavior)')
    else:
        print(f'   ❌ Unexpected status for save draft: {response.status_code}')
    
    print('\n' + '=' * 40)
    print('Form submission test completed.')


if __name__ == '__main__':
    test_wizard_submission()
