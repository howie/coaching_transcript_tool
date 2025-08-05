"""
Google OAuth authentication routes.

處理 Google OAuth 2.0 登入流程和 JWT token 管理。
"""
from datetime import datetime, timedelta
from typing import Optional
import httpx
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..core.config import settings
from ..core.database import get_db
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth 2.0 endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def create_access_token(user_id: str) -> str:
    """建立 Access Token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """建立 Refresh Token"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@router.get("/google/login")
async def google_login(redirect_uri: Optional[str] = None):
    """
    開始 Google OAuth 登入流程
    
    將用戶重定向到 Google 登入頁面。
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID."
        )
    
    # 如果沒有提供 redirect_uri，使用預設值
    if not redirect_uri:
        # 在生產環境使用完整的 URL
        if settings.ENVIRONMENT == "production":
            redirect_uri = f"https://api.doxa.com.tw{settings.API_V1_STR}/auth/google/callback"
        else:
            redirect_uri = f"http://localhost:8000{settings.API_V1_STR}/auth/google/callback"
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    # 建立授權 URL
    auth_url = f"{GOOGLE_AUTH_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for security"),
    db: Session = Depends(get_db)
):
    """
    處理 Google OAuth 回調
    
    接收 Google 返回的授權碼，交換 access token，
    獲取用戶資訊，並建立或更新用戶記錄。
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured properly."
        )
    
    # 1. 使用授權碼交換 access token
    redirect_uri = f"https://api.doxa.com.tw{settings.API_V1_STR}/auth/google/callback" \
        if settings.ENVIRONMENT == "production" \
        else f"http://localhost:8000{settings.API_V1_STR}/auth/google/callback"
    
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        # 獲取 access token
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {token_response.text}"
            )
        
        tokens = token_response.json()
        google_access_token = tokens.get("access_token")
        
        # 2. 使用 access token 獲取用戶資訊
        headers = {"Authorization": f"Bearer {google_access_token}"}
        userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail="Failed to get user information from Google"
            )
        
        google_user = userinfo_response.json()
    
    # 3. 查找或建立用戶
    email = google_user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")
    
    # 查找現有用戶
    stmt = select(User).where(User.email == email)
    existing_user = db.execute(stmt).scalar_one_or_none()
    
    if existing_user:
        # 更新現有用戶資訊
        existing_user.google_id = google_user.get("id")
        existing_user.avatar_url = google_user.get("picture")
        existing_user.updated_at = datetime.utcnow()
        db.commit()
        user = existing_user
    else:
        # 建立新用戶
        user = User(
            email=email,
            name=google_user.get("name", email.split("@")[0]),
            google_id=google_user.get("id"),
            avatar_url=google_user.get("picture"),
            email_verified=google_user.get("verified_email", False),
            plan="FREE"  # 新用戶預設為免費方案
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 4. 生成 JWT tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # 5. 重定向到前端，帶上 tokens
    # 在生產環境中，應該使用更安全的方式傳遞 tokens（如設置 HttpOnly cookies）
    frontend_url = "https://coachly.doxa.com.tw" if settings.ENVIRONMENT == "production" else "http://localhost:3000"
    redirect_url = f"{frontend_url}/dashboard?access_token={access_token}&refresh_token={refresh_token}"
    
    return RedirectResponse(url=redirect_url)

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    使用 Refresh Token 獲取新的 Access Token
    """
    try:
        # 驗證 refresh token
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 確認用戶存在
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 生成新的 access token
        new_access_token = create_access_token(str(user.id))
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 依賴注入：獲取 Authorization header
from fastapi import Header

async def get_authorization_header(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    return authorization

# 依賴注入：獲取當前用戶
async def get_current_user_dependency(
    authorization: str = Depends(get_authorization_header),
    db: Session = Depends(get_db)
) -> User:
    """
    從 JWT token 中獲取當前用戶
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 獲取用戶
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def get_current_user(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    獲取當前登入用戶資訊
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "monthly_minutes_used": current_user.monthly_minutes_used,
        "created_at": current_user.created_at
    }
