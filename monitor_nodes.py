"""
Node Monitor - Real-Time Hardware Telemetry Collection
Monitors CPU, RAM, network, and request metrics
Version: 31.0
"""

import os
import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging

from core.supabase_client import supabase
from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class NodeMonitor:
    """Collect and report hardware telemetry for all nodes"""
    
    NODE_ID = os.getenv("CLOUD_REGION_NODE", "GLOBAL_MESH_NODE_1")
    REGION = os.getenv("REGION", "GLOBAL")
    
    _monitoring_task = None
    
    @classmethod
    async def start_monitoring(cls):
        """Start the monitoring background task"""
        if cls._monitoring_task is None:
            cls._monitoring_task = asyncio.create_task(cls._monitor_loop())
            logger.info(f"Node monitor started for {cls.NODE_ID}")
    
    @classmethod
    async def stop_monitoring(cls):
        """Stop monitoring"""
        if cls._monitoring_task:
            cls._monitoring_task.cancel()
            cls._monitoring_task = None
    
    @classmethod
    async def _monitor_loop(cls):
        """Main monitoring loop"""
        while True:
            try:
                metrics = await cls.collect_metrics()
                await cls.report_metrics(metrics)
                await asyncio.sleep(15)  # Every 15 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)
    
    @classmethod
    async def collect_metrics(cls) -> Dict[str, Any]:
        """Collect system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        ram_used_mb = memory.used / 1024 / 1024
        ram_total_mb = memory.total / 1024 / 1024
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / 1024 / 1024 / 1024
        disk_total_gb = disk.total / 1024 / 1024 / 1024
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Process metrics
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / 1024 / 1024
        process_cpu_percent = process.cpu_percent()
        thread_count = process.num_threads()
        
        # Get request counts from Redis
        request_count = await redis_client.get(f"node_requests:{cls.NODE_ID}:day")
        request_count = int(request_count) if request_count else 0
        
        return {
            "node_id": cls.NODE_ID,
            "region": cls.REGION,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": round(cpu_percent, 2),
                "count": cpu_count,
                "process_percent": round(process_cpu_percent, 2)
            },
            "memory": {
                "used_mb": round(ram_used_mb, 2),
                "total_mb": round(ram_total_mb, 2),
                "percent": round(memory.percent, 2),
                "process_mb": round(process_memory_mb, 2)
            },
            "disk": {
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2),
                "percent": round(disk.percent, 2)
            },
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / 1024 / 1024, 2),
                "bytes_recv_mb": round(net_io.bytes_recv / 1024 / 1024, 2)
            },
            "process": {
                "threads": thread_count,
                "pid": process.pid
            },
            "requests": {
                "today_count": request_count
            },
            "status": "healthy" if cpu_percent < 85 and ram_used_mb / ram_total_mb < 0.9 else "degraded"
        }
    
    @classmethod
    async def report_metrics(cls, metrics: Dict[str, Any]):
        """Report metrics to database"""
        try:
            # Store in Supabase
            await supabase.table_insert("node_telemetry", metrics)
            
            # Cache latest metrics in Redis
            await redis_client.setex(
                f"node_metrics:{cls.NODE_ID}",
                60,
                json.dumps(metrics)
            )
            
            # Check for alert conditions
            await cls._check_alerts(metrics)
            
        except Exception as e:
            logger.error(f"Failed to report metrics: {e}")
    
    @classmethod
    async def _check_alerts(cls, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if metrics["cpu"]["percent"] > 85:
            alerts.append(f"High CPU: {metrics['cpu']['percent']}%")
        
        # Memory alert
        if metrics["memory"]["percent"] > 90:
            alerts.append(f"High Memory: {metrics['memory']['percent']}%")
        
        # Disk alert
        if metrics["disk"]["percent"] > 85:
            alerts.append(f"Low Disk Space: {metrics['disk']['percent']}% used")
        
        if alerts:
            await cls._send_alerts(alerts)
    
    @classmethod
    async def _send_alerts(cls, alerts: list):
        """Send alerts to monitoring systems"""
        logger.warning(f"Node {cls.NODE_ID} alerts: {alerts}")
        
        # In production, send to Slack/PagerDuty
        # from services.slack_alerter import SlackAlerter
        # await SlackAlerter.send_node_alert(cls.NODE_ID, alerts)
    
    @classmethod
    async def get_current_metrics(cls) -> Dict[str, Any]:
        """Get current cached metrics"""
        cached = await redis_client.get(f"node_metrics:{cls.NODE_ID}")
        if cached:
            return json.loads(cached)
        return await cls.collect_metrics()
