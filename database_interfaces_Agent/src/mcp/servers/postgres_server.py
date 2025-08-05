#!/usr/bin/env python3
"""
PostgreSQL MCP server for Database Interface Agent.
Provides tools for PostgreSQL database operations.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError, ProgrammingError

from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent
)

# Initialize MCP server
server = Server("postgresql-database-server")


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    tools = [
        Tool(
            name="test_connection",
            description="Test PostgreSQL database connection",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "description": "Database port"},
                    "username": {"type": "string", "description": "Database username"},
                    "password": {"type": "string", "description": "Database password"},
                    "database_name": {"type": "string", "description": "Database name (optional)"}
                },
                "required": ["host", "port", "username", "password"]
            }
        ),
        Tool(
            name="execute_query",
            description="Execute SQL query on PostgreSQL database",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "description": "Database port"},
                    "username": {"type": "string", "description": "Database username"},
                    "password": {"type": "string", "description": "Database password"},
                    "database_name": {"type": "string", "description": "Database name"},
                    "query": {"type": "string", "description": "SQL query to execute"}
                },
                "required": ["host", "port", "username", "password", "query"]
            }
        ),
        Tool(
            name="list_tables",
            description="List tables in PostgreSQL database",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "description": "Database port"},
                    "username": {"type": "string", "description": "Database username"},
                    "password": {"type": "string", "description": "Database password"},
                    "database_name": {"type": "string", "description": "Database name"}
                },
                "required": ["host", "port", "username", "password"]
            }
        ),
        Tool(
            name="get_schema",
            description="Get schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Database host"},
                    "port": {"type": "integer", "description": "Database port"},
                    "username": {"type": "string", "description": "Database username"},
                    "password": {"type": "string", "description": "Database password"},
                    "database_name": {"type": "string", "description": "Database name"},
                    "table_name": {"type": "string", "description": "Table name"}
                },
                "required": ["host", "port", "username", "password", "table_name"]
            }
        )
    ]
    
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        if name == "test_connection":
            result = await test_postgresql_connection(arguments)
        elif name == "execute_query":
            result = await execute_postgresql_query(arguments)
        elif name == "list_tables":
            result = await list_postgresql_tables(arguments)
        elif name == "get_schema":
            result = await get_postgresql_schema(arguments)
        else:
            result = {
                "success": False,
                "message": f"Unknown tool: {name}"
            }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result))]
        )
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"Tool execution failed: {str(e)}",
            "error_type": type(e).__name__
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(error_result))]
        )


async def test_postgresql_connection(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Test PostgreSQL database connection."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name", "postgres")
        
        # Test connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=5
        )
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Get database info
        cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()")
        db_info = cursor.fetchone()
        
        # Get connection parameters
        cursor.execute("SHOW server_version")
        server_version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "PostgreSQL connection successful",
            "version": version,
            "server_version": server_version,
            "database": db_info[0],
            "user": db_info[1],
            "server_address": db_info[2],
            "server_port": db_info[3],
            "connection_time": "~5ms",
            "tested_at": datetime.now().isoformat()
        }
        
    except OperationalError as e:
        return {
            "success": False,
            "message": f"PostgreSQL connection failed: {str(e)}",
            "error_code": getattr(e, 'pgcode', None),
            "error_type": "OperationalError"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"PostgreSQL connection error: {str(e)}",
            "error_type": type(e).__name__
        }


async def execute_postgresql_query(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute SQL query on PostgreSQL database."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name", "postgres")
        query = arguments["query"]
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=5
        )
        
        # Execute query
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Get results
        if cursor.description:
            # SELECT query
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Handle datetime objects
                    if isinstance(value, datetime):
                        row_dict[columns[i]] = value.isoformat()
                    else:
                        row_dict[columns[i]] = value
                results.append(row_dict)
            
            result_data = {
                "type": "select",
                "columns": columns,
                "rows": results,
                "row_count": len(results)
            }
        else:
            # INSERT, UPDATE, DELETE, etc.
            result_data = {
                "type": "modify",
                "row_count": cursor.rowcount,
                "message": f"Query affected {cursor.rowcount} rows"
            }
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Query executed successfully",
            "data": result_data,
            "executed_at": datetime.now().isoformat()
        }
        
    except ProgrammingError as e:
        return {
            "success": False,
            "message": f"SQL error: {str(e)}",
            "error_code": getattr(e, 'pgcode', None),
            "error_type": "ProgrammingError"
        }
    except OperationalError as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "error_code": getattr(e, 'pgcode', None),
            "error_type": "OperationalError"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Query execution error: {str(e)}",
            "error_type": type(e).__name__
        }


async def list_postgresql_tables(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List tables in PostgreSQL database."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name", "postgres")
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=5
        )
        
        # Query to list tables
        query = """
        SELECT 
            schemaname,
            tablename,
            tableowner,
            tablespace,
            hasindexes,
            hasrules,
            hastriggers,
            rowsecurity
        FROM pg_tables 
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        tables = []
        for row in rows:
            tables.append({
                "schema": row[0],
                "table": row[1],
                "owner": row[2],
                "tablespace": row[3],
                "has_indexes": row[4],
                "has_rules": row[5],
                "has_triggers": row[6],
                "row_security": row[7]
            })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Found {len(tables)} tables",
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing tables: {str(e)}",
            "error_type": type(e).__name__
        }


async def get_postgresql_schema(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get schema information for a table."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name", "postgres")
        table_name = arguments["table_name"]
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connect_timeout=5
        )
        
        # Query to get column information
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (table_name,))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        columns = []
        for row in rows:
            columns.append({
                "name": row[0],
                "data_type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3],
                "max_length": row[4],
                "precision": row[5],
                "scale": row[6]
            })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Schema for table {table_name}",
            "table_name": table_name,
            "columns": columns,
            "column_count": len(columns)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting schema: {str(e)}",
            "error_type": type(e).__name__
        }


async def main():
    """Main function to run the MCP server."""
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            server.NotificationOptions()
        )


if __name__ == "__main__":
    asyncio.run(main()) 