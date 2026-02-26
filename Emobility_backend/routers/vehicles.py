"""
Vehicles Router - EV management endpoints
Refactored for EV schema (EVID as PK/MAC)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Integer, Float, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import Session, relationship
from typing import List, Optional
from database import Base, get_db, now_karachi
from schemas import EVCreate, EVUpdate, EVResponse, MessageResponse, GPSResponse, EVDataResponse

class EV(Base):
    """EV table (was Vehicle)"""
    __tablename__ = "ev"
    
    ev_id = Column(String(50), primary_key=True) # Note: MAC Address / Registration Number
    manufacturer = Column(String(100))
    category = Column(String(50))
    chasis_num = Column(String(50), unique=True)
    city = Column(String(50))
    registration_datetime = Column(TIMESTAMP(timezone=True), default=now_karachi)
    vehicle_image = Column(Text)
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))
    registry_image = Column(Text)

    # Relationships
    registrar = relationship("Neubolt_User", back_populates="registered_evs", foreign_keys=[user_id])
    drivers = relationship("Driver", back_populates="allocated_vehicle", foreign_keys="Driver.ev_id")
    gps_logs = relationship("GPS", back_populates="ev")
    telemetry_logs = relationship("EV_Data", back_populates="ev")
    swaps = relationship("SWAP", back_populates="ev")

class GPS(Base):
    """GPS table"""
    __tablename__ = "gps"
    
    gps_id = Column(String(50), primary_key=True) 
    ev_id = Column(String(50), ForeignKey("ev.ev_id"))
    latitude = Column(Float) # DOUBLE PRECISION
    longitude = Column(Float) # DOUBLE PRECISION
    gps_timestamp = Column(TIMESTAMP(timezone=True), default=now_karachi)

    # Relationships
    ev = relationship("EV", back_populates="gps_logs")

class EV_Data(Base):
    """EV_Data table (Flattened Telemetry)"""
    __tablename__ = "ev_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ev_id = Column(String(50), ForeignKey("ev.ev_id"))
    log_time = Column(TIMESTAMP(timezone=True), default=now_karachi)
    
    ev_current = Column(Float)
    ev_voltage = Column(Float)
    ev_mcu_rpm = Column(Float)
    distance = Column(Float)
    e_mcu_tempflag = Column(Float)

    # Slot 1
    s1_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s1_temp = Column(Float)
    s1_soc = Column(Float)
    s1_soh = Column(Float)
    s1_vol = Column(Float)
    s1_curr = Column(Float)

    # Slot 2
    s2_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s2_temp = Column(Float)
    s2_soc = Column(Float)
    s2_soh = Column(Float)
    s2_vol = Column(Float)
    s2_curr = Column(Float)

    # Slot 3
    s3_battery_id = Column(String(50), ForeignKey("battery.battery_id"))
    s3_temp = Column(Float)
    s3_soc = Column(Float)
    s3_soh = Column(Float)
    s3_vol = Column(Float)
    s3_curr = Column(Float)

    # Relationships
    ev = relationship("EV", back_populates="telemetry_logs")
from authentication import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/vehicles", response_model=EVResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: EVCreate,
    current_user: dict = Depends(require_role(["admin", "crm"])),
    db: Session = Depends(get_db)
):
    """Register new EV"""
    existing_ev = db.query(EV).filter(EV.ev_id == vehicle_data.ev_id).first()
    if existing_ev:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EV with this ev_id already exists"
        )
    
    new_ev = EV(
        ev_id=vehicle_data.ev_id,
        manufacturer=vehicle_data.manufacturer,
        category=vehicle_data.category,
        chasis_num=vehicle_data.chasis_num,
        city=vehicle_data.city,
        vehicle_image=vehicle_data.vehicle_image,
        registry_image=vehicle_data.registry_image,
        user_id=current_user["user_id"]
    )
    
    db.add(new_ev)
    db.commit()
    db.refresh(new_ev)
    
    logger.info(f"EV registered: {new_ev.ev_id} by {current_user['username']}")
    
    return new_ev


@router.post("/ev_rikshaws", response_model=EVResponse, status_code=status.HTTP_201_CREATED)
async def create_ev_rikshaw_legacy(
    payload: dict,
    current_user: dict = Depends(require_role(["admin", "crm"])),
    db: Session = Depends(get_db)
):
    """Legacy alias for creating EV records"""
    ev_id = payload.get("ev_id") or payload.get("registration_number") or payload.get("rikshaw_id")
    manufacturer = payload.get("manufacturer") or payload.get("type") or "legacy"
    category = payload.get("category")
    chasis_num = payload.get("chasis_num") or payload.get("chasis_number")
    city = payload.get("city") or ""

    if not ev_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ev_id (or registration_number/rikshaw_id) is required")
    if not category:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="category is required")
    if not chasis_num:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="chasis_num (or chasis_number) is required")

    existing_ev = db.query(EV).filter(EV.ev_id == ev_id).first()
    if existing_ev:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EV with this ev_id already exists"
        )

    new_ev = EV(
        ev_id=ev_id,
        manufacturer=manufacturer,
        category=category,
        chasis_num=chasis_num,
        city=city,
        vehicle_image=payload.get("vehicle_image"),
        registry_image=payload.get("registry_image"),
        user_id=current_user["user_id"]
    )

    db.add(new_ev)
    db.commit()
    db.refresh(new_ev)

    logger.info(f"EV registered (legacy): {new_ev.ev_id} by {current_user['username']}")
    return new_ev


@router.get("/vehicles", response_model=List[EVResponse])
async def list_vehicles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all EVs"""
    evs = db.query(EV).offset(skip).limit(limit).all()
    return evs


