"""
Command-line interface for the Agentic AI Orchestration system.

This module provides the CLIInterface class that handles user interaction
through a command-line interface.
"""

import asyncio
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from core.agent import AgenticAgent

console = Console()


class CLIInterface:
    """
    Command-line interface for the Agentic AI Orchestration system.
    
    This class provides:
    - Interactive chat interface
    - Command processing
    - Session management
    - Help and documentation
    """
    
    def __init__(self, agent: AgenticAgent, verbose: bool = False):
        """Initialize the CLI interface."""
        self.agent = agent
        self.verbose = verbose
        self.current_session_id: Optional[str] = None
        self.running = True
        
        # Available commands
        self.commands = {
            "help": self._show_help,
            "quit": self._quit,
            "exit": self._quit,
            "clear": self._clear_screen,
            "session": self._show_session_info,
            "sessions": self._list_sessions,
            "workflow": self._show_workflow_trace,
            "memory": self._show_memory_stats,
            "servers": self._list_servers,
            "export": self._export_session,
            "import": self._import_session,
            "stats": self._show_stats
        }
        
        console.log("💻 CLIInterface initialized")
    
    async def start_chat(self, session_id: Optional[str] = None):
        """
        Start the interactive chat session.
        
        Args:
            session_id: Optional session ID to resume
        """
        if session_id:
            self.current_session_id = session_id
            console.print(f"📝 Resuming session: {session_id}")
        
        console.print("\n[bold blue]Agentic AI Orchestration[/bold blue]")
        console.print("Type 'help' for available commands or 'quit' to exit.\n")
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")
                
                if not user_input.strip():
                    continue
                
                # Check if it's a command
                if user_input.startswith("/"):
                    await self._process_command(user_input[1:])
                else:
                    # Process as conversation
                    await self._process_conversation(user_input)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit properly.[/yellow]")
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
    
    async def _process_conversation(self, user_input: str):
        """Process user input as conversation."""
        try:
            # Show processing indicator
            with console.status("[bold blue]Processing..."):
                # Process input through agent
                result = await self.agent.process_input(
                    user_input, 
                    self.current_session_id
                )
            
            # Update session ID if provided
            if result.get("session_id"):
                self.current_session_id = result["session_id"]
            
            # Display response
            response = result.get("response", "No response received")
            console.print(f"\n[bold blue]Agent[/bold blue]: {response}")
            
            # Show metadata if verbose
            if self.verbose and result.get("metadata"):
                await self._show_response_metadata(result["metadata"])
                
        except Exception as e:
            console.print(f"\n[red]Error processing input: {e}[/red]")
    
    async def _process_command(self, command: str):
        """Process a command."""
        try:
            # Parse command
            parts = command.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Execute command
            if cmd in self.commands:
                await self.commands[cmd](*args)
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
                console.print("Type 'help' for available commands.")
                
        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")
    
    async def _show_help(self, *args):
        """Show help information."""
        help_text = """
[bold]Available Commands:[/bold]

[bold]Conversation:[/bold]
  Just type your message to chat with the agent

[bold]Session Management:[/bold]
  /session                    - Show current session info
  /sessions                   - List all sessions
  /export [session_id]        - Export session data
  /import [file_path]         - Import session data

[bold]System Information:[/bold]
  /workflow [session_id]      - Show workflow trace
  /memory                     - Show memory statistics
  /servers                    - List MCP servers
  /stats                      - Show system statistics

[bold]System:[/bold]
  /clear                      - Clear screen
  /help                       - Show this help
  /quit, /exit                - Exit the application

[bold]Examples:[/bold]
  "Load the sales data into the analytics database"
  "Connect to the PostgreSQL server and run a query"
  "Use the filesystem server to copy files"
  /session
  /workflow
        """
        
        console.print(Panel(help_text, title="🤖 Help", border_style="blue"))
    
    async def _quit(self, *args):
        """Quit the application."""
        if Confirm.ask("Are you sure you want to quit?"):
            console.print("[yellow]Shutting down...[/yellow]")
            await self.agent.shutdown()
            self.running = False
            sys.exit(0)
    
    async def _clear_screen(self, *args):
        """Clear the screen."""
        console.clear()
        console.print("[bold blue]Agentic AI Orchestration[/bold blue]")
        console.print("Screen cleared.\n")
    
    async def _show_session_info(self, *args):
        """Show current session information."""
        if not self.current_session_id:
            console.print("[yellow]No active session.[/yellow]")
            return
        
        try:
            # Get session history
            history = await self.agent.get_session_history(self.current_session_id)
            
            # Get session stats
            stats = await self.agent.session_manager.get_session_stats(self.current_session_id)
            
            # Display session info
            table = Table(title=f"Session: {self.current_session_id}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Session ID", self.current_session_id)
            table.add_row("Total Messages", str(stats.get("total_messages", 0)))
            table.add_row("User Messages", str(stats.get("user_messages", 0)))
            table.add_row("Assistant Messages", str(stats.get("assistant_messages", 0)))
            table.add_row("Session Duration", stats.get("session_duration", "Unknown"))
            table.add_row("Created", stats.get("created_at", "Unknown"))
            table.add_row("Last Activity", stats.get("last_activity", "Unknown"))
            
            console.print(table)
            
            # Show recent messages
            if history:
                console.print("\n[bold]Recent Messages:[/bold]")
                for msg in history[-5:]:  # Last 5 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", "")
                    
                    if role == "user":
                        console.print(f"[green]You ({timestamp}):[/green] {content}")
                    elif role == "assistant":
                        console.print(f"[blue]Agent ({timestamp}):[/blue] {content}")
                        
        except Exception as e:
            console.print(f"[red]Error getting session info: {e}[/red]")
    
    async def _list_sessions(self, *args):
        """List all sessions."""
        try:
            sessions = await self.agent.list_sessions()
            
            if not sessions:
                console.print("[yellow]No sessions found.[/yellow]")
                return
            
            table = Table(title="Sessions")
            table.add_column("Session ID", style="cyan")
            table.add_column("User ID", style="green")
            table.add_column("Messages", style="yellow")
            table.add_column("Created", style="white")
            table.add_column("Status", style="magenta")
            
            for session in sessions:
                session_id = session.get("session_id", "Unknown")
                user_id = session.get("user_id", "Anonymous")
                messages = len(session.get("messages", []))
                created = session.get("created_at", "Unknown")
                status = session.get("status", "Unknown")
                
                # Highlight current session
                if session_id == self.current_session_id:
                    session_id = f"* {session_id}"
                
                table.add_row(session_id, user_id, str(messages), created, status)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing sessions: {e}[/red]")
    
    async def _show_workflow_trace(self, *args):
        """Show workflow trace for current or specified session."""
        session_id = args[0] if args else self.current_session_id
        
        if not session_id:
            console.print("[yellow]No session specified. Use: /workflow [session_id][/yellow]")
            return
        
        try:
            workflow_trace = await self.agent.get_workflow_trace(session_id)
            
            if not workflow_trace:
                console.print(f"[yellow]No workflow trace found for session: {session_id}[/yellow]")
                return
            
            console.print(f"\n[bold]Workflow Trace for Session: {session_id}[/bold]")
            
            for step in workflow_trace:
                step_type = step.get("type", "unknown")
                timestamp = step.get("timestamp", "Unknown")
                data = step.get("data", {})
                
                console.print(f"\n[cyan]{step_type}[/cyan] ({timestamp})")
                
                # Show step data in a formatted way
                if step_type == "api_call":
                    api_name = data.get("api_name", "Unknown")
                    duration = data.get("duration", "Unknown")
                    status = data.get("status", "Unknown")
                    console.print(f"  API: {api_name}, Duration: {duration}s, Status: {status}")
                    
                elif step_type == "tool_usage":
                    tool_name = data.get("tool_name", "Unknown")
                    success = data.get("success", False)
                    console.print(f"  Tool: {tool_name}, Success: {success}")
                    
                elif step_type == "decision":
                    decision_type = data.get("decision_type", "Unknown")
                    confidence = data.get("confidence", 0.0)
                    console.print(f"  Decision: {decision_type}, Confidence: {confidence}")
                    
                else:
                    console.print(f"  Data: {str(data)[:100]}...")
                    
        except Exception as e:
            console.print(f"[red]Error getting workflow trace: {e}[/red]")
    
    async def _show_memory_stats(self, *args):
        """Show memory statistics."""
        try:
            stats = await self.agent.memory_manager.get_memory_stats()
            
            table = Table(title="Memory Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Total Memory Entries", str(stats.get("total_memory_entries", 0)))
            table.add_row("Total Contexts", str(stats.get("total_contexts", 0)))
            table.add_row("Total Knowledge Domains", str(stats.get("total_knowledge_domains", 0)))
            table.add_row("Estimated Size (bytes)", str(stats.get("estimated_size_bytes", 0)))
            
            console.print(table)
            
            # Show most accessed entries
            most_accessed = stats.get("most_accessed", [])
            if most_accessed:
                console.print("\n[bold]Most Accessed Entries:[/bold]")
                for entry in most_accessed[:3]:
                    key = entry.get("key", "Unknown")
                    count = entry.get("access_count", 0)
                    console.print(f"  {key}: {count} accesses")
                    
        except Exception as e:
            console.print(f"[red]Error getting memory stats: {e}[/red]")
    
    async def _list_servers(self, *args):
        """List MCP servers."""
        try:
            servers = await self.agent.mcp_manager.list_servers()
            
            if not servers:
                console.print("[yellow]No MCP servers configured.[/yellow]")
                return
            
            table = Table(title="MCP Servers")
            table.add_column("Name", style="cyan")
            table.add_column("Host", style="green")
            table.add_column("Port", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Connected", style="white")
            
            for server in servers:
                name = server.get("name", "Unknown")
                config = server.get("config", {})
                host = config.get("host", "Unknown")
                port = str(config.get("port", "Unknown"))
                health = server.get("health", {})
                healthy = health.get("healthy", False)
                connected = "Yes" if server.get("connected", False) else "No"
                
                status = "🟢 Healthy" if healthy else "🔴 Unhealthy"
                
                table.add_row(name, host, port, status, connected)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing servers: {e}[/red]")
    
    async def _export_session(self, *args):
        """Export session data."""
        session_id = args[0] if args else self.current_session_id
        
        if not session_id:
            console.print("[yellow]No session specified. Use: /export [session_id][/yellow]")
            return
        
        try:
            export_data = await self.agent.session_manager.export_session(session_id)
            
            if not export_data:
                console.print(f"[red]Session not found: {session_id}[/red]")
                return
            
            # Save to file
            filename = f"session_{session_id}.json"
            import json
            
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            
            console.print(f"[green]Session exported to: {filename}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error exporting session: {e}[/red]")
    
    async def _import_session(self, *args):
        """Import session data."""
        if not args:
            console.print("[yellow]No file specified. Use: /import [file_path][/yellow]")
            return
        
        file_path = args[0]
        
        try:
            import json
            
            with open(file_path, "r") as f:
                session_data = json.load(f)
            
            new_session_id = await self.agent.session_manager.import_session(session_data)
            
            console.print(f"[green]Session imported with ID: {new_session_id}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error importing session: {e}[/red]")
    
    async def _show_stats(self, *args):
        """Show system statistics."""
        try:
            # Get various stats
            memory_stats = await self.agent.memory_manager.get_memory_stats()
            sessions = await self.agent.list_sessions()
            
            table = Table(title="System Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Memory Entries", str(memory_stats.get("total_memory_entries", 0)))
            table.add_row("Active Sessions", str(len(sessions)))
            table.add_row("Memory Size (bytes)", str(memory_stats.get("estimated_size_bytes", 0)))
            table.add_row("Knowledge Domains", str(memory_stats.get("total_knowledge_domains", 0)))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting system stats: {e}[/red]")
    
    async def _show_response_metadata(self, metadata: dict):
        """Show response metadata in verbose mode."""
        console.print("\n[dim]Response Metadata:[/dim]")
        
        if "context_analysis" in metadata:
            analysis = metadata["context_analysis"]
            intent = analysis.get("intent", {})
            console.print(f"  Intent: {intent.get('type', 'unknown')} (confidence: {intent.get('confidence', 0):.2f})")
        
        if "required_services" in metadata:
            services = metadata["required_services"]
            console.print(f"  Required Services: {', '.join(services) if services else 'None'}")
        
        if "actions" in metadata:
            actions = metadata["actions"]
            if actions:
                console.print(f"  Actions: {len(actions)} executed") 