from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from ..db.session import get_db
from ..models import User, UserRole
from ..schemas import (
    UserRegister, UserLogin, OTPRequest, OTPVerify, Token, UserResponse
)
from ..core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from ..core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return f"{random.randint(100000, 999999)}"


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with email/password or phone."""
    
    # Check if email already exists
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if phone already exists
    if user_data.phone:
        existing = db.query(User).filter(User.phone == user_data.phone).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create user
    hashed_password = None
    if user_data.password:
        hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=hashed_password,
        is_anonymous=user_data.is_anonymous,
        is_verified=True if user_data.email and user_data.password else False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email/password or phone/password."""
    
    # Try to find user by email or phone
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.phone == form_data.username)
    ).first()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/otp/request")
def request_otp(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Request OTP for phone authentication."""
    
    # Check rate limiting (simplified)
    user = db.query(User).filter(User.phone == otp_request.phone).first()
    
    if user and user.otp_expires_at:
        now = datetime.utcnow()
        if now < user.otp_expires_at and user.otp_attempts < 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another OTP"
            )
    
    # Generate OTP
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    # In production, send via Twilio
    # For demo, we'll store it and return in response
    if not user:
        user = User(phone=otp_request.phone)
        db.add(user)
    else:
        user.otp_attempts = 0
    
    user.otp_code = otp_code
    user.otp_expires_at = expires_at
    db.commit()
    
    # TODO: Send SMS via Twilio
    # twilio_client.messages.create(...)
    
    return {
        "message": "OTP sent successfully",
        "demo_otp": otp_code if settings.DEBUG else None  # Only in debug mode
    }


@router.post("/otp/verify", response_model=Token)
def verify_otp(otp_data: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP and login."""
    
    user = db.query(User).filter(User.phone == otp_data.phone).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.otp_code or not user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP requested"
        )
    
    now = datetime.utcnow()
    if now > user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
    
    user.otp_attempts += 1
    if user.otp_attempts > 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts"
        )
    
    if user.otp_code != otp_data.otp_code:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP code"
        )
    
    # OTP verified successfully
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token."""
    
    payload = decode_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
