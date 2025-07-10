from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom Social Account Adapter to handle social authentication.
    This allows us to customize the social authentication flow.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # Get the user's email from the social login
        email = sociallogin.user.email
        
        # You can add custom logic here, such as:
        # - Restrict signup to certain domains
        # - Link social accounts to existing users
        # - Set custom user attributes
        
        # Example: Check if the email domain is allowed
        # allowed_domains = ['example.com', 'yourapp.com']
        # if not any(email.endswith('@' + domain) for domain in allowed_domains):
        #     messages.error(request, 'Sign in with this provider is not allowed.')
        #     raise ImmediateHttpResponse(redirect(reverse('account_login')))
        
        return super().pre_social_login(request, sociallogin)
    
    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider info.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Example: Set the user's full name from the social provider
        if not user.name and data.get('name'):
            user.name = data.get('name')
            
        # Example: Set the user's first and last name
        if not user.first_name and data.get('first_name'):
            user.first_name = data.get('first_name')
            
        if not user.last_name and data.get('last_name'):
            user.last_name = data.get('last_name')
            
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully connecting
        a social account.
        """
        # You can customize where the user is redirected after connecting a social account
        return reverse('profile')  # Change 'profile' to your desired URL name
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Invoked when an authentication error occurs.
        """
        # Log the error for debugging
        if error:
            print(f"Authentication error with {provider_id}: {error}")
        if exception:
            print(f"Exception: {str(exception)}")
            
        # Add an error message for the user
        messages.error(request, 'An error occurred during authentication. Please try again.')
        
        # Redirect to the login page
        return redirect(reverse('account_login'))
