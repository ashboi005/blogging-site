from sqlalchemy import (
    Boolean, 
    String, 
    Text, 
    DateTime, 
    SmallInteger,
    CheckConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
    Index,
    Computed,
    text,
    ForeignKey,
    Column
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List
import uuid

Base = declarative_base()


class Users(Base):
    """
    Supabase auth.users table schema
    This mirrors the Supabase authentication table to enable proper foreign key relationships
    """
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "email_change_confirm_status >= 0 AND email_change_confirm_status <= 2",
            name="users_email_change_confirm_status_check",
        ),
        PrimaryKeyConstraint("id", name="users_pkey"),
        UniqueConstraint("phone", name="users_phone_key"),
        Index("confirmation_token_idx", "confirmation_token", unique=True),
        Index(
            "email_change_token_current_idx", "email_change_token_current", unique=True
        ),
        Index("email_change_token_new_idx", "email_change_token_new", unique=True),
        Index("reauthentication_token_idx", "reauthentication_token", unique=True),
        Index("recovery_token_idx", "recovery_token", unique=True),
        Index("users_email_partial_key", "email", unique=True),
        Index("users_instance_id_email_idx", "instance_id"),
        Index("users_instance_id_idx", "instance_id"),
        Index("users_is_anonymous_idx", "is_anonymous"),
        {
            "comment": "Auth: Stores user login data within a secure schema.",
            "schema": "auth",
        },
    )

    # Core fields
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    
    # Authentication fields
    is_sso_user: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.",
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    instance_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    aud: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(Text, server_default=text("NULL::character varying"))
    
    # Security fields
    encrypted_password: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Email confirmation
    email_confirmed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    confirmation_token: Mapped[Optional[str]] = mapped_column(String(255))
    confirmation_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Password recovery
    recovery_token: Mapped[Optional[str]] = mapped_column(String(255))
    recovery_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Email change process
    email_change_token_new: Mapped[Optional[str]] = mapped_column(String(255))
    email_change: Mapped[Optional[str]] = mapped_column(String(255))
    email_change_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    email_change_token_current: Mapped[Optional[str]] = mapped_column(
        String(255), server_default=text("''::character varying")
    )
    email_change_confirm_status: Mapped[Optional[int]] = mapped_column(SmallInteger, server_default=text("0"))
    
    # Phone change process
    phone_confirmed_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    phone_change: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''::character varying"))
    phone_change_token: Mapped[Optional[str]] = mapped_column(
        String(255), server_default=text("''::character varying")
    )
    phone_change_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Sign in tracking
    last_sign_in_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    invited_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Metadata
    raw_app_meta_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    raw_user_meta_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Admin and security
    is_super_admin: Mapped[Optional[bool]] = mapped_column(Boolean)
    banned_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Reauthentication
    reauthentication_token: Mapped[Optional[str]] = mapped_column(
        String(255), server_default=text("''::character varying")
    )
    reauthentication_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Timestamps
    created_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    updated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Computed field
    confirmed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(True),
        Computed("LEAST(email_confirmed_at, phone_confirmed_at)", persisted=True),
    )    # Relationships
    user_profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Follower relationships
    following_relationships: Mapped[List["UserFollower"]] = relationship(
        "UserFollower",
        foreign_keys="UserFollower.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    follower_relationships: Mapped[List["UserFollower"]] = relationship(
        "UserFollower",
        foreign_keys="UserFollower.following_id", 
        back_populates="following",
        cascade="all, delete-orphan"
    )


class UserProfile(Base):
    """
    Custom user profile table for additional user information
    This extends the basic auth.users table with application-specific data
    """
    __tablename__ = "user_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Profile information
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
      # Additional fields
    date_of_birth: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    timezone: Mapped[Optional[str]] = mapped_column(String(50))
    language: Mapped[Optional[str]] = mapped_column(String(10), default="en")
      # Custom styling fields for blogging
    custom_font: Mapped[Optional[str]] = mapped_column(String(100))
    custom_colors: Mapped[Optional[str]] = mapped_column(String(255))
    
    # User interests (same as blog tags for personalized content)
    interests: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    # Preferences (stored as JSON)
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True), 
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(True), 
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    # Relationship back to auth user
    user: Mapped["Users"] = relationship("Users", back_populates="user_profile")


