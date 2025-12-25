from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from customer.models import UserProfile


class Command(BaseCommand):
    """
    Management command to display all users in the database with their credentials.
    
    Usage:
        python manage.py get_users
    
    This command helps debug login issues by showing all available users
    and their account status.
    """
    
    help = 'Display all users in the database with their login information'
    
    def handle(self, *args, **options):
        """
        Execute the command to display user information.
        
        Retrieves all users from the database and displays their
        credentials and account status for testing purposes.
        """
        User = get_user_model()
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('ALL USERS IN DATABASE - Login Credentials'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in database!'))
            self.stdout.write('Create test users with:')
            self.stdout.write('User.objects.create_user("username", "email@example.com", "password")')
            return
        
        self.stdout.write(f'Total users found: {users.count()}')
        self.stdout.write('-' * 80)
        
        for i, user in enumerate(users, 1):
            self.stdout.write(f'USER #{i}')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Active: {user.is_active}')
            self.stdout.write(f'Staff: {user.is_staff}')
            self.stdout.write(f'Superuser: {user.is_superuser}')
            self.stdout.write(f'Date Joined: {user.date_joined}')
            
            # Check if user has profile
            try:
                profile = UserProfile.objects.get(user=user)
                self.stdout.write(f'Profile Name: {profile.full_name}')
                self.stdout.write(f'Phone: {profile.phone_number}')
            except UserProfile.DoesNotExist:
                self.stdout.write('Profile: Not found')
            
            self.stdout.write('Password: [Cannot display - passwords are hashed]')
            self.stdout.write('To test login, you need the original password or reset it')
            self.stdout.write('-' * 80)
        
        self.stdout.write(self.style.SUCCESS('\nTEST LOGIN URLS:'))
        self.stdout.write('- Customer Login: http://tetech.in:8000/login/')
        self.stdout.write('- Admin Login: http://tetech.in:8000/admin/')
        
        self.stdout.write(self.style.SUCCESS('\nTO CREATE TEST USER:'))
        self.stdout.write('User.objects.create_user("testuser", "test@example.com", "testpass123")')
        
        self.stdout.write(self.style.SUCCESS('\nTO RESET USER PASSWORD:'))
        self.stdout.write('user = User.objects.get(username="username")')
        self.stdout.write('user.set_password("new_password")')
        self.stdout.write('user.save()')
