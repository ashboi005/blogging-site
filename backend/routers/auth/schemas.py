from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Request schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Response schemas
class UserResponse(BaseModel):
    id: str  # This will be the user_profile ID
    user_id: str  # This will be the Supabase Auth user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    custom_font: Optional[str] = None
    custom_colors: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    interests: List[str] = []
    preferences: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None  # For email verification messages

class TokenResponse(BaseModel):
    access_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str
    access_token: str
    refresh_token: str  # Also need refresh token for proper reset