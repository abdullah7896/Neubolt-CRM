"""
Swaps Router - Swap transaction endpoints
Refactored for SWAP schema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Session, relationship
from typing import List
from database import Base, get_db, now_karachi
from schemas import SWAPCreate, SWAPResponse, MessageResponse
import logging
from config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SWAP(Base):
    """SWAP table"""
    __tablename__ = "swap"
    
    swap_id = Column(String(50), primary_key=True)
    swap_time = Column(TIMESTAMP(timezone=True), default=now_karachi)
    bss_id = Column(String(50), ForeignKey("bss.bss_id"))
    ev_id = Column(String(50), ForeignKey("ev.ev_id"))
    
    old_battery_id_1 = Column(String(50), ForeignKey("battery.battery_id"))
    old_battery_id_2 = Column(String(50), ForeignKey("battery.battery_id"))
    old_battery_id_3 = Column(String(50), ForeignKey("battery.battery_id"))
    new_battery_id_1 = Column(String(50), ForeignKey("battery.battery_id"))
    new_battery_id_2 = Column(String(50), ForeignKey("battery.battery_id"))
    new_battery_id_3 = Column(String(50), ForeignKey("battery.battery_id"))
    
    transaction_amount = Column(Float)
    transaction_energy = Column(Float)

    # Relationships
    bss = relationship("BSS", back_populates="swaps")
    ev = relationship("EV", back_populates="swaps")
    
    old_battery1 = relationship("Battery", foreign_keys=[old_battery_id_1], back_populates="swaps_old1")
    old_battery2 = relationship("Battery", foreign_keys=[old_battery_id_2], back_populates="swaps_old2")
    old_battery3 = relationship("Battery", foreign_keys=[old_battery_id_3], back_populates="swaps_old3")
    new_battery1 = relationship("Battery", foreign_keys=[new_battery_id_1], back_populates="swaps_new1")
    new_battery2 = relationship("Battery", foreign_keys=[new_battery_id_2], back_populates="swaps_new2")
    new_battery3 = relationship("Battery", foreign_keys=[new_battery_id_3], back_populates="swaps_new3")

from authentication import get_current_user, require_role

@router.post("/swaps", response_model=SWAPResponse, status_code=status.HTTP_201_CREATED)
async def create_swap(
    swap_data: SWAPCreate,
    current_user: dict = Depends(require_role(["admin", "operator", "crm"])),
    db: Session = Depends(get_db)
):
    """Record new Swap transaction"""
    # Check if swap ID exists
    existing = db.query(SWAP).filter(SWAP.swap_id == swap_data.swap_id).first()
    if existing:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Swap with this ID already exists"
        )
         
    new_swap = SWAP(
        swap_id=swap_data.swap_id,
        swap_time=now_karachi(),
        bss_id=swap_data.bss_id,
        ev_id=swap_data.ev_id,
        old_battery_id_1=swap_data.old_battery_id_1,
        old_battery_id_2=swap_data.old_battery_id_2,
        old_battery_id_3=swap_data.old_battery_id_3,
        new_battery_id_1=swap_data.new_battery_id_1,
        new_battery_id_2=swap_data.new_battery_id_2,
        new_battery_id_3=swap_data.new_battery_id_3,
        transaction_amount=swap_data.transaction_amount,
        transaction_energy=swap_data.transaction_energy
    )
    
    db.add(new_swap)
    db.commit()
    db.refresh(new_swap)
    
    logger.info(f"Swap recorded: {new_swap.swap_id} by {current_user['username']}")
    
    return new_swap


@router.get("/swaps", response_model=List[SWAPResponse])
async def list_swaps(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all swaps"""
    swaps = db.query(SWAP).offset(skip).limit(limit).all()
    return swaps


@router.get("/admin/get-swaps")
async def get_swaps(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all swaps (Legacy alias)"""
    return db.query(SWAP).all()
