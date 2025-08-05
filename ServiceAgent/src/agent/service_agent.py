"""
Main ServiceAgent class using LangGraph for orchestration.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ..core.state import AgentState, AgentRole, create_initial_state, add_message, add_tool_result, update_iteration, mark_complete
from ..core.config_manager import ConfigManager
from ..tool_extensions.tool_registry import tool_registry
from ..mcp_extensions.mcp_registry import mcp_registry


class ServiceAgent:
    """Main service agent using LangGraph for orchestration."""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        agent_config = self.config_manager.get_agent_config()
        self.llm = ChatOpenAI(
            model=agent_config.get("model", "gpt-4"),
            temperature=agent_config.get("temperature", 0.1),
            max_tokens=agent_config.get("max_tokens", 2000)
        )
        
        # Initialize tool and MCP registries
        self._initialize_extensions()
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        
        self.logger.info("ServiceAgent initialized successfully")
    
    def _initialize_extensions(self):
        """Initialize tool and MCP extensions."""
        # Load tools
        if self.config_manager.get_tool_config("tool_extensions", {}).get("enabled", False):
            tool_registry.load_tools_from_directory("src/tool_extensions", self.config_manager)
            self.logger.info(f"Loaded {len(tool_registry.list_enabled_tools())} enabled tools")
        
        # Load MCP servers
        if self.config_manager.get_mcp_config("mcp_extensions", {}).get("enabled", False):
            mcp_registry.load_servers_from_directory("src/mcp_extensions", self.config_manager)
            self.logger.info(f"Loaded {len(mcp_registry.list_enabled_servers())} enabled MCP servers")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("execute_mcp", self._execute_mcp)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("check_completion", self._check_completion)
        
        # Add edges
        workflow.add_edge("analyze_input", "execute_tools")
        workflow.add_edge("execute_tools", "execute_mcp")
        workflow.add_edge("execute_mcp", "generate_response")
        workflow.add_edge("generate_response", "check_completion")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "check_completion",
            self._should_continue,
            {
                "continue": "analyze_input",
                "end": END
            }
        )
        
        # Set entry point
        workflow.set_entry_point("analyze_input")
        
        return workflow.compile()
    
    def _analyze_input(self, state: AgentState) -> AgentState:
        """Analyze user input and determine required actions."""
        try:
            # Add user message to conversation
            state = add_message(state, AgentRole.USER, state.user_input)
            
            # Create system prompt for analysis
            system_prompt = """You are an AI assistant that analyzes user requests and determines what tools or MCP servers need to be used.

Available tools: {tools}
Available MCP servers: {mcp_servers}

Analyze the user's request and determine:
1. What tools need to be executed (if any)
2. What MCP servers need to be called (if any)
3. What the next step should be

