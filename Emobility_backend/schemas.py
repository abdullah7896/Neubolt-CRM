"""
Pydantic Schemas - Neubolt Backend (New Schema Refactored)
Refactored to match new SQL schema with snake_case column names.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# ============================================================
# AUTHENTICATION SCHEMAS
# ============================================================

class UserLogin(BaseModel):
    """Login request schema"""
    username: str = Field(..., description="Username or user_id (CNIC)")
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: str
    user_type: str
    success: bool = True

class TokenRefresh(BaseModel):
    """Refresh token request"""
    refresh_token: str

# ============================================================
# USER SCHEMAS (neubolt_user)
# ============================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100, alias="name")
    contact_no: Optional[str] = Field(None, pattern=r"^03\d{9}$", description="03XXXXXXXXX", alias="phone")
    email: str
    user_type: str = Field(..., description="admin, crm, maintenance, operator_head, operator", alias="role")
    address: Optional[str] = None
    dob: Optional[date] = None
    registration_date: Optional[date] = Field(None, alias="created_at")
    registered_by_user_id: Optional[str] = None

    class Config:
        populate_by_name = True

class UserCreate(UserBase):
    """Create user request"""
    user_id: Optional[str] = Field(None, pattern=r"^\d{13}$", description="CNIC", alias="userId")
    password: str = Field(..., min_length=6)
    user_image: Optional[str] = None

    class Config:
        populate_by_name = True

class UserUpdate(BaseModel):
    """Update user request"""
    display_name: Optional[str] = Field(None, alias="name")
    contact_no: Optional[str] = Field(None, alias="phone")
    email: Optional[str] = None
    password: Optional[str] = None
    address: Optional[str] = None
    user_image: Optional[str] = None

    class Config:
        populate_by_name = True

class UserResponse(UserBase):
    """User response schema"""
    user_id: str = Field(..., alias="userId")
    user_image: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True

class UserListResponse(BaseModel):
    """Response wrapper for list of users"""
    users: List[UserResponse]
    total: int
    success: bool = True

# ============================================================
# DRIVER SCHEMAS
# ============================================================

class DriverBase(BaseModel):
    """Base driver schema"""
    name: Optional[str] = None
    contact_no: Optional[str] = None
    dob: Optional[date]
    city: Optional[str] = None
    current_address: Optional[str] = None

class DriverCreate(DriverBase):
    """Create driver request"""
    dr_id: str = Field(..., pattern=r"^\d{13}$", description="CNIC")
    user_id: str # Registrar
    name: str
    contact_no: str
    city: str
    current_address: str
    ev_id: Optional[str] = None
    driver_image: Optional[str] = None
    cnic_front: Optional[str] = None
    cnic_back: Optional[str] = None
    linsence_img: Optional[str] = None
    criminal_record_img: Optional[str] = None

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    contact_no: Optional[str] = None
    current_address: Optional[str] = None
    ev_id: Optional[str] = None

class DriverResponse(DriverBase):
    """Driver response schema"""
    dr_id: str
    ev_id: Optional[str]
    registration_date: Optional[datetime]
    driver_image: Optional[str]
    cnic_front: Optional[str]
    cnic_back: Optional[str]
    linsence_img: Optional[str]
    criminal_record_img: Optional[str]
    user_id: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# EV SCHEMAS (ev)
# ============================================================

class EVBase(BaseModel):
    """Base EV schema"""
    manufacturer: str
    category: str
    chasis_num: str
    city: str

class EVCreate(EVBase):
    """Create EV request"""
    ev_id: str # MAC Address or Reg Num
    user_id: Optional[str] = None
    vehicle_image: Optional[str] = None
    registry_image: Optional[str] = None

class EVUpdate(BaseModel):
    city: Optional[str] = None
    vehicle_image: Optional[str] = None
    registry_image: Optional[str] = None

class EVResponse(EVBase):
    """EV response schema"""
    ev_id: str
    registration_datetime: Optional[datetime]
    vehicle_image: Optional[str]
    registry_image: Optional[str]
    user_id: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# BATTERY SCHEMAS
# ============================================================

class BatteryBase(BaseModel):
    """Base battery schema"""
    company: str
    model: str
    import_date: Optional[date]

class BatteryCreate(BatteryBase):
    """Create battery request"""
    battery_id: str
    user_id: str

class BatteryResponse(BatteryBase):
    """Battery response schema"""
    battery_id: str
    registration_date: Optional[date]
    user_id: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# BSS SCHEMAS (bss)
# ============================================================

class BSSBase(BaseModel):
    """Base BSS schema"""
    station_name: str
    location: str
    city: str

class BSSCreate(BSSBase):
    """Create BSS request"""
    bss_id: str
    user_id: str

class BSSResponse(BSSBase):
    """BSS response schema"""
    bss_id: str
    registration_date: Optional[date]
    user_id: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# SWAP SCHEMAS
# ============================================================

class SWAPCreate(BaseModel):
    """Create swap request"""
    swap_id: str
    bss_id: str
    ev_id: str
    old_battery_id_1: str
    old_battery_id_2: str
    old_battery_id_3: str
    new_battery_id_1: str
    new_battery_id_2: str
    new_battery_id_3: str
    transaction_amount: float
    transaction_energy: float

class SWAPResponse(BaseModel):
    """Swap response schema"""
    swap_id: str
    swap_time: datetime
    bss_id: str
    ev_id: str
    transaction_amount: float
    transaction_energy: float
    
    class Config:
        from_attributes = True

# ============================================================
# COMPLAINT SCHEMAS
# ============================================================

class ComplaintCreate(BaseModel):
    """Create complaint request"""
    complain_id: str
    user_id: str
    dr_id: str
    title: str
    description: str
    type: str
    location: Optional[str] = None

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    resolved_time: Optional[datetime] = None

class ComplaintResponse(BaseModel):
    """Complaint response schema"""
    complain_id: str
    complain_timestamp: datetime
    user_id: str
    dr_id: str
    driver_name: Optional[str] = None
    title: str
    description: str
    type: str
    status: Optional[str]
    resolved_time: Optional[datetime]
    location: Optional[str]
    
    class Config:
        from_attributes = True

# ============================================================
# TELEMETRY SCHEMAS
# ============================================================

class GPSResponse(BaseModel):
    gps_id: str
    ev_id: str
    latitude: float
    longitude: float
    gps_timestamp: datetime
    class Config:
        from_attributes = True

class EVDataResponse(BaseModel):
    id: int
    ev_id: str
    log_time: datetime
    
    ev_current: Optional[float]
    ev_voltage: Optional[float]
    ev_mcu_rpm: Optional[float]
    distance: Optional[float]
    e_mcu_tempflag: Optional[float]
    
    # Slot 1
    s1_battery_id: Optional[str]
    s1_temp: Optional[float]
    s1_soc: Optional[float]
    s1_soh: Optional[float]
    s1_vol: Optional[float]
    s1_curr: Optional[float]

    # Slot 2
    s2_battery_id: Optional[str]
    s2_temp: Optional[float]
    s2_soc: Optional[float]
    s2_soh: Optional[float]
    s2_vol: Optional[float]
    s2_curr: Optional[float]

    # Slot 3
    s3_battery_id: Optional[str]
    s3_temp: Optional[float]
    s3_soc: Optional[float]
    s3_soh: Optional[float]
    s3_vol: Optional[float]
    s3_curr: Optional[float]

    class Config:
        from_attributes = True

class BSSDataResponse(BaseModel):
    id: int
    bss_id: str
    log_time: datetime

    # Slot 1
    s1_battery_id: Optional[str]
    s1_temp: Optional[float]
    s1_soc: Optional[float]
    s1_soh: Optional[float]
    s1_vol: Optional[float]
    s1_curr: Optional[float]
    s1_cycle_cnt: Optional[int]
    s1_rem_cap: Optional[float]
    s1_full_cap: Optional[float]
    s1_chr_vol: Optional[float]
    s1_chr_curr: Optional[float]
    s1_status: Optional[str]
    s1_b_errorflags: Optional[str]
    s1_c_errorflags: Optional[str]

    # Slot 2
    s2_battery_id: Optional[str]
    s2_temp: Optional[float]
    s2_soc: Optional[float]
    s2_soh: Optional[float]
    s2_vol: Optional[float]
    s2_curr: Optional[float]
    s2_cycle_cnt: Optional[int]
    s2_rem_cap: Optional[float]
    s2_full_cap: Optional[float]
    s2_chr_vol: Optional[float]
    s2_chr_curr: Optional[float]
    s2_status: Optional[str]
    s2_b_errorflags: Optional[str]
    s2_c_errorflags: Optional[str]

    # Slot 3
    s3_battery_id: Optional[str]
    s3_temp: Optional[float]
    s3_soc: Optional[float]
    s3_soh: Optional[float]
    s3_vol: Optional[float]
    s3_curr: Optional[float]
    s3_cycle_cnt: Optional[int]
    s3_rem_cap: Optional[float]
    s3_full_cap: Optional[float]
    s3_chr_vol: Optional[float]
    s3_chr_curr: Optional[float]
    s3_status: Optional[str]
    s3_b_errorflags: Optional[str]
    s3_c_errorflags: Optional[str]

    class Config:
        from_attributes = True

# ============================================================
# COMMON
# ============================================================

class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    success: bool = False
