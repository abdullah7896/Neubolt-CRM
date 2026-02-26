"""
Stations Router - BSS management endpoints
Refactored for BSS schema (BSS_ID as PK/MAC)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Integer, Float, ForeignKey, TIMESTAMP, Text, Date
from sqlalchemy.orm import Session, relationship
from sqlalchemy import func
from typing import List, Optional
from database import Base, get_db, now_karachi
from schemas import BSSCreate, BSSResponse, BSSDataResponse, MessageResponse

class BSS(Base):
    """BSS table (Battery Swap Station)"""
    __tablename__ = "bss"
    
    bss_id = Column(String(50), primary_key=True) # Note: MAC Address / ID
    station_name = Column(String(100))
    location = Column(Text)
    city = Column(String(50))
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))
    registration_date = Column(Date, default=lambda: now_karachi().date())
    
    # Relationships
    registrar = relationship("Neubolt_User", back_populates="registered_bss", foreign_keys=[user_id])
    swaps = relationship("SWAP", back_populates="bss")
    bss_data = relationship("BSS_Data", back_populates="bss")

class BSS_Data(Base):
    """BSS_Data table (Flattened Battery-level telemetry inside the BSS)"""
    __tablename__ = "bss_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bss_id = Column(String(50), ForeignKey("bss.bss_id"))
    log_time = Column(TIMESTAMP(timezone=True), default=now_karachi)
    
    # Slot 1
    s1_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s1_temp = Column(Float)
    s1_soc = Column(Float)
    s1_soh = Column(Float)
    s1_vol = Column(Float)
    s1_curr = Column(Float)
    s1_cycle_cnt = Column(Integer)
    s1_rem_cap = Column(Float)
    s1_full_cap = Column(Float)
    s1_chr_vol = Column(Float)
    s1_chr_curr = Column(Float)
    s1_status = Column(String(50))
    s1_b_errorflags = Column(String(255))
    s1_c_errorflags = Column(String(255))

    # Slot 2
    s2_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s2_temp = Column(Float)
    s2_soc = Column(Float)
    s2_soh = Column(Float)
    s2_vol = Column(Float)
    s2_curr = Column(Float)
    s2_cycle_cnt = Column(Integer)
    s2_rem_cap = Column(Float)
    s2_full_cap = Column(Float)
    s2_chr_vol = Column(Float)
    s2_chr_curr = Column(Float)
    s2_status = Column(String(50))
    s2_b_errorflags = Column(String(255))
    s2_c_errorflags = Column(String(255))

    # Slot 3
    s3_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s3_temp = Column(Float)
    s3_soc = Column(Float)
    s3_soh = Column(Float)
    s3_vol = Column(Float)
    s3_curr = Column(Float)
    s3_cycle_cnt = Column(Integer)
    s3_rem_cap = Column(Float)
    s3_full_cap = Column(Float)
    s3_chr_vol = Column(Float)
    s3_chr_curr = Column(Float)
    s3_status = Column(String(50))
    s3_b_errorflags = Column(String(255))
    s3_c_errorflags = Column(String(255))

    # Relationships
    bss = relationship("BSS", back_populates="bss_data")
from authentication import get_current_user, require_role
import logging
import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stations", response_model=BSSResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_data: BSSCreate,
    current_user: dict = Depends(require_role(["admin", "crm", "operator"])),
    db: Session = Depends(get_db)
):
    """Register BSS (Station)"""
    existing_bss = db.query(BSS).filter(BSS.bss_id == station_data.bss_id).first()
    if existing_bss:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BSS with this ID already exists"
        )
    
    new_bss = BSS(
        bss_id=station_data.bss_id,
        station_name=station_data.station_name,
        location=station_data.location,
        city=station_data.city,
        user_id=current_user["user_id"]
    )
    
    db.add(new_bss)
    db.commit()
    db.refresh(new_bss)
    
    logger.info(f"BSS registered: {new_bss.bss_id} by {current_user['username']}")
    
    return new_bss


@router.get("/stations", response_model=List[BSSResponse])
async def list_stations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all stations"""
    stations = db.query(BSS).offset(skip).limit(limit).all()
    return stations


@router.get("/stations/{bss_id}", response_model=BSSResponse)
async def get_station(
    bss_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get station by bss_id"""
    station = db.query(BSS).filter(BSS.bss_id == bss_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@router.get("/stations/{bss_id}/telemetry", response_model=List[BSSDataResponse])
async def get_station_telemetry(
    bss_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    slot: Optional[int] = None,
    limit: int = 20
):
    """Get latest telemetry for Station (Adapted for flattened)"""
    telemetry = db.query(BSS_Data).filter(BSS_Data.bss_id == bss_id).order_by(BSS_Data.log_time.desc()).limit(limit).all()
    return telemetry


@router.get("/admin/get-station_stats")
async def get_station_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get station statistics (Legacy adapted)"""
    stations = db.query(BSS).all()
    stats = []
    
    now = datetime.datetime.now()
    month_start = datetime.datetime(now.year, now.month, 1)
    
    for s in stations:
        # Total Swaps & Revenue
        total_swaps = db.query(SWAP).filter(SWAP.bss_id == s.bss_id).count()
        total_rev = db.query(func.sum(SWAP.transaction_amount)).filter(SWAP.bss_id == s.bss_id).scalar() or 0
        
        # Monthly
        monthly_swaps = db.query(SWAP).filter(
            SWAP.bss_id == s.bss_id, 
            SWAP.swap_time >= month_start
        ).count()
        monthly_rev = db.query(func.sum(SWAP.transaction_amount)).filter(
            SWAP.bss_id == s.bss_id,
            SWAP.swap_time >= month_start
        ).scalar() or 0
        
        stats.append({
            "name": s.station_name,
            "id": s.bss_id,
            "location": s.location,
            "city": s.city,
            "monthly_revenue": monthly_rev,
            "monthly_swap_count": monthly_swaps,
            "total_revenue": total_rev,
            "total_swap_count": total_swaps
        })
        
    return stats
