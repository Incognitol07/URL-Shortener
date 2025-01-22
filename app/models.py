# app/models.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from app.database import Base

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False)
    url_key = Column(String, unique=True, index=True, nullable=False)
    secret_key = Column(String, unique=True, nullable=False)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Expiration date
    password = Column(String, nullable=True)  # New column for hashed password
