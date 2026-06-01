"""
Database Connection Pool - Async PostgreSQL Connection Management
High-performance connection pooling for Supabase/PostgreSQL
Version: 31.0
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import asyncpg
import logging

logger = logging.getLogger(__name__)


class DatabasePool:
    """Async database connection pool manager"""
    
    _pool = None
    _config = None
    
    @classmethod
    async def initialize(cls):
        """Initialize the connection pool"""
        if cls._pool is not None:
            return
        
        cls._config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "sovereign_grid"),
            "min_size": int(os.getenv("DB_MIN_POOL_SIZE", 10)),
            "max_size": int(os.getenv("DB_MAX_POOL_SIZE", 50)),
            "max_queries": 50000,
            "max_inactive_connection_lifetime": 300,
            "command_timeout": 60
        }
        
        try:
            cls._pool = await asyncpg.create_pool(**cls._config)
            logger.info(f"Database pool initialized with {cls._config['min_size']}-{cls._config['max_size']} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @classmethod
    async def close(cls):
        """Close the connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database pool closed")
    
    @classmethod
    @asynccontextmanager
    async def connection(cls):
        """Get a connection from the pool"""
        if cls._pool is None:
            await cls.initialize()
        
        async with cls._pool.acquire() as conn:
            yield conn
    
    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Execute a query and return status"""
        async with cls.connection() as conn:
            return await conn.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args) -> List[Dict]:
        """Fetch multiple rows"""
        async with cls.connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    @classmethod
    async def fetch_one(cls, query: str, *args) -> Optional[Dict]:
        """Fetch a single row"""
        async with cls.connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    @classmethod
    async def fetch_val(cls, query: str, *args) -> Any:
        """Fetch a single value"""
        async with cls.connection() as conn:
            return await conn.fetchval(query, *args)
    
    @classmethod
    async def transaction(cls):
        """Start a transaction"""
        if cls._pool is None:
            await cls.initialize()
        
        conn = await cls._pool.acquire()
        tr = conn.transaction()
        await tr.start()
        
        try:
            yield conn
            await tr.commit()
        except Exception:
            await tr.rollback()
            raise
        finally:
            await cls._pool.release(conn)
    
    @classmethod
    async def get_pool_stats(cls) -> Dict[str, int]:
        """Get pool statistics"""
        if not cls._pool:
            return {"status": "not_initialized"}
        
        return {
            "total_connections": cls._pool.get_size(),
            "idle_connections": cls._pool.get_idle_size(),
            "active_connections": cls._pool.get_size() - cls._pool.get_idle_size()
        }
