# app/schemas/url.py

from pydantic import BaseModel, Field
from typing import Optional

class URLBase(BaseModel):
    target_url: str
    password: str | None = Field(default=None, description="Optional password for URL protection.")
    custom_key: Optional[str] = None
    expiration_date: Optional[str] = None  # Accept expiration date as an ISO 8601 string

class URL(URLBase):
    is_active: bool
    clicks: int

    class Config:
        from_attributes = True

class URLInfo(BaseModel):
    target_url: str
    url_key: str
    expires_at: str | None = None

class PeekURL(BaseModel):
    target_url: str
    url_key: str

