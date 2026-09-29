from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from modules.schedule.scheduler import (
    get_future_boundaries,
    get_price_fingerprint,
    refresh_price_status,
)
from utils.log_error import logger
from utils.timezone import BUSINESS_TZ

scheduler = BackgroundScheduler(timezone=BUSINESS_TZ)

BOUNDARY_PREFIX = "price_refresh_"
WATCH_SECONDS = 10

_last_fingerprint = None


def _now():
    return datetime.now(BUSINESS_TZ).replace(tzinfo=None)


def _run_refresh():
    try:
        result = refresh_price_status()
        logger.info(f"[SCHEDULER] Price refresh done: {result}")
    except Exception:
        logger.exception("[SCHEDULER] Price refresh failed")


def _schedule_refresh_at(run_dt):
    if not run_dt or run_dt <= _now():
        return
    scheduler.add_job(
        _run_refresh,
        trigger="date",
        run_date=run_dt.replace(tzinfo=BUSINESS_TZ),
        id=f"{BOUNDARY_PREFIX}{run_dt:%Y%m%d%H%M%S}",
        replace_existing=True,
        misfire_grace_time=3600,
    )


def _rebuild_boundary_jobs():
    """Drop all start/end jobs and recreate them from the table."""
    for job in scheduler.get_jobs():
        if job.id.startswith(BOUNDARY_PREFIX):
            job.remove()

    boundaries = get_future_boundaries()
    for t in boundaries:
        _schedule_refresh_at(t)

    upcoming = min(boundaries) if boundaries else None
    logger.info(f"[SCHEDULER] {len(boundaries)} boundary job(s) scheduled; next at {upcoming}")


def _watch_price_table():
    """Runs every few seconds; acts only when PRICING_TABLE changed."""
    global _last_fingerprint
    try:
        fingerprint = get_price_fingerprint()
        if fingerprint == _last_fingerprint:
            return

        logger.info(f"[SCHEDULER] PRICING_TABLE changed {_last_fingerprint} -> {fingerprint}")
        _run_refresh()            # apply the change right away (e.g. past-dated edits)
        _rebuild_boundary_jobs()  # exact jobs for every upcoming start/end

        # The refresh may itself bump `updated`; record the post-refresh state
        _last_fingerprint = get_price_fingerprint()
    except Exception:
        logger.exception("[SCHEDULER] Price table watch failed")


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        _watch_price_table,
        trigger=IntervalTrigger(seconds=WATCH_SECONDS, timezone=BUSINESS_TZ),
        id="watch_price_table",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(BUSINESS_TZ),  # first run = startup recovery
        replace_existing=True,
    )

    # Safety net in case a boundary job is ever missed
    scheduler.add_job(
        _run_refresh,
        trigger=IntervalTrigger(minutes=15, timezone=BUSINESS_TZ),
        id="refresh_price_status",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"[SCHEDULER] Started (DB watch every {WATCH_SECONDS}s + exact start/end jobs).")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] Stopped.")