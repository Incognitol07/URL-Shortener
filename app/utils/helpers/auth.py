# app/utils/helpers/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import (
    User
)
from ..logging_config import logger
from ..security import verify_access_token
from app.database import get_db

# OAuth2 scheme to retrieve token from Authorization header
# The `tokenUrl` specifies the endpoint for obtaining a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Dependency to retrieve and verify the current user
# This will be used to secure routes that require user authentication
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Retrieves the current authenticated user by verifying the provided token.

    Args: \n
        token (str): The authentication token passed in the Authorization header.
        db (Session): The database session to query user information.

    Raises:
        HTTPException: If token validation fails or the user cannot be found.

    Returns:
        User: The authenticated user object from the database.
    """
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        # Verify the token and retrieve user information
        payload = verify_access_token(token)
        if payload is None:
            logger.warning("Token validation failed for a request.")
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            logger.error("Invalid token payload: Missing 'sub' field.")
            raise credentials_exception

        db_user = db.query(User).filter(User.username == username).first()
        if not db_user:
            logger.warning(f"Unauthorized access attempt by user '{username}'.")
            raise credentials_exception

        logger.info(f"User (ID: {db_user.id}) authenticated successfully.")
        return db_user
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during authentication",
        )