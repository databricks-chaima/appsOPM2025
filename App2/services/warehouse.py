"""
Warehouse SQL Service

Singleton service for querying Databricks SQL Warehouse.
Manages connection lifecycle with auto-refresh after 59 minutes.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

load_dotenv()


class Warehouse:
    """
    Singleton service for Databricks SQL Warehouse queries.
    
    Usage:
        rows = Warehouse.query("SELECT * FROM catalog.schema.table")
    """
    
    _instance: Optional['Warehouse'] = None
    _client: Optional[WorkspaceClient] = None
    _warehouse_id: Optional[str] = None
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
        """Create a new SQL warehouse connection"""
        cls._warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
        if not cls._warehouse_id:
            raise ValueError("DATABRICKS_WAREHOUSE_ID not found in environment variables")
        
        # Create workspace client (uses standard Databricks SDK auth)
        cls._client = WorkspaceClient()
        cls._connection_time = datetime.now()
    
    @classmethod
    def _ensure_connection(cls):
        """Ensure connection exists and is fresh"""
        if cls._client is None or cls._is_connection_expired():
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
            # Execute query using SQL statement execution API
            result = cls._client.statement_execution.execute_statement(
                warehouse_id=cls._warehouse_id,
                statement=sql_query,
                wait_timeout="30s"
            )
            
            # Extract rows from result
            rows = []
            if result.result and result.result.data_array:
                # Get column names
                columns = [col.name for col in result.manifest.schema.columns]
                
                # Convert each row array to dict
                for row_array in result.result.data_array:
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        row_dict[col_name] = row_array[i]
                    rows.append(row_dict)
            
            return rows
        except Exception as e:
            raise Exception(f"Query failed: {str(e)}") from e


# Convenience function for direct use
def query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL query against the warehouse.
    
    Args:
        sql_query: SQL query string
        
    Returns:
        List of row dictionaries
    """
    return Warehouse.query(sql_query)

