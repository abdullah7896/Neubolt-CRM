"""
Analytics Router - Dashboard and reports
Refactored for new schema
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, now_karachi
from routers.users import Neubolt_User
from routers.drivers import Driver
from routers.vehicles import EV
from routers.stations import BSS
from routers.swaps import SWAP
from datetime import datetime
from zoneinfo import ZoneInfo
from config import settings
from authentication import get_current_user

router = APIRouter()

# def get_current_time_karachi() removed as we use now_karachi from database.py

@router.get("/analytics/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    stats = {
        "total_users": db.query(Neubolt_User).count(),
        "total_drivers": db.query(Driver).count(),
        "total_vehicles": db.query(EV).count(),
        "total_stations": db.query(BSS).count(),
        "total_swaps": db.query(SWAP).count()
    }
    return stats


@router.get("/admin/get-driver_stats")
async def get_driver_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get driver statistics"""
    total_drivers = db.query(Driver).count()
    # Count drivers with allocated EV
    allocated = db.query(Driver).filter(
        Driver.ev_id != None, 
        Driver.ev_id != ""
    ).count()
    
    return {
        "total_drivers": total_drivers,
        "allocated_rickshaw_drivers": allocated
    }


@router.get("/admin/get-rikshaw_stats")
async def get_rikshaw_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get EV statistics (Renamed for compatibility but logic updated)"""
    total_vehicles = db.query(EV).count()
    return {
        "total_vehicles": total_vehicles
    }


@router.get("/admin/get-swap_stats")
async def get_swap_stats(
    period: str = "all", 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Get swap statistics"""
    query = db.query(SWAP)
    
    if period == "today":
        today = now_karachi().date()
        query = query.filter(func.date(SWAP.swap_time) == today)
    
    total_swaps = query.count()
    # Handle None result for sum
    total_amount = query.with_entities(func.sum(SWAP.transaction_amount)).scalar() or 0
    
    return {
        "total_swaps": total_swaps,
        "total_transaction_amount": total_amount
    }
