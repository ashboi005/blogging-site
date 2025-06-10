from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Request schemas
class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    custom_font: Optional[str] = None
    custom_colors: Optional[List[str]] = None
    date_of_birth: Optional[datetime] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class ProfileImageUpload(BaseModel):
    """Response schema for profile image upload"""
    avatar_url: str
    message: str

# Response schemas
class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    custom_font: Optional[str] = None
    custom_colors: Optional[List[str]] = None
    date_of_birth: Optional[datetime] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    preferences: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfilePublic(BaseModel):
    """Public profile information (without email)"""
    id: str
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    custom_font: Optional[str] = None
    custom_colors: Optional[List[str]] = None
    date_of_birth: Optional[datetime] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Follower/Following schemas
class FollowUserRequest(BaseModel):
    """Request to follow/unfollow a user"""
    user_id: str

class FollowerUser(BaseModel):
    """User information for follower/following lists"""
    id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    followed_at: datetime
    
    class Config:
        from_attributes = True

class FollowersResponse(BaseModel):
    """Response for followers list"""
    followers: List[FollowerUser]
    total_count: int

class FollowingResponse(BaseModel):
    """Response for following list"""
    following: List[FollowerUser]
    total_count: int

class FollowStatsResponse(BaseModel):
    """Response for follow statistics"""
    followers_count: int
    following_count: int
    is_following: Optional[bool] = None  # Whether current user follows this user

class FollowActionResponse(BaseModel):
    """Response for follow/unfollow actions"""
    success: bool
    message: str
    is_following: bool