@router.get("/ev_rikshaws", response_model=List[EVResponse])
async def list_ev_rikshaws_legacy(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Legacy alias for listing EV records"""
    return await list_vehicles(current_user=current_user, db=db, skip=skip, limit=limit)


@router.get("/vehicles/{ev_id}", response_model=EVResponse)
async def get_vehicle(
    ev_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get EV by ev_id"""
    ev = db.query(EV).filter(EV.ev_id == ev_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="EV not found")
    return ev


@router.put("/vehicles/{ev_id}", response_model=EVResponse)
async def update_vehicle(
    ev_id: str,
    vehicle_data: EVUpdate,
    current_user: dict = Depends(require_role(["admin", "crm", "maintenance"])),
    db: Session = Depends(get_db)
):
    """Update EV"""
    ev = db.query(EV).filter(EV.ev_id == ev_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="EV not found")
    
    if vehicle_data.city:
        ev.city = vehicle_data.city
    if vehicle_data.vehicle_image:
        ev.vehicle_image = vehicle_data.vehicle_image
    if vehicle_data.registry_image:
        ev.registry_image = vehicle_data.registry_image
    
    db.commit()
    db.refresh(ev)
    return ev


@router.get("/vehicles/{ev_id}/telemetry", response_model=List[EVDataResponse])
async def get_vehicle_telemetry(
    ev_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get latest telemetry for EV"""
    telemetry = db.query(EV_Data).filter(
        EV_Data.ev_id == ev_id
    ).order_by(EV_Data.log_time.desc()).limit(limit).all()
    
    # Return empty list instead of 404 for empty logs
    return telemetry


@router.get("/vehicles/{ev_id}/battery-telemetry", response_model=List[EVDataResponse])
async def get_vehicle_battery_telemetry(
    ev_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    slot: Optional[int] = None,
    limit: int = 20
):
    """Get latest battery slot telemetry for EV (Adapted for flattened)"""
    telemetry = db.query(EV_Data).filter(EV_Data.ev_id == ev_id).order_by(EV_Data.log_time.desc()).limit(limit).all()
    return telemetry


@router.get("/vehicles/{ev_id}/location", response_model=GPSResponse)
async def get_vehicle_location(
    ev_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get latest GPS location for EV"""
    location = db.query(GPS).filter(
        GPS.ev_id == ev_id
    ).order_by(GPS.gps_timestamp.desc()).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="No GPS data found")
    
    return location


@router.get("/admin/get-ev_rikshaws")
async def get_ev_rikshaws(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all EVs (Legacy alias)"""
    evs = db.query(EV).all()
    return evs
