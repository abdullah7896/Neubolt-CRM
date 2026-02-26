"""
Centralized Authentication and Authorization Module
Handles JWT tokens, password hashing, role-based access control, 
session management, and API endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
from jose import JWTError, jwt
import bcrypt
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, Boolean, Text, ForeignKey, TIMESTAMP, or_
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from database import Base, get_db, now_karachi
from config import settings
from schemas import UserLogin, TokenResponse, MessageResponse, UserCreate

# HTTP Bearer token security
security = HTTPBearer()
router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================
# MODELS
# ============================================================

class UserSession(Base):
    """User sessions table - track active sessions"""
    __tablename__ = "user_sessions"
    
    session_id = Column(String(32), primary_key=True)
    user_id = Column(String(50), ForeignKey("neubolt_user.user_id"), nullable=False, index=True)
    user_type = Column(String(15), nullable=False)
    refresh_token_jti = Column(String(36), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=now_karachi)
    last_activity = Column(DateTime(timezone=True), nullable=False, default=now_karachi, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)

class TokenBlacklist(Base):
    """Token blacklist table - revoked JWT tokens"""
    __tablename__ = "token_blacklist"
    
    jti = Column(String(36), primary_key=True)
    token_type = Column(String(10), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=False, default=now_karachi, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_by = Column(String(50)) # UserID
    reason = Column(String(50))

# ============================================================
# TIMEZONE UTILITY
# ============================================================

def get_current_time() -> datetime:
    """Get current time with timezone, fallback to UTC if configured timezone fails"""
    try:
        tz = ZoneInfo(settings.TIMEZONE)
        return datetime.now(tz)
    except Exception:
        return datetime.now(timezone.utc)

# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

# ============================================================
# JWT TOKEN UTILITIES
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = get_current_time() + expires_delta
    else:
        expire = get_current_time() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": get_current_time(),
        "jti": secrets.token_urlsafe(16)
    })
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict) -> tuple[str, str]:
    """Create JWT refresh token"""
    to_encode = data.copy()
    jti = secrets.token_urlsafe(16)
    expire = get_current_time() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": get_current_time(),
        "jti": jti,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt, jti

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def is_token_blacklisted(jti: str, db: Session) -> bool:
    """Check if a token is blacklisted"""
    token = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    return token is not None

# ============================================================
# SESSION MANAGEMENT
# ============================================================

def generate_session_id() -> str:
    return secrets.token_hex(16)

def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and User Agent"""
    client_ip = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.client.host))
    if client_ip and ',' in client_ip:
        client_ip = client_ip.split(',')[0].strip()
    return client_ip, request.headers.get('User-Agent', '')

def create_user_session(user_id: str, user_type: str, refresh_token_jti: str, request: Request, db: Session):
    """Create new user session"""
    client_ip, user_agent = get_client_info(request)
    now = get_current_time()
    
    if settings.MAX_CONCURRENT_SESSIONS > 0:
        active_sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id, UserSession.user_type == user_type, UserSession.is_active == True
        ).count()
        
        if active_sessions >= settings.MAX_CONCURRENT_SESSIONS:
            oldest = db.query(UserSession).filter(
                UserSession.user_id == user_id, UserSession.user_type == user_type, UserSession.is_active == True
            ).order_by(UserSession.last_activity.asc()).first()
            if oldest:
                oldest.is_active = False
                revoke_refresh_token(oldest.refresh_token_jti, user_id, 'session_limit', db)
    
    session = UserSession(
        session_id=generate_session_id(), user_id=user_id, user_type=user_type, refresh_token_jti=refresh_token_jti,
        created_at=now, last_activity=now, expires_at=now + timedelta(hours=settings.SESSION_TIMEOUT_HOURS),
        is_active=True, ip_address=client_ip, user_agent=user_agent
    )
    db.add(session); db.commit(); return session

def revoke_refresh_token(jti: str, revoked_by: str, reason: str, db: Session):
    """Blacklist refresh token"""
    existing = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first()
    if existing: return existing
    
    blacklisted = TokenBlacklist(
        jti=jti, token_type='refresh', expires_at=get_current_time() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        revoked_by=revoked_by, reason=reason
    )
    db.add(blacklisted); db.commit(); return blacklisted

# ============================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> dict:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti, db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    from routers.users import Neubolt_User
    user = db.query(Neubolt_User).filter(Neubolt_User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return {"user_id": user.user_id, "username": user.username, "user_type": user.user_type, "role": user.user_type}

def require_role(allowed_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Access denied. Required roles: {', '.join(allowed_roles)}")
        return current_user
    return role_checker

# ============================================================
# AUTHENTICATION HELPERS
# ============================================================

def authenticate_user(username: str, password: str, db: Session):
    """Authenticate user by username OR user_id (CNIC)"""
    from routers.users import Neubolt_User
    user = db.query(Neubolt_User).filter(
        or_(
            Neubolt_User.username == username, 
            Neubolt_User.user_id == username,
            Neubolt_User.email == username
        )
    ).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def get_user_role_name(user_type: str) -> str:
    """Pass-through for user role"""
    return user_type

# ============================================================
# ROUTER ENDPOINTS
# ============================================================

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """User login endpoint"""
    try:
        logger.info(f"Login attempt for user: {credentials.username}")
        user = authenticate_user(credentials.username, credentials.password, db)
        if not user:
            logger.warning(f"Failed login attempt: {credentials.username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        
        role_name = get_user_role_name(user.user_type)
        token_data = {"user_id": user.user_id, "username": user.username, "user_type": user.user_type, "role": role_name}
        
        access_token = create_access_token(token_data)
        refresh_token, refresh_jti = create_refresh_token(token_data)
        
        create_user_session(user_id=user.user_id, user_type=user.user_type, refresh_token_jti=refresh_jti, request=request, db=db)
        
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, user_id=user.user_id,
            user_type=user.user_type, success=True
        )
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")

@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """User logout endpoint"""
    refresh_jti = request.headers.get('X-Refresh-Token-JTI')
    if refresh_jti:
        session = db.query(UserSession).filter(UserSession.refresh_token_jti == refresh_jti, UserSession.is_active == True).first()
        if session:
            session.is_active = False; db.commit()
        revoke_refresh_token(jti=refresh_jti, revoked_by=current_user["user_id"], reason="logout", db=db)
    return MessageResponse(message="Logged out successfully", success=True)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Refresh access token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    refresh_token = auth_header.split(' ')[1]
    try: payload = decode_token(refresh_token)
    except HTTPException: raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    if payload.get("type") != "refresh": raise HTTPException(status_code=401, detail="Invalid token type")
    if is_token_blacklisted(payload["jti"], db): raise HTTPException(status_code=401, detail="Token revoked")
    
    token_data = {"user_id": payload["user_id"], "username": payload["username"], "user_type": payload["user_type"], "role": payload["role"]}
    new_access_token = create_access_token(token_data)
    new_refresh_token = refresh_token
    
    if settings.ENABLE_TOKEN_ROTATION:
        revoke_refresh_token(payload["jti"], payload["user_id"], "rotation", db)
        new_refresh_token, new_refresh_jti = create_refresh_token(token_data)
        session = db.query(UserSession).filter(UserSession.refresh_token_jti == payload["jti"]).first()
        if session:
            session.refresh_token_jti = new_refresh_jti; db.commit()
    
    return TokenResponse(
        access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, user_id=payload["user_id"],
        user_type=payload["user_type"], success=True
    )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user
