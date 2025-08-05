"""
FastAPI server for the ServiceAgent.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..agent.service_agent import ServiceAgent


class ProcessRequest(BaseModel):
    """Request model for processing user input."""
    user_input: str
    session_id: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response model for processed requests."""
    success: bool
    response: str
    conversation: list
    tool_results: list
    mcp_results: list
    iterations: int
    error: Optional[str] = None
    execution_time: Optional[float] = None


class StatusResponse(BaseModel):
    """Response model for agent status."""
    enabled_tools: list
    enabled_mcp_servers: list
    mcp_server_statuses: Dict[str, Any]
    config: Dict[str, Any]


class APIServer:
    """FastAPI server for the ServiceAgent."""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = config_path
        self.agent: Optional[ServiceAgent] = None
        self.logger = logging.getLogger(__name__)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="ServiceAgent API",
            description="API for the LangGraph-based ServiceAgent",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize the agent on startup."""
            try:
                self.agent = ServiceAgent(self.config_path)
                await self.agent.initialize()
                self.logger.info("ServiceAgent initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize ServiceAgent: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup the agent on shutdown."""
            if self.agent:
                await self.agent.cleanup()
                self.logger.info("ServiceAgent cleaned up successfully")
        
        @self.app.post("/process", response_model=ProcessResponse)
        async def process_request(request: ProcessRequest):
            """Process a user request."""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            try:
                result = await self.agent.process_request(request.user_input)
                return ProcessResponse(**result)
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status", response_model=StatusResponse)
        async def get_status():
            """Get agent status."""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            try:
                status = self.agent.get_status()
                return StatusResponse(**status)
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "agent_initialized": self.agent is not None}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available tools."""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            try:
                from ..tool_extensions.tool_registry import tool_registry
                return {
                    "enabled_tools": tool_registry.list_enabled_tools(),
                    "all_tools": tool_registry.list_tools(),
                    "tool_schemas": tool_registry.get_tool_schemas()
                }
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp-servers")
        async def list_mcp_servers():
            """List available MCP servers."""
            if not self.agent:
                raise HTTPException(status_code=503, detail="Agent not initialized")
            
            try:
                from ..mcp_extensions.mcp_registry import mcp_registry
                return {
                    "enabled_servers": mcp_registry.list_enabled_servers(),
                    "all_servers": mcp_registry.list_servers(),
                    "server_schemas": mcp_registry.get_server_schemas(),
                    "server_statuses": mcp_registry.get_server_statuses()
                }
            except Exception as e:
                self.logger.error(f"Error listing MCP servers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Run the API server."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )


# Create global API server instance
api_server = APIServer() 