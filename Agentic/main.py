#!/usr/bin/env python3
"""
Agentic AI Orchestration - Main Entry Point

This module provides the main entry point for the Agentic AI Orchestration system,
supporting both CLI and web interface modes.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn
from rich.console import Console
from rich.panel import Panel

from core.agent import AgenticAgent
from config.settings import Settings
from ui.cli import CLIInterface
from ui.web_ui import create_web_app

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Agentic AI Orchestration - Intelligent Conversational AI Agent"""
    pass


@cli.command()
@click.option("--config", "-c", default="config/settings.yaml", help="Configuration file path")
@click.option("--session-id", "-s", help="Session ID to resume")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def chat(config: str, session_id: Optional[str], verbose: bool):
    """Start the conversational agent in CLI mode"""
    asyncio.run(run_cli_chat(config, session_id, verbose))


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def web(host: str, port: int, reload: bool):
    """Start the web interface"""
    run_web_interface(host, port, reload)


@cli.command()
@click.option("--config", "-c", default="config/settings.yaml", help="Configuration file path")
def test(config: str):
    """Run the test suite"""
    run_tests(config)


async def run_cli_chat(config_path: str, session_id: Optional[str], verbose: bool):
    """Run the CLI chat interface"""
    try:
        # Load settings
        settings = Settings.from_yaml(config_path)
        
        # Initialize agent
        agent = AgenticAgent(settings)
        
        # Initialize CLI interface
        cli_interface = CLIInterface(agent, verbose=verbose)
        
        # Display welcome message
        console.print(Panel.fit(
            "[bold blue]Agentic AI Orchestration[/bold blue]\n"
            "Your intelligent conversational AI agent is ready!\n"
            "Type 'help' for commands or 'quit' to exit.",
            title="🤖 Welcome"
        ))
        
        # Start chat session
        await cli_interface.start_chat(session_id)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def run_web_interface(host: str, port: int, reload: bool):
    """Run the web interface"""
    try:
        app = create_web_app()
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        console.print(f"[red]Error starting web interface: {e}[/red]")
        sys.exit(1)


def run_tests(config_path: str):
    """Run the test suite"""
    try:
        import pytest
        import subprocess
        
        # Run pytest
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✅ All tests passed![/green]")
        else:
            console.print(f"[red]❌ Tests failed:[/red]\n{result.stdout}\n{result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error running tests: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli() 