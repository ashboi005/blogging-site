from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, exists
from config import get_db
from models import UserProfile, UserFollower, Users
from routers.auth.auth import get_current_user
from .schemas import (
    UserProfileUpdate,
    UserProfileResponse,
    ProfileImageUpload,
    FollowUserRequest,
    FollowersResponse,
    FollowingResponse,
    FollowStatsResponse,
    FollowActionResponse,
    FollowerUser,
    USER_INTERESTS
)
from .helpers import user_helpers
from typing import Optional, List
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/users", tags=["Users"])

# Security scheme for JWT tokens
security = HTTPBearer()

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Get current user's profile information"""
    profile = current_user["profile"]
    supabase_user = current_user["supabase_user"]
      # Debug logging
    logger.info(f"Current user profile data: display_name={profile.display_name}, avatar_url={profile.avatar_url}, username={profile.username}")
    
    # Parse custom_colors from string to list if it's a string
    custom_colors = profile.custom_colors
    if isinstance(custom_colors, str):
        try:
            import json
            custom_colors = json.loads(custom_colors)
        except (json.JSONDecodeError, TypeError):
            custom_colors = []
    elif custom_colors is None:
        custom_colors = []
    
    # Format response with all required fields
    return UserProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        username=profile.username,
        email=supabase_user.email,  # Get email from Supabase user
        first_name=profile.first_name,
        last_name=profile.last_name,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        custom_font=profile.custom_font,
        custom_colors=custom_colors,
        date_of_birth=profile.date_of_birth,
        timezone=profile.timezone,
        language=profile.language,
        interests=profile.interests or [],
        preferences=profile.preferences,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )

@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile information"""
    try:
        profile = current_user["profile"]
        supabase_user = current_user["supabase_user"]
        
        # Check if username is being updated and if it's available
        if profile_update.username and profile_update.username != profile.username:
            # Check if username is already taken
            result = await db.execute(
                select(UserProfile).where(
                    and_(
                        UserProfile.username == profile_update.username,
                        UserProfile.id != profile.id
                    )
                )
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
          # Update user profile fields
        update_data = profile_update.model_dump(exclude_unset=True)
          # Handle interests validation
        if "interests" in update_data:
            update_data["interests"] = user_helpers.validate_interests(update_data["interests"])
        
        # Handle custom_colors conversion (list to JSON string for database storage)
        if "custom_colors" in update_data and isinstance(update_data["custom_colors"], list):
            import json
            update_data["custom_colors"] = json.dumps(update_data["custom_colors"])
        
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        # Update timestamp
        profile.updated_at = datetime.utcnow()
          # Commit changes
        await db.commit()
        await db.refresh(profile)
        
        # Parse custom_colors from string to list if it's a string
        custom_colors = profile.custom_colors
        if isinstance(custom_colors, str):
            try:
                import json
                custom_colors = json.loads(custom_colors)
            except (json.JSONDecodeError, TypeError):
                custom_colors = []
        elif custom_colors is None:
            custom_colors = []
        
        # Return formatted response
        return UserProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            username=profile.username,
            email=supabase_user.email,  # Get email from Supabase user
            first_name=profile.first_name,
            last_name=profile.last_name,
            display_name=profile.display_name,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            custom_font=profile.custom_font,
            custom_colors=custom_colors,
            date_of_birth=profile.date_of_birth,
            timezone=profile.timezone,
            language=profile.language,
            interests=profile.interests or [],
            preferences=profile.preferences,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/me/profile-image", response_model=ProfileImageUpload)
async def upload_profile_image(
    file: UploadFile = File(..., description="Profile image file (JPEG, PNG, GIF, or WebP, max 5MB)"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new profile image
    
    Accepts image files in the following formats:
    - JPEG (.jpg, .jpeg)
    - PNG (.png) 
    - GIF (.gif)
    - WebP (.webp)
    
    Maximum file size: 5MB
    """
    try:
        profile = current_user["profile"]
        
        # Validate that a file was uploaded
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )
        
        # Delete old profile image if exists
        if profile.avatar_url:
            await user_helpers.delete_profile_image(profile.avatar_url)
        
        # Upload new profile image
        image_url = await user_helpers.upload_profile_image(str(profile.id), file)
        
        # Update user profile with new image URL
        profile.avatar_url = image_url
        profile.updated_at = datetime.utcnow()
        await db.commit()
        
        return ProfileImageUpload(
            avatar_url=image_url,
            message="Profile image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile image: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile image"
        )

@router.delete("/me/profile-image")
async def delete_profile_image(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user's profile image"""
    try:
        profile = current_user["profile"]
        
        if not profile.avatar_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No profile image found"
            )
        
        # Delete image from storage
        deleted = await user_helpers.delete_profile_image(profile.avatar_url)
        
        # Update user profile
        profile.avatar_url = None
        profile.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "message": "Profile image deleted successfully",
            "storage_deleted": deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile image: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile image"
        )


# ================== FOLLOWER/FOLLOWING ROUTES ==================

