from apscheduler.schedulers.background import BackgroundScheduler

def setup_scheduler(client):
    scheduler = BackgroundScheduler(timezone="UTC")
    # cada 60 min
    scheduler.add_job(client.sync_all, "interval", minutes=60, id="sync_job", max_instances=1, coalesce=True)
    scheduler.start()
