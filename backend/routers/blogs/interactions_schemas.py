from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Comment and Like schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_comment_id: Optional[str] = Field(None, description="ID of parent comment for replies")

    class Config:
        schema_extra = {
            "example": {
                "content": "Great article! Thanks for sharing.",
                "parent_comment_id": None
            }
        }

class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class CommentUserResponse(BaseModel):
    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class CommentResponse(BaseModel):
    id: str
    blog_id: str
    user: CommentUserResponse
    content: str
    parent_comment_id: Optional[str] = None
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CommentWithRepliesResponse(BaseModel):
    id: str
    blog_id: str
    user: CommentUserResponse
    content: str
    reply_count: int = 0
    replies: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CommentsListResponse(BaseModel):
    comments: List[CommentWithRepliesResponse]
    total_count: int
    has_next: bool
    has_previous: bool

class CommentActionResponse(BaseModel):
    success: bool
    message: str
    comment_id: Optional[str] = None

class LikeActionResponse(BaseModel):
    success: bool
    message: str
    is_liked: bool
    like_count: int

class BlogLikeStatsResponse(BaseModel):
    like_count: int
    is_liked: bool  # Whether current user has liked this blog
