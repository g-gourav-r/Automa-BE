from fastapi import APIRouter

from .endpoints import (
    auth,
    extraction_results,
    invoice,
    profile,
    template_management,
    template_upload,

)

# Initialise main API router
api_router = APIRouter()

# Auth routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Invoice-related routes
api_router.include_router(invoice.router, prefix="/invoice", tags=["invoice"])

# User profile routes
api_router.include_router(profile.router, prefix="/me", tags=["profile"])

# Template management routes
api_router.include_router(template_management.router, prefix="/template", tags=["template"])

# Template upload and processing routes
api_router.include_router(template_upload.router, prefix="/template", tags=["template"])

# Extraction results routes
api_router.include_router(extraction_results.router, prefix="/template", tags=["template"])
