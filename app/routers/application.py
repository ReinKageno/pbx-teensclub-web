
from fastapi import APIRouter

from app.services.exceptions import ResourceNotFoundError


router = APIRouter()

@router.get("/not-found", tags=["Web",])
def resource_err_not_found():
    """Resource Not Found page"""
    raise ResourceNotFoundError()