"""
Views for the accounts app.

This module contains views for user registration, profile management,
and authentication-related functionality.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .models import CustomUser, UserProfile, UserPreferences
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    UserPreferencesSerializer,
    RegisterSerializer,
    UserRoleUpdateSerializer
)
from .permissions import IsAdminUser

class RegisterView(APIView):
    """
    API endpoint for user registration.
    
    Allows new users to create an account with a username, email, and password.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, format=None):
        """
        Handle POST request for user registration.
        
        Args:
            request (Request): The HTTP request
            format (str, optional): Format for the response. Defaults to None.
            
        Returns:
            Response: HTTP response with user data and token or error messages
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=user)
            
            # Return user data and token
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'User registered successfully.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login.
    
    Authenticates users and returns an authentication token.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, format=None):
        """
        Handle POST request for user login.
        
        Args:
            request (Request): The HTTP request containing username and password
            format (str, optional): Format for the response. Defaults to None.
            
        Returns:
            Response: HTTP response with user data and token or error message
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Log the user in
                login(request, user)
                
                # Get or create token for the user
                token, created = Token.objects.get_or_create(user=user)
                
                # Return user data and token
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'message': 'Login successful.'
                })
            else:
                return Response(
                    {'error': 'Account is disabled'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
    """
    API endpoint for user logout.
    
    Logs out the currently authenticated user and deletes their auth token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """
        Handle POST request for user logout.
        
        Args:
            request (Request): The HTTP request
            format (str, optional): Format for the response. Defaults to None.
            
        Returns:
            Response: HTTP response with success message
        """
        # Delete the user's token to force re-authentication
        request.user.auth_token.delete()
        
        # Log the user out
        logout(request)
        
        return Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )

class UserProfileDetail(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating the authenticated user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Retrieve the user profile for the currently authenticated user.
        
        Returns:
            UserProfile: The profile of the currently authenticated user
        """
        return self.request.user.profile
    
    def perform_update(self, serializer):
        """
        Update the user profile instance.
        
        Args:
            serializer: The serializer instance
        """
        serializer.save(user=self.request.user)

class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating the authenticated user's preferences.
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Retrieve the user preferences for the currently authenticated user.
        
        Returns:
            UserPreferences: The preferences of the currently authenticated user
        """
        # Get or create user preferences if they don't exist
        preferences, created = UserPreferences.objects.get_or_create(user=self.request.user)
        return preferences
    
    def perform_update(self, serializer):
        """
        Update the user preferences instance.
        
        Args:
            serializer: The serializer instance
        """
        serializer.save(user=self.request.user)

class UserRoleUpdateView(APIView):
    """
    API endpoint for updating a user's role.
    
    Only accessible by administrators.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def put(self, request, user_id, format=None):
        """
        Update a user's role.
        
        Args:
            request (Request): The HTTP request containing the new role
            user_id (int): The ID of the user to update
            format (str, optional): Format for the response. Defaults to None.
            
        Returns:
            Response: HTTP response with updated user data or error message
        """
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent admins from changing their own role
        if user == request.user:
            return Response(
                {'error': 'You cannot change your own role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User role updated successfully',
                'user': UserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint for changing the authenticated user's password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """
        Handle POST request to change the user's password.
        
        Args:
            request (Request): The HTTP request containing old and new passwords
            format (str, optional): Format for the response. Defaults to None.
            
        Returns:
            Response: HTTP response with success or error message
        """
        user = self.request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Incorrect old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response(
            {'message': 'Password updated successfully'},
            status=status.HTTP_200_OK
        )
