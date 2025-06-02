from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


# ===============================
# Template Metadata Schemas
# ===============================

class TemplateResponse(BaseModel):
    """Schema for returning complete template metadata."""
    template_id: int
    company_id: int
    created_by_user_id: int
    description: Optional[str] = None  # Nullable description
    template_name: str
    template_format: dict  # JSON type maps to Python dict
    visibility: str
    created_at: datetime
    updated_at: datetime
    extraction_method: Optional[str] = None  # Nullable extraction method


class TemplateListResponse(BaseModel):
    """Schema for listing available templates (summary view)."""
    template_id: int
    template_name: str
    description: Optional[str] = None


class TemplateContentResponse(BaseModel):
    """Schema for retrieving the content of a specific template."""
    template_id: int
    template_format: Dict[str, Any] = Field(..., description="The JSON content of the template.")
    template_description: Optional[str] = Field(
        None, description="Optional description of the template."
    )

    model_config = ConfigDict(from_attributes=True)


# ===============================
# Extraction Results Schemas
# ===============================

class TemplateExtractionResultCreate(BaseModel):
    """Schema for creating a new template extraction result."""
    template_id: int
    source_file_name: Optional[str] = None
    parsed_data: Dict


class TemplateExtractionResultResponse(BaseModel):
    """Schema for returning a saved extraction result."""
    result_id: int
    template_id: int
    source_file_name: Optional[str]
    parsed_data: Dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)