@router.post("/follow", response_model=FollowActionResponse)
async def follow_user(
    request: FollowUserRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Follow a user"""
    try:
        follower_id = current_user["supabase_user"].id
        following_id = uuid.UUID(request.user_id)
        
        # Prevent self-following
        if follower_id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself"
            )
        
        # Check if target user exists
        target_user = await db.execute(
            select(Users).where(Users.id == following_id)
        )
        if not target_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already following
        existing = await db.execute(
            select(UserFollower).where(
                and_(
                    UserFollower.follower_id == follower_id,
                    UserFollower.following_id == following_id
                )
            )
        )
        if existing.scalar_one_or_none():
            return FollowActionResponse(
                success=True,
                message="Already following this user",
                is_following=True
            )
        
        # Create follow relationship
        follow_relationship = UserFollower(
            follower_id=follower_id,
            following_id=following_id
        )
        db.add(follow_relationship)
        await db.commit()
        
        return FollowActionResponse(
            success=True,
            message="Successfully followed user",
            is_following=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following user: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to follow user"
        )


@router.delete("/unfollow", response_model=FollowActionResponse)
async def unfollow_user(
    request: FollowUserRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unfollow a user"""
    try:
        follower_id = current_user["supabase_user"].id
        following_id = uuid.UUID(request.user_id)
        
        # Find and remove follow relationship
        result = await db.execute(
            select(UserFollower).where(
                and_(
                    UserFollower.follower_id == follower_id,
                    UserFollower.following_id == following_id
                )
            )
        )
        
        follow_relationship = result.scalar_one_or_none()
        if not follow_relationship:
            return FollowActionResponse(
                success=True,
                message="Not following this user",
                is_following=False
            )
        
        await db.delete(follow_relationship)
        await db.commit()
        
        return FollowActionResponse(
            success=True,
            message="Successfully unfollowed user",
            is_following=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing user: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unfollow user"
        )


@router.get("/followers", response_model=FollowersResponse)
async def get_followers(
    user_id: Optional[str] = Query(None, description="User ID to get followers for. If not provided, returns current user's followers"),
    skip: int = Query(0, ge=0, description="Number of followers to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of followers to return"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get followers list for a user"""
    try:
        # Determine target user ID
        if user_id:
            target_user_id = uuid.UUID(user_id)
        else:
            target_user_id = current_user["supabase_user"].id
        
        # Get followers with user profile info
        result = await db.execute(
            select(
                UserFollower.follower_id,
                UserFollower.created_at,
                UserProfile.username,
                UserProfile.display_name,
                UserProfile.avatar_url
            )
            .join(UserProfile, UserProfile.user_id == UserFollower.follower_id)
            .where(UserFollower.following_id == target_user_id)
            .order_by(UserFollower.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        followers = []
        for row in result.all():
            # Debug logging
            logger.info(f"Row data: follower_id={row.follower_id}, username={row.username}, display_name={row.display_name}, avatar_url={row.avatar_url}")
            
            followers.append(FollowerUser(
                id=str(row.follower_id),
                username=row.username,
                display_name=row.display_name,
                avatar_url=row.avatar_url,
                followed_at=row.created_at
            ))
        
        # Get total count
        count_result = await db.execute(
            select(func.count(UserFollower.follower_id))
            .where(UserFollower.following_id == target_user_id)
        )
        total_count = count_result.scalar()
        
        return FollowersResponse(
            followers=followers,
            total_count=total_count
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting followers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get followers"
        )


@router.get("/following", response_model=FollowingResponse)
async def get_following(
    user_id: Optional[str] = Query(None, description="User ID to get following for. If not provided, returns current user's following"),
    skip: int = Query(0, ge=0, description="Number of following to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of following to return"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get following list for a user"""
    try:
        # Determine target user ID
        if user_id:
            target_user_id = uuid.UUID(user_id)
        else:
            target_user_id = current_user["supabase_user"].id
        
        # Get following with user profile info
        result = await db.execute(
            select(
                UserFollower.following_id,
                UserFollower.created_at,
                UserProfile.username,
                UserProfile.display_name,
                UserProfile.avatar_url
            )
            .join(UserProfile, UserProfile.user_id == UserFollower.following_id)
            .where(UserFollower.follower_id == target_user_id)
            .order_by(UserFollower.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        following = []
        for row in result.all():
            # Debug logging
            logger.info(f"Row data: following_id={row.following_id}, username={row.username}, display_name={row.display_name}, avatar_url={row.avatar_url}")
            
            following.append(FollowerUser(
                id=str(row.following_id),
                username=row.username,
                display_name=row.display_name,
                avatar_url=row.avatar_url,
                followed_at=row.created_at
            ))
        
        # Get total count
        count_result = await db.execute(
            select(func.count(UserFollower.following_id))
            .where(UserFollower.follower_id == target_user_id)
        )
        total_count = count_result.scalar()
        
        return FollowingResponse(
            following=following,
            total_count=total_count
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting following: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get following"
        )


@router.get("/follow-stats", response_model=FollowStatsResponse)
async def get_follow_stats(
    user_id: Optional[str] = Query(None, description="User ID to get stats for. If not provided, returns current user's stats"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get follower/following statistics for a user"""
    try:
        # Determine target user ID
        if user_id:
            target_user_id = uuid.UUID(user_id)
        else:
            target_user_id = current_user["supabase_user"].id
        
        current_user_id = current_user["supabase_user"].id
        
        # Get follower count
        followers_result = await db.execute(
            select(func.count(UserFollower.follower_id))
            .where(UserFollower.following_id == target_user_id)
        )
        followers_count = followers_result.scalar()
        
        # Get following count
        following_result = await db.execute(
            select(func.count(UserFollower.following_id))
            .where(UserFollower.follower_id == target_user_id)
        )
        following_count = following_result.scalar()
        
        stats = FollowStatsResponse(
            followers_count=followers_count,
            following_count=following_count
        )
        
        # Check if current user follows this user (if different users)
        if target_user_id != current_user_id:
            is_following_result = await db.execute(
                select(exists().where(
                    and_(
                        UserFollower.follower_id == current_user_id,
                        UserFollower.following_id == target_user_id
                    )
                ))
            )
            stats.is_following = is_following_result.scalar()
        
        return stats
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting follow stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get follow stats"
        )


@router.get("/interests", response_model=List[str])
async def get_available_interests():
    """Get list of available user interests"""
    return USER_INTERESTS
