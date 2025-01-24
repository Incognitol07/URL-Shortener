# app/schemas/auth.py

from pydantic import BaseModel, EmailStr
from datetime import datetime


# Base schema for user-related attributes
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    username: str
    password: str


class UserLogin(UserBase):
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    joined_at: datetime

    class Config:
        from_attributes = True

class RegisterResponse(BaseModel):
    username: str
    email: EmailStr
    message: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    username: str


class DetailResponse(BaseModel):
    detail: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str


class RefreshToken(BaseModel):
    refresh_token: str 
