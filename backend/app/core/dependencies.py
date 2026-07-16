from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.exceptions import ForbiddenException
from app.core.security import decode_token
from app.database import get_db

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db=Depends(get_db),
):
    print("get_current_user called",credentials)
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    print("payload", payload)
    user = await db.users.find_one({"_id": ObjectId(payload.get("sub"))})
    print("user found", user)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def require_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

async def require_staff(current_user=Depends(get_current_user)):
    if current_user.get("role") not in ["admin", "staff"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return current_user



async def get_current_delivery_staff(current_user=Depends(get_current_user)):
    if current_user.get("role") != "delivery_staff":
        raise ForbiddenException("Only delivery staff can perform this action")
    return current_user


async def get_current_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") not in ("admin", "super_admin"):
        raise ForbiddenException("Admin access required")
    return current_user

async def get_current_super_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") != "super_admin":
        raise ForbiddenException("Super admin access required")
    return current_user

async def get_current_staff(current_user=Depends(get_current_user)):
    if current_user.get("role") not in ("delivery_staff", "admin", "super_admin"):
        raise ForbiddenException("Staff access required")
    return current_user


async def get_current_delivery_staff(current_user=Depends(get_current_user)):
    if current_user.get("role") != "delivery_staff":
        raise ForbiddenException("Delivery staff access required")
    return current_user