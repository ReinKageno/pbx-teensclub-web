
import logging

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

__all__= [
    "templates",
    "logger",
]