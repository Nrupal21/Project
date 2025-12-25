"""
Django management command to expire loyalty points.

This command should be run daily via cron to automatically expire
earned points that have passed their expiration date and create
expiration transactions for audit purposes.

Usage:
    python manage.py expire_loyalty_points [--dry-run]

Options:
    --dry-run: Show what would be expired without actually expiring points
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, models
from customer.models import LoyaltyTransaction, UserProfile
from datetime import timedelta


class Command(BaseCommand):
    """
    Management command to expire loyalty points.
    
    Finds all earned points that have expired and creates expiration
    transactions while updating user balances. Provides dry-run mode
    for testing and detailed logging.
    """
    
    help = 'Expire loyalty points that have passed their expiration date'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Argument parser instance
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually expiring points'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each expired transaction'
        )
    
    def handle(self, *args, **options):
        """
        Main command execution logic.
        
        Args:
            *args: Command line arguments
            **options: Command line options
        """
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS('🏆 Starting loyalty points expiration process...')
        )
        
        # Find all expired earned points that haven't been expired yet
        expired_transactions = LoyaltyTransaction.objects.filter(
            transaction_type='earned',
            expires_at__lte=timezone.now(),
            points__gt=0  # Only positive points (earned points)
        ).select_related('user')
        
        if not expired_transactions.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ No expired points found to process.')
            )
            return
        
        total_points_to_expire = expired_transactions.aggregate(
            total=models.Sum('points')
        )['total'] or 0
        
        total_users = expired_transactions.values('user').distinct().count()
        
        self.stdout.write(
            self.style.WARNING(
                f'📊 Found {expired_transactions.count()} expired transactions '
                f'worth {total_points_to_expire} points for {total_users} users'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
            
            if verbose:
                for trans in expired_transactions:
                    self.stdout.write(
                        f'  • {trans.user.username}: {trans.points} points '
                        f'(expired on {trans.expires_at.strftime("%Y-%m-%d")})'
                    )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Dry run completed. Use without --dry-run to actually expire points.')
            )
            return
        
        # Process expiration by user to avoid multiple transactions per user
        expired_by_user = {}
        for trans in expired_transactions:
            user_id = trans.user.id
            if user_id not in expired_by_user:
                expired_by_user[user_id] = {
                    'user': trans.user,
                    'total_points': 0,
                    'transactions': []
                }
            expired_by_user[user_id]['total_points'] += trans.points
            expired_by_user[user_id]['transactions'].append(trans)
        
        # Process each user's expired points
        successful_expirations = 0
        failed_expirations = 0
        
        for user_id, data in expired_by_user.items():
            user = data['user']
            total_expired = data['total_points']
            transactions = data['transactions']
            
            try:
                with transaction.atomic():
                    # Get user profile with lock to prevent race conditions
                    user_profile = UserProfile.objects.select_for_update().get(user=user)
                    
                    # Create expiration transaction
                    new_balance = user_profile.points_balance - total_expired
                    LoyaltyTransaction.objects.create(
                        user=user,
                        transaction_type='expired',
                        points=-total_expired,  # Negative for expiration
                        balance_after=new_balance,
                        description=f'{total_expired} points expired from {len(transactions)} transactions',
                    )
                    
                    # Update user profile balance
                    user_profile.points_balance = max(0, new_balance)  # Prevent negative balance
                    user_profile.save()
                    
                    successful_expirations += 1
                    
                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ {user.username}: Expired {total_expired} points '
                                f'(new balance: {user_profile.points_balance})'
                            )
                        )
                        
            except Exception as e:
                failed_expirations += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Failed to expire points for {user.username}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📈 EXPIRATION SUMMARY:'
                f'\n  • Users processed: {len(expired_by_user)}'
                f'\n  • Successful expirations: {successful_expirations}'
                f'\n  • Failed expirations: {failed_expirations}'
                f'\n  • Total points expired: {total_points_to_expire}'
            )
        )
        
        if failed_expirations > 0:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Some expirations failed. Please check the logs above.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '🎉 All expirations completed successfully!'
                )
            )
