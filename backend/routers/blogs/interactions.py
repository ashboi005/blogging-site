from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, exists
from config import get_db
from models import Blog, BlogComment, BlogLike, UserProfile
from routers.auth.auth import get_current_user
from .interactions_schemas import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentWithRepliesResponse,
    CommentsListResponse,
    CommentActionResponse,
    LikeActionResponse,
    BlogLikeStatsResponse,
    CommentUserResponse
)
from typing import Optional, List
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/blogs", tags=["Blog Interactions"])

# Security scheme for JWT tokens
security = HTTPBearer()

# ============== LIKES ENDPOINTS ==============

@router.post("/{blog_id}/like", response_model=LikeActionResponse)
async def toggle_blog_like(
    blog_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle like on a blog post (like/unlike)"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        user_id = current_user["supabase_user"].id
        
        # Check if blog exists and is published
        blog_result = await db.execute(
            select(Blog.id).where(and_(Blog.id == blog_uuid, Blog.is_published == True))
        )
        if not blog_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Check if user already liked this blog
        existing_like = await db.execute(
            select(BlogLike).where(
                and_(BlogLike.blog_id == blog_uuid, BlogLike.user_id == user_id)
            )
        )
        like = existing_like.scalar_one_or_none()
        
        if like:
            # Unlike - remove the like
            await db.delete(like)
            is_liked = False
            message = "Blog unliked successfully"
        else:
            # Like - add new like
            new_like = BlogLike(blog_id=blog_uuid, user_id=user_id)
            db.add(new_like)
            is_liked = True
            message = "Blog liked successfully"
        
        await db.commit()
        
        # Get updated like count
        like_count_result = await db.execute(
            select(func.count(BlogLike.user_id)).where(BlogLike.blog_id == blog_uuid)
        )
        like_count = like_count_result.scalar() or 0
        
        return LikeActionResponse(
            success=True,
            message=message,
            is_liked=is_liked,
            like_count=like_count
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
        logger.error(f"Error toggling blog like: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle like"
        )

@router.get("/{blog_id}/likes", response_model=BlogLikeStatsResponse)
async def get_blog_like_stats(
    blog_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get like statistics for a blog"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        user_id = current_user["supabase_user"].id
        
        # Check if blog exists
        blog_result = await db.execute(
            select(Blog.id).where(Blog.id == blog_uuid)
        )
        if not blog_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Get like count
        like_count_result = await db.execute(
            select(func.count(BlogLike.user_id)).where(BlogLike.blog_id == blog_uuid)
        )
        like_count = like_count_result.scalar() or 0
        
        # Check if current user liked this blog
        user_liked_result = await db.execute(
            select(exists().where(
                and_(BlogLike.blog_id == blog_uuid, BlogLike.user_id == user_id)
            ))
        )
        is_liked = user_liked_result.scalar() or False
        
        return BlogLikeStatsResponse(
            like_count=like_count,
            is_liked=is_liked
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except Exception as e:
        logger.error(f"Error getting blog like stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get like stats"
        )

# ============== COMMENTS ENDPOINTS ==============

@router.post("/{blog_id}/comments", response_model=CommentActionResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    blog_id: str,
    comment_data: CommentCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new comment or reply to a comment"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        user_id = current_user["supabase_user"].id
        
        # Check if blog exists and is published
        blog_result = await db.execute(
            select(Blog.id).where(and_(Blog.id == blog_uuid, Blog.is_published == True))
        )
        if not blog_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Validate parent comment if it's a reply
        parent_comment_uuid = None
        if comment_data.parent_comment_id:
            try:
                parent_comment_uuid = uuid.UUID(comment_data.parent_comment_id)
                
                # Check if parent comment exists and belongs to the same blog
                parent_result = await db.execute(
                    select(BlogComment).where(
                        and_(
                            BlogComment.id == parent_comment_uuid,
                            BlogComment.blog_id == blog_uuid,
                            BlogComment.parent_comment_id.is_(None)  # Only allow replies to main comments
                        )
                    )
                )
                if not parent_result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid parent comment"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parent comment ID format"
                )
        
        # Create comment
        new_comment = BlogComment(
            blog_id=blog_uuid,
            user_id=user_id,
            content=comment_data.content,
            parent_comment_id=parent_comment_uuid
        )
        
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
        
        comment_type = "Reply" if parent_comment_uuid else "Comment"
        
        return CommentActionResponse(
            success=True,
            message=f"{comment_type} created successfully",
            comment_id=str(new_comment.id)
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
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )

@router.get("/{blog_id}/comments", response_model=CommentsListResponse)
async def get_blog_comments(
    blog_id: str,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comments for a blog with replies"""
    try:
        blog_uuid = uuid.UUID(blog_id)
        
        # Check if blog exists
        blog_result = await db.execute(
            select(Blog.id).where(Blog.id == blog_uuid)
        )
        if not blog_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog not found"
            )
        
        # Get main comments (not replies) with user info
        main_comments_result = await db.execute(
            select(
                BlogComment.id,
                BlogComment.blog_id,
                BlogComment.user_id,
                BlogComment.content,
                BlogComment.created_at,
                BlogComment.updated_at,
                UserProfile.username,
                UserProfile.display_name,
                UserProfile.avatar_url
            )
            .join(UserProfile, UserProfile.user_id == BlogComment.user_id)
            .where(
                and_(
                    BlogComment.blog_id == blog_uuid,
                    BlogComment.parent_comment_id.is_(None)
                )
            )
            .order_by(BlogComment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        main_comments = main_comments_result.all()
        
        # Get total count of main comments
        count_result = await db.execute(
            select(func.count(BlogComment.id))
            .where(
                and_(
                    BlogComment.blog_id == blog_uuid,
                    BlogComment.parent_comment_id.is_(None)
                )
            )
        )
        total_count = count_result.scalar() or 0
        
        # Build response with replies
        comments_with_replies = []
        
        for comment_row in main_comments:
            # Get replies for this comment
            replies_result = await db.execute(
                select(
                    BlogComment.id,
                    BlogComment.blog_id,
                    BlogComment.user_id,
                    BlogComment.content,
                    BlogComment.parent_comment_id,
                    BlogComment.created_at,
                    BlogComment.updated_at,
                    UserProfile.username,
                    UserProfile.display_name,
                    UserProfile.avatar_url
                )
                .join(UserProfile, UserProfile.user_id == BlogComment.user_id)
                .where(BlogComment.parent_comment_id == comment_row.id)
                .order_by(BlogComment.created_at.asc())
            )
            
            replies = []
            for reply_row in replies_result.all():
                replies.append(CommentResponse(
                    id=str(reply_row.id),
                    blog_id=str(reply_row.blog_id),
                    user=CommentUserResponse(
                        user_id=str(reply_row.user_id),
                        username=reply_row.username,
                        display_name=reply_row.display_name,
                        avatar_url=reply_row.avatar_url
                    ),
                    content=reply_row.content,
                    parent_comment_id=str(reply_row.parent_comment_id),
                    created_at=reply_row.created_at,
                    updated_at=reply_row.updated_at
                ))
            
            comments_with_replies.append(CommentWithRepliesResponse(
                id=str(comment_row.id),
                blog_id=str(comment_row.blog_id),
                user=CommentUserResponse(
                    user_id=str(comment_row.user_id),
                    username=comment_row.username,
                    display_name=comment_row.display_name,
                    avatar_url=comment_row.avatar_url
                ),
                content=comment_row.content,
                reply_count=len(replies),
                replies=replies,
                created_at=comment_row.created_at,
                updated_at=comment_row.updated_at
            ))
        
        return CommentsListResponse(
            comments=comments_with_replies,
            total_count=total_count,
            has_next=skip + limit < total_count,
            has_previous=skip > 0
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid blog ID format"
        )
    except Exception as e:
        logger.error(f"Error getting blog comments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comments"
        )

@router.put("/comments/{comment_id}", response_model=CommentActionResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a comment (only by the comment author)"""
    try:
        comment_uuid = uuid.UUID(comment_id)
        user_id = current_user["supabase_user"].id
        
        # Get comment and check ownership
        result = await db.execute(
            select(BlogComment).where(
                and_(
                    BlogComment.id == comment_uuid,
                    BlogComment.user_id == user_id
                )
            )
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or you don't have permission to edit it"
            )
        
        # Update comment
        comment.content = comment_update.content
        comment.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return CommentActionResponse(
            success=True,
            message="Comment updated successfully",
            comment_id=str(comment.id)
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment"
        )

@router.delete("/comments/{comment_id}", response_model=CommentActionResponse)
async def delete_comment(
    comment_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a comment (only by the comment author)"""
    try:
        comment_uuid = uuid.UUID(comment_id)
        user_id = current_user["supabase_user"].id
        
        # Get comment and check ownership
        result = await db.execute(
            select(BlogComment).where(
                and_(
                    BlogComment.id == comment_uuid,
                    BlogComment.user_id == user_id
                )
            )
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or you don't have permission to delete it"
            )
        
        # Delete comment (this will also delete replies due to cascade)
        await db.delete(comment)
        await db.commit()
        
        return CommentActionResponse(
            success=True,
            message="Comment deleted successfully"
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )
