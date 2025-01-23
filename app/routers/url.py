# app/routers/url.py

import qrcode
from io import BytesIO
from validators import url as validate_url
from fastapi import( 
    APIRouter, 
    HTTPException, 
    status, 
    Depends, 
    BackgroundTasks
    )
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import URL
from app.config import settings
from app.schemas import (
    URLBase, 
    URLInfo, 
    PeekURL
    )
from app.utils import (
    create_unique_random_key,
    get_db_url_by_key,
    get_db_url_by_secret_key,
    deactivate_db_url_by_secret_key,
    is_url_valid_and_exists,
    update_clicks_in_background,
    hash_password, 
    verify_password
)

templates = Jinja2Templates(directory="app/templates")

url_router = APIRouter(tags=["URLs"])

@url_router.get("/admin")
def get_admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@url_router.post("/url", response_model=URLInfo)
def create_url(
    url_sent: URLBase,
    db: Session = Depends(get_db)
):
    if not validate_url(url_sent.target_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The provided URL is not valid."
        )

    # Check for custom key uniqueness
    if url_sent.custom_key and get_db_url_by_key(db, url_sent.custom_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom key already in use."
        )
    key = url_sent.custom_key or create_unique_random_key(db)

    # Validate and parse expiration date
    expires_at = None
    if url_sent.expiration_date:
        try:
            expires_at = datetime.fromisoformat(url_sent.expiration_date)
            if expires_at <= datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Expiration date must be in the future."
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid expiration date format."
            )

    hashed_password = hash_password(url_sent.password) if url_sent.password else None
    db_url = URL(
        target_url=url_sent.target_url,
        url_key=key,
        secret_key=f"{key}_{create_unique_random_key(db)}",
        expires_at=expires_at,
        password=hashed_password
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    db_url.expires_at = db_url.expires_at.ctime() if db_url.expires_at else None
    return db_url


@url_router.get("/{url_key}")
def forward_to_target_url(
    url_key: str,
    request: Request,
    background_tasks: BackgroundTasks,
    password: str | None = None,
    db: Session = Depends(get_db),
):
    db_url = get_db_url_by_key(db, url_key)
    if not db_url or not db_url.is_active:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message":f"URL with key '{url_key}' not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if db_url.expires_at and db_url.expires_at <= datetime.now():
        return templates.TemplateResponse(
            "expired.html",
            {"request": request},
            status_code=status.HTTP_410_GONE,
        )

    if db_url.password:
        if not password:
            return templates.TemplateResponse(
                "password.html",
                {
                    "request": request,
                    "url_key": db_url.url_key
                }
            )
        if not verify_password(password, db_url.password):
            return templates.TemplateResponse(
                "password.html",
                {
                    "request": request,
                    "url_key": db_url.url_key,
                    "error_message": "Incorrect password"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

    # Check if the target URL's domain exists
    if not is_url_valid_and_exists(db_url.target_url):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": "The domain of the target URL does not exist."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    background_tasks.add_task(update_clicks_in_background, db, db_url.id)
    return RedirectResponse(db_url.target_url)


@url_router.get("/peek/{url_key}", response_model=PeekURL)
def peek_url(
    url_key: str,
    request: Request,
    db: Session = Depends(get_db)
    ):
    db_url = get_db_url_by_key(db, url_key)
    if not db_url or db_url.password:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": f"URL Key {url_key} not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    db_url.expires_at = db_url.expires_at.ctime() if db_url.expires_at else None
    return db_url


@url_router.get("/admin/{secret_key}", response_model=URLInfo, name="Admin Info")
def get_url_info(
    secret_key: str, 
    request: Request,
    db: Session = Depends(get_db)
    ):
    db_url = get_db_url_by_secret_key(db, secret_key)
    if not db_url:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": f"URL with secret key {secret_key} not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    db_url.expires_at = db_url.expires_at.ctime() if db_url.expires_at else None
    return db_url


@url_router.delete("/admin/{secret_key}")
def delete_url(secret_key: str, db: Session = Depends(get_db)):
    db_url = deactivate_db_url_by_secret_key(db, secret_key)
    if not db_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with secret key {secret_key} not found."
        )
    message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
    return {"detail": message}


# New endpoint to generate QR code
@url_router.get("/{url_key}/qr", response_class=StreamingResponse)
def generate_qr_code(url_key: str, db: Session = Depends(get_db)):
    """
    Generate and return a QR code for the shortened URL.
    """
    db_url = get_db_url_by_key(db, url_key)
    if not db_url or not db_url.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL Key {url_key} not found or inactive."
        )
    if db_url.expires_at and db_url.expires_at <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The URL has expired."
        )

    # Generate the full shortened URL
    base_url = settings.DOMAIN  # Replace with your service's domain
    full_url = f"{base_url}/{url_key}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert the image to a bytes stream
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    # Return the image as a streaming response
    return StreamingResponse(
        img_byte_arr,
        media_type="image/png",
        headers={"Content-Disposition": f"filename={url_key}_qrcode.png"}
    )
