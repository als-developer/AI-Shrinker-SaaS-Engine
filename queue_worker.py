"""
Queue Worker - Redis-Based Background Task Processor
Async task queue for long-running operations
Version: 31.0
"""

import asyncio
import json
from typing import Dict, Any, Callable, Awaitable
from datetime import datetime
import logging

from core.redis_client import redis_client

logger = logging.getLogger(__name__)


class QueueWorker:
    """Background task processor using Redis queue"""
    
    _QUEUE_KEY = "task_queue"
    _PROCESSING_KEY = "processing_tasks"
    _worker_running = False
    _worker_task = None
    
    # Task handlers registry
    _handlers: Dict[str, Callable] = {}
    
    @classmethod
    def register_handler(cls, task_type: str, handler: Callable[[Dict], Awaitable[Any]]):
        """Register a handler for a specific task type"""
        cls._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    @classmethod
    async def enqueue(cls, task_type: str, payload: Dict[str, Any], priority: int = 5) -> str:
        """
        Enqueue a task for background processing
        
        Args:
            task_type: Type of task (e.g., 'send_email', 'process_payment')
            payload: Task payload
            priority: 1 (highest) to 10 (lowest)
        
        Returns:
            Task ID
        """
        task_id = f"task_{datetime.utcnow().timestamp()}_{task_type[:8]}"
        
        task = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        # Add to sorted set with priority score
        score = priority
        await redis_client.zadd(cls._QUEUE_KEY, {json.dumps(task): score})
        
        logger.info(f"Enqueued task {task_id} of type {task_type}")
        return task_id
    
    @classmethod
    async def start(cls):
        """Start the background worker"""
        if cls._worker_running:
            logger.warning("Worker already running")
            return
        
        cls._worker_running = True
        cls._worker_task = asyncio.create_task(cls._run())
        logger.info("Queue worker started")
    
    @classmethod
    async def stop(cls):
        """Stop the background worker"""
        cls._worker_running = False
        if cls._worker_task:
            cls._worker_task.cancel()
            try:
                await cls._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue worker stopped")
    
    @classmethod
    async def _run(cls):
        """Main worker loop"""
        while cls._worker_running:
            try:
                # Get next task from queue
                result = await redis_client.zpopmin(cls._QUEUE_KEY, 1)
                
                if not result:
                    await asyncio.sleep(0.5)
                    continue
                
                task_json, score = result[0]
                task = json.loads(task_json)
                
                # Process task
                await cls._process_task(task)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)
    
    @classmethod
    async def _process_task(cls, task: Dict):
        """Process a single task with retry logic"""
        task_id = task["id"]
        task_type = task["type"]
        
        # Mark as processing
        await redis_client.hset(cls._PROCESSING_KEY, task_id, json.dumps(task))
        
        try:
            # Get handler
            handler = cls._handlers.get(task_type)
            if not handler:
                logger.error(f"No handler for task type: {task_type}")
                return
            
            # Execute handler
            result = await handler(task["payload"])
            
            # Log success
            logger.info(f"Task {task_id} completed successfully")
            
            # Store result if needed
            if result:
                await redis_client.setex(f"task_result:{task_id}", 3600, json.dumps(result))
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
            # Retry logic
            task["attempts"] = task.get("attempts", 0) + 1
            task["last_error"] = str(e)
            
            if task["attempts"] < 3:
                # Requeue with increased priority (lower score = higher priority)
                new_priority = max(1, task["priority"] - 1)
                await redis_client.zadd(cls._QUEUE_KEY, {json.dumps(task): new_priority})
                logger.info(f"Task {task_id} requeued (attempt {task['attempts']}/3)")
            else:
                logger.error(f"Task {task_id} failed permanently after {task['attempts']} attempts")
                await cls._log_failed_task(task)
        
        finally:
            # Remove from processing set
            await redis_client.hdel(cls._PROCESSING_KEY, task_id)
    
    @classmethod
    async def _log_failed_task(cls, task: Dict):
        """Log permanently failed task"""
        try:
            from core.supabase_client import supabase
            supabase.table("failed_tasks").insert({
                "task_id": task["id"],
                "task_type": task["type"],
                "payload": task["payload"],
                "error": task.get("last_error"),
                "attempts": task["attempts"],
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log failed task: {e}")
    
    @classmethod
    async def get_queue_length(cls) -> int:
        """Get number of pending tasks"""
        return await redis_client.zcard(cls._QUEUE_KEY)
    
    @classmethod
    async def get_processing_count(cls) -> int:
        """Get number of processing tasks"""
        return await redis_client.hlen(cls._PROCESSING_KEY)
