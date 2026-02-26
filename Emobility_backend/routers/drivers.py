"""
Drivers Router - Driver management endpoints
Refactored for Driver schema (DrID as PK/CNIC)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, Date
from sqlalchemy.orm import Session, relationship
from typing import List
from database import Base, get_db, now_karachi
from schemas import DriverCreate, DriverUpdate, DriverResponse, MessageResponse

class Driver(Base):
    """Drivers table - EV drivers"""
    __tablename__ = "driver"
    
    dr_id = Column(String(50), primary_key=True) # Note: CNIC
    name = Column(String(100))
    contact_no = Column(String(20))
    driver_image = Column(Text)
    cnic_front = Column(Text)
    cnic_back = Column(Text)
    linsence_img = Column(Text)
    ev_id = Column(String(50), ForeignKey("ev.ev_id"))
    dob = Column(Date)
    city = Column(String(50))
    current_address = Column(Text)
    criminal_record_img = Column(Text)
    registration_date = Column(TIMESTAMP(timezone=True), default=now_karachi)
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))

    # Relationships
    registrar = relationship("Neubolt_User", back_populates="registered_drivers", foreign_keys=[user_id])
    allocated_vehicle = relationship("EV", back_populates="drivers", foreign_keys=[ev_id])
    complaints = relationship("Complaints", back_populates="driver", foreign_keys="Complaints.dr_id")
from authentication import get_current_user, require_role
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_data: DriverCreate,
    current_user: dict = Depends(require_role(["admin", "crm", "operator"])),
    db: Session = Depends(get_db)
):
    """Register new driver"""
    # Check if driver exists
    existing_driver = db.query(Driver).filter(Driver.dr_id == driver_data.dr_id).first()
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver with this dr_id (CNIC) already exists"
        )
    
    # Assign registrar if not provided or override for security
    registrar_id = current_user["user_id"]
    
    new_driver = Driver(
        dr_id=driver_data.dr_id,
        name=driver_data.name,
        contact_no=driver_data.contact_no,
        driver_image=driver_data.driver_image,
        cnic_front=driver_data.cnic_front,
        cnic_back=driver_data.cnic_back,
        linsence_img=driver_data.linsence_img,
        ev_id=driver_data.ev_id,
        dob=driver_data.dob,
        city=driver_data.city,
        current_address=driver_data.current_address,
        criminal_record_img=driver_data.criminal_record_img,
        user_id=registrar_id
    )
    
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    
    logger.info(f"Driver registered: {new_driver.dr_id} by {registrar_id}")
    
    return new_driver


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all drivers"""
    drivers = db.query(Driver).offset(skip).limit(limit).all()
    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get driver by dr_id"""
    driver = db.query(Driver).filter(Driver.dr_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_data: DriverUpdate,
    current_user: dict = Depends(require_role(["admin", "crm"])),
    db: Session = Depends(get_db)
):
    """Update driver"""
    driver = db.query(Driver).filter(Driver.dr_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    if driver_data.name:
        driver.name = driver_data.name
    if driver_data.contact_no:
        driver.contact_no = driver_data.contact_no
    if driver_data.current_address:
        driver.current_address = driver_data.current_address
    if driver_data.ev_id:
        driver.ev_id = driver_data.ev_id
    
    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/drivers/{driver_id}", response_model=MessageResponse)
async def delete_driver(
    driver_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete driver"""
    driver = db.query(Driver).filter(Driver.dr_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    db.delete(driver)
    db.commit()
    return MessageResponse(message="Driver deleted successfully", success=True)


@router.get("/admin/get-drivers")
async def get_drivers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all drivers (Legacy alias)"""
    return db.query(Driver).all()
