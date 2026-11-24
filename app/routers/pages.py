from fastapi import APIRouter, Request, status
from starlette.exceptions import HTTPException as SHTTPException

from app import templates, logger
from app.services.exceptions import ResourceUnderConstructionError


router = APIRouter(tags=["Web", "Page"])

@router.get("/")
def homepage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@router.get("/community")
def page_community(request: Request):
    logger.info("'community' page is unavailable")
    raise ResourceUnderConstructionError()

@router.get("/about")
def page_community(request: Request):
    logger.info("'about' page is unavailable")
    raise ResourceUnderConstructionError()