# app/background_jobs/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .jobs import deactivate_expired_urls

scheduler = BackgroundScheduler()

def start_scheduler():
    # Add jobs to the scheduler
    scheduler.add_job(deactivate_expired_urls, IntervalTrigger(hours=1))
    print("Starting the scheduler...")
    # Start the scheduler
    scheduler.start()
