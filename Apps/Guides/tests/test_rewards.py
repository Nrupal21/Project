"""
Test cases for the rewards app.

This module contains comprehensive test cases for all functionality
in the rewards app, including models, views, and reward program features.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from rewards.models import RewardProgram, RewardTier, RewardPoints, PointsTransaction, Redemption
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class RewardProgramModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RewardProgram model in the rewards app.
    
    These tests verify that RewardProgram objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the RewardProgram model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RewardProgram tests.
        
        Extends the base setUp method to include reward programs for testing.
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
    
    def test_reward_program_creation(self):
        """
        Test that a RewardProgram can be created with the expected attributes.
        
        Verifies that the RewardProgram model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new reward program
        program = RewardProgram.objects.create(
            name="Premium Rewards",
            description="Exclusive rewards for premium members",
            points_expiry_months=24,
            terms_and_conditions="Premium terms apply",
            is_active=True
        )
        
        # Verify the reward program was created with the correct attributes
        self.assertEqual(program.name, "Premium Rewards")
        self.assertEqual(program.description, "Exclusive rewards for premium members")
        self.assertEqual(program.points_expiry_months, 24)
        self.assertEqual(program.terms_and_conditions, "Premium terms apply")
        self.assertTrue(program.is_active)
        
    def test_reward_program_str_method(self):
        """
        Test the string representation of a RewardProgram object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the program name.
        """
        self.assertEqual(str(self.reward_program), "TravelGuide Rewards")
        
    def test_reward_program_get_absolute_url(self):
        """
        Test the get_absolute_url method of the RewardProgram model.
        
        Verifies that the URL generated for a program detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('rewards:program_detail', kwargs={'pk': self.reward_program.pk})
        self.assertEqual(self.reward_program.get_absolute_url(), expected_url)


class RewardTierModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RewardTier model in the rewards app.
    
    These tests verify that RewardTier objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the RewardTier model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RewardTier tests.
        
        Extends the base setUp method to include reward programs and tiers for testing.
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
        
        self.gold_tier = RewardTier.objects.create(
            program=self.reward_program,
            name="Gold",
            minimum_points=5000,
            maximum_points=9999,
            benefits="Gold benefits including priority support and free upgrades",
            icon="gold_medal.png"
        )
    
    def test_reward_tier_creation(self):
        """
        Test that a RewardTier can be created with the expected attributes.
        
        Verifies that the RewardTier model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new reward tier
        platinum_tier = RewardTier.objects.create(
            program=self.reward_program,
            name="Platinum",
            minimum_points=10000,
            maximum_points=None,  # No maximum
            benefits="Platinum benefits including all perks and exclusive offers",
            icon="platinum_medal.png"
        )
        
        # Verify the reward tier was created with the correct attributes
        self.assertEqual(platinum_tier.program, self.reward_program)
        self.assertEqual(platinum_tier.name, "Platinum")
        self.assertEqual(platinum_tier.minimum_points, 10000)
        self.assertIsNone(platinum_tier.maximum_points)
        self.assertEqual(platinum_tier.benefits, "Platinum benefits including all perks and exclusive offers")
        self.assertEqual(platinum_tier.icon, "platinum_medal.png")
        
    def test_reward_tier_str_method(self):
        """
        Test the string representation of a RewardTier object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the tier name and program name.
        """
        expected_str = "Bronze - TravelGuide Rewards"
        self.assertEqual(str(self.bronze_tier), expected_str)
        
    def test_get_tier_for_points(self):
        """
        Test the get_tier_for_points method of the RewardTier model.
        
        Verifies that the correct tier is returned for a given number of points.
        """
        # Test bronze tier (0-999 points)
        tier = RewardTier.objects.get_tier_for_points(self.reward_program, 500)
        self.assertEqual(tier, self.bronze_tier)
        
        # Test silver tier (1000-4999 points)
        tier = RewardTier.objects.get_tier_for_points(self.reward_program, 2500)
        self.assertEqual(tier, self.silver_tier)
        
        # Test gold tier (5000-9999 points)
        tier = RewardTier.objects.get_tier_for_points(self.reward_program, 7500)
        self.assertEqual(tier, self.gold_tier)
        
        # Test edge case (exactly 1000 points - should be silver)
        tier = RewardTier.objects.get_tier_for_points(self.reward_program, 1000)
        self.assertEqual(tier, self.silver_tier)
        
        # Test edge case (exactly 5000 points - should be gold)
        tier = RewardTier.objects.get_tier_for_points(self.reward_program, 5000)
        self.assertEqual(tier, self.gold_tier)


class RewardPointsModelTests(TravelGuideBaseTestCase):
    """
    Tests for the RewardPoints model in the rewards app.
    
    These tests verify that RewardPoints objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the RewardPoints model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for RewardPoints tests.
        
        Extends the base setUp method to include reward programs, tiers,
        and points for testing.
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
            points=500,
            tier=self.bronze_tier,
            last_activity_date=timezone.now()
        )
    
    def test_reward_points_creation(self):
        """
        Test that a RewardPoints can be created with the expected attributes.
        
        Verifies that the RewardPoints model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create reward points for the admin user
        admin_points = RewardPoints.objects.create(
            user=self.admin_user,
            program=self.reward_program,
            points=1500,
            tier=self.silver_tier,
            last_activity_date=timezone.now()
        )
        
        # Verify the reward points were created with the correct attributes
        self.assertEqual(admin_points.user, self.admin_user)
        self.assertEqual(admin_points.program, self.reward_program)
        self.assertEqual(admin_points.points, 1500)
        self.assertEqual(admin_points.tier, self.silver_tier)
        self.assertIsNotNone(admin_points.last_activity_date)
        
    def test_reward_points_str_method(self):
        """
        Test the string representation of a RewardPoints object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the user's username and points.
        """
        expected_str = f"testuser: 500 points"
        self.assertEqual(str(self.reward_points), expected_str)
        
    def test_reward_points_add_points(self):
        """
        Test the add_points method of the RewardPoints model.
        
        Verifies that points can be added correctly and that the tier
        is updated accordingly.
        """
        # Initially the user has 500 points and is in the Bronze tier
        self.assertEqual(self.reward_points.points, 500)
        self.assertEqual(self.reward_points.tier, self.bronze_tier)
        
        # Add 600 points
        self.reward_points.add_points(600)
        
        # Now the user should have 1100 points and be in the Silver tier
        self.assertEqual(self.reward_points.points, 1100)
        self.assertEqual(self.reward_points.tier, self.silver_tier)
        
        # The last activity date should be updated
        self.assertAlmostEqual(
            self.reward_points.last_activity_date,
            timezone.now(),
            delta=datetime.timedelta(seconds=10)
        )
        
    def test_reward_points_deduct_points(self):
        """
        Test the deduct_points method of the RewardPoints model.
        
        Verifies that points can be deducted correctly and that the tier
        is updated accordingly.
        """
        # Create a user with 1500 points in the Silver tier
        silver_points = RewardPoints.objects.create(
            user=self.admin_user,
            program=self.reward_program,
            points=1500,
            tier=self.silver_tier,
            last_activity_date=timezone.now()
        )
        
        # Deduct 600 points
        silver_points.deduct_points(600)
        
        # Now the user should have 900 points and be in the Bronze tier
        self.assertEqual(silver_points.points, 900)
        self.assertEqual(silver_points.tier, self.bronze_tier)
        
        # The last activity date should be updated
        self.assertAlmostEqual(
            silver_points.last_activity_date,
            timezone.now(),
            delta=datetime.timedelta(seconds=10)
        )
        
        # Test that deducting more points than available raises an error
        with self.assertRaises(ValueError):
            silver_points.deduct_points(1000)
            
    def test_reward_points_update_tier(self):
        """
        Test the update_tier method of the RewardPoints model.
        
        Verifies that the tier is updated correctly based on the current points.
        """
        # Initially the user has 500 points and is in the Bronze tier
        self.assertEqual(self.reward_points.tier, self.bronze_tier)
        
        # Update points to 1500
        self.reward_points.points = 1500
        self.reward_points.update_tier()
        
        # Now the user should be in the Silver tier
        self.assertEqual(self.reward_points.tier, self.silver_tier)
        
        # Update points to 200
        self.reward_points.points = 200
        self.reward_points.update_tier()
        
        # Now the user should be back in the Bronze tier
        self.assertEqual(self.reward_points.tier, self.bronze_tier)


