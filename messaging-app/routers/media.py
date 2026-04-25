import hashlib
import hmac
import time
import os
from fastapi import APIRouter, Depends, HTTPException
from schemas import CloudinarySignature
from auth import get_current_user
from models.models import User

router = APIRouter(tags=["Media"])

CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")


@router.get("/upload-signature", response_model=CloudinarySignature)
async def get_upload_signature(
    current_user: User = Depends(get_current_user),
):
    """
    Returns a signed Cloudinary upload signature so the frontend
    can upload files directly to Cloudinary without exposing your API secret.
    """
    if not CLOUDINARY_API_SECRET:
        raise HTTPException(status_code=500, detail="Cloudinary not configured")

    timestamp = int(time.time())
    params_to_sign = f"timestamp={timestamp}{CLOUDINARY_API_SECRET}"
    signature = hashlib.sha256(params_to_sign.encode()).hexdigest()

    return CloudinarySignature(
        signature=signature,
        timestamp=timestamp,
        api_key=CLOUDINARY_API_KEY,
        cloud_name=CLOUDINARY_CLOUD_NAME,
    )
