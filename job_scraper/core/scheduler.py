from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler(job_func, run_time: str) -> BackgroundScheduler:
    hour, minute = map(int, run_time.split(":"))
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_func, "cron", hour=hour, minute=minute)
    scheduler.start()
    return scheduler
