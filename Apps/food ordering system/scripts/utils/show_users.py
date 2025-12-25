import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings')
django.setup()

from django.contrib.auth import get_user_model
from customer.models import UserProfile

User = get_user_model()

print("="*80)
print("ALL USERS IN DATABASE - Login Credentials")
print("="*80)

users = User.objects.all()
if not users.exists():
    print("No users found in database!")
    print("\nTo create a test user, run:")
    print("User.objects.create_user('testuser', 'test@example.com', 'testpass123')")
else:
    print(f"Total users found: {users.count()}")
    print("-"*80)
    
    for i, user in enumerate(users, 1):
        print(f"\nUSER #{i}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Active: {user.is_active}")
        print(f"Staff: {user.is_staff}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Date Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M') if user.date_joined else 'N/A'}")
        
        # Check if user has profile
        try:
            profile = UserProfile.objects.get(user=user)
            print(f"Full Name: {profile.full_name}")
            print(f"Phone: {profile.phone_number}")
            print(f"Address: {profile.get_full_address()}")
        except UserProfile.DoesNotExist:
            print("Profile: Not found")
        
        print("Password: [Hashed - cannot be displayed]")
        print("-"*80)

print("\n" + "="*80)
print("LOGIN TESTING INSTRUCTIONS:")
print("="*80)
print("1. Try logging in with the above usernames")
print("2. If you don't remember the password, reset it with:")
print("   python manage.py shell")
print("   >>> from django.contrib.auth import get_user_model")
print("   >>> User = get_user_model()")
print("   >>> user = User.objects.get(username='USERNAME')")
print("   >>> user.set_password('NEW_PASSWORD')")
print("   >>> user.save()")
print("\n3. Test login at: http://tetech.in:8000/login/")
print("4. Admin login at: http://tetech.in:8000/admin/")
