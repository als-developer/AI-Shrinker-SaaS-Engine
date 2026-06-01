"""
Supabase Client - Production Database Interface
Async wrapper for Supabase with retry logic and connection pooling
Version: 31.0
"""

import os
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client with retry logic"""
    
    _instance: Optional[Client] = None
    _url: str = None
    _key: str = None
    
    @classmethod
    def initialize(cls):
        """Initialize the Supabase client"""
        if cls._instance is not None:
            return cls._instance
        
        cls._url = os.getenv("SUPABASE_URL", "")
        cls._key = os.getenv("SUPABASE_KEY", "")
        
        if not cls._url or not cls._key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        cls._instance = create_client(cls._url, cls._key)
        logger.info("Supabase client initialized")
        return cls._instance
    
    @classmethod
    def get_client(cls) -> Client:
        """Get the Supabase client instance"""
        if cls._instance is None:
            cls.initialize()
        return cls._instance
    
    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def execute_query(cls, table: str, operation: str, data: Dict = None, filters: Dict = None):
        """Execute a query with retry logic"""
        client = cls.get_client()
        
        try:
            query = client.table(table)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if operation == "insert":
                result = query.insert(data).execute()
            elif operation == "update":
                result = query.update(data).execute()
            elif operation == "select":
                result = query.select("*").execute()
            elif operation == "delete":
                result = query.delete().execute()
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return result.data
            
        except Exception as e:
            logger.error(f"Supabase query failed: {e}")
            raise
    
    @classmethod
    async def table_insert(cls, table: str, data: Dict) -> List:
        """Insert a record into a table"""
        return await cls.execute_query(table, "insert", data=data)
    
    @classmethod
    async def table_select(cls, table: str, filters: Dict = None) -> List:
        """Select records from a table"""
        return await cls.execute_query(table, "select", filters=filters)
    
    @classmethod
    async def table_update(cls, table: str, data: Dict, filters: Dict) -> List:
        """Update records in a table"""
        client = cls.get_client()
        query = client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data
    
    @classmethod
    async def table_delete(cls, table: str, filters: Dict) -> List:
        """Delete records from a table"""
        client = cls.get_client()
        query = client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data
    
    @classmethod
    async def rpc_call(cls, function_name: str, params: Dict = None) -> Any:
        """Call a Supabase RPC function"""
        client = cls.get_client()
        result = client.rpc(function_name, params or {}).execute()
        return result.data


# Export singleton
supabase = SupabaseClient()
