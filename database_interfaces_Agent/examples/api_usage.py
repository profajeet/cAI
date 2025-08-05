#!/usr/bin/env python3
"""
Example: API usage with Database Interface Agent.
Demonstrates how to interact with the agent via REST API.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def api_example():
    """Example API usage."""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Create a session
            print("Creating session...")
            async with session.post(f"{base_url}/sessions") as response:
                session_data = await response.json()
                if session_data["success"]:
                    reference_id = session_data["reference_id"]
                    print(f"Session created: {reference_id}")
                else:
                    print(f"Failed to create session: {session_data['error']}")
                    return
            
            # 2. Connect to database
            print("Connecting to database...")
            connection_data = {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "postgres",
                "password": "your_password_here",
                "database_name": "testdb"
            }
            
            async with session.post(
                f"{base_url}/sessions/{reference_id}/connect",
                json=connection_data
            ) as response:
                connection_result = await response.json()
                if connection_result["success"]:
                    print(f"✓ {connection_result['message']}")
                else:
                    print(f"✗ {connection_result['message']}")
                    if connection_result.get("error"):
                        print(f"Error: {connection_result['error']}")
                    return
            
            # 3. List tables
            print("\nListing tables...")
            async with session.get(f"{base_url}/sessions/{reference_id}/tables") as response:
                tables_result = await response.json()
                if tables_result["success"]:
                    tables = tables_result.get("tables", [])
                    print(f"Found {len(tables)} tables")
                    for table in tables[:5]:  # Show first 5 tables
                        print(f"  - {table.get('schema', '')}.{table.get('table', '')}")
                else:
                    print(f"Failed to list tables: {tables_result['message']}")
            
            # 4. Execute a query
            print("\nExecuting query...")
            query_data = {"query": "SELECT version()"}
            async with session.post(
                f"{base_url}/sessions/{reference_id}/query",
                json=query_data
            ) as response:
                query_result = await response.json()
                if query_result["success"]:
                    data = query_result.get("data", {})
                    if data.get("type") == "select" and data.get("rows"):
                        version = data["rows"][0].get("version", "Unknown")
                        print(f"Database version: {version}")
                else:
                    print(f"Query failed: {query_result['message']}")
            
            # 5. Get table schema (if tables exist)
            if tables_result["success"] and tables_result.get("tables"):
                first_table = tables_result["tables"][0]
                table_name = first_table.get("table")
                if table_name:
                    print(f"\nGetting schema for table: {table_name}")
                    schema_data = {"table_name": table_name}
                    async with session.post(
                        f"{base_url}/sessions/{reference_id}/schema",
                        json=schema_data
                    ) as response:
                        schema_result = await response.json()
                        if schema_result["success"]:
                            columns = schema_result.get("columns", [])
                            print(f"Table has {len(columns)} columns")
                            for col in columns[:3]:  # Show first 3 columns
                                print(f"  - {col.get('name')}: {col.get('data_type')}")
                        else:
                            print(f"Failed to get schema: {schema_result['message']}")
            
            # 6. Get session information
            print("\nSession information:")
            async with session.get(f"{base_url}/sessions/{reference_id}") as response:
                session_info = await response.json()
                if session_info["success"]:
                    session = session_info["session"]
                    print(f"  Status: {session['agent_status']}")
                    print(f"  Connection: {session['connection_status']}")
                    print(f"  Created: {session['created_at']}")
                    print(f"  TTL: {session['ttl']} seconds")
                else:
                    print(f"Failed to get session info: {session_info['message']}")
            
            # 7. List all sessions
            print("\nAll sessions:")
            async with session.get(f"{base_url}/sessions") as response:
                sessions_result = await response.json()
                if sessions_result["success"]:
                    sessions = sessions_result.get("sessions", [])
                    print(f"Total sessions: {len(sessions)}")
                    for sess in sessions[:3]:  # Show first 3 sessions
                        print(f"  - {sess['reference_id']}: {sess['agent_status']}")
                else:
                    print(f"Failed to list sessions: {sessions_result['message']}")
            
            # 8. Health check
            print("\nHealth check:")
            async with session.get(f"{base_url}/health") as response:
                health = await response.json()
                print(f"Service status: {health['status']}")
            
            # 9. Clean up - delete session
            print(f"\nDeleting session: {reference_id}")
            async with session.delete(f"{base_url}/sessions/{reference_id}") as response:
                delete_result = await response.json()
                if delete_result["success"]:
                    print("Session deleted successfully")
                else:
                    print(f"Failed to delete session: {delete_result['message']}")
        
        except aiohttp.ClientError as e:
            print(f"API request failed: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


def main():
    """Main function."""
    print("Database Interface Agent - API Example")
    print("Make sure the API server is running on localhost:8000")
    print("You can start it with: python scripts/run_agent.py --api")
    print()
    
    asyncio.run(api_example())


if __name__ == "__main__":
    main() 