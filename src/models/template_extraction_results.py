from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.config import Base

class TemplateExtractionResult(Base):
    __tablename__ = "template_extraction_results"

    result_id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.template_id"), nullable=False)
    source_file_name = Column(String, nullable=True)  # optional: the file you parsed
    parsed_data = Column(JSON, nullable=False)  # this is your dynamic key-value output
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to parent template
    template = relationship("Template", back_populates="extraction_results")

    def __repr__(self):
        return f"<TemplateExtractionResult(id={self.result_id}, template_id={self.template_id})>"
    
