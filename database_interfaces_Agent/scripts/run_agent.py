#!/usr/bin/env python3
"""
Main CLI script for running the Database Interface Agent.
Supports interactive, structured input, and API modes.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

import click
import uvicorn
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import from src
from src.agent.database_agent import get_agent
from src.utils.logger import setup_logging
from config.settings import settings, validate_settings

console = Console()


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading config file: {str(e)}[/red]")
        sys.exit(1)


async def test_mode():
    """Run agent in test mode (no Redis required)."""
    console.print(Panel.fit(
        "[bold blue]Database Interface Agent - Test Mode[/bold blue]\n"
        "This mode demonstrates the agent functionality without requiring Redis.",
        title="Test Mode"
    ))
    
    try:
        # Test the validation utilities
        console.print("\n[bold]Testing Input Validation[/bold]")
        
        from src.utils.validators import InputValidator, ConnectionValidator
        
        # Test host validation
        test_hosts = ["localhost", "192.168.1.1", "example.com", "invalid@host"]
        for host in test_hosts:
            is_valid = InputValidator.is_valid_host(host)
            status = "✅" if is_valid else "❌"
            console.print(f"  {status} {host}: {is_valid}")
        
        # Test port validation
        test_ports = [5432, 3306, 1024, 65535, 0, 65536]
        for port in test_ports:
            is_valid = InputValidator.is_valid_port(port)
            status = "✅" if is_valid else "❌"
            console.print(f"  {status} Port {port}: {is_valid}")
        
        # Test credential validation
        console.print("\n[bold]Testing Credential Validation[/bold]")
        
        valid_credentials = {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "username": "testuser",
            "password": "testpass"
        }
        
        errors = InputValidator.validate_credentials(valid_credentials)
        if not errors:
            console.print("  ✅ Valid credentials: No errors")
        else:
            console.print(f"  ❌ Valid credentials: {errors}")
        
        invalid_credentials = {
            "database_type": "postgresql",
            "host": "invalid@host",
            "port": 99999,
            "username": "user@name"
            # Missing password
        }
        
        errors = InputValidator.validate_credentials(invalid_credentials)
        if errors:
            console.print("  ✅ Invalid credentials: Errors detected")
            for field, field_errors in errors.items():
                console.print(f"    - {field}: {field_errors}")
        else:
            console.print("  ❌ Invalid credentials: No errors detected")
        
        # Test database-specific validation
        console.print("\n[bold]Testing Database-Specific Validation[/bold]")
        
        postgres_errors = ConnectionValidator.validate_postgresql_connection(valid_credentials)
        if not postgres_errors:
            console.print("  ✅ PostgreSQL validation: No errors")
        else:
            console.print(f"  ❌ PostgreSQL validation: {postgres_errors}")
        
        mysql_credentials = valid_credentials.copy()
        mysql_credentials["database_type"] = "mysql"
        mysql_credentials["port"] = 3306
        
        mysql_errors = ConnectionValidator.validate_mysql_connection(mysql_credentials)
        if not mysql_errors:
            console.print("  ✅ MySQL validation: No errors")
        else:
            console.print(f"  ❌ MySQL validation: {mysql_errors}")
        
        # Test encryption utilities
        console.print("\n[bold]Testing Encryption Utilities[/bold]")
        
        from src.storage.encryption import EncryptionManager
        
        encryption_manager = EncryptionManager()
        
        # Test encryption/decryption
        test_data = "sensitive_database_password"
        encrypted = encryption_manager.encrypt(test_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        if test_data == decrypted:
            console.print("  ✅ Encryption/Decryption: Working correctly")
        else:
            console.print("  ❌ Encryption/Decryption: Failed")
        
        # Test dict encryption
        test_dict = {"username": "testuser", "password": "testpass"}
        encrypted_dict = encryption_manager.encrypt_dict(test_dict)
        decrypted_dict = encryption_manager.decrypt_dict(encrypted_dict)
        
        if test_dict == decrypted_dict:
            console.print("  ✅ Dict Encryption/Decryption: Working correctly")
        else:
            console.print("  ❌ Dict Encryption/Decryption: Failed")
        
        console.print("\n[green]✅ All tests completed successfully![/green]")
        console.print("\n[bold]To run with full functionality:[/bold]")
        console.print("1. Install and start Redis server")
        console.print("2. Run: python3 run_agent.py --interactive")
        console.print("3. Or run: python3 run_agent.py --api")
        
    except Exception as e:
        console.print(f"[red]Test error: {str(e)}[/red]")


async def interactive_mode():
    """Run agent in interactive mode."""
    console.print(Panel.fit(
        "[bold blue]Database Interface Agent - Interactive Mode[/bold blue]\n"
        "This mode will guide you through connecting to a database step by step.",
        title="Welcome"
    ))
    
    try:
        # Initialize agent
        agent = await get_agent()
        
        # Create session
        session_result = await agent.create_session()
        if not session_result["success"]:
            console.print(f"[red]Failed to create session: {session_result['error']}[/red]")
            return
        
        reference_id = session_result["reference_id"]
        console.print(f"[green]Session created: {reference_id}[/green]")
        
        # Collect credentials interactively
        console.print("\n[bold]Database Connection Setup[/bold]")
        
        database_type = Prompt.ask(
            "Database type",
            choices=["postgresql", "mysql"],
            default="postgresql"
        )
        
        host = Prompt.ask("Host", default="localhost")
        port = int(Prompt.ask("Port", default="5432" if database_type == "postgresql" else "3306"))
        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)
        database_name = Prompt.ask("Database name (optional)", default="")
        
        credentials = {
            "database_type": database_type,
            "host": host,
            "port": port,
            "username": username,
            "password": password
        }
        
        if database_name:
            credentials["database_name"] = database_name
        
        # Connect to database
        console.print("\n[bold]Testing connection...[/bold]")
        connection_result = await agent.connect_database(reference_id, credentials)
        
        if connection_result["success"]:
            console.print(f"[green]✓ {connection_result['message']}[/green]")
            
            # Interactive operations
            await interactive_operations(agent, reference_id)
        else:
            console.print(f"[red]✗ {connection_result['message']}[/red]")
            if connection_result.get("error"):
                console.print(f"[red]Error: {connection_result['error']}[/red]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
    finally:
        # Cleanup
        if 'agent' in locals():
            await agent.cleanup()


async def interactive_operations(agent, reference_id: str):
    """Handle interactive database operations."""
    while True:
        console.print("\n[bold]Available Operations:[/bold]")
        console.print("1. Execute query")
        console.print("2. List tables")
        console.print("3. Get table schema")
        console.print("4. Show session info")
        console.print("5. Exit")
        
        choice = Prompt.ask("Choose operation", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            await execute_query_interactive(agent, reference_id)
        elif choice == "2":
            await list_tables_interactive(agent, reference_id)
        elif choice == "3":
            await get_schema_interactive(agent, reference_id)
        elif choice == "4":
            await show_session_info_interactive(agent, reference_id)
        elif choice == "5":
            console.print("[yellow]Exiting...[/yellow]")
            break


async def execute_query_interactive(agent, reference_id: str):
    """Execute query interactively."""
    query = Prompt.ask("Enter SQL query")
    if not query:
        return
    
    console.print("[bold]Executing query...[/bold]")
    result = await agent.execute_query(reference_id, query)
    
    if result["success"]:
        console.print("[green]Query executed successfully![/green]")
        
        data = result.get("data", {})
        if data.get("type") == "select":
            # Display results in table
            table = Table(title="Query Results")
            columns = data.get("columns", [])
            for col in columns:
                table.add_column(col)
            
            rows = data.get("rows", [])
            for row in rows:
                table.add_row(*[str(row.get(col, "")) for col in columns])
            
            console.print(table)
        else:
            console.print(f"Rows affected: {data.get('row_count', 0)}")
    else:
        console.print(f"[red]Query failed: {result['message']}[/red]")


async def list_tables_interactive(agent, reference_id: str):
    """List tables interactively."""
    console.print("[bold]Fetching tables...[/bold]")
    result = await agent.list_tables(reference_id)
    
    if result["success"]:
        tables = result.get("tables", [])
        if tables:
            table = Table(title="Database Tables")
            table.add_column("Schema")
            table.add_column("Table")
            table.add_column("Owner")
            table.add_column("Type")
            
            for t in tables:
                table.add_row(
                    str(t.get("schema", "")),
                    str(t.get("table", "")),
                    str(t.get("owner", "")),
                    str(t.get("table_type", ""))
                )
            
            console.print(table)
        else:
            console.print("[yellow]No tables found[/yellow]")
    else:
        console.print(f"[red]Failed to list tables: {result['message']}[/red]")


async def get_schema_interactive(agent, reference_id: str):
    """Get schema interactively."""
    table_name = Prompt.ask("Enter table name")
    if not table_name:
        return
    
    console.print(f"[bold]Fetching schema for {table_name}...[/bold]")
    result = await agent.get_schema(reference_id, table_name)
    
    if result["success"]:
        columns = result.get("columns", [])
        if columns:
            table = Table(title=f"Schema for {table_name}")
            table.add_column("Column")
            table.add_column("Type")
            table.add_column("Nullable")
            table.add_column("Default")
            
            for col in columns:
                table.add_row(
                    str(col.get("name", "")),
                    str(col.get("data_type", "")),
                    str(col.get("nullable", "")),
                    str(col.get("default", ""))
                )
            
            console.print(table)
        else:
            console.print("[yellow]No columns found[/yellow]")
    else:
        console.print(f"[red]Failed to get schema: {result['message']}[/red]")


async def show_session_info_interactive(agent, reference_id: str):
    """Show session info interactively."""
    result = await agent.get_session_info(reference_id)
    
    if result["success"]:
        session = result["session"]
        
        info_table = Table(title="Session Information")
        info_table.add_column("Property")
        info_table.add_column("Value")
        
        info_table.add_row("Reference ID", session["reference_id"])
        info_table.add_row("Status", session["agent_status"])
        info_table.add_row("Connection Status", session["connection_status"])
        info_table.add_row("Created", session["created_at"])
        info_table.add_row("Last Accessed", session["last_accessed"])
        info_table.add_row("TTL", str(session["ttl"]))
        info_table.add_row("Active", str(session["is_active"]))
        
        console.print(info_table)
    else:
        console.print(f"[red]Failed to get session info: {result['message']}[/red]")


async def structured_input_mode(config_path: str):
    """Run agent with structured input from config file."""
    console.print(f"[bold]Loading configuration from: {config_path}[/bold]")
    
    config = load_config_file(config_path)
    
    try:
        # Initialize agent
        agent = await get_agent()
        
        # Create session
        session_result = await agent.create_session()
        if not session_result["success"]:
            console.print(f"[red]Failed to create session: {session_result['error']}[/red]")
            return
        
        reference_id = session_result["reference_id"]
        console.print(f"[green]Session created: {reference_id}[/green]")
        
        # Connect to database
        console.print("[bold]Connecting to database...[/bold]")
        connection_result = await agent.connect_database(reference_id, config)
        
        if connection_result["success"]:
            console.print(f"[green]✓ {connection_result['message']}[/green]")
            
            # Execute operations if specified
            if "operations" in config:
                await execute_operations(agent, reference_id, config["operations"])
        else:
            console.print(f"[red]✗ {connection_result['message']}[/red]")
            if connection_result.get("error"):
                console.print(f"[red]Error: {connection_result['error']}[/red]")
    
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
    finally:
        # Cleanup
        if 'agent' in locals():
            await agent.cleanup()


async def execute_operations(agent, reference_id: str, operations: list):
    """Execute operations from config."""
    for operation in operations:
        op_type = operation.get("type")
        
        if op_type == "query":
            query = operation.get("query")
            if query:
                console.print(f"[bold]Executing query: {query}[/bold]")
                result = await agent.execute_query(reference_id, query)
                if result["success"]:
                    console.print("[green]Query executed successfully![/green]")
                else:
                    console.print(f"[red]Query failed: {result['message']}[/red]")
        
        elif op_type == "list_tables":
            console.print("[bold]Listing tables...[/bold]")
            result = await agent.list_tables(reference_id)
            if result["success"]:
                console.print(f"[green]Found {len(result.get('tables', []))} tables[/green]")
            else:
                console.print(f"[red]Failed to list tables: {result['message']}[/red]")


def run_api_server(host: str, port: int):
    """Run the API server."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    app = FastAPI(title="Database Interface Agent API", version="1.0.0")
    
    # Pydantic models
    class ConnectionRequest(BaseModel):
        database_type: str
        host: str
        port: int
        username: str
        password: str
        database_name: Optional[str] = None
    
    class QueryRequest(BaseModel):
        query: str
    
    class SchemaRequest(BaseModel):
        table_name: str
    
    # Global agent instance
    agent_instance = None
    
    @app.on_event("startup")
    async def startup_event():
        nonlocal agent_instance
        agent_instance = await get_agent()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        if agent_instance:
            await agent_instance.cleanup()
    
    @app.post("/sessions")
    async def create_session():
        """Create a new session."""
        try:
            result = await agent_instance.create_session()
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/sessions/{reference_id}/connect")
    async def connect_database(reference_id: str, request: ConnectionRequest):
        """Connect to database."""
        try:
            credentials = request.dict()
            result = await agent_instance.connect_database(reference_id, credentials)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/sessions/{reference_id}/query")
    async def execute_query(reference_id: str, request: QueryRequest):
        """Execute a database query."""
        try:
            result = await agent_instance.execute_query(reference_id, request.query)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/sessions/{reference_id}/tables")
    async def list_tables(reference_id: str):
        """List tables in database."""
        try:
            result = await agent_instance.list_tables(reference_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/sessions/{reference_id}/schema")
    async def get_schema(reference_id: str, request: SchemaRequest):
        """Get table schema."""
        try:
            result = await agent_instance.get_schema(reference_id, request.table_name)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/sessions/{reference_id}")
    async def get_session_info(reference_id: str):
        """Get session information."""
        try:
            result = await agent_instance.get_session_info(reference_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/sessions")
    async def list_sessions():
        """List all sessions."""
        try:
            result = await agent_instance.list_sessions()
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/sessions/{reference_id}")
    async def delete_session(reference_id: str):
        """Delete a session."""
        try:
            result = await agent_instance.delete_session(reference_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "Database Interface Agent"}
    
    # Run the server
    uvicorn.run(app, host=host, port=port)


@click.command()
@click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
@click.option("--config", "-c", type=str, help="Path to configuration JSON file")
@click.option("--api", is_flag=True, help="Run as API server")
@click.option("--host", default="0.0.0.0", help="API server host (default: 0.0.0.0)")
@click.option("--port", default=8000, help="API server port (default: 8000)")
@click.option("--log-level", default="INFO", help="Log level (default: INFO)")
@click.option("--test", is_flag=True, help="Run in test mode (no Redis required)")
def main(interactive, config, api, host, port, log_level, test):
    """Database Interface Agent CLI."""
    
    # Setup logging
    setup_logging(log_level=log_level)
    
    # Validate settings
    try:
        validate_settings()
    except ValueError as e:
        console.print(f"[red]Configuration error: {str(e)}[/red]")
        sys.exit(1)
    
    if test:
        asyncio.run(test_mode())
    elif api:
        console.print(f"[bold]Starting API server on {host}:{port}[/bold]")
        run_api_server(host, port)
    elif config:
        asyncio.run(structured_input_mode(config))
    elif interactive:
        asyncio.run(interactive_mode())
    else:
        # Default to test mode if no Redis
        console.print("[yellow]No mode specified. Running in test mode...[/yellow]")
        asyncio.run(test_mode())


if __name__ == "__main__":
    main() 