# GET    /rewards                    My points balance + current tier
# GET    /rewards/transactions       Points earning/redemption history
# GET    /rewards/tiers              Tier benefits info
# POST   /rewards/redeem             Apply points at checkout

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.schemas.reward import (
    RewardBalanceResponse,
    TransactionListResponse,
    TiersResponse,
    RedeemPointsRequest,
    RedeemResponse,
)
from app.services import reward_service
from app.utils.helpers import success_response

router = APIRouter()


@router.get("/tiers", response_model=SuccessResponse[TiersResponse])
async def get_tiers():
    # static info — no auth needed, safe to declare before /{param} routes anyway (there are none here)
    result = reward_service.get_tiers_info()
    return success_response(data=result)


@router.get("", response_model=SuccessResponse[RewardBalanceResponse])
async def get_balance(current_user=Depends(get_current_user), db=Depends(get_db)):
    result = await reward_service.get_balance(db=db, user_id=current_user["_id"])
    return success_response(data=result)


@router.get("/transactions", response_model=SuccessResponse[TransactionListResponse])
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await reward_service.list_transactions(db=db, user_id=current_user["_id"], page=page, limit=limit)
    return success_response(data=result)


@router.post("/redeem", response_model=SuccessResponse[RedeemResponse])
async def redeem_points(
    body: RedeemPointsRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    result = await reward_service.redeem_points(db=db, user_id=current_user["_id"], points=body.points)
    return success_response(data=result, message="Points applied to cart")