"""
Serializers for the accounts app.

This module contains serializers for the User, UserProfile, and UserPreferences models.
These serializers handle the conversion of model instances to JSON and vice versa.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import CustomUser, UserProfile, UserPreferences

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    
    Handles the serialization of the User model with role-based access control.
    Includes password field for write operations but excludes it from read operations.
    """
    role = serializers.ChoiceField(
        choices=CustomUser.UserRole.choices,
        default=CustomUser.UserRole.USER,
        required=False
    )
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'password', 'role', 'is_active', 'is_staff')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'is_active': {'read_only': True},
            'is_staff': {'read_only': True}
        }
    
    def create(self, validated_data):
        """
        Create and return a new User instance.
        
        Args:
            validated_data (dict): Validated user data
            
        Returns:
            User: Newly created user instance
        """
        # Hash the password before saving
        validated_data['password'] = make_password(validated_data.get('password'))
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing User instance.
        
        Args:
            instance (User): User instance to update
            validated_data (dict): Validated user data
            
        Returns:
            User: Updated user instance
        """
        # Hash the password if it's being updated
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data.get('password'))
        return super().update(instance, validated_data)

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model.
    
    Includes nested user information and handles profile picture uploads.
    """
    user = UserSerializer(required=True)
    age = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = serializers.ChoiceField(
        source='user.role',
        choices=CustomUser.UserRole.choices,
        read_only=True,
        help_text="User's role in the system"
    )
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'date_of_birth', 'phone_number', 
                 'profile_picture', 'bio', 'created_at', 'updated_at',
                 'age', 'full_name', 'role')
        read_only_fields = ('created_at', 'updated_at', 'role')
    
    def update(self, instance, validated_data):
        """
        Update and return an existing UserProfile instance.
        
        Also handles updating the nested User instance if user data is provided.
        
        Args:
            instance (UserProfile): UserProfile instance to update
            validated_data (dict): Validated profile data
            
        Returns:
            UserProfile: Updated user profile instance
        """
        user_data = validated_data.pop('user', None)
        
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update nested User fields if provided
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if attr == 'password':
                    user.set_password(value)
                else:
                    setattr(user, attr, value)
            user.save()
        
        instance.save()
        return instance

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user roles.
    
    This serializer is used by administrators to update user roles.
    """
    class Meta:
        model = CustomUser
        fields = ('role',)
        extra_kwargs = {
            'role': {'required': True}
        }
    
    def update(self, instance, validated_data):
        """
        Update the user's role.
        
        Args:
            instance: The user instance to update
            validated_data: Validated data containing the new role
            
        Returns:
            CustomUser: Updated user instance
        """
        instance.role = validated_data['role']
        instance.save()
        return instance


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserPreferences model.
    
    Handles the serialization of user preferences.
    """
    class Meta:
        model = UserPreferences
        fields = ('id', 'preferred_currency', 'language', 
                 'newsletter_subscription', 'marketing_emails',
                 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class RegisterSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    
    Handles the validation and creation of new users with their profiles.
    By default, all new users are registered with the 'user' role.
    """
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=CustomUser.UserRole.choices,
        default=CustomUser.UserRole.USER,
        required=False,
        help_text="User role (default: user)"
    )
    
    def validate(self, attrs):
        """
        Validate the registration data.
        
        Checks if passwords match and if the username/email is already taken.
        
        Args:
            attrs (dict): Registration data
            
        Returns:
            dict: Validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "A user with that username already exists."})
            
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with that email already exists."})
            
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user and user profile.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            CustomUser: Newly created user instance
        """
        # Remove password_confirm from the data as it's not needed anymore
        validated_data.pop('password_confirm', None)
        
        # Get the role, default to USER if not provided
        role = validated_data.pop('role', CustomUser.UserRole.USER)
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=role
        )
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Create default user preferences
        UserPreferences.objects.create(user=user)
        
        return user
