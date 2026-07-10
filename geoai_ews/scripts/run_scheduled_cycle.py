"""
Scheduler entry point — runs the full 10-step advisory workflow for every
registered plot, on a recurring schedule (e.g. weekly, matching Phase 1 of
the roadmap).

Usage:
    python scripts/run_scheduled_cycle.py --once
    python scripts/run_scheduled_cycle.py --daemon   # runs continuously via APScheduler
"""
from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from db.database import SessionLocal, init_db
from db.models import Plot
from ews.orchestrator import AdvisoryOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("scheduler")


def run_all_plots_once() -> None:
    session = SessionLocal()
    try:
        orchestrator = AdvisoryOrchestrator(session)
        plots = session.query(Plot).all()
        logger.info("Running advisory cycle for %d plot(s)", len(plots))
        for plot in plots:
            try:
                orchestrator.run_cycle_for_plot(plot)
            except Exception:  # noqa: BLE001
                logger.exception("Advisory cycle failed for plot %s", plot.id)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Run the agentic advisory cycle")
    parser.add_argument("--once", action="store_true", help="Run a single cycle immediately and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously on a weekly schedule")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables before running")
    args = parser.parse_args()

    if args.init_db:
        init_db()

    if args.once:
        run_all_plots_once()
    elif args.daemon:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_all_plots_once, "interval", weeks=1, id="weekly_advisory_cycle")
        logger.info("Scheduler started — weekly advisory cycle.")
        scheduler.start()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
