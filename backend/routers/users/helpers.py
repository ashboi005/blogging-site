from fastapi import HTTPException, status, UploadFile
from supabase import Client
from config import get_supabase_admin_client, get_supabase_storage, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, exists
from models import UserFollower, UserProfile, Users
import uuid
import os
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserHelpers:
    """Helper functions for user operations"""
    
    def __init__(self):
        self._admin_client = None
        self._storage = None
    
    @property
    def admin_client(self) -> Client:
        if self._admin_client is None:
            self._admin_client = get_supabase_admin_client()
        return self._admin_client
    
    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_supabase_storage()
        return self._storage
    
    async def upload_profile_image(self, user_id: str, file: UploadFile) -> str:
        """
        Upload profile image to Supabase Storage and return the public URL
        """        
        try:            
            logger.info(f"Starting upload for user_id: {user_id}")
            
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
            
            # Read and validate file size
            file_content = await file.read()
            if len(file_content) > 5 * 1024 * 1024:  # 5MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size must be less than 5MB"
                )
            
            # Reset file position for re-reading if needed
            await file.seek(0)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            unique_filename = f"profiles/{user_id}/{uuid.uuid4()}{file_extension}"
            
            # Get bucket name
            bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "blog-media")
            
            # Try a simpler upload approach
            try:
                # Get the storage client
                supabase_client = get_supabase_admin_client()
                
                # Upload using the simpler method
                response = supabase_client.storage.from_(bucket_name).upload(
                    path=unique_filename,
                    file=file_content,
                    file_options={"content-type": file.content_type}
                )
                
                logger.info(f"Upload response: {response}")
                
                # Check for errors
                if hasattr(response, 'error') and response.error:
                    logger.error(f"Upload error: {response.error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to upload image"
                    )
                
                # Get public URL
                public_url = supabase_client.storage.from_(bucket_name).get_public_url(unique_filename)
                logger.info(f"Public URL: {public_url}")
                
                return public_url
                
            except Exception as upload_error:
                logger.error(f"Upload error: {str(upload_error)}")
                logger.error(f"Upload error type: {type(upload_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Upload failed: {str(upload_error)}"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading profile image: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
    
    async def delete_profile_image(self, image_url: str) -> bool:
        """
        Delete profile image from Supabase Storage
        """
        try:
            bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "blog-media")
            
            # Extract file path from URL
            # URL format: https://project.supabase.co/storage/v1/object/public/bucket/path
            if "/storage/v1/object/public/" in image_url:
                # Split and get the path after bucket name
                parts = image_url.split("/storage/v1/object/public/")[1]
                path_parts = parts.split("/", 1)
                if len(path_parts) > 1:
                    file_path = path_parts[1]  # Get everything after bucket name
                    
                    # Delete file
                    response = self.storage.from_(bucket_name).remove([file_path])
                    
                    if response.get("error"):
                        logger.warning(f"Failed to delete image from storage: {response['error']}")
                        return False
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting profile image: {str(e)}")
            return False
        
    @staticmethod
    def validate_interests(interests: List[str]) -> List[str]:
        """
        Validate and filter interests against allowed interests
        """
        from .schemas import USER_INTERESTS
        
        if not interests:
            return []
        
        # Filter to only include valid interests
        valid_interests = [interest for interest in interests if interest in USER_INTERESTS]
        
        # Remove duplicates while preserving order
        seen = set()
        return [interest for interest in valid_interests if not (interest in seen or seen.add(interest))]


# Create global instance
user_helpers = UserHelpers()
