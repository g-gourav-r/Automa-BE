from fastapi import APIRouter
from .endpoints import invoice, auth

api_router = APIRouter()

# Include the auth router (signup/login)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include the other API endpoints (e.g., invoice routes)
api_router.include_router(invoice.router, prefix="/invoice", tags=["invoice"])
