from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from config import get_db
from models import Blog, BlogAuthor, UserProfile
from routers.auth.auth import get_current_user
from .schemas import (
    BlogCreate,
    BlogUpdate,
    BlogSearch,
    BlogResponse,
    BlogSummaryResponse,
    BlogListResponse,
    BlogCreateResponse,
    BlogActionResponse,
    BlogImageUpload,
    BLOG_TAGS
)
from .helpers import blog_helpers
from typing import Optional, List
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/blogs", tags=["Blogs"])

# Security scheme for JWT tokens
security = HTTPBearer()

@router.get("/tags", response_model=List[str])
async def get_available_tags():
    """Get list of available blog tags"""
    return BLOG_TAGS

@router.post("/", response_model=BlogCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog_data: BlogCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post"""
    try:
        # Validate tags
        valid_tags = blog_helpers.validate_tags(blog_data.tags)
        
        # Create blog
        new_blog = Blog(
            title=blog_data.title,
            description=blog_data.description,
            content=blog_data.content,
            tags=valid_tags,
            is_published=blog_data.is_published,
            published_at=datetime.utcnow() if blog_data.is_published else None
        )
        
        db.add(new_blog)
        await db.flush()  # Get blog ID without committing
        
        # Add primary author (current user)
        primary_author = BlogAuthor(
            blog_id=new_blog.id,
            user_id=current_user["supabase_user"].id,
            is_primary_author=True
        )
        db.add(primary_author)
        
        # Add co-authors if specified
        if blog_data.co_author_ids:
            for co_author_id in blog_data.co_author_ids:
                try:
                    co_author_uuid = uuid.UUID(co_author_id)
                    
                    # Check if co-author exists and is not the same as primary author
                    if co_author_uuid != current_user["supabase_user"].id:
                        # Verify user exists
                        user_check = await db.execute(
                            select(UserProfile.user_id).where(UserProfile.user_id == co_author_uuid)
                        )
                        if user_check.scalar_one_or_none():
                            co_author = BlogAuthor(
                                blog_id=new_blog.id,
                                user_id=co_author_uuid,
                                is_primary_author=False
                            )
                            db.add(co_author)
                except (ValueError, Exception) as e:
                    logger.warning(f"Invalid co-author ID {co_author_id}: {str(e)}")
                    continue
        
        await db.commit()
        
        return BlogCreateResponse(
            id=str(new_blog.id),
            title=new_blog.title,
            message="Blog created successfully" + (" and published" if blog_data.is_published else ""),
            is_published=new_blog.is_published
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating blog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create blog"
        )

@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a blog post by ID"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Get blog with details
        blog_data = await blog_helpers.get_blog_with_details(db, blog_uuid)
        
        if not blog_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Check if blog is published or user is an author
        if not blog_data["is_published"]:
            user_is_author = any(
                author["user_id"] == str(current_user["supabase_user"].id) 
                for author in blog_data["authors"]
            )
            if not user_is_author:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Blog not found"
                )
        
        return BlogResponse(**blog_data)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blog"
        )

@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_update: BlogUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog post"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Check if user can edit this blog
        if not await blog_helpers.user_can_edit_blog(db, blog_uuid, current_user["supabase_user"].id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this blog"
            )
        
        # Get existing blog
        result = await db.execute(
            select(Blog).where(Blog.id == blog_uuid)
        )
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Update fields
        update_data = blog_update.model_dump(exclude_unset=True)
        
        # Handle tags validation
        if "tags" in update_data:
            update_data["tags"] = blog_helpers.validate_tags(update_data["tags"])
        
        # Handle publishing
        if "is_published" in update_data and update_data["is_published"] and not blog.is_published:
            update_data["published_at"] = datetime.utcnow()
        
        # Handle co-author updates
        co_author_ids = update_data.pop("co_author_ids", None)
        
        for field, value in update_data.items():
            setattr(blog, field, value)
        
        blog.updated_at = datetime.utcnow()
        
        # Update co-authors if specified
        if co_author_ids is not None:
            # Remove existing co-authors (keep primary author)
            await db.execute(
                select(BlogAuthor).where(
                    and_(
                        BlogAuthor.blog_id == blog_uuid,
                        BlogAuthor.is_primary_author == False
                    )
                ).delete()
            )
            
            # Add new co-authors
            for co_author_id in co_author_ids:
                try:
                    co_author_uuid = uuid.UUID(co_author_id)
                    
                    # Check if co-author exists and is not the primary author
                    if co_author_uuid != current_user["supabase_user"].id:
                        user_check = await db.execute(
                            select(UserProfile.user_id).where(UserProfile.user_id == co_author_uuid)
                        )
                        if user_check.scalar_one_or_none():
                            co_author = BlogAuthor(
                                blog_id=blog_uuid,
                                user_id=co_author_uuid,
                                is_primary_author=False
                            )
                            db.add(co_author)
                except (ValueError, Exception) as e:
                    logger.warning(f"Invalid co-author ID {co_author_id}: {str(e)}")
                    continue
        
        await db.commit()
        
        # Get updated blog data
        blog_data = await blog_helpers.get_blog_with_details(db, blog_uuid)
        
        return BlogResponse(**blog_data)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating blog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update blog"
        )

@router.delete("/{blog_id}", response_model=BlogActionResponse)
async def delete_blog(
    blog_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog post"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Check if user can edit this blog
        if not await blog_helpers.user_can_edit_blog(db, blog_uuid, current_user["supabase_user"].id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this blog"
            )
        
        # Get and delete blog
        result = await db.execute(
            select(Blog).where(Blog.id == blog_uuid)
        )
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        await db.delete(blog)
        await db.commit()
        
        return BlogActionResponse(
            success=True,
            message="Blog deleted successfully"
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting blog: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete blog"
        )

@router.get("/user/{user_id}", response_model=BlogListResponse)
async def get_blogs_by_user(
    user_id: str,
    skip: int = Query(0, ge=0, description="Number of blogs to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of blogs to return"),
    include_unpublished: bool = Query(False, description="Include unpublished blogs (only if user is viewing their own blogs)"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all blogs by a specific user"""
    try:
        target_user_id = uuid.UUID(user_id)
        current_user_id = current_user["supabase_user"].id
        
        # Check if user is viewing their own blogs
        is_own_blogs = target_user_id == current_user_id
        
        # Build query
        base_query = select(Blog.id).join(BlogAuthor, BlogAuthor.blog_id == Blog.id)
        filters = [BlogAuthor.user_id == target_user_id]
        
        # Add published filter if not viewing own blogs or not requesting unpublished
        if not is_own_blogs or not include_unpublished:
            filters.append(Blog.is_published == True)
        
        query = base_query.where(and_(*filters))
        
        # Get total count
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = count_result.scalar() or 0
        
        # Get paginated blog IDs
        result = await db.execute(
            query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
        )
        blog_ids = [row.id for row in result.all()]
        
        # Get blog details
        blogs = []
        for blog_id in blog_ids:
            blog_data = await blog_helpers.get_blog_summary_with_details(db, blog_id)
            if blog_data:
                blogs.append(BlogSummaryResponse(**blog_data))
        
        return BlogListResponse(
            blogs=blogs,
            total_count=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting blogs by user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blogs"
        )

@router.get("/", response_model=BlogListResponse)
async def search_blogs(
    query: Optional[str] = Query(None, description="Search in title, description, and content"),
    author: Optional[str] = Query(None, description="Search by author username"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    skip: int = Query(0, ge=0, description="Number of blogs to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of blogs to return"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search blogs with various filters"""
    try:
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            tag_list = blog_helpers.validate_tags(tag_list)
        
        # Search blogs
        blog_ids, total_count = await blog_helpers.search_blogs(
            db=db,
            query=query,
            author=author,
            tags=tag_list,
            is_published=True,  # Only search published blogs
            skip=skip,
            limit=limit
        )
        
        # Get blog details
        blogs = []
        for blog_id in blog_ids:
            blog_data = await blog_helpers.get_blog_summary_with_details(db, blog_id)
            if blog_data:
                blogs.append(BlogSummaryResponse(**blog_data))
        
        return BlogListResponse(
            blogs=blogs,
            total_count=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )
        
    except Exception as e:
        logger.error(f"Error searching blogs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search blogs"
        )

@router.post("/{blog_id}/cover-image", response_model=BlogImageUpload)
async def upload_blog_cover_image(
    blog_id: str,
    file: UploadFile = File(..., description="Blog cover image (JPEG, PNG, GIF, or WebP, max 10MB)"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a cover image for a blog post"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Check if user can edit this blog
        if not await blog_helpers.user_can_edit_blog(db, blog_uuid, current_user["supabase_user"].id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this blog"
            )
        
        # Get existing blog
        result = await db.execute(
            select(Blog).where(Blog.id == blog_uuid)
        )
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Validate that a file was uploaded
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )
        
        # Delete old cover image if exists
        if blog.cover_image_url:
            await blog_helpers.delete_blog_cover_image(blog.cover_image_url)
        
        # Upload new cover image
        image_url = await blog_helpers.upload_blog_cover_image(str(blog.id), file)
        
        # Update blog with new image URL
        blog.cover_image_url = image_url
        blog.updated_at = datetime.utcnow()
        await db.commit()
        
        return BlogImageUpload(
            cover_image_url=image_url,
            message="Blog cover image uploaded successfully"
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading blog cover image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload cover image"
        )

@router.delete("/{blog_id}/cover-image", response_model=BlogActionResponse)
async def delete_blog_cover_image(
    blog_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog's cover image"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Check if user can edit this blog
        if not await blog_helpers.user_can_edit_blog(db, blog_uuid, current_user["supabase_user"].id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this blog"
            )
        
        # Get existing blog
        result = await db.execute(
            select(Blog).where(Blog.id == blog_uuid)
        )
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        if not blog.cover_image_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No cover image found"
            )
        
        # Delete image from storage
        deleted = await blog_helpers.delete_blog_cover_image(blog.cover_image_url)
        
        # Update blog
        blog.cover_image_url = None
        blog.updated_at = datetime.utcnow()
        await db.commit()
        
        return BlogActionResponse(
            success=True,
            message="Blog cover image deleted successfully"
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting blog cover image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cover image"
        )

@router.get("/recommended", response_model=BlogListResponse)
async def get_recommended_blogs(
    skip: int = Query(0, ge=0, description="Number of blogs to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of blogs to return"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized blog recommendations based on user interests"""
    try:
        profile = current_user["profile"]
        user_interests = profile.interests or []
        
        if not user_interests:
            # If user has no interests, return general popular blogs
            blog_ids, total_count = await blog_helpers.search_blogs(
                db=db,
                is_published=True,
                skip=skip,
                limit=limit
            )
        else:
            # Search for blogs that match user interests
            blog_ids, total_count = await blog_helpers.search_blogs(
                db=db,
                tags=user_interests,
                is_published=True,
                skip=skip,
                limit=limit
            )
        
        # Get blog details
        blogs = []
        for blog_id in blog_ids:
            blog_data = await blog_helpers.get_blog_summary_with_details(db, blog_id)
            if blog_data:
                blogs.append(BlogSummaryResponse(**blog_data))
        
        return BlogListResponse(
            blogs=blogs,
            total_count=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )
        
    except Exception as e:
        logger.error(f"Error getting recommended blogs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommended blogs"
        )
