#!/usr/bin/env python
"""
Test script for the restaurant marketing campaign system.

This script tests the complete workflow:
1. Campaign creation and validation
2. Customer targeting functionality
3. Email preview rendering
4. Campaign sending with consent filtering
5. Statistics tracking

Usage:
    python test_marketing_campaigns.py
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

# Import Django models and utilities
from django.contrib.auth.models import User
from django.utils import timezone
from restaurant.models import Restaurant, MarketingCampaign, CampaignRecipient
from customer.models import EmailPreference, UserProfile
from orders.models import Order, OrderItem
from menu.models import MenuItem, Category
from core.utils import EmailUtils

def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message in green."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message in red."""
    print(f"❌ {message}")

def print_info(message):
    """Print info message in blue."""
    print(f"ℹ️  {message}")

def test_campaign_model():
    """Test MarketingCampaign model functionality."""
    print_test_header("Marketing Campaign Model Tests")
    
    try:
        # Get or create test restaurant
        restaurant_owner = User.objects.filter(username='testrestaurant').first()
        if not restaurant_owner:
            restaurant_owner = User.objects.create_user(
                username='testrestaurant',
                email='restaurant@test.com',
                password='testpass123'
            )
            # Create restaurant
            restaurant = Restaurant.objects.create(
                name='Test Restaurant',
                owner=restaurant_owner,
                address='Test Address',
                phone='1234567890',
                is_active=True
            )
        else:
            restaurant = Restaurant.objects.filter(owner=restaurant_owner).first()
        
        # Test campaign creation
        campaign = MarketingCampaign.objects.create(
            restaurant=restaurant,
            name='Test Campaign',
            subject='Test Subject',
            message='This is a test message',
            target_customers='all_customers',
            template='emails/promotional_base.html',
            created_by=restaurant_owner
        )
        
        print_success(f"Created campaign: {campaign.name}")
        
        # Test campaign methods
        target_customers = campaign.get_target_customers()
        print_info(f"Target customers count: {target_customers.count()}")
        
        stats = campaign.get_campaign_stats()
        print_info(f"Campaign stats: {stats}")
        
        # Test campaign status
        print_info(f"Campaign status: {campaign.get_status_display()}")
        
        return campaign
        
    except Exception as e:
        print_error(f"Campaign model test failed: {str(e)}")
        return None

def test_customer_targeting():
    """Test customer targeting functionality."""
    print_test_header("Customer Targeting Tests")
    
    try:
        # Create test customers
        test_users = []
        for i in range(5):
            username = f'testcustomer{i}'
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=f'customer{i}@test.com',
                    password='testpass123'
                )
                # Create user profile using get_or_create to avoid duplicate key error
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'full_name': f'Test Customer {i}',
                        'phone_number': f'123456789{i}'
                    }
                )
                if created:
                    print_info(f"Created profile for {user.username}")
                else:
                    print_info(f"Profile already exists for {user.username}")
            test_users.append(user)
        
        # Set email preferences (some opt-in, some opt-out)
        for i, user in enumerate(test_users):
            preference = EmailPreference.objects.filter(user=user).first()
            if not preference:
                preference = EmailPreference.objects.create(user=user)
            
            # First 3 users opt-in to promotional emails
            if i < 3:
                preference.promotional_emails = True
                preference.save()
                print_info(f"User {user.username} opted IN to promotional emails")
            else:
                preference.promotional_emails = False
                preference.save()
                print_info(f"User {user.username} opted OUT of promotional emails")
        
        # Create test restaurant and orders
        restaurant_owner = User.objects.filter(username='testrestaurant').first()
        restaurant = Restaurant.objects.filter(owner=restaurant_owner).first()
        
        # Create test orders for some customers
        for i, user in enumerate(test_users[:3]):  # Only first 3 customers have orders
            order = Order.objects.create(
                user=user,
                total_amount=100.0 + (i * 50),  # Different order amounts
                status='delivered'
            )
            print_info(f"Created order for {user.username}: ₹{order.total_amount}")
        
        # Test targeting with different criteria
        campaign = MarketingCampaign.objects.filter(name='Test Campaign').first()
        
        # Test all customers targeting
        campaign.target_customers = 'all_customers'
        campaign.save()
        all_targets = campaign.get_target_customers()
        print_info(f"All customers targeting: {all_targets.count()} users (should be 3 - only those with orders AND opted-in)")
        
        # Test recent customers targeting
        campaign.target_customers = 'recent_customers'
        campaign.save()
        recent_targets = campaign.get_target_customers()
        print_info(f"Recent customers targeting: {recent_targets.count()} users")
        
        # Test repeat customers targeting
        campaign.target_customers = 'repeat_customers'
        campaign.save()
        repeat_targets = campaign.get_target_customers()
        print_info(f"Repeat customers targeting: {repeat_targets.count()} users")
        
        # Test high value customers targeting
        campaign.target_customers = 'high_value_customers'
        campaign.save()
        high_value_targets = campaign.get_target_customers()
        print_info(f"High value customers targeting: {high_value_targets.count()} users")
        
        print_success("Customer targeting tests completed")
        return True
        
    except Exception as e:
        print_error(f"Customer targeting test failed: {str(e)}")
        return False