class UserFollower(Base):
    """
    Many-to-many relationship table for user followers/following
    """
    __tablename__ = "user_followers"
    __table_args__ = (
        PrimaryKeyConstraint("follower_id", "following_id", name="user_followers_pkey"),
        Index("idx_follower_id", "follower_id"),
        Index("idx_following_id", "following_id"),
        CheckConstraint("follower_id != following_id", name="no_self_follow_check"),
    )
    
    follower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    # Relationships
    follower: Mapped["Users"] = relationship(
        "Users",
        foreign_keys=[follower_id],
        back_populates="following_relationships"
    )
    following: Mapped["Users"] = relationship(
        "Users", 
        foreign_keys=[following_id],
        back_populates="follower_relationships"
    )


class Blog(Base):
    """
    Blog posts table
    """
    __tablename__ = "blogs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Blog status and visibility
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True), 
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(True), 
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    published_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(True))
    
    # Indexes for better search performance
    __table_args__ = (
        Index("idx_blogs_title", "title"),
        Index("idx_blogs_tags", "tags"),
        Index("idx_blogs_published", "is_published"),
        Index("idx_blogs_created_at", "created_at"),
    )
    
    # Relationships
    authors: Mapped[List["BlogAuthor"]] = relationship("BlogAuthor", back_populates="blog", cascade="all, delete-orphan")
    comments: Mapped[List["BlogComment"]] = relationship("BlogComment", back_populates="blog", cascade="all, delete-orphan")
    likes: Mapped[List["BlogLike"]] = relationship("BlogLike", back_populates="blog", cascade="all, delete-orphan")


class BlogAuthor(Base):
    """
    Many-to-many relationship table for blog authors
    Allows multiple authors per blog for co-authored posts
    """
    __tablename__ = "blog_authors"
    __table_args__ = (
        PrimaryKeyConstraint("blog_id", "user_id", name="blog_authors_pkey"),
        Index("idx_blog_authors_blog_id", "blog_id"),
        Index("idx_blog_authors_user_id", "user_id"),
    )
    
    blog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blogs.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )
    is_primary_author: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="authors")
    user: Mapped["Users"] = relationship("Users")


class BlogLike(Base):
    """
    Blog likes table - each user can like a blog only once
    """
    __tablename__ = "blog_likes"
    __table_args__ = (
        PrimaryKeyConstraint("blog_id", "user_id", name="blog_likes_pkey"),
        Index("idx_blog_likes_blog_id", "blog_id"),
        Index("idx_blog_likes_user_id", "user_id"),
    )
    
    blog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blogs.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="likes")
    user: Mapped["Users"] = relationship("Users")


class BlogComment(Base):
    """
    Blog comments table with support for replies (one level deep)
    """
    __tablename__ = "blog_comments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blog_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blogs.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # For replies - parent_comment_id links to main comment (no threading)
    parent_comment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blog_comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_blog_comments_blog_id", "blog_id"),
        Index("idx_blog_comments_user_id", "user_id"),
        Index("idx_blog_comments_parent_id", "parent_comment_id"),
        Index("idx_blog_comments_created_at", "created_at"),
    )
    
    # Relationships
    blog: Mapped["Blog"] = relationship("Blog", back_populates="comments")
    user: Mapped["Users"] = relationship("Users")
    parent_comment: Mapped[Optional["BlogComment"]] = relationship("BlogComment", remote_side=[id], back_populates="replies")
    replies: Mapped[List["BlogComment"]] = relationship("BlogComment", back_populates="parent_comment", cascade="all, delete-orphan")

