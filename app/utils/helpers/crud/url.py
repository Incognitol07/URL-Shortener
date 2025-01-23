# app/helpers/crud.py

from sqlalchemy.orm import Session
from app.schemas.url import URLBase
from app.models.url import URL
from ..keygen import create_random_key

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

def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> URL:
    db_url = get_db_url_by_secret_key(db, secret_key)
    if db_url:
        db_url.is_active = False
        db.commit()
        db.refresh(db_url)
    return db_url

def update_clicks_in_background(db: Session, url_id: int):
    with db.begin():
        db_url = db.query(URL).filter(URL.id == url_id).first()
        if db_url:
            db_url.clicks += 1
            db.add(db_url)