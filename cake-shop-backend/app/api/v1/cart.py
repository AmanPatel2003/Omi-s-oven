# GET    /cart                       Get my current cart
# POST   /cart/add                   Add item to cart
# PUT    /cart/update                Update item quantity
# DELETE /cart/remove/:product_id    Remove item from cart
# DELETE /cart/clear                 Empty entire cart
# POST   /cart/apply-coupon          Apply promo code to cart
# DELETE /cart/remove-coupon         Remove applied coupon
# GET    /cart/summary               Cart total with tax, delivery fee, discount

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.cart import (
    AddCartItemRequest,
    UpdateCartItemRequest,
    ApplyCouponRequest,
    CartResponse,
    CartSummaryResponse,
)
from app.services import cart_service
from app.utils.helpers import success_response

router = APIRouter()


@router.get("", response_model=SuccessResponse[CartResponse])
async def get_cart(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await cart_service.get_cart(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.post("/add", response_model=SuccessResponse[CartResponse])
async def add_to_cart(
    body: AddCartItemRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await cart_service.add_item(
        db=db,
        user_id=current_user["_id"],
        product_id=body.product_id,
        variant_name=body.variant_name,
        qty=body.qty,
    )
    return success_response(data=result, message="Item added to cart")


@router.put("/update", response_model=SuccessResponse[CartResponse])
async def update_cart_item(
    body: UpdateCartItemRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await cart_service.update_item(
        db=db,
        user_id=current_user["_id"],
        product_id=body.product_id,
        variant_name=body.variant_name,
        qty=body.qty,
    )
    return success_response(data=result, message="Cart updated")


@router.delete("/remove/{product_id}", response_model=SuccessResponse[CartResponse])
async def remove_from_cart(
    product_id: str,
    variant_name: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await cart_service.remove_item(
        db=db, user_id=current_user["_id"], product_id=product_id, variant_name=variant_name
    )
    return success_response(data=result, message="Item removed from cart")


@router.delete("/clear", response_model=SuccessResponse[CartResponse])
async def clear_cart(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await cart_service.clear_cart(db=db, user_id=current_user["_id"])
    return success_response(data=result, message="Cart cleared")


@router.post("/apply-coupon", response_model=SuccessResponse[CartResponse])
async def apply_coupon(
    body: ApplyCouponRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await cart_service.apply_coupon(db=db, user_id=current_user["_id"], code=body.code)
    return success_response(data=result, message="Coupon applied successfully")


@router.delete("/remove-coupon", response_model=SuccessResponse[CartResponse])
async def remove_coupon(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await cart_service.remove_coupon(db=db, user_id=current_user["_id"])
    return success_response(data=result, message="Coupon removed")


@router.get("/summary", response_model=SuccessResponse[CartSummaryResponse])
async def cart_summary(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await cart_service.get_cart_summary(db=db, user_id=current_user["_id"])
    return success_response(data=result)