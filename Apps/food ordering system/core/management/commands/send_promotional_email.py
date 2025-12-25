"""
Django management command for sending promotional emails.
Allows administrators to send marketing emails to users who have opted in.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils import timezone
from customer.models import EmailPreference
from core.utils import EmailUtils
import argparse


class Command(BaseCommand):
    """
    Management command to send promotional emails to opted-in users.
    
    Usage:
        python manage.py send_promotional_email --template "emails/special_offer.html" --subject "Weekend Special!" --test
    
    Options:
        --template: Path to HTML email template (required)
        --subject: Email subject line (required)
        --test: Send test email only (to admin users)
        --users: Comma-separated list of usernames (optional, sends to specific users)
        --type: Type of promotional email (promotional|newsletter) (default: promotional)
    """
    
    help = 'Send promotional emails to users who have opted in'
    
    def add_arguments(self, parser):
        """
        Add command line arguments for the promotional email command.
        
        Args:
            parser: Argument parser instance
        """
        parser.add_argument(
            '--template',
            type=str,
            required=True,
            help='Path to HTML email template (e.g., "emails/special_offer.html")'
        )
        parser.add_argument(
            '--subject',
            type=str,
            required=True,
            help='Email subject line'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test email only (to admin users)'
        )
        parser.add_argument(
            '--users',
            type=str,
            help='Comma-separated list of usernames to send to (optional)'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['promotional', 'newsletter'],
            default='promotional',
            help='Type of promotional email (default: promotional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show who would receive emails without sending'
        )
    
    def handle(self, *args, **options):
        """
        Handle the command execution.
        
        Processes the promotional email sending based on provided options.
        """
        template = options['template']
        subject = options['subject']
        test_mode = options['test']
        user_list = options['users']
        email_type = options['type']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('🍔 Starting Promotional Email Campaign'))
        self.stdout.write(f"Template: {template}")
        self.stdout.write(f"Subject: {subject}")
        self.stdout.write(f"Type: {email_type}")
        self.stdout.write(f"Test Mode: {test_mode}")
        self.stdout.write(f"Dry Run: {dry_run}")
        
        try:
            # Validate template exists
            try:
                render_to_string(template, {})
                self.stdout.write(self.style.SUCCESS('✅ Template validation passed'))
            except Exception as e:
                raise CommandError(f"Template validation failed: {e}")
            
            # Get target users
            if test_mode:
                # Send to admin users only
                target_users = User.objects.filter(is_staff=True)
                self.stdout.write(f"Target: {target_users.count()} admin users")
            elif user_list:
                # Send to specific users
                usernames = [u.strip() for u in user_list.split(',')]
                target_users = User.objects.filter(username__in=usernames)
                self.stdout.write(f"Target: {target_users.count()} specific users")
            else:
                # Send to all opted-in users
                if email_type == 'promotional':
                    target_users = User.objects.filter(
                        email_preferences__promotional_emails=True
                    )
                else:  # newsletter
                    target_users = User.objects.filter(
                        email_preferences__newsletter_emails=True
                    )
                self.stdout.write(f"Target: {target_users.count()} opted-in users")
            
            if not target_users.exists():
                self.stdout.write(self.style.WARNING('⚠️  No target users found'))
                return
            
            # Prepare email context
            context = {
                'site_name': 'Food Ordering System',
                'site_url': 'https://tetech.in/',
                'site_domain': 'tetech.in',
                'current_year': timezone.now().year,
                'campaign_date': timezone.now().strftime('%B %d, %Y'),
            }
            
            if dry_run:
                # Show who would receive emails without sending
                self.stdout.write(self.style.SUCCESS('\n📋 Dry Run - Users who would receive emails:'))
                for user in target_users:
                    email_pref = user.email_preferences
                    preferences = email_pref.get_active_preferences()
                    self.stdout.write(f"  - {user.username} ({user.email}) - {', '.join(preferences)}")
                self.stdout.write(self.style.SUCCESS(f'\nTotal emails that would be sent: {target_users.count()}'))
                return
            
            # Send emails
            self.stdout.write(self.style.SUCCESS('\n📧 Sending promotional emails...'))
            
            results = EmailUtils.send_promotional_email(
                subject=subject,
                template_name=template,
                context=context,
                user_list=target_users,
                fail_silently=False,
            )
            
            # Display results
            self.stdout.write(self.style.SUCCESS('\n📊 Campaign Results:'))
            self.stdout.write(f"  ✅ Successful: {results['success']}")
            self.stdout.write(f"  ❌ Failed: {len(results['failed'])}")
            
            if results['failed']:
                self.stdout.write(self.style.WARNING('\nFailed deliveries:'))
                for email in results['failed']:
                    self.stdout.write(f"  - {email}")
            
            self.stdout.write(self.style.SUCCESS(f'\n🎉 Campaign completed! {results["success"]}/{target_users.count()} emails sent successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Campaign failed: {str(e)}'))
            raise CommandError(f'Promotional email campaign failed: {str(e)}')
