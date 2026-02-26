"""
Complaints Router - Complaint management endpoints
Refactored for Complaints schema
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, Text, text
from sqlalchemy.orm import Session, relationship
from typing import List
from database import Base, get_db, now_karachi
from schemas import ComplaintCreate, ComplaintUpdate, ComplaintResponse, MessageResponse
import logging
from config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def serialize_complaint(complaint: "Complaints", driver_map: dict):
    driver = driver_map.get(complaint.dr_id, {})
    return {
        "complaint_id": complaint.complain_id,
        "complaint_name": complaint.title,
        "description": complaint.description,
        "driver_name": driver.get("name", ""),
        "driver_number": complaint.dr_id,
        "ev_id": driver.get("ev_id"),
        "status": complaint.status,
        "type": complaint.type,
        "complaint_register_time": complaint.complain_timestamp,
        "resolved_time": complaint.resolved_time,
        "location": complaint.location,
        "user_id": complaint.user_id,
        "dr_id": complaint.dr_id
    }

class Complaints(Base):
    """Complaints table"""
    __tablename__ = "complaints"
    
    complain_id = Column(String(50), primary_key=True)
    complain_timestamp = Column(TIMESTAMP(timezone=True), default=now_karachi)
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"))
    dr_id = Column(String(50), ForeignKey("driver.dr_id"))
    type = Column(String(50))
    description = Column(Text)
    status = Column(String(50))
    title = Column(String(255))
    resolved_time = Column(TIMESTAMP(timezone=True))
    location = Column(Text)

    # Relationships
    user = relationship("Neubolt_User", back_populates="complaints", foreign_keys=[user_id])
    driver = relationship("Driver", back_populates="complaints", foreign_keys=[dr_id])

from authentication import get_current_user, require_role

@router.post("/complaints", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register Complaint"""
    existing = db.query(Complaints).filter(Complaints.complain_id == complaint_data.complain_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint with this ID already exists"
        )
    
    new_complaint = Complaints(
        complain_id=complaint_data.complain_id,
        complain_timestamp=now_karachi(),
        user_id=complaint_data.user_id,
        dr_id=complaint_data.dr_id,
        title=complaint_data.title,
        description=complaint_data.description,
        type=complaint_data.type,
        location=complaint_data.location,
        status="Pending"
    )
    
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    
    logger.info(f"Complaint registered: {new_complaint.complain_id} by {current_user['username']}")
    
    return new_complaint


@router.get("/complaints", response_model=List[ComplaintResponse])
async def list_complaints(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all complaints"""
    complaints = db.query(Complaints).offset(skip).limit(limit).all()
    for c in complaints:
        if c.driver:
            c.driver_name = c.driver.name
    return complaints


@router.put("/complaints/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: str,
    complaint_data: ComplaintUpdate,
    current_user: dict = Depends(require_role(["admin", "crm"])),
    db: Session = Depends(get_db)
):
    """Update complaint status (Admin/CRM only)"""
    complaint = db.query(Complaints).filter(Complaints.complain_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if complaint_data.status:
        complaint.status = complaint_data.status
        if complaint_data.status == "Resolved":
            complaint.resolved_time = now_karachi()
        
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/admin/get-complaints")
async def get_complaints(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Get all complaints with UI-ready fields and summary"""
    complaints = db.query(Complaints).all()

    driver_rows = db.execute(text("SELECT dr_id, name, ev_id FROM driver")).fetchall()
    driver_map = {
        row._mapping["dr_id"]: {
            "name": row._mapping["name"],
            "ev_id": row._mapping["ev_id"]
        }
        for row in driver_rows
    }

    complaint_rows = [serialize_complaint(complaint, driver_map) for complaint in complaints]

    summary = {
        "total": len(complaint_rows),
        "active": len([c for c in complaint_rows if c["status"] in ("Pending", "Requested")]),
        "resolved": len([c for c in complaint_rows if c["status"] == "Resolved"])
    }

    return {
        "complaints": complaint_rows,
        "summary": summary
    }
