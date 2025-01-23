# app/jobs.py

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.url import URL

def deactivate_expired_urls():
    db: Session = SessionLocal()
    try:
        expired_urls = db.query(URL).filter(
            URL.expires_at <= datetime.now(),
            URL.is_active == True
        ).all()
        for url in expired_urls:
            url.is_active = False
        db.commit()
    finally:
        db.close()
