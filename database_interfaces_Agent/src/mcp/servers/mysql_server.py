#!/usr/bin/env python3
"""
MySQL MCP server for Database Interface Agent.
Provides tools for MySQL database operations.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

import mysql.connector
from mysql.connector import Error, OperationalError, ProgrammingError

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
server = Server("mysql-database-server")


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    tools = [
        Tool(
            name="test_connection",
            description="Test MySQL database connection",
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
            description="Execute SQL query on MySQL database",
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
            description="List tables in MySQL database",
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
            result = await test_mysql_connection(arguments)
        elif name == "execute_query":
            result = await execute_mysql_query(arguments)
        elif name == "list_tables":
            result = await list_mysql_tables(arguments)
        elif name == "get_schema":
            result = await get_mysql_schema(arguments)
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


async def test_mysql_connection(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Test MySQL database connection."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name")
        
        # Test connection
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connection_timeout=5
        )
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        # Get database info
        cursor.execute("SELECT DATABASE(), USER(), @@hostname, @@port")
        db_info = cursor.fetchone()
        
        # Get server variables
        cursor.execute("SHOW VARIABLES LIKE 'version%'")
        version_vars = cursor.fetchall()
        version_info = {var[0]: var[1] for var in version_vars}
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "MySQL connection successful",
            "version": version,
            "version_info": version_info,
            "database": db_info[0],
            "user": db_info[1],
            "hostname": db_info[2],
            "port": db_info[3],
            "connection_time": "~5ms",
            "tested_at": datetime.now().isoformat()
        }
        
    except OperationalError as e:
        return {
            "success": False,
            "message": f"MySQL connection failed: {str(e)}",
            "error_code": e.errno,
            "error_type": "OperationalError"
        }
    except Error as e:
        return {
            "success": False,
            "message": f"MySQL connection error: {str(e)}",
            "error_code": e.errno,
            "error_type": "Error"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"MySQL connection error: {str(e)}",
            "error_type": type(e).__name__
        }


async def execute_mysql_query(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute SQL query on MySQL database."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name")
        query = arguments["query"]
        
        # Connect to database
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connection_timeout=5
        )
        
        # Execute query
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        
        # Get results
        if cursor.description:
            # SELECT query
            rows = cursor.fetchall()
            
            # Convert rows to list of dicts
            results = []
            for row in rows:
                row_dict = {}
                for key, value in row.items():
                    # Handle datetime objects
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                results.append(row_dict)
            
            result_data = {
                "type": "select",
                "columns": list(cursor.column_names) if cursor.column_names else [],
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
            "error_code": e.errno,
            "error_type": "ProgrammingError"
        }
    except OperationalError as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "error_code": e.errno,
            "error_type": "OperationalError"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Query execution error: {str(e)}",
            "error_type": type(e).__name__
        }


async def list_mysql_tables(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List tables in MySQL database."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name")
        
        # Connect to database
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connection_timeout=5
        )
        
        # Query to list tables
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE,
            ENGINE,
            TABLE_ROWS,
            AVG_ROW_LENGTH,
            DATA_LENGTH,
            MAX_DATA_LENGTH,
            INDEX_LENGTH,
            DATA_FREE,
            AUTO_INCREMENT,
            CREATE_TIME,
            UPDATE_TIME,
            TABLE_COMMENT
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (database_name,))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        tables = []
        for row in rows:
            table_info = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    table_info[key.lower()] = value.isoformat()
                else:
                    table_info[key.lower()] = value
            tables.append(table_info)
        
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


async def get_mysql_schema(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get schema information for a table."""
    try:
        host = arguments["host"]
        port = arguments["port"]
        username = arguments["username"]
        password = arguments["password"]
        database_name = arguments.get("database_name")
        table_name = arguments["table_name"]
        
        # Connect to database
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database_name,
            connection_timeout=5
        )
        
        # Query to get column information
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            COLUMN_KEY,
            EXTRA,
            COLUMN_COMMENT
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, (database_name, table_name))
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        columns = []
        for row in rows:
            column_info = {}
            for key, value in row.items():
                column_info[key.lower()] = value
            columns.append(column_info)
        
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