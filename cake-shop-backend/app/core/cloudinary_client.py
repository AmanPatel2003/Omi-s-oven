import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import BadRequestException

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


async def upload_image(file: UploadFile, folder: str) -> dict:
    """
    Uploads a single image to Cloudinary under the given folder.
    Returns {"url": ..., "public_id": ...} — store both; public_id is
    required to delete the image later (URL alone isn't enough).
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise BadRequestException("Only JPEG, PNG, or WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise BadRequestException("Image must be under 5MB")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=folder,
            resource_type="image",
            transformation=[{"quality": "auto", "fetch_format": "auto"}],  # auto-optimize
        )
    except Exception as e:
        raise BadRequestException(f"Image upload failed: {str(e)}")

    return {"url": result["secure_url"], "public_id": result["public_id"]}


def delete_image(public_id: str) -> bool:
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False