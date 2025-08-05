#!/usr/bin/env python3
"""
Main entry point for the ServiceAgent.
"""
import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agent.service_agent import ServiceAgent
from src.api.server import APIServer
from src.core.config_manager import ConfigManager


def setup_logging(config: dict):
    """Setup logging configuration."""
    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "INFO").upper())
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = log_config.get("file", "logs/agent.log")
    
    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def run_cli_mode(config_path: str):
    """Run the agent in CLI mode."""
    try:
        # Initialize agent
        agent = ServiceAgent(config_path)
        await agent.initialize()
        
        print("ServiceAgent CLI Mode")
        print("Type 'quit' or 'exit' to stop")
        print("Type 'status' to see agent status")
        print("Type 'help' for available commands")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() == 'status':
                    status = agent.get_status()
                    print(f"Enabled tools: {status['enabled_tools']}")
                    print(f"Enabled MCP servers: {status['enabled_mcp_servers']}")
                    continue
                elif user_input.lower() == 'help':
                    print("Available commands:")
                    print("  status - Show agent status")
                    print("  quit/exit - Exit the application")
                    print("  help - Show this help message")
                    continue
                elif not user_input:
                    continue
                
                # Process request
                print("Processing...")
                result = await agent.process_request(user_input)
                
                if result["success"]:
                    print(f"Agent: {result['response']}")
                    if result.get("tool_results"):
                        print(f"Tools used: {len(result['tool_results'])}")
                    if result.get("mcp_results"):
                        print(f"MCP calls: {len(result['mcp_results'])}")
                    print(f"Iterations: {result['iterations']}")
                    if result.get("execution_time"):
                        print(f"Execution time: {result['execution_time']:.2f}s")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
                
                print("-" * 50)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        await agent.cleanup()
        print("Goodbye!")
        
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        sys.exit(1)


def run_api_mode(config_path: str):
    """Run the agent in API mode."""
    try:
        # Load config for API settings
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        api_config = config_manager.get_api_config()
        
        # Setup logging
        setup_logging(config)
        
        # Create and run API server
        api_server = APIServer(config_path)
        api_server.run(
            host=api_config.get("host", "0.0.0.0"),
            port=api_config.get("port", 8000),
            reload=False
        )
        
    except Exception as e:
        print(f"Failed to start API server: {e}")
        sys.exit(1)


async def run_test_mode(config_path: str):
    """Run the agent in test mode with sample requests."""
    try:
        # Initialize agent
        agent = ServiceAgent(config_path)
        await agent.initialize()
        
        print("ServiceAgent Test Mode")
        print("Running sample requests...")
        print("-" * 50)
        
        # Sample requests
        test_requests = [
            "Calculate 15 * 23 + 7",
            "List the contents of the current directory",
            "Create a test file with the content 'Hello, World!'",
            "What is 2 to the power of 10?"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\nTest {i}: {request}")
            print("-" * 30)
            
            result = await agent.process_request(request)
            
            if result["success"]:
                print(f"Response: {result['response']}")
                print(f"Success: {result['success']}")
                print(f"Iterations: {result['iterations']}")
                if result.get("execution_time"):
                    print(f"Time: {result['execution_time']:.2f}s")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Cleanup
        await agent.cleanup()
        print("\nTest mode completed!")
        
    except Exception as e:
        print(f"Failed to run test mode: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ServiceAgent - LangGraph-based AI Agent")
    parser.add_argument(
        "--mode",
        choices=["cli", "api", "test"],
        default="cli",
        help="Run mode: cli (interactive), api (REST server), test (sample requests)"
    )
    parser.add_argument(
        "--config",
        default="config/agent_config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for API server (api mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API server (api mode only)"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Run in specified mode
    if args.mode == "cli":
        asyncio.run(run_cli_mode(args.config))
    elif args.mode == "api":
        run_api_mode(args.config)
    elif args.mode == "test":
        asyncio.run(run_test_mode(args.config))
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main() 