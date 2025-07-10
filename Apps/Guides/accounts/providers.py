from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error

class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """
    Custom Google OAuth2 adapter to handle additional user information.
    """
    def complete_login(self, request, app, token, **kwargs):
        try:
            # Call the parent's complete_login to get the basic user info
            login = super().complete_login(request, app, token, **kwargs)
            
            # Extract additional user data from the response
            extra_data = login.account.extra_data
            
            # Add any additional processing here
            # For example, you can fetch the user's profile picture:
            if 'picture' in extra_data:
                login.account.extra_data['avatar_url'] = extra_data['picture']
                
            return login
        except Exception as e:
            raise OAuth2Error(f"Error completing Google OAuth2 login: {str(e)}")

class CustomGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    """
    Custom GitHub OAuth2 adapter to handle additional user information.
    """
    def complete_login(self, request, app, token, **kwargs):
        try:
            # Call the parent's complete_login to get the basic user info
            login = super().complete_login(request, app, token, **kwargs)
            
            # Extract additional user data from the response
            extra_data = login.account.extra_data
            
            # Add any additional processing here
            # For example, you can fetch the user's avatar URL:
            if 'avatar_url' in extra_data:
                login.account.extra_data['avatar_url'] = extra_data['avatar_url']
                
            return login
        except Exception as e:
            raise OAuth2Error(f"Error completing GitHub OAuth2 login: {str(e)}")

class CustomFacebookOAuth2Adapter(FacebookOAuth2Adapter):
    """
    Custom Facebook OAuth2 adapter to handle additional user information.
    """
    def complete_login(self, request, app, token, **kwargs):
        try:
            # Call the parent's complete_login to get the basic user info
            login = super().complete_login(request, app, token, **kwargs)
            
            # Extract additional user data from the response
            extra_data = login.account.extra_data
            
            # Add any additional processing here
            # For example, you can fetch the user's profile picture:
            if 'picture' in extra_data and 'data' in extra_data['picture']:
                login.account.extra_data['avatar_url'] = extra_data['picture']['data']['url']
                
            return login
        except Exception as e:
            raise OAuth2Error(f"Error completing Facebook OAuth2 login: {str(e)}")

# Register the custom adapters
provider_classes = {
    'google': CustomGoogleOAuth2Adapter,
    'github': CustomGitHubOAuth2Adapter,
    'facebook': CustomFacebookOAuth2Adapter,
}

def get_provider_adapter(provider_id):
    """
    Returns the custom adapter class for the given provider ID, or None if not found.
    """
    return provider_classes.get(provider_id)
