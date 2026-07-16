from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.auth import ChangePasswordRequest
from app.schemas.user import (
    UpdateProfileRequest,
    AddressRequest,
    UserResponse,
)
from app.services.auth_service import get_me
from app.services import user_service
from app.utils.helpers import success_response

router = APIRouter()


# ======================
# PROFILE
# ======================

@router.get("/profile", response_model=SuccessResponse[UserResponse])
async def get_profile(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await get_me(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.put("/profile", response_model=SuccessResponse[UserResponse])
async def profile_update(
    body: UpdateProfileRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await user_service.update_profile(
        db=db,
        user_id=current_user["_id"],
        name=body.name,
        email=body.email,
        phone=body.phone,
    )
    return success_response(data=result, message="Profile updated successfully")


@router.put("/password")
async def change_password(
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    await user_service.change_password(
        db=db,
        user_id=current_user["_id"],
        current_password=body.old_password,
        new_password=body.new_password,
    )
    return success_response(message="Password changed successfully")


# ======================
# ADDRESSES
# ======================

@router.get("/addresses")
async def list_addresses(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await user_service.list_addresses(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.post("/addresses")
async def add_address(
    body: AddressRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await user_service.add_address(db=db, user_id=current_user["_id"], address=body.model_dump())
    return success_response(data=result, message="Address added successfully")


@router.put("/addresses/{address_id}")
async def update_address(
    address_id: str,
    body: AddressRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await user_service.update_address(
        db=db, user_id=current_user["_id"], address_id=address_id, address=body.model_dump()
    )
    return success_response(data=result, message="Address updated successfully")


@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    await user_service.delete_address(db=db, user_id=current_user["_id"], address_id=address_id)
    return success_response(message="Address deleted successfully")


@router.put("/addresses/{address_id}/default")
async def set_default_address(
    address_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await user_service.set_default_address(db=db, user_id=current_user["_id"], address_id=address_id)
    return success_response(data=result, message="Default address updated")