# app/utils/helpers/crud/url.py

from sqlalchemy.orm import Session
from app.schemas import URLBase
from app.models import URL, User
from ..keygen import create_random_key

def get_db_url_by_key(db: Session, url_key: str, user: User = None) -> URL:
    query = (
        db.query(URL)
        .filter(URL.url_key == url_key, URL.is_active)
    )
    if user:
        query.filter(URL.user_id == user.id)
    db_url = query.first()
    return db_url


def create_unique_random_key(db: Session) -> str:
    key = create_random_key()
    while get_db_url_by_key(db, key):
        key = create_random_key()
    return key


def deactivate_db_url_by_key(db: Session, url_key: str, user: User) -> URL:
    db_url = get_db_url_by_key(db, url_key, user)
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