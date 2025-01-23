# app/helpers.py

import secrets
import string
from sqlalchemy.orm import Session
from app.schemas import URLBase
from app.models import URL
from urllib.parse import urlparse
import socket

def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def create_db_url(db: Session, url: URLBase) -> URL:
    key = create_random_key()
    secret_key = create_random_key(length=8)
    db_url = URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_db_url_by_key(db: Session, url_key: str) -> URL:
    return (
        db.query(URL)
        .filter(URL.url_key == url_key, URL.is_active)
        .first()
    )

def create_unique_random_key(db: Session) -> str:
    key = create_random_key()
    while get_db_url_by_key(db, key):
        key = create_random_key()
    return key


def create_db_url(db: Session, url: URLBase) -> URL:
    key = create_unique_random_key(db)
    secret_key = f"{key}_{create_random_key(length=8)}"
    db_url = URL(
        target_url=url.target_url, url_key=key, secret_key=secret_key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url


def get_db_url_by_secret_key(db: Session, secret_key: str) -> URL:
    return (
        db.query(URL)
        .filter(URL.secret_key == secret_key, URL.is_active)
        .first()
    )

def update_db_clicks(db: Session, db_url: URL) -> URL:
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url

def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> URL:
    db_url = get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url


def is_url_valid_and_exists(target_url: str) -> bool:
    """
    Check if the domain of the target URL exists via DNS lookup.
    """
    try:
        parsed_url = urlparse(target_url)
        domain = parsed_url.netloc
        if not domain:
            return False
        # Perform DNS lookup
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False
