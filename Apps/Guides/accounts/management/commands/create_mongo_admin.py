"""
Management command to create a superuser with admin role for MongoDB.
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils.text import capfirst

User = get_user_model()

class Command(BaseCommand):
    """
    Command to create a superuser with admin role for MongoDB.
    """
    help = 'Create a superuser with admin role for MongoDB'
    requires_migrations_checks = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)
    
    def handle(self, *args, **options):
        username = None
        email = None
        password = None
        
        # Get username from input
        while username is None or username.strip() == '':
            username = input('Username: ').strip()
            if not username:
                self.stderr.write('Error: Username cannot be blank.')
        
        # Get email from input
        while email is None or email.strip() == '':
            email = input('Email address: ').strip()
            if not email:
                self.stderr.write('Error: Email cannot be blank.')
        
        # Get password from input
        while password is None or password.strip() == '':
            password = input('Password: ')
            if not password:
                self.stderr.write('Error: Password cannot be blank.')
            if len(password) < 8:
                self.stderr.write('Error: Password must be at least 8 characters long.')
                password = None
        
        # Check if user already exists
        if self.UserModel.objects.filter(username=username).exists():
            self.stderr.write(f'Error: Username "{username}" is already taken.')
            return
        
        if self.UserModel.objects.filter(email=email).exists():
            self.stderr.write(f'Error: Email "{email}" is already registered.')
            return
        
        try:
            # Create the superuser
            user = self.UserModel(
                username=username,
                email=email,
                is_staff=True,
                is_superuser=True,
                is_active=True,
                role='admin'  # Set the role to admin
            )
            
            user.set_password(password)
            user.save(using=self._db)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
            
        except Exception as e:
            self.stderr.write(f'Error creating admin user: {e}')
            if 'username' in str(e).lower():
                self.stderr.write('Error: That username is already taken.')
            if 'email' in str(e).lower():
                self.stderr.write('Error: That email is already registered.')
            sys.exit(1)
