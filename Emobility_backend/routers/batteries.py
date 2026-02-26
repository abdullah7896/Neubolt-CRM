"""
Batteries Router - Battery management endpoints
Refactored for Battery schema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import Session, relationship
from typing import List
from database import Base, get_db, now_karachi
from schemas import BatteryCreate, BatteryResponse, MessageResponse

class Battery(Base):
    """Battery table"""
    __tablename__ = "battery"
    
    battery_id = Column(String(50), primary_key=True)
    company = Column(String(100))
    model = Column(String(100))
    import_date = Column(Date)
    registration_date = Column(Date, default=lambda: now_karachi().date())
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))

    # Relationships
    registrar = relationship("Neubolt_User", back_populates="registered_batteries", foreign_keys=[user_id])
    
    # Swaps relationships (Old/New Battery 1, 2, 3)
    swaps_old1 = relationship("SWAP", foreign_keys="SWAP.old_battery_id_1", back_populates="old_battery1")
    swaps_old2 = relationship("SWAP", foreign_keys="SWAP.old_battery_id_2", back_populates="old_battery2")
    swaps_old3 = relationship("SWAP", foreign_keys="SWAP.old_battery_id_3", back_populates="old_battery3")
    swaps_new1 = relationship("SWAP", foreign_keys="SWAP.new_battery_id_1", back_populates="new_battery1")
    swaps_new2 = relationship("SWAP", foreign_keys="SWAP.new_battery_id_2", back_populates="new_battery2")
    swaps_new3 = relationship("SWAP", foreign_keys="SWAP.new_battery_id_3", back_populates="new_battery3")
from authentication import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/batteries", response_model=BatteryResponse, status_code=status.HTTP_201_CREATED)
async def create_battery(
    battery_data: BatteryCreate,
    current_user: dict = Depends(require_role(["admin", "crm", "maintenance"])),
    db: Session = Depends(get_db)
):
    """Register Battery"""
    existing_battery = db.query(Battery).filter(Battery.battery_id == battery_data.battery_id).first()
    if existing_battery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Battery with this ID already exists"
        )
    
    new_battery = Battery(
        battery_id=battery_data.battery_id,
        company=battery_data.company,
        model=battery_data.model,
        import_date=battery_data.import_date,
        user_id=current_user["user_id"]
    )
    
    db.add(new_battery)
    db.commit()
    db.refresh(new_battery)
    
    logger.info(f"Battery registered: {new_battery.battery_id} by {current_user['username']}")
    
    return new_battery


@router.get("/batteries", response_model=List[BatteryResponse])
async def list_batteries(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all batteries"""
    batteries = db.query(Battery).offset(skip).limit(limit).all()
    return batteries


@router.get("/batteries/{battery_id}", response_model=BatteryResponse)
async def get_battery(
    battery_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get battery by ID"""
    battery = db.query(Battery).filter(Battery.battery_id == battery_id).first()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery
