# Main entry point for the FastAPI application
# This file serves as the core of the application, handling routing, middleware,
# and template configuration for the AI platform.

#################################################
# IMPORTS
#################################################
# FastAPI and related dependencies
from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from app.api.auth import get_current_user, oauth2_scheme

#################################################
# ROUTER IMPORTS
#################################################
# Authentication and user management routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router

# Core AI feature routers
from app.api.code_ai import router as code_router
from app.api.design_ai import router as design_router
from app.api.productivity_ai import router as productivity_router

# Specialized AI model routers
from app.api.text_ai import router as text_router
from app.api.image_ai import router as image_router
from app.api.audio_ai import router as audio_router
from app.api.video_ai import router as video_router

# Unified AI and subscription routers
from app.api.unified_ai import router as unified_router
from app.api import subscription

#################################################
# APP INITIALIZATION
#################################################
# Create an instance of the FastAPI application
app = FastAPI(
    title="All-in-One AI Platform",
    description="A web-based platform that supports code creation, graphic design, and productivity enhancements",
    version="1.0.0"
)

#################################################
# MIDDLEWARE CONFIGURATION
#################################################
# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#################################################
# STATIC FILES AND TEMPLATES
#################################################
# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

#################################################
# ROUTER REGISTRATION
#################################################
# Include routers from different modules
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(code_router, prefix="/code", tags=["Code AI"])
app.include_router(design_router, prefix="/design", tags=["Design AI"])
app.include_router(productivity_router, prefix="/productivity", tags=["Productivity AI"])
# Include new AI model routers
app.include_router(text_router, prefix="/text", tags=["Text AI"])
app.include_router(image_router, prefix="/image", tags=["Image AI"])
app.include_router(audio_router, prefix="/audio", tags=["Audio AI"])
app.include_router(video_router, prefix="/video", tags=["Video AI"])
# Include unified AI router
app.include_router(unified_router, prefix="/ai", tags=["Unified AI"])
app.include_router(subscription.router, prefix="/api/subscription", tags=["subscription"])

#################################################
# HELPER FUNCTIONS
#################################################
async def get_current_user_from_cookie(request: Request, access_token: Optional[str] = Cookie(None)):
    """
    Extracts and validates the current user from the session cookie.
    
    Args:
        request (Request): The incoming FastAPI request object
        access_token (Optional[str]): JWT token stored in cookie, defaults to None
        
    Returns:
        Optional[User]: The current user object if authenticated, None otherwise
        
    Notes:
        - Handles both Bearer token and raw token formats
        - Silently returns None on authentication failures
    """
    if not access_token:
        return None
    
    try:
        token = access_token.split()[1] if access_token.startswith("Bearer ") else access_token
        return await get_current_user(token)
    except:
        return None

#################################################
# ROUTE DEFINITIONS
#################################################
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user = Depends(get_current_user_from_cookie)):
    """
    Renders the main landing page of the application.
    
    Args:
        request (Request): The incoming FastAPI request object
        current_user (Optional[User]): The current authenticated user, if any
        
    Returns:
        TemplateResponse: Rendered index.html with user context
        
    Notes:
        - Accessible to both authenticated and unauthenticated users
        - Provides personalized content if user is logged in
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user = Depends(get_current_user_from_cookie)):
    """
    Renders the user dashboard with personalized AI tools and analytics.
    
    Args:
        request (Request): The incoming FastAPI request object
        current_user (Optional[User]): The current authenticated user, if any
        
    Returns:
        TemplateResponse: Rendered dashboard.html with user context and analytics
        
    Notes:
        - Displays user-specific AI usage statistics
        - Shows available AI tools and recent activities
    """
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request, current_user = Depends(get_current_user_from_cookie)):
    """
    Renders the interactive AI chat interface.
    
    Args:
        request (Request): The incoming FastAPI request object
        current_user (Optional[User]): The current authenticated user, if any
        
    Returns:
        TemplateResponse: Rendered chat.html with user context
        
    Notes:
        - Provides real-time AI chat functionality
        - Supports multiple AI models and conversation history
    """
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/subscription", response_class=HTMLResponse)
async def subscription_page(request: Request, current_user = Depends(get_current_user_from_cookie)):
    """
    Renders the subscription plans and pricing page.
    
    Args:
        request (Request): The incoming FastAPI request object
        current_user (Optional[User]): The current authenticated user, if any
        
    Returns:
        TemplateResponse: Rendered subscription.html with user context
        
    Notes:
        - Displays available subscription tiers
        - Shows current subscription status for logged-in users
        - Handles subscription management and upgrades
    """
    return templates.TemplateResponse("subscription.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/health")
async def health_check():
    """
    System health check endpoint for monitoring and alerting.
    
    Returns:
        dict: Simple status response indicating system health
        
    Notes:
        - Used by monitoring systems to check application availability
        - Returns 200 OK when system is functioning normally
    """
    return {"status": "healthy"}

#################################################
# APP EXECUTION
#################################################
if __name__ == "__main__":
    import uvicorn
    # Start the application server on localhost:8000
    # Enable auto-reload for development convenience
    uvicorn.run(app, host="127.0.0.1", port=8000)
