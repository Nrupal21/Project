# Social Authentication Setup Guide

This guide will walk you through setting up social authentication for the Guides application.

## Prerequisites

1. Python 3.8+
2. Django 4.0+
3. PostgreSQL
4. Social media developer accounts (Google, GitHub, etc.)

## Setting Up Social Authentication

### 1. Configure Environment Variables

Update the `.env` file with your social authentication credentials:

```bash
# Google OAuth2 settings
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth2 settings
GITHUB_OAUTH2_CLIENT_ID=your_github_client_id
GITHUB_OAUTH2_CLIENT_SECRET=your_github_client_secret

# Facebook OAuth2 settings
FACEBOOK_OAUTH2_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH2_CLIENT_SECRET=your_facebook_app_secret

# Twitter OAuth2 settings
TWITTER_OAUTH2_CLIENT_ID=your_twitter_api_key
TWITTER_OAUTH2_CLIENT_SECRET=your_twitter_api_secret

# LinkedIn OAuth2 settings
LINKEDIN_OAUTH2_CLIENT_ID=your_linkedin_client_id
LINKEDIN_OAUTH2_CLIENT_SECRET=your_linkedin_client_secret
```

### 2. Setting Up Google OAuth2

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Configure the consent screen if prompted
6. Select "Web application" as the application type
7. Set the following authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `https://your-production-domain.com/accounts/google/login/callback/`
8. Copy the Client ID and Client Secret to your `.env` file

### 3. Setting Up GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the application details:
   - Application name: Your App Name
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/accounts/github/login/callback/`
4. Click "Register application"
5. Generate a new client secret
6. Copy the Client ID and Client Secret to your `.env` file

### 4. Setting Up Facebook Login

1. Go to [Facebook for Developers](https://developers.facebook.com/)
2. Create a new app or select an existing one
3. Add the "Facebook Login" product
4. Configure the OAuth redirect URIs:
   - `http://localhost:8000/accounts/facebook/login/callback/`
   - `https://your-production-domain.com/accounts/facebook/login/callback/`
5. In App Settings > Basic, add your app domains
6. Copy the App ID and App Secret to your `.env` file

### 5. Setting Up Twitter OAuth2

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. In the app settings, enable OAuth 2.0
4. Set the callback URLs:
   - `http://localhost:8000/accounts/twitter/login/callback/`
   - `https://your-production-domain.com/accounts/twitter/login/callback/`
5. Set the website URL to `http://localhost:8000`
6. Copy the API Key and API Secret to your `.env` file

### 6. Setting Up LinkedIn OAuth2

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. In the "Auth" tab, add the following redirect URLs:
   - `http://localhost:8000/accounts/linkedin_oauth2/login/callback/`
   - `https://your-production-domain.com/accounts/linkedin_oauth2/login/callback/`
4. Under "Products", request access to "Sign In with LinkedIn"
5. Copy the Client ID and Client Secret to your `.env` file

## Testing Social Authentication

1. Start your development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the login page and click on the social provider buttons
3. You should be redirected to the provider's login page
4. After authenticating, you'll be redirected back to your application

## Troubleshooting

- **Redirect URI mismatch**: Ensure the redirect URIs in your provider settings match exactly with what's in your code
- **Invalid credentials**: Double-check that you've copied the client ID and secret correctly
- **HTTPS required in production**: Most providers require HTTPS in production. Use a service like ngrok for testing callbacks in development
- **App not verified**: Some providers may show warnings about your app not being verified. You can usually proceed anyway in development

## Security Considerations

1. Never commit your client secrets to version control
2. Use environment variables for all sensitive data
3. Set appropriate OAuth scopes (only request permissions you need)
4. Implement proper error handling for OAuth failures
5. Regularly rotate your OAuth credentials in production

## Next Steps

- [ ] Implement email verification for social accounts
- [ ] Add social account connection management in user profile
- [ ] Set up proper error pages for OAuth failures
- [ ] Add logging for social authentication events
