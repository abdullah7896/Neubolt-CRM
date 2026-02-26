"""
Users Router
Handles user management (CRUD operations for Neubolt_User table)
Refactored for Neubolt_User schema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Date, Text, ForeignKey, or_
from sqlalchemy.orm import Session, relationship
from typing import List
import logging

from database import Base, get_db, now_karachi
from schemas import UserCreate, UserUpdate, UserResponse, MessageResponse, UserListResponse

class Neubolt_User(Base):
    """
    Users table - unified for all user types
    user_id acting as CNIC (Primary Key)
    """
    __tablename__ = "neubolt_user"
    
    user_id = Column(String(50), primary_key=True) # Note: CNIC
    user_type = Column(String(50))
    username = Column(String(50), unique=True)
    password = Column(String(255))
    display_name = Column(String(100))
    contact_no = Column(String(20))
    email = Column(String(100))
    user_image = Column(Text)
    dob = Column(Date)
    address = Column(Text)
    registration_date = Column(Date, default=lambda: now_karachi().date())
    registered_by_user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))

    # Relationships
    registered_drivers = relationship("Driver", back_populates="registrar", foreign_keys="Driver.user_id")
    registered_evs = relationship("EV", back_populates="registrar", foreign_keys="EV.user_id")
    registered_batteries = relationship("Battery", back_populates="registrar", foreign_keys="Battery.user_id")
    registered_bss = relationship("BSS", back_populates="registrar", foreign_keys="BSS.user_id")
    complaints = relationship("Complaints", back_populates="user", foreign_keys="Complaints.user_id")
from authentication import get_current_user, require_role, hash_password

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Create new user (Admin only)"""
    # Check if user already exists (by CNIC or username)
    existing_user = db.query(Neubolt_User).filter(
        or_(
            Neubolt_User.user_id == user_data.user_id,
            Neubolt_User.username == user_data.username
        )
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this CNIC or username already exists"
        )
    
    # Create new user
    import secrets
    
    # Handle missing user_id (CNIC) if it's optional in schema
    user_id = user_data.user_id
    if not user_id:
        # Generate a random 13-digit number if missing
        user_id = "".join([str(secrets.randbelow(10)) for _ in range(13)])
        logger.info(f"Generated user_id for {user_data.username}: {user_id}")
    
    # Handle missing contact_no
    contact_no = user_data.contact_no
    if not contact_no:
        contact_no = "03" + "".join([str(secrets.randbelow(10)) for _ in range(9)])

    new_user = Neubolt_User(
        user_id=user_id,
        user_type=user_data.user_type,
        username=user_data.username,
        password=hash_password(user_data.password),
        display_name=user_data.display_name,
        contact_no=contact_no,
        email=user_data.email,
        user_image=user_data.user_image,
        address=user_data.address,
        dob=user_data.dob,
        registered_by_user_id=current_user.get("user_id")
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User created: {new_user.username} by {current_user['username']}")
    
    return new_user


@router.get("/users", response_model=UserListResponse, response_model_by_alias=True)
async def list_users(
    user_type: str = None,
    current_user: dict = Depends(require_role(["admin", "crm"])),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all users, optionally filtered by type"""
    query = db.query(Neubolt_User)
    if user_type:
        query = query.filter(Neubolt_User.user_type == user_type)
    
    users = query.offset(skip).limit(limit).all()
    return {"users": users, "total": len(users), "success": True}


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by user_id (CNIC)"""
    # Users can see their own profile, admins/crm can see anyone
    if current_user["user_id"] != user_id and current_user["role"] not in ["admin", "crm"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    user = db.query(Neubolt_User).filter(Neubolt_User.UserId == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user"""
    if current_user["user_id"] != user_id and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(Neubolt_User).filter(Neubolt_User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_data.display_name:
        user.display_name = user_data.display_name
    if user_data.contact_no:
        user.contact_no = user_data.contact_no
    if user_data.email:
        user.email = user_data.email
    if user_data.password:
        user.password = hash_password(user_data.password)
    if user_data.address:
        user.address = user_data.address
    if user_data.user_image:
        user.user_image = user_data.user_image
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated: {user.username} by {current_user['username']}")
    
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete user (Admin only)"""
    user = db.query(Neubolt_User).filter(Neubolt_User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User deleted: {user.username} by {current_user['username']}")
    
    return MessageResponse(
        message=f"User {user.username} deleted successfully",
        success=True
    )