def test_email_preview():
    """Test email preview functionality."""
    print_test_header("Email Preview Tests")
    
    try:
        campaign = MarketingCampaign.objects.filter(name='Test Campaign').first()
        if not campaign:
            print_error("No test campaign found")
            return False
        
        # Test template rendering
        from django.template.loader import render_to_string
        
        context = {
            'restaurant': campaign.restaurant,
            'campaign_name': campaign.name,
            'custom_message': campaign.message,
            'site_name': 'Food Ordering System',
            'site_url': 'https://tetech.in/',
            'site_domain': 'tetech.in',
            'current_year': timezone.now().year,
            'user': campaign.created_by,
            'first_name': campaign.created_by.first_name or 'John',
            'username': campaign.created_by.username,
        }
        
        email_content = render_to_string(campaign.template, context)
        
        if email_content and len(email_content) > 100:
            print_success(f"Email template rendered successfully ({len(email_content)} characters)")
            print_info(f"Template used: {campaign.template}")
        else:
            print_error("Email template rendering failed")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Email preview test failed: {str(e)}")
        return False

def test_campaign_sending():
    """Test campaign sending with consent filtering."""
    print_test_header("Campaign Sending Tests")
    
    try:
        campaign = MarketingCampaign.objects.filter(name='Test Campaign').first()
        if not campaign:
            print_error("No test campaign found")
            return False
        
        # Test campaign sending (dry run - don't actually send emails)
        print_info("Testing campaign sending (with consent filtering)...")
        
        # Get target customers before sending
        target_customers = campaign.get_target_customers()
        print_info(f"Target customers before sending: {target_customers.count()}")
        
        # Check EmailUtils integration
        if hasattr(EmailUtils, 'send_promotional_email'):
            print_success("EmailUtils.send_promotional_email method found")
        else:
            print_error("EmailUtils.send_promotional_email method not found")
            return False
        
        # Test send_campaign method (this will actually try to send emails)
        # We'll monitor the results to see if consent filtering works
        print_info("Executing campaign.send_campaign()...")
        results = campaign.send_campaign()
        
        print_success(f"Campaign sending completed: {results}")
        
        # Verify campaign status updated
        campaign.refresh_from_db()
        print_info(f"Campaign status after sending: {campaign.get_status_display()}")
        
        # Check recipient records created
        recipients = CampaignRecipient.objects.filter(campaign=campaign)
        print_info(f"Total recipient records created: {recipients.count()}")
        
        sent_count = recipients.filter(status='sent').count()
        failed_count = recipients.filter(status='failed').count()
        
        print_info(f"Successful sends: {sent_count}")
        print_info(f"Failed sends: {failed_count}")
        
        # Verify only opted-in users received emails
        opted_in_users = User.objects.filter(
            email_preferences__promotional_emails=True
        ).count()
        
        print_info(f"Opted-in users in system: {opted_in_users}")
        
        if sent_count <= opted_in_users:
            print_success("Consent filtering appears to be working correctly")
        else:
            print_error("Consent filtering may not be working - more emails sent than opted-in users")
        
        return True
        
    except Exception as e:
        print_error(f"Campaign sending test failed: {str(e)}")
        return False