Respond with a JSON object containing:
{
    "tools_to_execute": [{"name": "tool_name", "params": {...}}],
    "mcp_requests": [{"server": "server_name", "method": "method_name", "params": {...}}],
    "reasoning": "explanation of your analysis"
}"""

            # Get available tools and MCP servers
            tools = tool_registry.list_enabled_tools()
            mcp_servers = mcp_registry.list_enabled_servers()
            
            # Create messages for analysis
            messages = [
                SystemMessage(content=system_prompt.format(
                    tools=tools,
                    mcp_servers=mcp_servers
                )),
                HumanMessage(content=state.user_input)
            ]
            
            # Get analysis from LLM
            response = self.llm.invoke(messages)
            
            # Parse response and update state
            try:
                import json
                analysis = json.loads(response.content)
                state.memory["analysis"] = analysis
                state.memory["tools_to_execute"] = analysis.get("tools_to_execute", [])
                state.memory["mcp_requests"] = analysis.get("mcp_requests", [])
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM analysis response")
                state.memory["tools_to_execute"] = []
                state.memory["mcp_requests"] = []
            
            # Add assistant message
            state = add_message(state, AgentRole.ASSISTANT, response.content)
            
        except Exception as e:
            self.logger.error(f"Error in analyze_input: {e}")
            state.error = str(e)
        
        return state
    
    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute required tools."""
        try:
            tools_to_execute = state.memory.get("tools_to_execute", [])
            
            for tool_request in tools_to_execute:
                tool_name = tool_request.get("name")
                params = tool_request.get("params", {})
                
                if tool_name and tool_name in tool_registry.list_enabled_tools():
                    try:
                        result = tool_registry.execute_tool(tool_name, **params)
                        state = add_tool_result(state, result)
                        
                        # Add tool result to memory
                        if "tool_results" not in state.memory:
                            state.memory["tool_results"] = []
                        state.memory["tool_results"].append({
                            "tool": tool_name,
                            "result": result.dict()
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error executing tool {tool_name}: {e}")
                        error_result = {
                            "tool": tool_name,
                            "error": str(e)
                        }
                        if "tool_results" not in state.memory:
                            state.memory["tool_results"] = []
                        state.memory["tool_results"].append(error_result)
            
        except Exception as e:
            self.logger.error(f"Error in execute_tools: {e}")
            state.error = str(e)
        
        return state
    
    async def _execute_mcp(self, state: AgentState) -> AgentState:
        """Execute MCP server requests."""
        try:
            mcp_requests = state.memory.get("mcp_requests", [])
            
            for mcp_request in mcp_requests:
                server_name = mcp_request.get("server")
                method = mcp_request.get("method")
                params = mcp_request.get("params", {})
                
                if server_name and method and server_name in mcp_registry.list_enabled_servers():
                    try:
                        from ..mcp_extensions.base_mcp import MCPRequest
                        request = MCPRequest(method=method, params=params)
                        response = await mcp_registry.handle_request(server_name, request)
                        
                        # Add MCP result to memory
                        if "mcp_results" not in state.memory:
                            state.memory["mcp_results"] = []
                        state.memory["mcp_results"].append({
                            "server": server_name,
                            "method": method,
                            "result": response.dict()
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error executing MCP request {server_name}.{method}: {e}")
                        error_result = {
                            "server": server_name,
                            "method": method,
                            "error": str(e)
                        }
                        if "mcp_results" not in state.memory:
                            state.memory["mcp_results"] = []
                        state.memory["mcp_results"].append(error_result)
            
        except Exception as e:
            self.logger.error(f"Error in execute_mcp: {e}")
            state.error = str(e)
        
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response based on tool and MCP results."""
        try:
            # Create system prompt for response generation
            system_prompt = """You are an AI assistant that generates helpful responses based on tool execution results and MCP server responses.

Use the following information to generate a comprehensive response:
- Tool execution results: {tool_results}
- MCP server responses: {mcp_results}
- Original user request: {user_input}

Provide a clear, helpful response that addresses the user's request using the available information."""

            # Prepare context for response generation
            tool_results = state.memory.get("tool_results", [])
            mcp_results = state.memory.get("mcp_results", [])
            
            # Create messages for response generation
            messages = [
                SystemMessage(content=system_prompt.format(
                    tool_results=tool_results,
                    mcp_results=mcp_results,
                    user_input=state.user_input
                )),
                HumanMessage(content=state.user_input)
            ]
            
            # Generate response
            response = self.llm.invoke(messages)
            
            # Add assistant response to conversation
            state = add_message(state, AgentRole.ASSISTANT, response.content)
            
            # Store final response in memory
            state.memory["final_response"] = response.content
            
        except Exception as e:
            self.logger.error(f"Error in generate_response: {e}")
            state.error = str(e)
        
        return state
    
    def _check_completion(self, state: AgentState) -> AgentState:
        """Check if the workflow should continue or end."""
        try:
            # Update iteration count
            state = update_iteration(state)
            
            # Check if max iterations reached
            if state.iteration >= state.max_iterations:
                state = mark_complete(state, "Maximum iterations reached")
                return state
            
            # Check if there's an error
            if state.error:
                state = mark_complete(state, state.error)
                return state
            
            # Check if response is complete (simple heuristic)
            final_response = state.memory.get("final_response", "")
            if len(final_response) > 50:  # Simple completion check
                state = mark_complete(state)
            
        except Exception as e:
            self.logger.error(f"Error in check_completion: {e}")
            state.error = str(e)
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if the workflow should continue."""
        if state.is_complete:
            return "end"
        else:
            return "continue"
    
    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """Process a user request through the agent workflow."""
        try:
            # Create initial state
            initial_state = create_initial_state(self.config)
            initial_state.user_input = user_input
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Prepare response
            response = {
                "success": not bool(final_state.error),
                "response": final_state.memory.get("final_response", ""),
                "conversation": [msg.dict() for msg in final_state.messages],
                "tool_results": final_state.memory.get("tool_results", []),
                "mcp_results": final_state.memory.get("mcp_results", []),
                "iterations": final_state.iteration,
                "error": final_state.error,
                "execution_time": (final_state.end_time - final_state.start_time).total_seconds() if final_state.end_time else None
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "An error occurred while processing your request."
            }
    
    async def initialize(self):
        """Initialize the agent and all extensions."""
        try:
            # Initialize MCP servers
            if mcp_registry.list_enabled_servers():
                await mcp_registry.initialize_all_servers()
            
            self.logger.info("ServiceAgent initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup the agent and all extensions."""
        try:
            # Cleanup MCP servers
            if mcp_registry.server_instances:
                await mcp_registry.cleanup_all_servers()
            
            self.logger.info("ServiceAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "enabled_tools": tool_registry.list_enabled_tools(),
            "enabled_mcp_servers": mcp_registry.list_enabled_servers(),
            "mcp_server_statuses": mcp_registry.get_server_statuses(),
            "config": {
                "agent": self.config_manager.get_agent_config(),
                "behavior": self.config_manager.get_behavior_config()
            }
        } 