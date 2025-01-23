# app/models/url.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False)
    url_key = Column(String, unique=True, index=True, nullable=False)
    clicks = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    password = Column(String, nullable=True)  
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="urls")
