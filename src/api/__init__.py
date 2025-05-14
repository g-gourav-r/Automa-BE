from fastapi import APIRouter
from .endpoints import invoice, auth, profile, template

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(invoice.router, prefix="/invoice", tags=["invoice"])

api_router.include_router(profile.router, prefix="/me", tags=["profile"]) 

api_router.include_router(template.router, prefix="/template", tags=["template"]) 