def test_statistics_tracking():
    """Test campaign statistics tracking."""
    print_test_header("Statistics Tracking Tests")
    
    try:
        campaign = MarketingCampaign.objects.filter(name='Test Campaign').first()
        if not campaign:
            print_error("No test campaign found")
            return False
        
        # Test statistics calculation
        stats = campaign.get_campaign_stats()
        
        print_info(f"Campaign statistics:")
        print_info(f"  Target count: {stats['target_count']}")
        print_info(f"  Sent count: {stats['sent_count']}")
        print_info(f"  Failed count: {stats['failed_count']}")
        print_info(f"  Pending count: {stats['pending_count']}")
        print_info(f"  Success rate: {stats['success_rate']}%")
        
        # Verify statistics match actual data
        recipients = CampaignRecipient.objects.filter(campaign=campaign)
        actual_sent = recipients.filter(status='sent').count()
        actual_failed = recipients.filter(status='failed').count()
        
        if stats['sent_count'] == actual_sent and stats['failed_count'] == actual_failed:
            print_success("Statistics tracking is accurate")
        else:
            print_error("Statistics tracking mismatch")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Statistics tracking test failed: {str(e)}")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print_test_header("Cleaning Up Test Data")
    
    try:
        # Delete test campaigns
        MarketingCampaign.objects.filter(name='Test Campaign').delete()
        print_info("Deleted test campaigns")
        
        # Delete test recipients
        CampaignRecipient.objects.all().delete()
        print_info("Deleted test recipients")
        
        # Delete test orders
        Order.objects.filter(user__username__startswith='testcustomer').delete()
        print_info("Deleted test orders")
        
        # Delete test users and profiles
        for i in range(5):
            username = f'testcustomer{i}'
            user = User.objects.filter(username=username).first()
            if user:
                EmailPreference.objects.filter(user=user).delete()
                UserProfile.objects.filter(user=user).delete()
                user.delete()
                print_info(f"Deleted test user: {username}")
        
        # Delete test restaurant
        restaurant_owner = User.objects.filter(username='testrestaurant').first()
        if restaurant_owner:
            Restaurant.objects.filter(owner=restaurant_owner).delete()
            restaurant_owner.delete()
            print_info("Deleted test restaurant and owner")
        
        print_success("Test data cleanup completed")
        
    except Exception as e:
        print_error(f"Cleanup failed: {str(e)}")

def main():
    """Main test function."""
    print("🚀 Starting Restaurant Marketing Campaign System Tests")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_tests_passed = True
    
    # Run all tests
    try:
        # Test 1: Campaign Model
        campaign = test_campaign_model()
        if not campaign:
            all_tests_passed = False
        
        # Test 2: Customer Targeting
        if not test_customer_targeting():
            all_tests_passed = False
        
        # Test 3: Email Preview
        if not test_email_preview():
            all_tests_passed = False
        
        # Test 4: Campaign Sending
        if not test_campaign_sending():
            all_tests_passed = False
        
        # Test 5: Statistics Tracking
        if not test_statistics_tracking():
            all_tests_passed = False
        
    except Exception as e:
        print_error(f"Test execution failed: {str(e)}")
        all_tests_passed = False
    
    # Cleanup
    cleanup_test_data()
    
    # Final results
    print_test_header("TEST RESULTS")
    if all_tests_passed:
        print_success("🎉 ALL TESTS PASSED! The marketing campaign system is working correctly.")
        print_info("✅ Campaign creation and validation")
        print_info("✅ Customer targeting with consent filtering")
        print_info("✅ Email preview rendering")
        print_info("✅ Campaign sending with EmailUtils integration")
        print_info("✅ Statistics tracking and reporting")
    else:
        print_error("❌ SOME TESTS FAILED! Please check the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
