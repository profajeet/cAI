"""
Session management for the Agentic AI Orchestration system.

This module provides the SessionManager class that handles session
creation, storage, retrieval, and management.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings
from memory.session_store import SessionStore

console = Console()


class SessionManager:
    """
    Manages user sessions and conversation history.
    
    This class provides:
    - Session creation and management
    - Conversation history storage
    - Session persistence and retrieval
    - Session cleanup and maintenance
    """
    
    def __init__(self, settings: Settings):
        """Initialize the session manager."""
        self.settings = settings
        self.session_store = SessionStore(settings)
        
        # Active sessions cache
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Session cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
        console.log("📝 SessionManager initialized")
    
    async def create_session(
        self, 
        user_id: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            user_id: Optional user ID for multi-user support
            session_data: Optional initial session data
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "messages": [],
            "context": {},
            "metadata": session_data or {},
            "status": "active"
        }
        
        # Store session
        await self.session_store.save_session(session_id, session)
        
        # Add to active sessions
        self.active_sessions[session_id] = session
        
        console.log(f"📝 Created session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session data or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["last_accessed"] = datetime.utcnow().isoformat()
            return session
        
        # Load from storage
        session = await self.session_store.get_session(session_id)
        
        if session:
            # Add to active sessions
            self.active_sessions[session_id] = session
            session["last_accessed"] = datetime.utcnow().isoformat()
            
            console.log(f"📝 Loaded session: {session_id}")
        
        return session
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data.
        
        Args:
            session_id: The session ID
            session_data: The session data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last accessed time
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            
            # Save to storage
            await self.session_store.save_session(session_id, session_data)
            
            # Update active sessions
            self.active_sessions[session_id] = session_data
            
            return True
            
        except Exception as e:
            console.log(f"❌ Error saving session {session_id}: {e}")
            return False
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to a session.
        
        Args:
            session_id: The session ID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        
        if not session:
            console.log(f"❌ Session not found: {session_id}")
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        session["messages"].append(message)
        
        # Limit message history to prevent memory issues
        max_messages = self.settings.session_storage.get("max_messages", 100)
        if len(session["messages"]) > max_messages:
            session["messages"] = session["messages"][-max_messages:]
        
        return await self.save_session(session_id, session)
    
    async def update_context(
        self, 
        session_id: str, 
        context_data: Dict[str, Any]
    ) -> bool:
        """
        Update session context.
        
        Args:
            session_id: The session ID
            context_data: Context data to update
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        
        if not session:
            return False
        
        # Merge context data
        session["context"].update(context_data)
        
        return await self.save_session(session_id, session)
    
    async def list_sessions(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List sessions.
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        sessions = await self.session_store.list_sessions(user_id, limit)
        
        # Add active session status
        for session in sessions:
            if session["session_id"] in self.active_sessions:
                session["status"] = "active"
        
        return sessions
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from active sessions
            self.active_sessions.pop(session_id, None)
            
            # Delete from storage
            await self.session_store.delete_session(session_id)
            
            console.log(f"🗑️ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error deleting session {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Get session timeout
            timeout_hours = self.settings.session_cleanup_interval // 3600
            
            # Find expired sessions
            expired_sessions = []
            current_time = datetime.utcnow()
            
            for session_id, session in self.active_sessions.items():
                last_accessed = datetime.fromisoformat(session["last_accessed"])
                if current_time - last_accessed > timedelta(hours=timeout_hours):
                    expired_sessions.append(session_id)
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                await self.delete_session(session_id)
            
            console.log(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)
            
        except Exception as e:
            console.log(f"❌ Error cleaning up sessions: {e}")
            return 0
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session statistics
        """
        session = await self.get_session(session_id)
        
        if not session:
            return {}
        
        messages = session.get("messages", [])
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        
        stats = {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "session_duration": self._calculate_session_duration(session),
            "last_activity": session.get("last_accessed"),
            "created_at": session.get("created_at")
        }
        
        return stats
    
    def _calculate_session_duration(self, session: Dict[str, Any]) -> Optional[str]:
        """Calculate session duration."""
        try:
            created_at = datetime.fromisoformat(session["created_at"])
            last_accessed = datetime.fromisoformat(session["last_accessed"])
            duration = last_accessed - created_at
            
            # Format duration
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            
            if hours > 0:
                return f"{int(hours)}h {int(minutes)}m"
            else:
                return f"{int(minutes)}m"
                
        except Exception:
            return None
    
    async def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export session data.
        
        Args:
            session_id: The session ID
            
        Returns:
            Exported session data or None if not found
        """
        session = await self.get_session(session_id)
        
        if not session:
            return None
        
        # Create export data
        export_data = {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "created_at": session["created_at"],
            "last_accessed": session["last_accessed"],
            "messages": session["messages"],
            "context": session["context"],
            "metadata": session["metadata"],
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return export_data
    
    async def import_session(self, session_data: Dict[str, Any]) -> str:
        """
        Import session data.
        
        Args:
            session_data: Session data to import
            
        Returns:
            New session ID
        """
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        
        # Create new session with imported data
        session = {
            "session_id": new_session_id,
            "user_id": session_data.get("user_id"),
            "created_at": session_data.get("created_at", datetime.utcnow().isoformat()),
            "last_accessed": datetime.utcnow().isoformat(),
            "messages": session_data.get("messages", []),
            "context": session_data.get("context", {}),
            "metadata": session_data.get("metadata", {}),
            "status": "active"
        }
        
        # Save session
        await self.save_session(new_session_id, session)
        
        console.log(f"📥 Imported session as: {new_session_id}")
        return new_session_id
    
    async def start_cleanup_task(self):
        """Start the session cleanup task."""
        if self.cleanup_task and not self.cleanup_task.done():
            return
        
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        console.log("🧹 Started session cleanup task")
    
    async def stop_cleanup_task(self):
        """Stop the session cleanup task."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            console.log("🛑 Stopped session cleanup task")
    
    async def _cleanup_loop(self):
        """Cleanup loop for expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.settings.session_cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.log(f"❌ Error in cleanup loop: {e}")
    
    async def shutdown(self):
        """Shutdown the session manager."""
        await self.stop_cleanup_task()
        
        # Save all active sessions
        for session_id, session in self.active_sessions.items():
            await self.save_session(session_id, session)
        
        console.log("🔄 SessionManager shutdown complete") 