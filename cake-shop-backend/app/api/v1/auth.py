#  FILE: app/api/v1/auth.py
# PURPOSE: Auth route handlers.
#          Routes are thin — they only validate input,
#          call the service, and return the response.
#          Zero business logic here.
#
# ENDPOINTS:
#   POST /auth/register
#   POST /auth/login
#   POST /auth/google-login   (TODO: implement in future)
#   POST /auth/refresh
#   POST /auth/logout          (TODO: implement in future)
#   POST /auth/send-otp         (TODO: implement in future)
#   POST /auth/verify-otp       (TODO: implement in future)
#   POST /auth/forgot-password   (TODO: implement in future)
#   PUT  /auth/change-password
#   GET  /auth/me
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from datetime import datetime 
from app.schemas.auth import RefreshRequest, RegisterRequest, LoginRequest, GoogleLoginRequest, ChangePasswordRequest

from fastapi import APIRouter, Depends


from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.auth_service import google_login_user
from app.services.auth_service import (
    register_user,
    login_user,
    refresh_access_token,
    get_me,
    change_password,
)
from app.utils.helpers import success_response

router = APIRouter()




# ── ROUTES ───────────────────────────────────────────────────

@router.post("/register", summary="Register a new customer account")
async def register(body: RegisterRequest, db=Depends(get_db)):
    """
    Register a new customer.
    - Validates email + phone uniqueness
    - Hashes password with bcrypt
    - Creates empty rewards document
    - Returns JWT access + refresh tokens
    """
    result = await register_user(
        db=db,
        name=body.name,
        email=body.email,
        phone=body.phone,
        password=body.password,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return success_response(data=result, message="Account created successfully")


@router.post("/login", summary="Login with email or phone + password")
async def login(body: LoginRequest, db=Depends(get_db)):
    """
    Login with email OR phone number + password.
    Returns JWT access token (30 min) and refresh token (7 days).
    """
    result = await login_user(
        db=db,
        identifier=body.identifier,
        password=body.password,
    )
    return success_response(data=result, message="Login successful")


@router.post("/google-login", summary="Login with Google")
async def google_login(
    body: GoogleLoginRequest,
    db=Depends(get_db)
):
    result = await google_login_user(
        db=db,
        token=body.token
    )

    return success_response(
        data=result,
        message="Google login successful"
    )

@router.post("/refresh", summary="Get new access token using refresh token")
async def refresh(body: RefreshRequest, db=Depends(get_db)):
    """
    Called automatically by frontend when access token expires.
    Returns new access token + new refresh token.
    """
    result = await refresh_access_token(db=db, refresh_token=body.refresh_token)
    return success_response(data=result, message="Token refreshed")

@router.post("/logout", summary="Logout user")
async def logout():
    """
    Logout the current user.

    Since JWTs are stateless, logout is handled on the client by
    removing the stored access and refresh tokens.
    """
    return success_response(
        data={},
        message="Logged out successfully"
    )

@router.put("/change-password", summary="Change password (logged in)")
async def update_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Change password for the currently logged-in user."""
    await change_password(
        db=db,
        user_id=current_user["_id"],
        old_password=body.old_password,
        new_password=body.new_password,
    )
    return success_response(message="Password changed successfully")


@router.get("/me", summary="Get currently logged-in user profile")
async def me(current_user=Depends(get_current_user), db=Depends(get_db)):
    """
    Returns full profile of the authenticated user.
    Requires: Authorization: Bearer <access_token>
    """
    
    
    
    result = await get_me(db=db, user_id=current_user["_id"])
    return success_response(data=result)
