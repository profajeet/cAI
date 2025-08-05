#!/usr/bin/env python3
"""
Example: Interactive session with Database Interface Agent.
Demonstrates programmatic usage of the agent.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.database_agent import get_agent
from src.utils.logger import setup_logging


async def main():
    """Example interactive session."""
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    try:
        # Initialize agent
        agent = await get_agent()
        
        # Create session
        print("Creating session...")
        session_result = await agent.create_session()
        if not session_result["success"]:
            print(f"Failed to create session: {session_result['error']}")
            return
        
        reference_id = session_result["reference_id"]
        print(f"Session created: {reference_id}")
        
        # Define database credentials
        credentials = {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "your_password_here",
            "database_name": "testdb"
        }
        
        # Connect to database
        print("Connecting to database...")
        connection_result = await agent.connect_database(reference_id, credentials)
        
        if connection_result["success"]:
            print(f"✓ {connection_result['message']}")
            
            # Execute some operations
            print("\n--- Executing Operations ---")
            
            # List tables
            print("Listing tables...")
            tables_result = await agent.list_tables(reference_id)
            if tables_result["success"]:
                tables = tables_result.get("tables", [])
                print(f"Found {len(tables)} tables")
                for table in tables[:5]:  # Show first 5 tables
                    print(f"  - {table.get('schema', '')}.{table.get('table', '')}")
            else:
                print(f"Failed to list tables: {tables_result['message']}")
            
            # Execute a query
            print("\nExecuting query...")
            query_result = await agent.execute_query(reference_id, "SELECT version()")
            if query_result["success"]:
                data = query_result.get("data", {})
                if data.get("type") == "select" and data.get("rows"):
                    version = data["rows"][0].get("version", "Unknown")
                    print(f"Database version: {version}")
            else:
                print(f"Query failed: {query_result['message']}")
            
            # Get session info
            print("\nSession information:")
            session_info = await agent.get_session_info(reference_id)
            if session_info["success"]:
                session = session_info["session"]
                print(f"  Status: {session['agent_status']}")
                print(f"  Connection: {session['connection_status']}")
                print(f"  Created: {session['created_at']}")
                print(f"  TTL: {session['ttl']} seconds")
            
        else:
            print(f"✗ {connection_result['message']}")
            if connection_result.get("error"):
                print(f"Error: {connection_result['error']}")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        # Cleanup
        if 'agent' in locals():
            await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 