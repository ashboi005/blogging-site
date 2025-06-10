from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Blog tags enum - predefined popular blog topics
BLOG_TAGS = [
    "technology",
    "programming",
    "web-development",
    "data-science",
    "machine-learning",
    "artificial-intelligence",
    "life",
    "fiction",
    "business",
    "startup",
    "marketing",
    "design",
    "lifestyle",
    "health",
    "travel",
    "food",
    "education"
]

# Request schemas
class BlogCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    tags: List[str] = Field(default=[], description="List of tags from predefined options")
    co_author_ids: Optional[List[str]] = Field(default=[], description="List of co-author user IDs")
    is_published: bool = Field(default=False, description="Whether to publish immediately")

    class Config:
        schema_extra = {
            "example": {
                "title": "Getting Started with FastAPI",
                "description": "A comprehensive guide to building APIs with FastAPI",
                "content": "FastAPI is a modern, fast web framework for building APIs...",
                "tags": ["programming", "web-development", "technology"],
                "co_author_ids": [],
                "is_published": True
            }
        }

class BlogUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    co_author_ids: Optional[List[str]] = None
    is_published: Optional[bool] = None

class BlogSearch(BaseModel):
    query: Optional[str] = Field(None, description="Search in title, description, and content")
    author: Optional[str] = Field(None, description="Search by author username")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_published: Optional[bool] = Field(True, description="Filter by published status")

# Response schemas
class BlogAuthorResponse(BaseModel):
    user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_primary_author: bool

    class Config:
        from_attributes = True

class BlogResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content: str
    tags: List[str]
    cover_image_url: Optional[str] = None
    is_published: bool
    is_featured: bool
    authors: List[BlogAuthorResponse]
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BlogSummaryResponse(BaseModel):
    """Lighter response for blog lists"""
    id: str
    title: str
    description: Optional[str] = None
    tags: List[str]
    cover_image_url: Optional[str] = None
    is_published: bool
    is_featured: bool
    authors: List[BlogAuthorResponse]
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BlogListResponse(BaseModel):
    blogs: List[BlogSummaryResponse]
    total_count: int
    has_next: bool
    has_previous: bool

class BlogCreateResponse(BaseModel):
    id: str
    title: str
    message: str
    is_published: bool

class BlogActionResponse(BaseModel):
    success: bool
    message: str

class BlogImageUpload(BaseModel):
    """Response schema for blog cover image upload"""
    cover_image_url: str
    message: str
