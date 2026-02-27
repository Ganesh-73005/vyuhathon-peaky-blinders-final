from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from models.user import User, BusinessType, ShopLocation
from config.settings import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    shop_name: str
    business_type: str = "kirana"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = "Chennai"
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        user = await User.find_one(User.user_id == user_id)
        return user
    except JWTError:
        return None

@router.post("/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    # Check if email already exists
    existing = await User.find_one(User.email == request.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create location if provided
    location = None
    if request.latitude and request.longitude:
        location = ShopLocation(
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address or "",
            city=request.city or "Chennai"
        )
    
    # Map business type
    try:
        business_type = BusinessType(request.business_type.lower())
    except ValueError:
        business_type = BusinessType.KIRANA
    
    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        shop_name=request.shop_name,
        business_type=business_type,
        location=location,
        phone=request.phone
    )
    await user.save()
    
    # Generate token
    token = create_access_token({"user_id": user.user_id, "email": user.email})
    
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "shop_name": user.shop_name,
            "business_type": user.business_type.value,
            "location": user.location.dict() if user.location else None
        }
    }

@router.post("/login")
async def login(request: LoginRequest):
    """Login user"""
    user = await User.find_one(User.email == request.email)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Update last login
    user.last_login = datetime.now()
    await user.save()
    
    # Generate token
    token = create_access_token({"user_id": user.user_id, "email": user.email})
    
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "shop_name": user.shop_name,
            "business_type": user.business_type.value,
            "location": user.location.dict() if user.location else None,
            "language_preference": user.language_preference,
            "voice_enabled": user.voice_enabled
        }
    }

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "shop_name": user.shop_name,
        "business_type": user.business_type.value,
        "location": user.location.dict() if user.location else None,
        "language_preference": user.language_preference,
        "voice_enabled": user.voice_enabled
    }

@router.put("/preferences")
async def update_preferences(
    language: Optional[str] = None,
    voice_enabled: Optional[bool] = None,
    user: User = Depends(get_current_user)
):
    """Update user preferences"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if language:
        user.language_preference = language
    if voice_enabled is not None:
        user.voice_enabled = voice_enabled
    
    await user.save()
    
    return {"success": True, "message": "Preferences updated"}
