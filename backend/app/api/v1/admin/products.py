# POST   /admin/products                  Create new product
# PUT    /admin/products/:id              Update product details
# DELETE /admin/products/:id              Soft-delete (is_available = false)
# PUT    /admin/products/:id/toggle       Toggle available/unavailable
# PUT    /admin/products/:id/featured     Toggle featured flag
# POST   /admin/products/:id/images       Upload product images → Cloudinary
# DELETE /admin/products/:id/images       Remove a product image
# PUT    /admin/products/:id/stock        Update stock qty for a variant

from fastapi import APIRouter, Depends, UploadFile, File, Query

from app.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.common import SuccessResponse
from app.schemas.admin_product import (
    CreateProductRequest,
    UpdateProductRequest,
    UpdateStockRequest,
    AdminProductResponse,
)
from app.services import admin_product_service
from app.utils.helpers import success_response

router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.post("", response_model=SuccessResponse[AdminProductResponse])
async def create_product(body: CreateProductRequest, db=Depends(get_db)):
    result = await admin_product_service.create_product(db=db, data=body.model_dump())
    return success_response(data=result, message="Product created successfully")


@router.put("/{product_id}", response_model=SuccessResponse[AdminProductResponse])
async def update_product(product_id: str, body: UpdateProductRequest, db=Depends(get_db)):
    result = await admin_product_service.update_product(
        db=db, product_id=product_id, data=body.model_dump(exclude_unset=True)
    )
    return success_response(data=result, message="Product updated successfully")


@router.delete("/{product_id}", response_model=SuccessResponse[AdminProductResponse])
async def delete_product(product_id: str, db=Depends(get_db)):
    result = await admin_product_service.delete_product(db=db, product_id=product_id)
    return success_response(data=result, message="Product deactivated")


@router.put("/{product_id}/toggle", response_model=SuccessResponse[AdminProductResponse])
async def toggle_availability(product_id: str, db=Depends(get_db)):
    result = await admin_product_service.toggle_availability(db=db, product_id=product_id)
    status = "available" if result["is_available"] else "unavailable"
    return success_response(data=result, message=f"Product marked {status}")


@router.put("/{product_id}/featured", response_model=SuccessResponse[AdminProductResponse])
async def toggle_featured(product_id: str, db=Depends(get_db)):
    result = await admin_product_service.toggle_featured(db=db, product_id=product_id)
    status = "featured" if result["is_featured"] else "unfeatured"
    return success_response(data=result, message=f"Product {status}")


@router.post("/{product_id}/images", response_model=SuccessResponse[AdminProductResponse])
async def upload_images(
    product_id: str,
    files: list[UploadFile] = File(...),
    db=Depends(get_db),
):
    result = await admin_product_service.add_images(db=db, product_id=product_id, files=files)
    return success_response(data=result, message="Images uploaded successfully")


@router.delete("/{product_id}/images", response_model=SuccessResponse[AdminProductResponse])
async def remove_image(
    product_id: str,
    public_id: str = Query(..., description="Cloudinary public_id of the image to remove"),
    db=Depends(get_db),
):
    result = await admin_product_service.remove_image(db=db, product_id=product_id, public_id=public_id)
    return success_response(data=result, message="Image removed")


@router.put("/{product_id}/stock", response_model=SuccessResponse[AdminProductResponse])
async def update_stock(
    product_id: str,
    body: UpdateStockRequest,
    db=Depends(get_db),
):
    result = await admin_product_service.update_stock(
        db=db, product_id=product_id, variant_name=body.variant_name, stock=body.stock
    )
    return success_response(data=result, message="Stock updated")