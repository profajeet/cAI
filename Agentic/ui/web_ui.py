"""
Web interface for the Agentic AI Orchestration system.

This module provides a FastAPI-based web interface with:
- REST API endpoints for chat and management
- WebSocket support for real-time chat
- HTML interface for user interaction
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.agent import AgenticAgent
from config.settings import Settings

# Global variables for the web app
agent: Optional[AgenticAgent] = None
settings: Optional[Settings] = None

# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    status: str
    metadata: Optional[Dict[str, Any]] = None

class SessionInfo(BaseModel):
    session_id: str
    user_id: Optional[str]
    created_at: str
    last_accessed: str
    message_count: int

class WorkflowStep(BaseModel):
    step_id: str
    type: str
    timestamp: str
    data: Dict[str, Any]

class MemoryStats(BaseModel):
    total_memory_entries: int
    total_contexts: int
    total_knowledge_domains: int
    estimated_size_bytes: int

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic AI Orchestration</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            display: flex;
            height: 600px;
        }
        .chat-section {
            flex: 2;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #eee;
        }
        .sidebar {
            flex: 1;
            padding: 20px;
            background: #f8f9fa;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        .message {
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
        }
        .assistant-message {
            background: #e9ecef;
            color: #333;
        }
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        .chat-input input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            border-color: #007bff;
        }
        .chat-input button {
            padding: 12px 25px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        .chat-input button:hover {
            background: #0056b3;
        }
        .sidebar h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .button-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .sidebar button {
            padding: 10px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        .sidebar button:hover {
            background: #545b62;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Agentic AI Orchestration</h1>
            <p>Intelligent Conversational AI Agent</p>
        </div>
        
        <div class="content">
            <div class="chat-section">
                <div class="chat-messages" id="chatMessages">
                    <div class="message assistant-message">
                        Hello! I'm your Agentic AI assistant. I can help you with various tasks including file operations, database queries, API calls, and MCP server interactions. How can I assist you today?
                    </div>
                </div>
                
                <div class="chat-input">
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <div class="sidebar">
                <h3>📊 System Stats</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="memoryEntries">-</div>
                        <div class="stat-label">Memory Entries</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="activeSessions">-</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                </div>
                
                <h3>🆔 Session Info</h3>
                <div class="stat-card">
                    <div class="stat-value" id="sessionId">-</div>
                    <div class="stat-label">Session ID</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="messageCount">0</div>
                    <div class="stat-label">Messages</div>
                </div>
                
                <h3>🛠️ Actions</h3>
                <div class="button-group">
                    <button onclick="showSessions()">📋 View Sessions</button>
                    <button onclick="showWorkflow()">🔄 View Workflow</button>
                    <button onclick="showServers()">🔌 View Servers</button>
                    <button onclick="clearChat()">🗑️ Clear Chat</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let messageCount = 0;

        // Load stats on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
        });

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage('user', message);
            input.value = '';
            
            // Show loading
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant-message loading';
            loadingDiv.textContent = 'Thinking...';
            document.getElementById('chatMessages').appendChild(loadingDiv);
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: currentSessionId
                    })
                });
                
                const data = await response.json();
                
                // Remove loading message
                loadingDiv.remove();
                
                // Add assistant response
                addMessage('assistant', data.response);
                
                // Update session info
                currentSessionId = data.session_id;
                messageCount += 2; // User + Assistant messages
                updateSessionInfo();
                updateMessageCount();
                
                // Reload stats
                loadStats();
                
            } catch (error) {
                loadingDiv.remove();
                addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
                console.error('Error:', error);
            }
        }

        function addMessage(sender, text) {
            const chatMessages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function updateSessionInfo() {
            const sessionIdSpan = document.getElementById('sessionId');
            sessionIdSpan.textContent = currentSessionId || '-';
        }

        function updateMessageCount() {
            const messageCountSpan = document.getElementById('messageCount');
            messageCountSpan.textContent = messageCount;
        }

        async function loadStats() {
            try {
                const response = await fetch('/api/memory/stats');
                const stats = await response.json();
                
                document.getElementById('memoryEntries').textContent = stats.total_memory_entries;
                
                const sessionsResponse = await fetch('/api/sessions');
                const sessions = await sessionsResponse.json();
                document.getElementById('activeSessions').textContent = sessions.length;
                
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        async function showSessions() {
            try {
                const response = await fetch('/api/sessions');
                const sessions = await response.json();
                
                let sessionsText = 'Sessions:\\n';
                sessions.forEach(session => {
                    sessionsText += `- ${session.session_id} (${session.message_count} messages)\\n`;
                });
                
                alert(sessionsText);
            } catch (error) {
                alert('Error loading sessions: ' + error.message);
            }
        }

        async function showWorkflow() {
            if (!currentSessionId) {
                alert('No active session');
                return;
            }
            
            try {
                const response = await fetch(`/api/sessions/${currentSessionId}/workflow`);
                const workflow = await response.json();
                
                let workflowText = 'Workflow Steps:\\n';
                workflow.forEach(step => {
                    workflowText += `- ${step.type} (${step.timestamp})\\n`;
                });
                
                alert(workflowText);
            } catch (error) {
                alert('Error loading workflow: ' + error.message);
            }
        }

        async function showServers() {
            try {
                const response = await fetch('/api/servers');
                const data = await response.json();
                
                let serversText = 'MCP Servers:\\n';
                data.servers.forEach(server => {
                    const status = server.health.healthy ? '🟢' : '🔴';
                    serversText += `${status} ${server.name} (${server.config.host}:${server.config.port})\\n`;
                });
                
                alert(serversText);
            } catch (error) {
                alert('Error loading servers: ' + error.message);
            }
        }

        function clearChat() {
            document.getElementById('chatMessages').innerHTML = `
                <div class="message assistant-message">
                    Hello! I'm your Agentic AI assistant. I can help you with various tasks including file operations, database queries, API calls, and MCP server interactions. How can I assist you today?
                </div>
            `;
            currentSessionId = null;
            messageCount = 0;
            updateSessionInfo();
            updateMessageCount();
        }
    </script>
</body>
</html>
"""

