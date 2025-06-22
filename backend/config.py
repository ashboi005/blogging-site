import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base, UserProfile
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# AWS Region (Automatically set in Lambda)
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Supabase Storage Configuration
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

PRODUCTION_URL = os.getenv("PRODUCTION_URL")

# Lazy initialization for Lambda compatibility
_supabase_client = None
_supabase_admin_client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        # Simple client initialization for maximum Lambda compatibility
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    return _supabase_client

def get_supabase_admin_client() -> Client:
    global _supabase_admin_client
    if _supabase_admin_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        
        # Simple client initialization for maximum Lambda compatibility
        _supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    return _supabase_admin_client

# Supabase Storage Configuration
def get_supabase_storage():
    """Get Supabase storage client for file operations"""
    client = get_supabase_admin_client()
    return client.storage

# Database engine configuration
if DATABASE_URL:
    # Synchronous engine for Alembic migrations (using psycopg2)
    sync_engine = create_engine(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    
    # Asynchronous engine for FastAPI application
    # Try direct asyncpg without pgbouncer complications
    asyncpg_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    # Remove any existing parameters and add our own
    if "?" in asyncpg_url:
        base_url = asyncpg_url.split("?")[0]
    else:
        base_url = asyncpg_url
    
    # Add parameters to work with Supabase
    asyncpg_url = f"{base_url}?prepared_statement_cache_size=0"
    
    async_engine = create_async_engine(
        asyncpg_url,
        echo=False,
        pool_pre_ping=False,  # Disable for Supabase
        pool_size=5,
        max_overflow=0
    )
    
    # Async session maker for FastAPI application
    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
else:
    sync_engine = None
    async_engine = None
    AsyncSessionLocal = None

# Function to get an async DB session for FastAPI
async def get_db():
    if AsyncSessionLocal is None:
        raise Exception("Database not configured")
    async with AsyncSessionLocal() as session:
        yield session


# Function to initialize the database (for startup scripts)
async def init_db():
    if async_engine is None:
        raise Exception("Database not configured")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Function to get synchronous engine for Alembic migrations
def get_sync_engine():
    if sync_engine is None:
        raise Exception("Database not configured")
    return sync_engine

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
DEBUG = ENVIRONMENT == "dev"
