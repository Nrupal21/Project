from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.api.auth import get_current_active_user, User

# Users router
router = APIRouter()

# Models
class UserProfile(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[dict] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[dict] = None

# Mock user database (replace with actual DB in production)
fake_profiles_db = {
    "johndoe": {
        "username": "johndoe",
        "email": "johndoe@example.com",
        "full_name": "John Doe",
        "bio": "Software engineer and AI enthusiast",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    }
}

# Routes
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    if current_user.username not in fake_profiles_db:
        fake_profiles_db[current_user.username] = {
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "bio": "",
            "preferences": {"theme": "light", "notifications": True}
        }
    return fake_profiles_db[current_user.username]

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.username not in fake_profiles_db:
        fake_profiles_db[current_user.username] = {
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "bio": "",
            "preferences": {"theme": "light", "notifications": True}
        }
    
    user_profile = fake_profiles_db[current_user.username]
    
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            user_profile[field] = value
    
    fake_profiles_db[current_user.username] = user_profile
    return user_profile 