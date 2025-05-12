# models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.config import Base

class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True, nullable=False)
    industry = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    platform_users = relationship("PlatformUser", back_populates="company")

class PlatformUser(Base):
    __tablename__ = "platform_users"
    
    platform_user_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"))
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    roles = Column(String)  # A simple role system, e.g., 'admin', 'user'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    company = relationship("Company", back_populates="platform_users")
    credentials = relationship("UserCredentials", uselist=False, back_populates="user")

class UserCredentials(Base):
    __tablename__ = "user_credentials"
    
    user_credential_id = Column(Integer, primary_key=True, index=True)
    platform_user_id = Column(Integer, ForeignKey("platform_users.platform_user_id"), unique=True)
    password_hash = Column(String)
    salt = Column(String)  # Optional, if you decide to use salt separately from password
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("PlatformUser", back_populates="credentials")
