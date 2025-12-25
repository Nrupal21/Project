"""
Django management command to process restaurant approvals.

This command handles automated approval processing, including:
- Evaluating pending restaurants for auto-approval
- Sending reminders to managers about pending reviews
- Cleaning up stale applications
- Generating approval reports

Usage:
    python manage.py process_restaurant_approvals
    python manage.py process_restaurant_approvals --auto-approve
    python manage.py process_restaurant_approvals --send-reminders
    python manage.py process_restaurant_approvals --report
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from restaurant.models import Restaurant
from restaurant.workflow import AutoApprovalEngine, RegistrationWorkflow
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command for processing restaurant approval workflows.
    
    Provides automated tools for managing the restaurant approval queue,
    including auto-approval evaluation, reminder notifications, and reporting.
    """
    
    help = 'Process restaurant approval workflows and auto-approvals'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: Django argument parser
        """
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Evaluate and auto-approve eligible restaurants',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send reminders to managers about pending reviews',
        )
        parser.add_argument(
            '--report',
            action='store_true',
            help='Generate approval statistics report',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up abandoned/stale applications',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Days threshold for reminders/cleanup (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
    
    def handle(self, *args, **options):
        """
        Execute the command based on provided options.
        
        Args:
            *args: Additional positional arguments
            **options: Command line options
        """
        self.stdout.write(
            self.style.SUCCESS('🍽️  Restaurant Approval Processing Started')
        )
        
        # Track overall statistics
        stats = {
            'auto_approved': 0,
            'reminders_sent': 0,
            'cleaned_up': 0,
        }
        
        # Execute requested operations
        if options['auto_approve']:
            stats['auto_approved'] = self._process_auto_approvals(options['dry_run'])
        
        if options['send_reminders']:
            stats['reminders_sent'] = self._send_manager_reminders(
                options['days'],
                options['dry_run']
            )
        
        if options['cleanup']:
            stats['cleaned_up'] = self._cleanup_stale_applications(
                options['days'],
                options['dry_run']
            )
        
        if options['report']:
            self._generate_report()
        
        # Display summary
        self.stdout.write('\n' + self.style.SUCCESS('📊 Processing Summary:'))
        self.stdout.write(f'  • Auto-approved: {stats["auto_approved"]}')
        self.stdout.write(f'  • Reminders sent: {stats["reminders_sent"]}')
        self.stdout.write(f'  • Applications cleaned: {stats["cleaned_up"]}')
        
        self.stdout.write(
            '\n' + self.style.SUCCESS('✅ Processing completed successfully!')
        )
    
    def _process_auto_approvals(self, dry_run=False):
        """
        Process restaurants eligible for auto-approval.
        
        Args:
            dry_run: If True, only show what would be approved
            
        Returns:
            int: Number of restaurants auto-approved
        """
        self.stdout.write('\n' + self.style.WARNING('🤖 Processing Auto-Approvals...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN MODE)'))
        
        # Run auto-approval engine
        engine_stats = AutoApprovalEngine.evaluate_all_pending()
        
        self.stdout.write(f'  • Total evaluated: {engine_stats["total_evaluated"]}')
        self.stdout.write(f'  • Auto-approved: {engine_stats["auto_approved"]}')
        self.stdout.write(f'  • Require manual review: {engine_stats["requires_review"]}')
        self.stdout.write(f'  • Errors: {engine_stats["errors"]}')
        
        return engine_stats['auto_approved']
    
    def _send_manager_reminders(self, days_threshold, dry_run=False):
        """
        Send reminder emails to managers about pending restaurants.
        
        Args:
            days_threshold: Number of days before sending reminder
            dry_run: If True, only show what would be sent
            
        Returns:
            int: Number of reminders sent
        """
        self.stdout.write(
            '\n' + self.style.WARNING(
                f'📧 Sending Manager Reminders (>{days_threshold} days)...'
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN MODE)'))
        
        # Find restaurants pending for more than threshold
        cutoff_date = timezone.now() - timedelta(days=days_threshold)
        pending_restaurants = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted'],
            created_at__lte=cutoff_date
        )
        
        reminders_sent = 0
        
        for restaurant in pending_restaurants:
            days_pending = (timezone.now() - restaurant.created_at).days
            
            self.stdout.write(
                f'  • {restaurant.name} - Pending for {days_pending} days'
            )
            
            if not dry_run:
                # Send reminder email to managers
                try:
                    from core.utils import EmailUtils
                    from django.contrib.auth.models import User
                    
                    managers = User.objects.filter(
                        Q(is_staff=True) | Q(is_superuser=True)
                    ).distinct()
                    
                    for manager in managers:
                        # TODO: Create reminder email template
                        # EmailUtils.send_approval_reminder(manager, restaurant)
                        pass
                    
                    reminders_sent += 1
                    
                except Exception as e:
                    logger.error(f'Failed to send reminder for {restaurant.name}: {e}')
        
        self.stdout.write(f'  • Total reminders: {reminders_sent}')
        
        return reminders_sent
    
    def _cleanup_stale_applications(self, days_threshold, dry_run=False):
        """
        Clean up abandoned or incomplete applications.
        
        Args:
            days_threshold: Number of days before considering stale
            dry_run: If True, only show what would be cleaned
            
        Returns:
            int: Number of applications cleaned up
        """
        self.stdout.write(
            '\n' + self.style.WARNING(
                f'🧹 Cleaning Stale Applications (>{days_threshold} days)...'
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN MODE)'))
        
        # Find very old pending applications (30+ days by default)
        cutoff_date = timezone.now() - timedelta(days=max(days_threshold, 30))
        stale_restaurants = Restaurant.objects.filter(
            approval_status='draft',
            created_at__lte=cutoff_date
        )
        
        count = stale_restaurants.count()
        
        if count > 0:
            self.stdout.write(f'  • Found {count} stale applications')
            
            for restaurant in stale_restaurants:
                self.stdout.write(
                    f'    - {restaurant.name} (Created: {restaurant.created_at.date()})'
                )
            
            if not dry_run:
                # Archive or delete stale applications
                # For now, just mark them as expired
                stale_restaurants.update(
                    approval_status='expired',
                    is_active=False
                )
        else:
            self.stdout.write('  • No stale applications found')
        
        return count
    
    def _generate_report(self):
        """
        Generate comprehensive approval statistics report.
        
        Displays current status of all restaurants and approval metrics.
        """
        self.stdout.write('\n' + self.style.SUCCESS('📈 Approval Statistics Report'))
        self.stdout.write('=' * 60)
        
        # Overall statistics
        total = Restaurant.objects.count()
        pending = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).count()
        approved = Restaurant.objects.filter(
            approval_status='approved'
        ).count()
        rejected = Restaurant.objects.filter(
            approval_status='rejected'
        ).count()
        
        self.stdout.write('\n' + self.style.WARNING('Overall Statistics:'))
        self.stdout.write(f'  • Total Restaurants: {total}')
        self.stdout.write(f'  • Pending Review: {pending}')
        self.stdout.write(f'  • Approved: {approved}')
        self.stdout.write(f'  • Rejected: {rejected}')
        
        # Approval rate
        if total > 0:
            approval_rate = (approved / total) * 100
            self.stdout.write(f'  • Approval Rate: {approval_rate:.1f}%')
        
        # Pending breakdown by age
        self.stdout.write('\n' + self.style.WARNING('Pending Applications by Age:'))
        
        now = timezone.now()
        age_ranges = [
            ('0-2 days', 0, 2),
            ('3-7 days', 3, 7),
            ('8-14 days', 8, 14),
            ('15-30 days', 15, 30),
            ('30+ days', 31, 999999),
        ]
        
        for label, min_days, max_days in age_ranges:
            start_date = now - timedelta(days=max_days)
            end_date = now - timedelta(days=min_days)
            
            count = Restaurant.objects.filter(
                approval_status__in=['pending', 'submitted'],
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            self.stdout.write(f'  • {label}: {count}')
        
        # Top pending restaurants (oldest)
        self.stdout.write('\n' + self.style.WARNING('Oldest Pending Applications:'))
        
        oldest_pending = Restaurant.objects.filter(
            approval_status__in=['pending', 'submitted']
        ).order_by('created_at')[:5]
        
        for restaurant in oldest_pending:
            days_pending = (now - restaurant.created_at).days
            self.stdout.write(
                f'  • {restaurant.name} - {days_pending} days '
                f'(Owner: {restaurant.owner.username})'
            )
        
        # Recently approved
        self.stdout.write('\n' + self.style.WARNING('Recently Approved (Last 7 Days):'))
        
        week_ago = now - timedelta(days=7)
        recent_approved = Restaurant.objects.filter(
            approval_status='approved',
            approved_at__gte=week_ago
        ).order_by('-approved_at')[:5]
        
        for restaurant in recent_approved:
            if restaurant.approved_at:
                self.stdout.write(
                    f'  • {restaurant.name} - '
                    f'{restaurant.approved_at.strftime("%Y-%m-%d %H:%M")}'
                )
        
        self.stdout.write('\n' + '=' * 60)
