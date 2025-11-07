import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from typing import Callable, List

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Handles scheduling of automated reports"""
    
    def __init__(self, tz: str = 'Asia/Kolkata'):
        self.scheduler = AsyncIOScheduler(timezone=timezone(tz))
        self.timezone = timezone(tz)
        self.is_running = False
    
    def schedule_reports(self, report_func: Callable, hours: List[int]):
        """
        Schedule reports to run at specific hours every day
        
        Args:
            report_func: Async function to call for generating reports
            hours: List of hours (0-23) to run reports
        """
        for hour in hours:
            trigger = CronTrigger(
                hour=hour,
                minute=0,
                timezone=self.timezone
            )
            
            self.scheduler.add_job(
                report_func,
                trigger=trigger,
                id=f'report_{hour}',
                name=f'Scheduled Report ({hour}:00)',
                replace_existing=True
            )
            
            logger.info(f"Scheduled report for {hour}:00 {self.timezone}")
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler started successfully")
            
            # Log next run times
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"Next run: {job.name} at {job.next_run_time}")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time as a formatted string"""
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return "No scheduled jobs"
        
        next_job = min(jobs, key=lambda j: j.next_run_time)
        next_time = next_job.next_run_time
        
        now = datetime.now(self.timezone)
        delta = next_time - now
        
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