def create_web_app() -> FastAPI:
    """Create and configure the FastAPI web application."""
    app = FastAPI(
        title="Agentic AI Orchestration",
        description="Intelligent Conversational AI Agent",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        global agent, settings
        settings = Settings.from_yaml("config/settings.yaml")
        agent = AgenticAgent(settings)
        await agent.mcp_manager.initialize()
        await agent.verification_manager.initialize()
        await agent.session_manager.start_cleanup_task()
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        if agent:
            await agent.shutdown()
    
    # Chat endpoint
    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            result = await agent.process_input(
                request.message, request.session_id, request.user_id
            )
            
            return ChatResponse(
                response=result["response"],
                session_id=result["session_id"],
                status=result["status"],
                metadata=result.get("metadata")
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Sessions endpoints
    @app.get("/api/sessions", response_model=List[SessionInfo])
    async def list_sessions(user_id: Optional[str] = None):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            sessions = await agent.list_sessions(user_id)
            return [
                SessionInfo(
                    session_id=session["session_id"],
                    user_id=session.get("user_id"),
                    created_at=session["created_at"],
                    last_accessed=session["last_accessed"],
                    message_count=len(session.get("messages", []))
                )
                for session in sessions
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/sessions/{session_id}/history")
    async def get_session_history(session_id: str):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            history = await agent.get_session_history(session_id)
            return {"messages": history}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            success = await agent.delete_session(session_id)
            if success:
                return {"message": "Session deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Session not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Workflow endpoints
    @app.get("/api/sessions/{session_id}/workflow", response_model=List[WorkflowStep])
    async def get_workflow_trace(session_id: str):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            workflow = await agent.get_workflow_trace(session_id)
            return [
                WorkflowStep(
                    step_id=step.get("step_id", ""),
                    type=step.get("type", ""),
                    timestamp=step.get("timestamp", ""),
                    data=step.get("data", {})
                )
                for step in workflow
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Memory endpoints
    @app.get("/api/memory/stats", response_model=MemoryStats)
    async def get_memory_stats():
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            stats = await agent.memory_manager.get_memory_stats()
            return MemoryStats(
                total_memory_entries=stats.get("total_memory_entries", 0),
                total_contexts=stats.get("total_contexts", 0),
                total_knowledge_domains=stats.get("total_knowledge_domains", 0),
                estimated_size_bytes=stats.get("estimated_size_bytes", 0)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Servers endpoints
    @app.get("/api/servers")
    async def list_servers():
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            servers = await agent.mcp_manager.list_servers()
            return {"servers": servers}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Session export/import endpoints
    @app.post("/api/sessions/{session_id}/export")
    async def export_session(session_id: str):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            export_data = await agent.session_manager.export_session(session_id)
            if export_data:
                return export_data
            else:
                raise HTTPException(status_code=404, detail="Session not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/sessions/import")
    async def import_session(session_data: Dict[str, Any]):
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            new_session_id = await agent.session_manager.import_session(session_data)
            return {"session_id": new_session_id, "message": "Session imported successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "agent_initialized": agent is not None,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    # WebSocket endpoint for real-time chat
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if not agent:
                    await websocket.send_text(json.dumps({
                        "error": "Agent not initialized"
                    }))
                    continue
                
                try:
                    result = await agent.process_input(
                        message_data.get("message", ""),
                        message_data.get("session_id"),
                        message_data.get("user_id")
                    )
                    
                    await websocket.send_text(json.dumps(result))
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "error": str(e)
                    }))
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_text(json.dumps({
                "error": str(e)
            }))
    
    # Add HTML routes
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return HTML_TEMPLATE
    
    @app.get("/index.html", response_class=HTMLResponse)
    async def index():
        return HTML_TEMPLATE
    
    return app 