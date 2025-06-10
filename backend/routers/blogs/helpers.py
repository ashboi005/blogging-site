from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from models import Blog, BlogAuthor, BlogLike, BlogComment, UserProfile
from typing import Optional, List, Tuple
import uuid
import logging
import os

logger = logging.getLogger(__name__)

class BlogHelpers:
    """Helper functions for blog operations"""
    
    @staticmethod
    async def get_blog_with_details(db: AsyncSession, blog_id: uuid.UUID) -> Optional[dict]:
        """
        Get blog with author details, like count, and comment count
        """
        try:            # Get blog with authors
            result = await db.execute(
                select(
                    Blog.id,
                    Blog.title,
                    Blog.description,
                    Blog.content,
                    Blog.tags,
                    Blog.cover_image_url,
                    Blog.is_published,
                    Blog.is_featured,
                    Blog.created_at,
                    Blog.updated_at,
                    Blog.published_at,
                    BlogAuthor.user_id,
                    BlogAuthor.is_primary_author,
                    UserProfile.username,
                    UserProfile.display_name,
                    UserProfile.avatar_url
                )
                .join(BlogAuthor, BlogAuthor.blog_id == Blog.id)
                .join(UserProfile, UserProfile.user_id == BlogAuthor.user_id)
                .where(Blog.id == blog_id)
            )
            
            rows = result.all()
            if not rows:
                return None
              # Build blog data from first row
            first_row = rows[0]
            blog_data = {
                "id": str(first_row.id),
                "title": first_row.title,
                "description": first_row.description,
                "content": first_row.content,
                "tags": first_row.tags or [],
                "cover_image_url": first_row.cover_image_url,
                "is_published": first_row.is_published,
                "is_featured": first_row.is_featured,
                "created_at": first_row.created_at,
                "updated_at": first_row.updated_at,
                "published_at": first_row.published_at,
                "authors": []
            }
            
            # Collect all authors
            for row in rows:
                blog_data["authors"].append({
                    "user_id": str(row.user_id),
                    "username": row.username,
                    "display_name": row.display_name,
                    "avatar_url": row.avatar_url,
                    "is_primary_author": row.is_primary_author
                })
            
            # Get like count
            like_count_result = await db.execute(
                select(func.count(BlogLike.user_id)).where(BlogLike.blog_id == blog_id)
            )
            blog_data["like_count"] = like_count_result.scalar() or 0
            
            # Get comment count (only main comments, not replies)
            comment_count_result = await db.execute(
                select(func.count(BlogComment.id))
                .where(and_(
                    BlogComment.blog_id == blog_id,
                    BlogComment.parent_comment_id.is_(None)
                ))
            )
            blog_data["comment_count"] = comment_count_result.scalar() or 0
            
            return blog_data
            
        except Exception as e:
            logger.error(f"Error getting blog with details: {str(e)}")
            return None
    
    @staticmethod
    async def get_blog_summary_with_details(db: AsyncSession, blog_id: uuid.UUID) -> Optional[dict]:
        """
        Get blog summary (without content) with author details, like count, and comment count
        """
        try:            # Get blog with authors (excluding content for performance)
            result = await db.execute(
                select(
                    Blog.id,
                    Blog.title,
                    Blog.description,
                    Blog.tags,
                    Blog.cover_image_url,
                    Blog.is_published,
                    Blog.is_featured,
                    Blog.created_at,
                    Blog.published_at,
                    BlogAuthor.user_id,
                    BlogAuthor.is_primary_author,
                    UserProfile.username,
                    UserProfile.display_name,
                    UserProfile.avatar_url
                )
                .join(BlogAuthor, BlogAuthor.blog_id == Blog.id)
                .join(UserProfile, UserProfile.user_id == BlogAuthor.user_id)
                .where(Blog.id == blog_id)
            )
            
            rows = result.all()
            if not rows:
                return None
              # Build blog data from first row
            first_row = rows[0]
            blog_data = {
                "id": str(first_row.id),
                "title": first_row.title,
                "description": first_row.description,
                "tags": first_row.tags or [],
                "cover_image_url": first_row.cover_image_url,
                "is_published": first_row.is_published,
                "is_featured": first_row.is_featured,
                "created_at": first_row.created_at,
                "published_at": first_row.published_at,
                "authors": []
            }
            
            # Collect all authors
            for row in rows:
                blog_data["authors"].append({
                    "user_id": str(row.user_id),
                    "username": row.username,
                    "display_name": row.display_name,
                    "avatar_url": row.avatar_url,
                    "is_primary_author": row.is_primary_author
                })
            
            # Get like count
            like_count_result = await db.execute(
                select(func.count(BlogLike.user_id)).where(BlogLike.blog_id == blog_id)
            )
            blog_data["like_count"] = like_count_result.scalar() or 0
            
            # Get comment count (only main comments, not replies)
            comment_count_result = await db.execute(
                select(func.count(BlogComment.id))
                .where(and_(
                    BlogComment.blog_id == blog_id,
                    BlogComment.parent_comment_id.is_(None)
                ))
            )
            blog_data["comment_count"] = comment_count_result.scalar() or 0
            
            return blog_data
            
        except Exception as e:
            logger.error(f"Error getting blog summary with details: {str(e)}")
            return None
    
    @staticmethod
    async def search_blogs(
        db: AsyncSession,
        query: Optional[str] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_published: Optional[bool] = True,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[uuid.UUID], int]:
        """
        Search blogs and return blog IDs with total count
        """
        try:
            # Build the base query
            base_query = select(Blog.id.distinct()).join(BlogAuthor, BlogAuthor.blog_id == Blog.id)
            
            # Add filters
            filters = []
            
            if is_published is not None:
                filters.append(Blog.is_published == is_published)
            
            if query:
                # Search in title, description, and content
                search_filter = or_(
                    Blog.title.ilike(f"%{query}%"),
                    Blog.description.ilike(f"%{query}%"),
                    Blog.content.ilike(f"%{query}%")
                )
                filters.append(search_filter)
            
            if author:
                # Join with UserProfile to search by username or display_name
                base_query = base_query.join(UserProfile, UserProfile.user_id == BlogAuthor.user_id)
                author_filter = or_(
                    UserProfile.username.ilike(f"%{author}%"),
                    UserProfile.display_name.ilike(f"%{author}%")
                )
                filters.append(author_filter)
            
            if tags:
                # Search for blogs that contain any of the specified tags
                for tag in tags:
                    filters.append(Blog.tags.contains([tag]))
            
            if filters:
                base_query = base_query.where(and_(*filters))
            
            # Get total count
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # Get paginated results
            result_query = base_query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
            result = await db.execute(result_query)
            blog_ids = [row.id for row in result.all()]
            
            return blog_ids, total_count
            
        except Exception as e:
            logger.error(f"Error searching blogs: {str(e)}")
            return [], 0
    
    @staticmethod
    async def user_can_edit_blog(db: AsyncSession, blog_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Check if user can edit the blog (must be one of the authors)
        """
        try:
            result = await db.execute(
                select(BlogAuthor.user_id)
                .where(and_(
                    BlogAuthor.blog_id == blog_id,
                    BlogAuthor.user_id == user_id
                ))
            )
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking edit permissions: {str(e)}")
            return False
    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """
        Validate and filter tags against allowed tags
        """
        from .schemas import BLOG_TAGS
        
        if not tags:
            return []
        
        # Filter to only include valid tags
        valid_tags = [tag for tag in tags if tag in BLOG_TAGS]
        
        # Remove duplicates while preserving order
        seen = set()
        return [tag for tag in valid_tags if not (tag in seen or seen.add(tag))]
    
    @staticmethod
    async def upload_blog_cover_image(blog_id: str, file) -> str:
        """
        Upload blog cover image to Supabase Storage and return the public URL
        """        
        try:
            # Import here to avoid circular imports
            from fastapi import HTTPException, status
            from config import get_supabase_admin_client
            
            logger.info(f"Starting blog cover image upload for blog_id: {blog_id}")
            
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
            
            # Read and validate file size
            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:  # 10MB limit for blog covers
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size must be less than 10MB"
                )
            
            # Reset file position for re-reading if needed
            await file.seek(0)
            
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            unique_filename = f"blog-covers/{blog_id}/{uuid.uuid4()}{file_extension}"
            
            # Get bucket name
            bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "blog-media")
            
            # Upload using Supabase client
            supabase_client = get_supabase_admin_client()
            
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
            
        except Exception as e:
            logger.error(f"Error uploading blog cover image: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload cover image"
            )
    
    @staticmethod
    async def delete_blog_cover_image(image_url: str) -> bool:
        """
        Delete blog cover image from Supabase Storage
        """
        try:
            # Import here to avoid circular imports
            from config import get_supabase_admin_client
            
            bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "blog-media")
            
            # Extract file path from URL
            if "/storage/v1/object/public/" in image_url:
                # Split and get the path after bucket name
                parts = image_url.split("/storage/v1/object/public/")[1]
                path_parts = parts.split("/", 1)
                if len(path_parts) > 1:
                    file_path = path_parts[1]  # Get everything after bucket name
                    
                    # Delete file
                    supabase_client = get_supabase_admin_client()
                    response = supabase_client.storage.from_(bucket_name).remove([file_path])
                    
                    if response.get("error"):
                        logger.warning(f"Failed to delete cover image from storage: {response['error']}")
                        return False
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting blog cover image: {str(e)}")
            return False

# Create a single instance to use throughout the app
blog_helpers = BlogHelpers()