class PointsTransactionModelTests(TravelGuideBaseTestCase):
    """
    Tests for the PointsTransaction model in the rewards app.
    
    These tests verify that PointsTransaction objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the PointsTransaction model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for PointsTransaction tests.
        
        Extends the base setUp method to include reward programs, points,
        and transactions for testing.
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
        
        # Create reward points for the test user
        self.reward_points = RewardPoints.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=500,
            tier=self.bronze_tier,
            last_activity_date=timezone.now()
        )
        
        # Create a points transaction
        self.transaction = PointsTransaction.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=100,
            transaction_type='earn',
            description='Booking completion bonus',
            transaction_date=timezone.now(),
            expiry_date=timezone.now() + datetime.timedelta(days=365)
        )
    
    def test_points_transaction_creation(self):
        """
        Test that a PointsTransaction can be created with the expected attributes.
        
        Verifies that the PointsTransaction model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create a new points transaction
        transaction = PointsTransaction.objects.create(
            user=self.test_user,
            program=self.reward_program,
            points=50,
            transaction_type='redeem',
            description='Discount redemption',
            transaction_date=timezone.now(),
            expiry_date=None  # No expiry for redemptions
        )
        
        # Verify the transaction was created with the correct attributes
        self.assertEqual(transaction.user, self.test_user)
        self.assertEqual(transaction.program, self.reward_program)
        self.assertEqual(transaction.points, 50)
        self.assertEqual(transaction.transaction_type, 'redeem')
        self.assertEqual(transaction.description, 'Discount redemption')
        self.assertIsNotNone(transaction.transaction_date)
        self.assertIsNone(transaction.expiry_date)
        
    def test_points_transaction_str_method(self):
        """
        Test the string representation of a PointsTransaction object.
        
        Verifies that the __str__ method returns the expected string,
        which should include the transaction type, points, and user.
        """
        expected_str = f"Earn: 100 points for testuser"
        self.assertEqual(str(self.transaction), expected_str)
        
    def test_points_transaction_is_expired(self):
        """
        Test the is_expired property of the PointsTransaction model.
        
        Verifies that the is_expired property correctly determines
        if the transaction is expired based on the expiry date.
        """
        # Initially the transaction is not expired
        self.assertFalse(self.transaction.is_expired)
        
        # Set the expiry date to yesterday
        self.transaction.expiry_date = timezone.now() - datetime.timedelta(days=1)
        self.transaction.save()
        
        # Now the transaction should be expired
        self.assertTrue(self.transaction.is_expired)
        
        # Set the expiry date to None (no expiry)
        self.transaction.expiry_date = None
        self.transaction.save()
        
        # The transaction should not be expired
        self.assertFalse(self.transaction.is_expired)
        
    def test_points_transaction_create_for_user(self):
        """
        Test the create_for_user method of the PointsTransaction model.
        
        Verifies that a transaction can be created for a user and that
        the user's points are updated accordingly.
        """
        # Initially the user has 500 points
        self.assertEqual(self.reward_points.points, 500)
        
        # Create an 'earn' transaction for 200 points
        transaction = PointsTransaction.create_for_user(
            user=self.test_user,
            program=self.reward_program,
            points=200,
            transaction_type='earn',
            description='Review submission bonus'
        )
        
        # Verify the transaction was created
        self.assertEqual(transaction.user, self.test_user)
        self.assertEqual(transaction.points, 200)
        self.assertEqual(transaction.transaction_type, 'earn')
        
        # Refresh the reward points from the database
        self.reward_points.refresh_from_db()
        
        # The user should now have 700 points (500 + 200)
        self.assertEqual(self.reward_points.points, 700)
        
        # Create a 'redeem' transaction for 100 points
        transaction = PointsTransaction.create_for_user(
            user=self.test_user,
            program=self.reward_program,
            points=100,
            transaction_type='redeem',
            description='Discount redemption'
        )
        
        # Verify the transaction was created
        self.assertEqual(transaction.user, self.test_user)
        self.assertEqual(transaction.points, 100)
        self.assertEqual(transaction.transaction_type, 'redeem')
        
        # Refresh the reward points from the database
        self.reward_points.refresh_from_db()
        
        # The user should now have 600 points (700 - 100)
        self.assertEqual(self.reward_points.points, 600)
