# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    RegisterResponse,
    LoginResponse,
    DetailResponse,
    RefreshResponse,
    RefreshToken,
)
from app.models.user import User
from app.utils import (
    logger,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
)
from app.database import get_db

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=1)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Register route to create a new user account
@auth_router.post("/register", response_model=RegisterResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Attempt to register with an existing email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"Attempt to register with an existing username: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
            )

    # Hash the password before storing
    password = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        password=password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered successfully: '{new_user.username}' ({new_user.email}).")
    return {
        "username": new_user.username,
        "email": new_user.email,
        "message": "Registered successfully",
    }


# Login route for user authentication and token generation
@auth_router.post("/user/login", response_model=LoginResponse)
async def user_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not db_user.is_active:
        logger.warning(f"Login attempt for non-existent or inactive account: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )

    # Check if the user is locked out
    now = datetime.now()
    if db_user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        time_since_last_login = now - db_user.last_login

        # Reset failed attempts if lockout duration has passed
        if time_since_last_login > LOCKOUT_DURATION:
            db_user.failed_login_attempts = 0
            db.commit()
        else:
            logger.warning(f"Account locked due to multiple failed login attempts: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked. Try again later.",
            )

    # Verify the password
    if not verify_password(user.password, db_user.password):
        db_user.failed_login_attempts += 1
        db_user.last_login = now  # Update last login to track failed attempts timing
        db.commit()
        logger.warning(f"Failed login attempt for email: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )

    # Reset failed login attempts after successful login
    db_user.failed_login_attempts = 0
    db_user.last_login = now
    db.commit()

    # Generate tokens
    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})

    logger.info(f"User '{db_user.id}' logged in successfully.")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username,
        "role": "admin" if db_user.is_admin else "user"
    }


# Token refresh route
@auth_router.post("/refresh-token", response_model=RefreshResponse)
async def get_refresh_token(token: RefreshToken, db: Session = Depends(get_db)):
    payload = verify_refresh_token(token.refresh_token)
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload"
        )

    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}


# Protected route for testing
@auth_router.get("/protected-route", response_model=DetailResponse)
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"detail": f"Hello, {current_user.username}! You have access to this protected route."}


# Login route for user authentication and token generation
@auth_router.post("/login", include_in_schema=False)
async def login_for_oauth_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )

    db_user.last_login = datetime.now()
    db.commit()
    # Create and return the JWT access token
    access_token = create_access_token(data={"sub": db_user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
