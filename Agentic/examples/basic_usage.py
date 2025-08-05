#!/usr/bin/env python3
"""
Basic usage example for the Agentic AI Orchestration system.

This example demonstrates how to:
1. Initialize the agent
2. Process user input
3. Handle sessions
4. Work with MCP servers
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import AgenticAgent
from config.settings import Settings


async def main():
    """Main example function."""
    print("🤖 Agentic AI Orchestration - Basic Usage Example")
    print("=" * 50)
    
    try:
        # Load settings
        settings = Settings.from_yaml("config/settings.yaml")
        
        # Initialize agent
        print("Initializing agent...")
        agent = AgenticAgent(settings)
        
        # Initialize components
        await agent.mcp_manager.initialize()
        await agent.verification_manager.initialize()
        await agent.session_manager.start_cleanup_task()
        
        print("✅ Agent initialized successfully!")
        
        # Example 1: Basic conversation
        print("\n📝 Example 1: Basic Conversation")
        print("-" * 30)
        
        response = await agent.process_input("Hello, how are you?")
        print(f"User: Hello, how are you?")
        print(f"Agent: {response['response']}")
        print(f"Session ID: {response['session_id']}")
        
        # Example 2: File operation request
        print("\n📁 Example 2: File Operation Request")
        print("-" * 30)
        
        response = await agent.process_input(
            "Load the sales data from /data/sales.csv into the analytics database",
            session_id=response['session_id']
        )
        print(f"User: Load the sales data from /data/sales.csv into the analytics database")
        print(f"Agent: {response['response']}")
        
        # Example 3: Database operation request
        print("\n🗄️ Example 3: Database Operation Request")
        print("-" * 30)
        
        response = await agent.process_input(
            "Connect to the PostgreSQL database and run a query to get all users",
            session_id=response['session_id']
        )
        print(f"User: Connect to the PostgreSQL database and run a query to get all users")
        print(f"Agent: {response['response']}")
        
        # Example 4: MCP server operation
        print("\n🔌 Example 4: MCP Server Operation")
        print("-" * 30)
        
        response = await agent.process_input(
            "Use the filesystem MCP server to list files in the current directory",
            session_id=response['session_id']
        )
        print(f"User: Use the filesystem MCP server to list files in the current directory")
        print(f"Agent: {response['response']}")
        
        # Example 5: Session management
        print("\n📋 Example 5: Session Management")
        print("-" * 30)
        
        # List sessions
        sessions = await agent.list_sessions()
        print(f"Total sessions: {len(sessions)}")
        
        # Get session history
        session_id = response['session_id']
        history = await agent.get_session_history(session_id)
        print(f"Session {session_id} has {len(history)} messages")
        
        # Example 6: Workflow tracing
        print("\n🔄 Example 6: Workflow Tracing")
        print("-" * 30)
        
        workflow_trace = await agent.get_workflow_trace(session_id)
        print(f"Workflow trace has {len(workflow_trace)} steps")
        
        for i, step in enumerate(workflow_trace[:3]):  # Show first 3 steps
            print(f"  Step {i+1}: {step['type']} at {step['timestamp']}")
        
        # Example 7: Memory statistics
        print("\n🧠 Example 7: Memory Statistics")
        print("-" * 30)
        
        memory_stats = await agent.memory_manager.get_memory_stats()
        print(f"Memory entries: {memory_stats['total_memory_entries']}")
        print(f"Contexts: {memory_stats['total_contexts']}")
        print(f"Knowledge domains: {memory_stats['total_knowledge_domains']}")
        
        # Example 8: MCP server status
        print("\n🔌 Example 8: MCP Server Status")
        print("-" * 30)
        
        servers = await agent.mcp_manager.list_servers()
        print(f"Configured MCP servers: {len(servers)}")
        
        for server in servers:
            status = "🟢 Healthy" if server['health']['healthy'] else "🔴 Unhealthy"
            print(f"  {server['name']}: {status}")
        
        print("\n✅ All examples completed successfully!")
        
        # Shutdown
        await agent.shutdown()
        
    except Exception as e:
        print(f"❌ Error in example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 