"""
Cron Scheduler - Automated Scheduled Task Manager
Handles recurring jobs like billing, reconciliation, and cleanup
Version: 31.0
"""

import asyncio
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)


class CronScheduler:
    """Schedule and manage recurring background jobs"""
    
    _scheduler_task = None
    _running = False
    _jobs: Dict[str, schedule.Job] = {}
    
    @classmethod
    async def start(cls):
        """Start the scheduler"""
        if cls._running:
            return
        
        cls._running = True
        cls._scheduler_task = asyncio.create_task(cls._run())
        logger.info("Cron scheduler started")
        
        # Register default jobs
        cls._register_default_jobs()
    
    @classmethod
    async def stop(cls):
        """Stop the scheduler"""
        cls._running = False
        if cls._scheduler_task:
            cls._scheduler_task.cancel()
        logger.info("Cron scheduler stopped")
    
    @classmethod
    def _register_default_jobs(cls):
        """Register default scheduled jobs"""
        
        # Daily reconciliation at midnight
        cls.add_job(
            "daily_reconciliation",
            "00:00",
            cls._run_daily_reconciliation
        )
        
        # Hourly telemetry collection
        cls.add_job(
            "hourly_telemetry",
            "hourly",
            cls._run_hourly_telemetry
        )
        
        # Weekly invoice generation on Monday at 8 AM
        cls.add_job(
            "weekly_invoices",
            "08:00",
            cls._run_weekly_invoices,
            days=["monday"]
        )
        
        # Monthly billing reset on 1st at 00:01
        cls.add_job(
            "monthly_reset",
            "00:01",
            cls._run_monthly_reset,
            days=["1st"]
        )
        
        # Cleanup old logs every day at 3 AM
        cls.add_job(
            "cleanup_logs",
            "03:00",
            cls._run_cleanup_logs
        )
    
    @classmethod
    def add_job(
        cls,
        name: str,
        time_str: str,
        func: Callable[[], Awaitable[None]],
        days: list = None
    ):
        """
        Add a scheduled job
        
        Args:
            name: Unique job name
            time_str: Time string ("HH:MM" or "hourly" or "daily")
            func: Async function to run
            days: Optional days of week or month
        """
        try:
            if time_str == "hourly":
                job = schedule.every().hour.do(lambda: asyncio.create_task(func()))
            elif time_str == "daily":
                job = schedule.every().day.at("00:00").do(lambda: asyncio.create_task(func()))
            else:
                # Parse time
                if days:
                    for day in days:
                        if day == "monday":
                            job = schedule.every().monday.at(time_str).do(lambda: asyncio.create_task(func()))
                        elif day == "tuesday":
                            job = schedule.every().tuesday.at(time_str).do(lambda: asyncio.create_task(func()))
                        elif day == "1st":
                            job = schedule.every().day.at(time_str).do(lambda: asyncio.create_task(func()))
                else:
                    job = schedule.every().day.at(time_str).do(lambda: asyncio.create_task(func()))
            
            cls._jobs[name] = job
            logger.info(f"Scheduled job: {name} at {time_str}")
            
        except Exception as e:
            logger.error(f"Failed to schedule job {name}: {e}")
    
    @classmethod
    async def _run(cls):
        """Main scheduler loop"""
        while cls._running:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    @classmethod
    async def _run_daily_reconciliation(cls):
        """Run daily ledger reconciliation"""
        logger.info("Running daily reconciliation...")
        try:
            from services.reconcile_ledger import LedgerReconciler
            result = await LedgerReconciler.reconcile_all()
            logger.info(f"Daily reconciliation completed: {result}")
        except Exception as e:
            logger.error(f"Daily reconciliation failed: {e}")
    
    @classmethod
    async def _run_hourly_telemetry(cls):
        """Collect hourly telemetry metrics"""
        logger.info("Collecting hourly telemetry...")
        try:
            from core.telemetry import TelemetryManager
            await TelemetryManager.collect_metrics()
        except Exception as e:
            logger.error(f"Telemetry collection failed: {e}")
    
    @classmethod
    async def _run_weekly_invoices(cls):
        """Generate weekly invoices for all active merchants"""
        logger.info("Generating weekly invoices...")
        try:
            from services.invoice_generator import InvoiceGenerator
            count = await InvoiceGenerator.generate_weekly_invoices()
            logger.info(f"Generated {count} weekly invoices")
        except Exception as e:
            logger.error(f"Invoice generation failed: {e}")
    
    @classmethod
    async def _run_monthly_reset(cls):
        """Reset monthly credits and generate reports"""
        logger.info("Running monthly reset...")
        try:
            from services.tenant_manager import TenantManager
            # Reset monthly usage counters
            supabase.table("organizations").update({
                "credits_used": 0,
                "monthly_reset_at": datetime.utcnow().isoformat()
            }).execute()
            logger.info("Monthly reset completed")
        except Exception as e:
            logger.error(f"Monthly reset failed: {e}")
    
    @classmethod
    async def _run_cleanup_logs(cls):
        """Clean up old logs (keep last 90 days)"""
        logger.info("Cleaning up old logs...")
        try:
            cutoff = datetime.utcnow() - timedelta(days=90)
            # Delete old audit logs
            supabase.table("audit_logs").delete().lt("created_at", cutoff.isoformat()).execute()
            logger.info("Log cleanup completed")
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
