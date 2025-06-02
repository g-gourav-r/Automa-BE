from sqlalchemy import Column, Integer, String, ForeignKey, JSON, TIMESTAMP, text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.config import Base


class Template(Base):
    __tablename__ = "templates"

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("platform_users.platform_user_id"), nullable=False)
    description = Column(String(255))
    template_format = Column(JSON)
    visibility = Column(String(50), nullable=False, default='personal')
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    extraction_method = Column(String(255))
    template_name = Column(String(255), nullable=False)

    # Relationships (optional, if you'd like ORM join support)
    company = relationship("Company", back_populates="templates")
    creator = relationship("PlatformUser", back_populates="templates")
    extraction_results = relationship("TemplateExtractionResult", back_populates="template", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Template(id={self.template_id}, name={self.description}, company_id={self.company_id})>"