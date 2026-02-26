"""
Database Configuration and Session Management
Single unified PostgreSQL database for all Neubolt data
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max overflow connections
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def now_karachi():
    """Helper function to get current time in Karachi timezone"""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from config import settings
    try:
        return datetime.now(ZoneInfo(settings.TIMEZONE))
    except Exception:
        from datetime import timezone
        return datetime.now(timezone.utc)

def get_db() -> Generator[Session, None, None]:
    # ... (rest of get_db)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    Called on application startup
    """
    try:
        # Import all models from their new router locations to register them with Base
        from routers import (
            users, drivers, vehicles, stations, batteries, swaps, complaints, files
        )
        from authentication import UserSession, TokenBlacklist
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create initial admin user if not exists
        create_initial_admin()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


def create_initial_admin():
    """Create initial admin user if no admin exists"""
    from routers.users import Neubolt_User
    from authentication import hash_password
    
    db = SessionLocal()
    try:
        # Check if any admin user exists
        admin_exists = db.query(Neubolt_User).filter(Neubolt_User.user_type == "admin").first()
        
        if not admin_exists:
            # Create default admin user
            admin = Neubolt_User(
                user_id="3520212345678",  # Default CNIC
                user_type="admin",
                username="admin",
                password=hash_password("admin123"),
                display_name="System Administrator",
                contact_no="03001234567",
                email="admin@neubolt.com"
            )
            
            db.add(admin)
            db.commit()
            
            logger.info("🔐 Initial admin user created:")
            logger.info("   Username: admin")
            logger.info("   Password: admin123")
            logger.info("   ⚠️  Please change the default password after first login!")
        else:
            logger.info(f"Admin user already exists")
            
    except Exception as e:
        logger.error(f"Failed to create initial admin: {str(e)}")
        db.rollback()
    finally:
        db.close()


def drop_all_tables():
    """
    Drop all database tables - USE WITH CAUTION!
    Only for development/testing
    """
    if settings.DEBUG:
        Base.metadata.drop_all(bind=engine)
        logger.warning("⚠️ All database tables dropped")
    else:
        logger.error("Cannot drop tables in production mode")
