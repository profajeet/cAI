#!/usr/bin/env python3
"""
Basic usage example for the ServiceAgent.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agent.service_agent import ServiceAgent


async def main():
    """Demonstrate basic ServiceAgent usage."""
    print("ServiceAgent Basic Usage Example")
    print("=" * 50)
    
    try:
        # Initialize the agent
        print("Initializing ServiceAgent...")
        agent = ServiceAgent("config/agent_config.yaml")
        await agent.initialize()
        
        # Get agent status
        status = agent.get_status()
        print(f"Enabled tools: {status['enabled_tools']}")
        print(f"Enabled MCP servers: {status['enabled_mcp_servers']}")
        print()
        
        # Example requests
        requests = [
            "Calculate 25 * 4 + 10",
            "What is 2 to the power of 8?",
            "List the contents of the current directory",
            "Create a test file with the content 'Hello from ServiceAgent!'"
        ]
        
        for i, request in enumerate(requests, 1):
            print(f"Request {i}: {request}")
            print("-" * 40)
            
            # Process the request
            result = await agent.process_request(request)
            
            if result["success"]:
                print(f"Response: {result['response']}")
                print(f"Tools used: {len(result.get('tool_results', []))}")
                print(f"MCP calls: {len(result.get('mcp_results', []))}")
                print(f"Iterations: {result['iterations']}")
                if result.get("execution_time"):
                    print(f"Execution time: {result['execution_time']:.2f}s")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            print()
        
        # Cleanup
        await agent.cleanup()
        print("Example completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 