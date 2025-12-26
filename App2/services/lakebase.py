"""
Lakebase PostgreSQL Service

Singleton service for querying Databricks Lakebase PostgreSQL.
Manages connection lifecycle with OAuth token refresh after 59 minutes.
Based on: https://apps-cookbook.dev/docs/streamlit/tables/lakebase_read
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()


class Lakebase:
    """
    Singleton service for Databricks Lakebase PostgreSQL queries.
    
    Usage:
        rows = Lakebase.query("SELECT * FROM opm.factories_synched")
    """
    
    _instance: Optional['Lakebase'] = None
    _connection: Optional[Any] = None
    _workspace_client: Optional[WorkspaceClient] = None
    _database_instance: Optional[Any] = None
    _postgres_password: Optional[str] = None
    _connection_time: Optional[datetime] = None
    _CONNECTION_TIMEOUT_MINUTES = 59
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def _is_connection_expired(cls) -> bool:
        """Check if connection is older than 59 minutes"""
        if cls._connection_time is None:
            return True
        age = datetime.now() - cls._connection_time
        return age > timedelta(minutes=cls._CONNECTION_TIMEOUT_MINUTES)
    
    @classmethod
    def _create_connection(cls):
        """
        Create a new Lakebase PostgreSQL connection with OAuth token.
        Uses standard PostgreSQL environment variables (PGHOST, PGUSER, etc.)
        See: https://apps-cookbook.dev/docs/streamlit/tables/lakebase_read
        """
        # Initialize Databricks SDK client
        cls._workspace_client = WorkspaceClient()
        
        # Get OAuth token from workspace client config (cookbook method)
        token = cls._workspace_client.config.oauth_token().access_token
        cls._postgres_password = token
        
        # Get connection parameters from standard PostgreSQL environment variables
        host = os.getenv("PGHOST")
        port = int(os.getenv("PGPORT", "5432"))
        database = os.getenv("PGDATABASE")
        username = os.getenv("PGUSER")
        sslmode = os.getenv("PGSSLMODE", "require")
        
        # Validate required parameters
        if not all([host, database, username]):
            raise ValueError(
                "Missing required PostgreSQL environment variables. "
                "Please set PGHOST, PGDATABASE, and PGUSER"
            )
        
        # Create PostgreSQL connection (cookbook pattern)
        cls._connection = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=token,
            sslmode=sslmode,
            connect_timeout=30
        )
        
        cls._connection_time = datetime.now()
    
    @classmethod
    def _ensure_connection(cls):
        """Ensure connection exists and is fresh"""
        if cls._connection is None or cls._is_connection_expired():
            if cls._connection is not None:
                try:
                    cls._connection.close()
                except Exception:
                    pass
            cls._create_connection()
    
    @classmethod
    def query(cls, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the rows as list of dicts.
        
        Args:
            sql_query: SQL query string
            
        Returns:
            List of row dictionaries
            
        Raises:
            Exception: If query execution fails
        """
        cls._ensure_connection()
        
        try:
            with cls._connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql_query)
                
                # Fetch all rows and convert to list of dicts
                rows = cursor.fetchall()
                cls._connection.commit()
                
                # Convert RealDictRow to regular dict
                return [dict(row) for row in rows]
        except Exception as e:
            # Rollback on error
            if cls._connection:
                cls._connection.rollback()
            raise Exception(f"Query failed: {str(e)}") from e


# Convenience function for direct use
def query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query against Lakebase.
    
    Args:
        sql_query: SQL query string
        
    Returns:
        List of row dictionaries
    """
    return Lakebase.query(sql_query)

