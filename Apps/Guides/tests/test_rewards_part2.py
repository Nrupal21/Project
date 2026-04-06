"""
Test cases for the rewards app (part 2).

This module contains additional comprehensive test cases for the rewards app,
focusing on the Redemption model and views. Every test function is thoroughly
documented to make understanding the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from rewards.models import RewardProgram, RewardTier, RewardPoints, PointsTransaction, Redemption, RedemptionOption
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class RedemptionOptionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RedemptionOption model in the rewards app.
    
    These tests verify that RedemptionOption objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the RedemptionOption model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RedemptionOption tests.
        
        Extends the base setUp method to include reward programs and redemption options for testing.
        """
        super().setUp()
        
        # Create a reward program
        self.reward_program = RewardProgram.objects.create(
            name="TravelGuide Rewards",
            description="Earn points for bookings and redeem for discounts and perks",
            points_expiry_months=12,
            terms_and_conditions="Standard terms apply",
            is_active=True
        )
        
        # Create redemption options
        self.discount_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="10% Discount on Tours",
            description="Get a 10% discount on any tour booking",
            points_required=500,
            value=Decimal('0.10'),  # 10% discount
            is_percentage=True,
            is_active=True,
            image="redemptions/discount.png",
            max_redemptions_per_user=5
        )
        
        self.gift_card_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="$50 Gift Card",
            description="Redeem for a $50 gift card",
            points_required=2000,
            value=Decimal('50.00'),
            is_percentage=False,
            is_active=True,
            image="redemptions/gift_card.png",
            max_redemptions_per_user=1
        )
    
    def test_redemption_option_creation(self):
        """
        Test that a RedemptionOption can be created with the expected attributes.
        
        Verifies that the RedemptionOption model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new redemption option
        free_tour_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="Free City Tour",
            description="Redeem for a free city tour of your choice",
            points_required=3000,
            value=Decimal('100.00'),
            is_percentage=False,
            is_active=True,
            image="redemptions/free_tour.png",
            max_redemptions_per_user=1
        )
        
        # Verify the redemption option was created with the correct attributes
        self.assertEqual(free_tour_option.program, self.reward_program)
        self.assertEqual(free_tour_option.name, "Free City Tour")
        self.assertEqual(free_tour_option.description, "Redeem for a free city tour of your choice")
        self.assertEqual(free_tour_option.points_required, 3000)
        self.assertEqual(free_tour_option.value, Decimal('100.00'))
        self.assertFalse(free_tour_option.is_percentage)
        self.assertTrue(free_tour_option.is_active)
        self.assertEqual(free_tour_option.image, "redemptions/free_tour.png")
        self.assertEqual(free_tour_option.max_redemptions_per_user, 1)
        
    def test_redemption_option_str_method(self):
        """
        Test the string representation of a RedemptionOption object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the option name.
        """
        self.assertEqual(str(self.discount_option), "10% Discount on Tours")
        self.assertEqual(str(self.gift_card_option), "$50 Gift Card")
        
    def test_redemption_option_get_absolute_url(self):
        """
        Test the get_absolute_url method of the RedemptionOption model.
        
        Verifies that the URL generated for an option detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('rewards:redemption_option_detail', kwargs={'pk': self.discount_option.pk})
        self.assertEqual(self.discount_option.get_absolute_url(), expected_url)
        
    def test_redemption_option_formatted_value(self):
        """
        Test the formatted_value property of the RedemptionOption model.
        
        Verifies that the formatted_value property correctly formats
        the value based on whether it's a percentage or a fixed amount.
        """
        # For percentage discount
        self.assertEqual(self.discount_option.formatted_value, "10%")
        
        # For fixed amount
        self.assertEqual(self.gift_card_option.formatted_value, "$50.00")
        
    def test_redemption_option_user_redemption_count(self):
        """
        Test the user_redemption_count method of the RedemptionOption model.
        
        Verifies that the method correctly counts how many times a user
        has redeemed a particular option.
        """
        # Initially the user has not redeemed any options
        self.assertEqual(self.discount_option.user_redemption_count(self.test_user), 0)
        
        # Create reward points for the test user
        reward_points = RewardPoints.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=1000,
            tier=RewardTier.objects.create(
                program=self.reward_program,
                name="Bronze",
                minimum_points=0,
                maximum_points=999,
                benefits="Basic benefits",
                icon="bronze_medal.png"
            ),
            last_activity_date=timezone.now()
        )
        
        # Create a redemption
        redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.discount_option,
            points_used=500,
            value=Decimal('0.10'),
            code="DISC123",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # Now the user has redeemed the discount option once
        self.assertEqual(self.discount_option.user_redemption_count(self.test_user), 1)
        
        # Create another redemption
        redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.discount_option,
            points_used=500,
            value=Decimal('0.10'),
            code="DISC456",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # Now the user has redeemed the discount option twice
        self.assertEqual(self.discount_option.user_redemption_count(self.test_user), 2)
        
        # The user has not redeemed the gift card option
        self.assertEqual(self.gift_card_option.user_redemption_count(self.test_user), 0)
        
    def test_redemption_option_can_be_redeemed_by_user(self):
        """
        Test the can_be_redeemed_by_user method of the RedemptionOption model.
        
        Verifies that the method correctly determines if a user can redeem
        an option based on their points and previous redemptions.
        """
        # Create reward points for the test user with 1000 points
        reward_points = RewardPoints.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=1000,
            tier=RewardTier.objects.create(
                program=self.reward_program,
                name="Bronze",
                minimum_points=0,
                maximum_points=999,
                benefits="Basic benefits",
                icon="bronze_medal.png"
            ),
            last_activity_date=timezone.now()
        )
        
        # The user can redeem the discount option (requires 500 points)
        self.assertTrue(self.discount_option.can_be_redeemed_by_user(self.test_user))
        
        # The user cannot redeem the gift card option (requires 2000 points)
        self.assertFalse(self.gift_card_option.can_be_redeemed_by_user(self.test_user))
        
        # Update the user's points to 2500
        reward_points.points = 2500
        reward_points.save()
        
        # Now the user can redeem the gift card option
        self.assertTrue(self.gift_card_option.can_be_redeemed_by_user(self.test_user))
        
        # Create max_redemptions_per_user redemptions for the gift card option
        redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.gift_card_option,
            points_used=2000,
            value=Decimal('50.00'),
            code="GIFT123",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # Now the user cannot redeem the gift card option again
        self.assertFalse(self.gift_card_option.can_be_redeemed_by_user(self.test_user))


class RedemptionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Redemption model in the rewards app.
    
    These tests verify that Redemption objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the Redemption model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Redemption tests.
        
        Extends the base setUp method to include reward programs, redemption options,
        and redemptions for testing.
        """
        super().setUp()
        
        # Create a reward program
        self.reward_program = RewardProgram.objects.create(
            name="TravelGuide Rewards",
            description="Earn points for bookings and redeem for discounts and perks",
            points_expiry_months=12,
            terms_and_conditions="Standard terms apply",
            is_active=True
        )
        
        # Create a reward tier
        self.bronze_tier = RewardTier.objects.create(
            program=self.reward_program,
            name="Bronze",
            minimum_points=0,
            maximum_points=999,
            benefits="Basic benefits",
            icon="bronze_medal.png"
        )
        
        # Create reward points for the test user
        self.reward_points = RewardPoints.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=1000,
            tier=self.bronze_tier,
            last_activity_date=timezone.now()
        )
        
        # Create a redemption option
        self.discount_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="10% Discount on Tours",
            description="Get a 10% discount on any tour booking",
            points_required=500,
            value=Decimal('0.10'),  # 10% discount
            is_percentage=True,
            is_active=True,
            image="redemptions/discount.png",
            max_redemptions_per_user=5
        )
        
        # Create a redemption
        self.redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.discount_option,
            points_used=500,
            value=Decimal('0.10'),
            code="DISC123",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
    
    def test_redemption_creation(self):
        """
        Test that a Redemption can be created with the expected attributes.
        
        Verifies that the Redemption model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new redemption
        redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.discount_option,
            points_used=500,
            value=Decimal('0.10'),
            code="DISC456",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # Verify the redemption was created with the correct attributes
        self.assertEqual(redemption.user, self.test_user)
        self.assertEqual(redemption.option, self.discount_option)
        self.assertEqual(redemption.points_used, 500)
        self.assertEqual(redemption.value, Decimal('0.10'))
        self.assertEqual(redemption.code, "DISC456")
        self.assertEqual(redemption.status, "active")
        self.assertIsNotNone(redemption.redemption_date)
        self.assertIsNotNone(redemption.expiry_date)
        
    def test_redemption_str_method(self):
        """
        Test the string representation of a Redemption object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the option name and user.
        """
        expected_str = f"10% Discount on Tours redeemed by testuser"
        self.assertEqual(str(self.redemption), expected_str)
        
    def test_redemption_is_expired(self):
        """
        Test the is_expired property of the Redemption model.
        
        Verifies that the is_expired property correctly determines
        if the redemption is expired based on the expiry date.
        """
        # Initially the redemption is not expired
        self.assertFalse(self.redemption.is_expired)
        
        # Set the expiry date to yesterday
        self.redemption.expiry_date = timezone.now() - datetime.timedelta(days=1)
        self.redemption.save()
        
        # Now the redemption should be expired
        self.assertTrue(self.redemption.is_expired)
        
    def test_redemption_is_active(self):
        """
        Test the is_active property of the Redemption model.
        
        Verifies that the is_active property correctly determines
        if the redemption is active based on the status and expiry date.
        """
        # Initially the redemption is active
        self.assertTrue(self.redemption.is_active)
        
        # Set the status to 'used'
        self.redemption.status = 'used'
        self.redemption.save()
        
        # Now the redemption should not be active
        self.assertFalse(self.redemption.is_active)
        
        # Reset the status to 'active'
        self.redemption.status = 'active'
        
        # Set the expiry date to yesterday
        self.redemption.expiry_date = timezone.now() - datetime.timedelta(days=1)
        self.redemption.save()
        
        # Now the redemption should not be active due to expiry
        self.assertFalse(self.redemption.is_active)
        
    def test_redemption_formatted_value(self):
        """
        Test the formatted_value property of the Redemption model.
        
        Verifies that the formatted_value property correctly formats
        the value based on whether it's a percentage or a fixed amount.
        """
        # For percentage discount
        self.assertEqual(self.redemption.formatted_value, "10%")
        
        # Create a fixed amount redemption
        gift_card_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="$50 Gift Card",
            description="Redeem for a $50 gift card",
            points_required=2000,
            value=Decimal('50.00'),
            is_percentage=False,
            is_active=True,
            image="redemptions/gift_card.png",
            max_redemptions_per_user=1
        )
        
        fixed_redemption = Redemption.objects.create(
            user=self.test_user,
            option=gift_card_option,
            points_used=2000,
            value=Decimal('50.00'),
            code="GIFT123",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # For fixed amount
        self.assertEqual(fixed_redemption.formatted_value, "$50.00")
        
    def test_redemption_create_for_user(self):
        """
        Test the create_for_user method of the Redemption model.
        
        Verifies that a redemption can be created for a user and that
        the user's points are deducted accordingly.
        """
        # Initially the user has 1000 points
        self.assertEqual(self.reward_points.points, 1000)
        
        # Create a new redemption option
        gift_card_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="$50 Gift Card",
            description="Redeem for a $50 gift card",
            points_required=500,
            value=Decimal('50.00'),
            is_percentage=False,
            is_active=True,
            image="redemptions/gift_card.png",
            max_redemptions_per_user=1
        )
        
        # Create a redemption for the user
        redemption = Redemption.create_for_user(
            user=self.test_user,
            option=gift_card_option
        )
        
        # Verify the redemption was created
        self.assertEqual(redemption.user, self.test_user)
        self.assertEqual(redemption.option, gift_card_option)
        self.assertEqual(redemption.points_used, 500)
        self.assertEqual(redemption.value, Decimal('50.00'))
        self.assertEqual(redemption.status, "active")
        
        # Refresh the reward points from the database
        self.reward_points.refresh_from_db()
        
        # The user should now have 500 points (1000 - 500)
        self.assertEqual(self.reward_points.points, 500)
        
        # Verify that a points transaction was created
        transaction = PointsTransaction.objects.filter(
            user=self.test_user,
            program=self.reward_program,
            points=500,
            transaction_type='redeem'
        ).exists()
        
        self.assertTrue(transaction)
        
        # Try to create a redemption for an option the user cannot afford
        expensive_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="Luxury Tour",
            description="Redeem for a luxury tour",
            points_required=1000,
            value=Decimal('500.00'),
            is_percentage=False,
            is_active=True,
            image="redemptions/luxury_tour.png",
            max_redemptions_per_user=1
        )
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            Redemption.create_for_user(
                user=self.test_user,
                option=expensive_option
            )


class RewardsViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the rewards app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for rewards view tests.
        
        Extends the base setUp method to include necessary rewards data.
        """
        super().setUp()
        
        # Create a reward program
        self.reward_program = RewardProgram.objects.create(
            name="TravelGuide Rewards",
            description="Earn points for bookings and redeem for discounts and perks",
            points_expiry_months=12,
            terms_and_conditions="Standard terms apply",
            is_active=True
        )
        
        # Create reward tiers
        self.bronze_tier = RewardTier.objects.create(
            program=self.reward_program,
            name="Bronze",
            minimum_points=0,
            maximum_points=999,
            benefits="Basic benefits",
            icon="bronze_medal.png"
        )
        
        self.silver_tier = RewardTier.objects.create(
            program=self.reward_program,
            name="Silver",
            minimum_points=1000,
            maximum_points=4999,
            benefits="Silver benefits including priority support",
            icon="silver_medal.png"
        )
        
        # Create reward points for the test user
        self.reward_points = RewardPoints.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=1000,
            tier=self.silver_tier,
            last_activity_date=timezone.now()
        )
        
        # Create redemption options
        self.discount_option = RedemptionOption.objects.create(
            program=self.reward_program,
            name="10% Discount on Tours",
            description="Get a 10% discount on any tour booking",
            points_required=500,
            value=Decimal('0.10'),  # 10% discount
            is_percentage=True,
            is_active=True,
            image="redemptions/discount.png",
            max_redemptions_per_user=5
        )
        
        # Create a redemption
        self.redemption = Redemption.objects.create(
            user=self.test_user,
            option=self.discount_option,
            points_used=500,
            value=Decimal('0.10'),
            code="DISC123",
            status="active",
            redemption_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=30)
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_rewards_dashboard_view(self):
        """
        Test the rewards dashboard view.
        
        Verifies that the rewards dashboard view returns a 200 status code,
        uses the correct template, and includes the expected context data.
        """
        response = self.client.get(reverse('rewards:dashboard'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/dashboard.html')
        
        # Check that the reward points are in the context
        self.assertIn('reward_points', response.context)
        self.assertEqual(response.context['reward_points'], self.reward_points)
        
        # Check that the redemptions are in the context
        self.assertIn('redemptions', response.context)
        self.assertEqual(list(response.context['redemptions']), [self.redemption])
        
    def test_redemption_option_list_view(self):
        """
        Test the redemption option list view.
        
        Verifies that the redemption option list view returns a 200 status code,
        uses the correct template, and includes the redemption options in the context.
        """
        response = self.client.get(reverse('rewards:redemption_option_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/redemption_option_list.html')
        
        # Check that the redemption options are in the context
        self.assertIn('options', response.context)
        self.assertEqual(list(response.context['options']), [self.discount_option])
        
    def test_redemption_option_detail_view(self):
        """
        Test the redemption option detail view.
        
        Verifies that the redemption option detail view returns a 200 status code,
        uses the correct template, and includes the option in the context.
        """
        response = self.client.get(reverse('rewards:redemption_option_detail', kwargs={'pk': self.discount_option.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/redemption_option_detail.html')
        
        # Check that the option is in the context
        self.assertEqual(response.context['option'], self.discount_option)
        
        # Check that the can_redeem flag is in the context
        self.assertIn('can_redeem', response.context)
        self.assertTrue(response.context['can_redeem'])
        
    def test_redeem_option_view(self):
        """
        Test the redeem option view.
        
        Verifies that the redeem option view returns a 200 status code,
        uses the correct template, and allows redeeming an option.
        """
        response = self.client.get(reverse('rewards:redeem_option', kwargs={'pk': self.discount_option.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/redeem_option.html')
        
        # Submit the redemption form
        response = self.client.post(reverse('rewards:redeem_option', kwargs={'pk': self.discount_option.pk}))
        
        # Check that the redemption was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that a new redemption was created
        self.assertEqual(Redemption.objects.count(), 2)
        
        # Refresh the reward points from the database
        self.reward_points.refresh_from_db()
        
        # The user should now have 500 points (1000 - 500)
        self.assertEqual(self.reward_points.points, 500)
        
    def test_redemption_list_view(self):
        """
        Test the redemption list view.
        
        Verifies that the redemption list view returns a 200 status code,
        uses the correct template, and includes the user's redemptions in the context.
        """
        response = self.client.get(reverse('rewards:redemption_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/redemption_list.html')
        
        # Check that the redemptions are in the context
        self.assertIn('redemptions', response.context)
        self.assertEqual(list(response.context['redemptions']), [self.redemption])
        
    def test_redemption_detail_view(self):
        """
        Test the redemption detail view.
        
        Verifies that the redemption detail view returns a 200 status code,
        uses the correct template, and includes the redemption in the context.
        """
        response = self.client.get(reverse('rewards:redemption_detail', kwargs={'pk': self.redemption.pk}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/redemption_detail.html')
        
        # Check that the redemption is in the context
        self.assertEqual(response.context['redemption'], self.redemption)
        
    def test_transaction_list_view(self):
        """
        Test the transaction list view.
        
        Verifies that the transaction list view returns a 200 status code,
        uses the correct template, and includes the user's transactions in the context.
        """
        # Create a points transaction
        transaction = PointsTransaction.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=100,
            transaction_type='earn',
            description='Booking completion bonus',
            transaction_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=365)
        )
        
        response = self.client.get(reverse('rewards:transaction_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/transaction_list.html')
        
        # Check that the transactions are in the context
        self.assertIn('transactions', response.context)
        self.assertEqual(list(response.context['transactions']), [transaction])
        
    def test_tier_list_view(self):
        """
        Test the tier list view.
        
        Verifies that the tier list view returns a 200 status code,
        uses the correct template, and includes the tiers in the context.
        """
        response = self.client.get(reverse('rewards:tier_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'rewards/tier_list.html')
        
        # Check that the tiers are in the context
        self.assertIn('tiers', response.context)
        self.assertEqual(list(response.context['tiers']), [self.bronze_tier, self.silver_tier])
        
        # Check that the user's current tier is in the context
        self.assertIn('current_tier', response.context)
        self.assertEqual(response.context['current_tier'], self.silver_tier)
