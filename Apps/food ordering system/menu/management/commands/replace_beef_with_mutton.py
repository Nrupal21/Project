"""
Django management command to replace all beef menu items with mutton items.

This command safely replaces beef-related content in menu items with mutton equivalents.
It includes a dry-run mode to preview changes before committing them.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from menu.models import MenuItem
import re


class Command(BaseCommand):
    """
    Management command to replace beef items with mutton items.
    
    Usage:
        python manage.py replace_beef_with_mutton --dry-run  # Preview changes
        python manage.py replace_beef_with_mutton --confirm  # Apply changes
        python manage.py replace_beef_with_mutton --restaurant-id 1  # Specific restaurant
    """
    
    help = 'Replace all beef menu items with mutton items in the menu system'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what changes will be made without applying them'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm and apply the changes'
        )
        parser.add_argument(
            '--restaurant-id',
            type=int,
            help='Limit replacement to specific restaurant ID (optional)'
        )
        parser.add_argument(
            '--case-sensitive',
            action='store_true',
            help='Make the search case-sensitive (default: case-insensitive)'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        dry_run = options['dry_run']
        confirm = options['confirm']
        restaurant_id = options.get('restaurant_id')
        case_sensitive = options['case_sensitive']
        
        # Validate arguments
        if not dry_run and not confirm:
            self.stdout.write(
                self.style.ERROR('Please use either --dry-run to preview changes or --confirm to apply them.')
            )
            return
        
        if dry_run and confirm:
            self.stdout.write(
                self.style.ERROR('Cannot use --dry-run and --confirm together.')
            )
            return
        
        try:
            # Get menu items to process
            queryset = MenuItem.objects.all()
            if restaurant_id:
                queryset = queryset.filter(restaurant_id=restaurant_id)
                self.stdout.write(f"Limiting to restaurant ID: {restaurant_id}")
            
            # Count total items
            total_items = queryset.count()
            if total_items == 0:
                self.stdout.write(self.style.WARNING('No menu items found.'))
                return
            
            self.stdout.write(f"Found {total_items} menu items to check...")
            
            # Find items containing beef
            beef_items = self.find_beef_items(queryset, case_sensitive)
            
            if not beef_items:
                self.stdout.write(self.style.SUCCESS('No beef items found to replace.'))
                return
            
            self.stdout.write(f"Found {len(beef_items)} items containing beef:")
            
            # Show preview of changes
            self.show_preview(beef_items, case_sensitive)
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS('Dry run completed. Use --confirm to apply these changes.')
                )
                return
            
            if confirm:
                # Ask for final confirmation
                response = input(f"\nAre you sure you want to replace {len(beef_items)} items? (yes/no): ")
                if response.lower() != 'yes':
                    self.stdout.write(self.style.WARNING('Operation cancelled.'))
                    return
                
                # Apply changes
                self.apply_changes(beef_items, case_sensitive)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully replaced {len(beef_items)} beef items with mutton.')
                )
        
        except Exception as e:
            raise CommandError(f'Error during replacement: {str(e)}')
    
    def find_beef_items(self, queryset, case_sensitive):
        """
        Find menu items containing beef-related content.
        
        Args:
            queryset: MenuItem queryset to search
            case_sensitive: Whether search should be case-sensitive
        
        Returns:
            list: List of MenuItem objects containing beef
        """
        beef_items = []
        
        for item in queryset:
            # Check name and description for beef (handle None description)
            text_to_check = f"{item.name} {item.description or ''}"
            
            if case_sensitive:
                # Case-sensitive search for different capitalizations
                if re.search(r'\bbeef\b', text_to_check) or \
                   re.search(r'\bBeef\b', text_to_check) or \
                   re.search(r'\bBEEF\b', text_to_check):
                    beef_items.append(item)
            else:
                # Case-insensitive search
                if re.search(r'\bbeef\b', text_to_check, re.IGNORECASE):
                    beef_items.append(item)
        
        return beef_items
    
    def show_preview(self, beef_items, case_sensitive):
        """
        Show preview of changes that will be made.
        
        Args:
            beef_items: List of MenuItem objects containing beef
            case_sensitive: Whether replacement is case-sensitive
        """
        self.stdout.write("\n" + "="*80)
        self.stdout.write("PREVIEW OF CHANGES:")
        self.stdout.write("="*80)
        
        for i, item in enumerate(beef_items, 1):
            self.stdout.write(f"\n{i}. Restaurant: {item.restaurant.name if item.restaurant else 'Unknown'}")
            self.stdout.write(f"   Category: {item.category.name}")
            self.stdout.write(f"   Current Name: {item.name}")
            self.stdout.write(f"   New Name: {self.replace_text(item.name, case_sensitive)}")
            
            if item.description:
                self.stdout.write(f"   Current Description: {item.description[:100]}...")
                new_desc = self.replace_text(item.description, case_sensitive)
                self.stdout.write(f"   New Description: {new_desc[:100]}...")
        
        self.stdout.write("\n" + "="*80)
    
    def replace_text(self, text, case_sensitive):
        """
        Replace beef with mutton in the given text.
        
        Args:
            text: Text to replace in
            case_sensitive: Whether replacement should be case-sensitive
        
        Returns:
            str: Text with beef replaced by mutton
        """
        if case_sensitive:
            # Case-sensitive replacement
            text = re.sub(r'\bbeef\b', 'mutton', text)
            text = re.sub(r'\bBeef\b', 'Mutton', text)
            text = re.sub(r'\bBEEF\b', 'MUTTON', text)
        else:
            # Case-insensitive replacement with case preservation
            def replace_match(match):
                word = match.group()
                if word.isupper():
                    return 'MUTTON'
                elif word.islower():
                    return 'mutton'
                elif word[0].isupper() and word[1:].islower():
                    return 'Mutton'
                else:
                    return 'mutton'
            
            text = re.sub(r'\bbeef\b', replace_match, text, flags=re.IGNORECASE)
        
        return text
    
    def apply_changes(self, beef_items, case_sensitive):
        """
        Apply the beef to mutton replacement.
        
        Args:
            beef_items: List of MenuItem objects to update
            case_sensitive: Whether replacement should be case-sensitive
        """
        with transaction.atomic():
            for item in beef_items:
                # Update name
                item.name = self.replace_text(item.name, case_sensitive)
                
                # Update description
                if item.description:
                    item.description = self.replace_text(item.description, case_sensitive)
                
                # Save the item
                item.save()
                
                self.stdout.write(f"Updated: {item.name}")
