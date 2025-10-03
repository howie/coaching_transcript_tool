"""
Google OAuth authentication routes.

處理 Google OAuth 2.0 登入流程和 JWT token 管理。
"""

from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

import httpx
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.models.user import UserPlan
from ...models.user import User  # Infrastructure model for SQLAlchemy queries

router = APIRouter(tags=["authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    recaptcha_token: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    plan: UserPlan
    auth_provider: Optional[str] = None
    google_connected: Optional[bool] = None
    preferences: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Google OAuth 2.0 endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(user_id: str) -> str:
    """建立 Access Token"""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """建立 Refresh Token"""
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def verify_recaptcha(token: str, remote_ip: str) -> tuple[bool, float, str]:
    """Verify reCAPTCHA token with Google's API"""
    if not settings.RECAPTCHA_ENABLED:
        return True, 1.0, "signup"  # Skip verification if disabled

    if not token:
        return False, 0.0, ""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": settings.RECAPTCHA_SECRET,
                    "response": token,
                    "remoteip": remote_ip,
                },
                timeout=5,
            )

        if resp.status_code != 200:
            print(f"reCAPTCHA verification failed with status {resp.status_code}")
            return False, 0.0, ""

        data = resp.json()
        success = data.get("success", False)
        score = data.get("score", 0.0)
        action = data.get("action", "")

        # Log verification result for debugging
        print(
            f"reCAPTCHA verification: success={success}, score={score}, action={action}"
        )

        return success, score, action
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        # Return failure but don't block signup if reCAPTCHA service is down
        return False, 0.0, ""


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Verify reCAPTCHA if enabled
    if settings.RECAPTCHA_ENABLED:
        # Get client IP
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Verify reCAPTCHA token
        success, score, action = await verify_recaptcha(
            user.recaptcha_token or "", client_ip
        )

        # Check verification result
        if not success or (action and action != "signup"):
            raise HTTPException(status_code=403, detail="Failed Human Verification")

        # Check score threshold
        if score < settings.RECAPTCHA_MIN_SCORE:
            print(
                f"reCAPTCHA score {score} below threshold "
                f"{settings.RECAPTCHA_MIN_SCORE}"
            )
            raise HTTPException(status_code=403, detail="Failed Human Verification")

    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/google/login")
async def google_login(redirect_uri: Optional[str] = None):
    """
    開始 Google OAuth 登入流程

    將用戶重定向到 Google 登入頁面。
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID.",
        )

    # 如果沒有提供 redirect_uri，使用預設值
    if not redirect_uri:
        # 在生產環境使用完整的 URL
        if settings.ENVIRONMENT == "production":
            redirect_uri = (
                f"https://api.doxa.com.tw{settings.API_V1_STR}/auth/google/callback"
            )
        else:
            redirect_uri = (
                f"http://localhost:8000{settings.API_V1_STR}/auth/google/callback"
            )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    # 建立授權 URL
    auth_url = f"{GOOGLE_AUTH_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for security"),
    db: Session = Depends(get_db),
):
    """
    處理 Google OAuth 回調

    接收 Google 返回的授權碼，交換 access token，
    獲取用戶資訊，並建立或更新用戶記錄。
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, detail="Google OAuth not configured properly."
        )

    # 1. 使用授權碼交換 access token
    redirect_uri = (
        f"https://api.doxa.com.tw{settings.API_V1_STR}/auth/google/callback"
        if settings.ENVIRONMENT == "production"
        else f"http://localhost:8000{settings.API_V1_STR}/auth/google/callback"
    )

    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    # 設定 httpx 客戶端超時和重試
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 獲取 access token
            token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Failed to exchange authorization code: {token_response.text}"
                    ),
                )

            tokens = token_response.json()
            google_access_token = tokens.get("access_token")

            if not google_access_token:
                raise HTTPException(
                    status_code=400,
                    detail="No access token received from Google",
                )

            # 2. 使用 access token 獲取用戶資訊
            headers = {"Authorization": f"Bearer {google_access_token}"}
            userinfo_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)

            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user information from Google",
                )

            google_user = userinfo_response.json()

    except httpx.ConnectTimeout:
        raise HTTPException(
            status_code=503,
            detail=("Unable to connect to Google services. Please try again later."),
        )
    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=503,
            detail=(
                "Google services took too long to respond. Please try again later."
            ),
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Network error while connecting to Google: {str(e)}",
        )

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
        existing_user.updated_at = datetime.now(UTC)
        db.commit()
        user = existing_user
    else:
        # 建立新用戶
        user = User(
            email=email,
            name=google_user.get("name", email.split("@")[0]),
            google_id=google_user.get("id"),
            avatar_url=google_user.get("picture"),
            plan=UserPlan.FREE,  # 新用戶預設為免費方案
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. 生成 JWT tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # 5. 重定向到前端，帶上 tokens
    # 在生產環境中，應該使用更安全的方式傳遞 tokens（如設置 HttpOnly cookies）
    # Use configured FRONTEND_URL for better multi-domain support
    # Auto-detects production URL if not explicitly configured
    frontend_url = settings.get_frontend_url.rstrip("/")
    redirect_url = (
        f"{frontend_url}/dashboard?access_token={access_token}"
        f"&refresh_token={refresh_token}"
    )

    return RedirectResponse(url=redirect_url)


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    使用 Refresh Token 獲取新的 Access Token
    """
    try:
        # 驗證 refresh token
        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 確認用戶存在
        stmt = select(User).where(User.id == UUID(user_id))
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 生成新的 access token
        new_access_token = create_access_token(str(user.id))

        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# 依賴注入：獲取 Authorization header


async def get_authorization_header(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    return authorization


# 依賴注入：獲取當前用戶
async def get_current_user_dependency(
    authorization: str = Depends(get_authorization_header),
    db: Session = Depends(get_db),
) -> User:
    """
    從 JWT token 中獲取當前用戶

    如果 TEST_MODE=true，則返回測試用戶而不需要認證
    """
    # TEST_MODE: 如果啟用測試模式，返回測試用戶
    if settings.TEST_MODE:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("🚨 TEST_MODE 已啟用 - 跳過認證檢查，使用測試用戶")

        # 查找或創建測試用戶
        test_email = "test@example.com"
        stmt = select(User).where(User.email == test_email)
        test_user = db.execute(stmt).scalar_one_or_none()

        if not test_user:
            # 創建測試用戶
            test_user = User(
                email=test_email,
                name="Test User",
                plan=UserPlan.PRO,  # 給予 PRO 權限以便測試所有功能
                hashed_password="",  # 測試用戶不需要密碼
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info(f"📝 創建測試用戶: {test_email}")

        return test_user

    # 正常認證流程
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 獲取用戶
        stmt = select(User).where(User.id == UUID(user_id))
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_dependency),
):
    """
    獲取當前登入用戶資訊
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=(
            current_user.plan.value
            if hasattr(current_user.plan, "value")
            else current_user.plan
        ),
        auth_provider=current_user.auth_provider,
        google_connected=current_user.google_connected,
        preferences=current_user.get_preferences(),
    )
