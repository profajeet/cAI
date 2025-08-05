"""
Session storage for the Agentic AI Orchestration system.

This module provides the SessionStore class that handles session
persistence and storage.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings

console = Console()


class SessionStore:
    """
    Handles session persistence and storage.
    
    This class provides:
    - Session storage and retrieval
    - Session listing and management
    - Session cleanup
    """
    
    def __init__(self, settings: Settings):
        """Initialize the session store."""
        self.settings = settings
        self.storage_dir = "data/sessions"
        
        # Create storage directory
        os.makedirs(self.storage_dir, exist_ok=True)
        
        console.log("💾 SessionStore initialized")
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data to storage.
        
        Args:
            session_id: Session ID
            session_data: Session data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{session_id}.json")
            
            # Save to file
            with open(filename, "w") as f:
                json.dump(session_data, f, indent=2)
            
            return True
            
        except Exception as e:
            console.log(f"❌ Error saving session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data from storage.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{session_id}.json")
            
            # Check if file exists
            if not os.path.exists(filename):
                return None
            
            # Load from file
            with open(filename, "r") as f:
                session_data = json.load(f)
            
            return session_data
            
        except Exception as e:
            console.log(f"❌ Error loading session {session_id}: {e}")
            return None
    
    async def list_sessions(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List sessions from storage.
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        try:
            sessions = []
            
            # List all session files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]  # Remove .json extension
                    
                    # Load session data
                    session_data = await self.get_session(session_id)
                    
                    if session_data:
                        # Filter by user ID if specified
                        if user_id is None or session_data.get("user_id") == user_id:
                            sessions.append(session_data)
            
            # Sort by last accessed time
            sessions.sort(key=lambda x: x.get("last_accessed", ""), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            console.log(f"❌ Error listing sessions: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from storage.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{session_id}.json")
            
            # Check if file exists
            if not os.path.exists(filename):
                return False
            
            # Delete file
            os.remove(filename)
            
            console.log(f"🗑️ Deleted session: {session_id}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error deleting session {session_id}: {e}")
            return False
    
    async def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up old sessions.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleaned_count = 0
            
            # List all session files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]
                    
                    # Load session data
                    session_data = await self.get_session(session_id)
                    
                    if session_data:
                        # Check last accessed time
                        last_accessed = session_data.get("last_accessed")
                        if last_accessed:
                            try:
                                session_date = datetime.fromisoformat(last_accessed)
                                if session_date < cutoff_date:
                                    # Delete old session
                                    if await self.delete_session(session_id):
                                        cleaned_count += 1
                            except Exception:
                                # Skip sessions with invalid dates
                                pass
            
            console.log(f"🧹 Cleaned up {cleaned_count} old sessions")
            return cleaned_count
            
        except Exception as e:
            console.log(f"❌ Error cleaning up sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session storage statistics.
        
        Returns:
            Session storage statistics
        """
        try:
            total_sessions = 0
            total_size = 0
            
            # Count sessions and calculate size
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    total_sessions += 1
                    
                    filepath = os.path.join(self.storage_dir, filename)
                    total_size += os.path.getsize(filepath)
            
            return {
                "total_sessions": total_sessions,
                "total_size_bytes": total_size,
                "storage_directory": self.storage_dir
            }
            
        except Exception as e:
            console.log(f"❌ Error getting session stats: {e}")
            return {
                "total_sessions": 0,
                "total_size_bytes": 0,
                "storage_directory": self.storage_dir
            } 