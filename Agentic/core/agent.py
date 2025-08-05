"""
Main Agentic Agent implementation.

This module contains the core AgenticAgent class that orchestrates
conversational AI, context understanding, MCP integration, and workflow management.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel

from config.settings import Settings
from core.context import ContextManager
from core.session import SessionManager
from core.workflow import WorkflowManager
from mcp.manager import MCPServerManager
from memory.memory_manager import MemoryManager
from validation.verification import VerificationManager

console = Console()


class AgenticAgent:
    """
    Main conversational AI agent that orchestrates all components.
    
    This agent provides:
    - Natural language conversation
    - Context-aware task understanding
    - Dynamic MCP server integration
    - Session and workflow management
    - Input validation and verification
    """
    
    def __init__(self, settings: Settings):
        """Initialize the agent with configuration."""
        self.settings = settings
        self.session_manager = SessionManager(settings)
        self.workflow_manager = WorkflowManager(settings)
        self.context_manager = ContextManager(settings)
        self.mcp_manager = MCPServerManager(settings)
        self.memory_manager = MemoryManager(settings)
        self.verification_manager = VerificationManager(settings)
        
        # Initialize AI client
        self._init_ai_client()
        
        # Active sessions
        self.active_sessions: Dict[str, Dict] = {}
        
        console.log("🤖 AgenticAgent initialized successfully")
    
    def _init_ai_client(self):
        """Initialize the AI client based on configuration."""
        try:
            if self.settings.ai.provider == "openai":
                from openai import AsyncOpenAI
                self.ai_client = AsyncOpenAI(
                    api_key=self.settings.ai.api_key,
                    timeout=self.settings.ai.timeout
                )
            else:
                raise ValueError(f"Unsupported AI provider: {self.settings.ai.provider}")
        except Exception as e:
            console.log(f"⚠️ Warning: AI client initialization failed: {e}")
            self.ai_client = None
    
    async def process_input(
        self, 
        user_input: str, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user input and generate a response.
        
        Args:
            user_input: The user's natural language input
            session_id: Optional session ID to resume
            user_id: Optional user ID for multi-user support
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Load or create session
            session = await self._get_or_create_session(session_id, user_id)
            
            # Add user input to session
            session["messages"].append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Analyze context and intent
            context_analysis = await self.context_manager.analyze_input(
                user_input, session
            )
            
            # Validate input if enabled
            if self.settings.validation_enabled:
                validation_result = await self._validate_input(user_input, context_analysis)
                if not validation_result["valid"]:
                    return {
                        "response": f"❌ Validation failed: {validation_result['error']}",
                        "session_id": session_id,
                        "status": "validation_error",
                        "metadata": validation_result
                    }
            
            # Determine required services/tools
            required_services = await self._identify_required_services(context_analysis)
            
            # Verify and activate services
            if self.settings.verification_enabled:
                verification_result = await self._verify_services(required_services)
                if not verification_result["verified"]:
                    return {
                        "response": f"⚠️ Service verification failed: {verification_result['error']}",
                        "session_id": session_id,
                        "status": "verification_error",
                        "metadata": verification_result
                    }
            
            # Generate AI response
            ai_response = await self._generate_ai_response(
                user_input, context_analysis, session
            )
            
            # Execute any required actions
            actions_result = await self._execute_actions(
                context_analysis, required_services, session
            )
            
            # Update session with response
            session["messages"].append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "actions": actions_result
            })
            
            # Save session
            await self.session_manager.save_session(session_id, session)
            
            # Update workflow
            await self.workflow_manager.record_step(
                session_id, "process_input", {
                    "input": user_input,
                    "context_analysis": context_analysis,
                    "ai_response": ai_response,
                    "actions": actions_result
                }
            )
            
            return {
                "response": ai_response,
                "session_id": session_id,
                "status": "success",
                "metadata": {
                    "context_analysis": context_analysis,
                    "actions": actions_result,
                    "required_services": required_services
                }
            }
            
        except Exception as e:
            console.log(f"❌ Error processing input: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "session_id": session_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_or_create_session(
        self, 
        session_id: str, 
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get existing session or create a new one."""
        session = await self.session_manager.get_session(session_id)
        
        if not session:
            session = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "messages": [],
                "context": {},
                "metadata": {}
            }
            await self.session_manager.save_session(session_id, session)
        
        self.active_sessions[session_id] = session
        return session
    
    async def _validate_input(
        self, 
        user_input: str, 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate user input based on context analysis."""
        # Basic validation
        if not user_input.strip():
            return {"valid": False, "error": "Input cannot be empty"}
        
        # Context-specific validation
        intent = context_analysis.get("intent", {})
        
        if intent.get("type") == "file_operation":
            # Validate file paths
            file_paths = context_analysis.get("entities", {}).get("file_paths", [])
            for path in file_paths:
                if not self._is_safe_path(path):
                    return {
                        "valid": False, 
                        "error": f"Unsafe file path: {path}"
                    }
        
        elif intent.get("type") == "database_operation":
            # Validate database credentials
            db_config = context_analysis.get("entities", {}).get("database", {})
            if not await self._validate_database_config(db_config):
                return {
                    "valid": False,
                    "error": "Invalid database configuration"
                }
        
        return {"valid": True}
    
    async def _verify_services(self, required_services: List[str]) -> Dict[str, Any]:
        """Verify that required services are available and accessible."""
        verification_results = {}
        
        for service in required_services:
            result = await self.verification_manager.verify_service(service)
            verification_results[service] = result
            
            if not result["verified"]:
                return {
                    "verified": False,
                    "error": f"Service '{service}' verification failed: {result['error']}",
                    "details": verification_results
                }
        
        return {
            "verified": True,
            "details": verification_results
        }
    
    async def _identify_required_services(
        self, 
        context_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify which services/tools are required for the task."""
        required_services = []
        
        intent = context_analysis.get("intent", {})
        entities = context_analysis.get("entities", {})
        
        # Map intent to services
        if intent.get("type") == "file_operation":
            required_services.append("filesystem")
        
        elif intent.get("type") == "database_operation":
            required_services.append("database")
            db_type = entities.get("database", {}).get("type")
            if db_type:
                required_services.append(f"database_{db_type}")
        
        elif intent.get("type") == "api_operation":
            required_services.append("api_client")
        
        elif intent.get("type") == "mcp_operation":
            mcp_server = entities.get("mcp_server")
            if mcp_server:
                required_services.append(f"mcp_{mcp_server}")
        
        return required_services
    
    async def _generate_ai_response(
        self, 
        user_input: str, 
        context_analysis: Dict[str, Any],
        session: Dict[str, Any]
    ) -> str:
        """Generate AI response using the configured AI provider."""
        if not self.ai_client:
            return "I'm sorry, but I'm currently unable to generate responses due to AI service configuration issues."
        
        try:
            # Prepare conversation history
            messages = []
            
            # Add system message
            system_prompt = self._build_system_prompt(context_analysis)
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history (last 10 messages)
            recent_messages = session["messages"][-10:]
            for msg in recent_messages:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = await self.ai_client.chat.completions.create(
                model=self.settings.ai.model,
                messages=messages,
                temperature=self.settings.ai.temperature,
                max_tokens=self.settings.ai.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            console.log(f"⚠️ AI response generation failed: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    def _build_system_prompt(self, context_analysis: Dict[str, Any]) -> str:
        """Build system prompt based on context analysis."""
        intent = context_analysis.get("intent", {})
        
        base_prompt = """You are an intelligent conversational AI agent that helps users with various tasks. 
        You can interact with databases, file systems, APIs, and MCP servers. 
        Be helpful, conversational, and ask clarifying questions when needed."""
        
        if intent.get("type") == "file_operation":
            base_prompt += "\n\nYou are currently working with file operations. Be careful with file paths and permissions."
        
        elif intent.get("type") == "database_operation":
            base_prompt += "\n\nYou are currently working with database operations. Be careful with data integrity and security."
        
        elif intent.get("type") == "api_operation":
            base_prompt += "\n\nYou are currently working with API operations. Be mindful of rate limits and authentication."
        
        return base_prompt
    
    async def _execute_actions(
        self, 
        context_analysis: Dict[str, Any],
        required_services: List[str],
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute actions based on context analysis."""
        actions_result = {}
        
        intent = context_analysis.get("intent", {})
        entities = context_analysis.get("entities", {})
        
        try:
            if intent.get("type") == "file_operation":
                actions_result["file_operations"] = await self._execute_file_operations(
                    intent, entities
                )
            
            elif intent.get("type") == "database_operation":
                actions_result["database_operations"] = await self._execute_database_operations(
                    intent, entities
                )
            
            elif intent.get("type") == "mcp_operation":
                actions_result["mcp_operations"] = await self._execute_mcp_operations(
                    intent, entities
                )
            
            # Store results in memory
            await self.memory_manager.store_action_results(
                session["session_id"], actions_result
            )
            
        except Exception as e:
            console.log(f"❌ Error executing actions: {e}")
            actions_result["error"] = str(e)
        
        return actions_result
    
    async def _execute_file_operations(
        self, 
        intent: Dict[str, Any], 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute file system operations."""
        # This would integrate with the filesystem tools
        return {"status": "not_implemented", "message": "File operations not yet implemented"}
    
    async def _execute_database_operations(
        self, 
        intent: Dict[str, Any], 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database operations."""
        # This would integrate with the database tools
        return {"status": "not_implemented", "message": "Database operations not yet implemented"}
    
    async def _execute_mcp_operations(
        self, 
        intent: Dict[str, Any], 
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute MCP server operations."""
        mcp_server = entities.get("mcp_server")
        if not mcp_server:
            return {"status": "error", "message": "No MCP server specified"}
        
        try:
            result = await self.mcp_manager.execute_operation(
                mcp_server, intent, entities
            )
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if a file path is safe to access."""
        # Basic path safety checks
        unsafe_patterns = ["..", "~", "/etc", "/var", "/usr"]
        return not any(pattern in path for pattern in unsafe_patterns)
    
    async def _validate_database_config(self, db_config: Dict[str, Any]) -> bool:
        """Validate database configuration."""
        # Basic validation - would be expanded based on database type
        required_fields = ["host", "port", "database"]
        return all(field in db_config for field in required_fields)
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        session = await self.session_manager.get_session(session_id)
        return session.get("messages", []) if session else []
    
    async def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sessions for a user."""
        return await self.session_manager.list_sessions(user_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return await self.session_manager.delete_session(session_id)
    
    async def get_workflow_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """Get workflow trace for a session."""
        return await self.workflow_manager.get_workflow_trace(session_id)
    
    async def shutdown(self):
        """Shutdown the agent and cleanup resources."""
        console.log("🔄 Shutting down AgenticAgent...")
        
        # Close MCP connections
        await self.mcp_manager.shutdown()
        
        # Save active sessions
        for session_id, session in self.active_sessions.items():
            await self.session_manager.save_session(session_id, session)
        
        console.log("✅ AgenticAgent shutdown complete") 