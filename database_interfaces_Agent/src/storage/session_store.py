"""
Session store for managing encrypted session data with TTL support.
Uses Redis for persistence and encryption for security.
"""

import json
import uuid
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import asyncio

import redis.asyncio as redis
from pydantic import BaseModel

# Add project root to path for config import
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.settings import settings
from src.agent.state import SessionState
from src.storage.encryption import EncryptionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SessionStore:
    """Session store for managing encrypted session data."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.encryption_manager = EncryptionManager()
        self.session_prefix = "db_agent_session:"
        self.reference_prefix = "db_agent_ref:"
        
    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Session store initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize session store: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Session store connection closed")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"{self.session_prefix}{uuid.uuid4().hex}"
    
    def _generate_reference_id(self) -> str:
        """Generate a unique reference ID."""
        return f"{self.reference_prefix}{uuid.uuid4().hex[:12]}"
    
    async def create_session(self, ttl: Optional[int] = None) -> SessionState:
        """Create a new session."""
        try:
            session_id = self._generate_session_id()
            reference_id = self._generate_reference_id()
            
            if ttl is None:
                ttl = settings.session_ttl
            
            session = SessionState(
                session_id=session_id,
                reference_id=reference_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl,
                is_active=True
            )
            
            # Encrypt and store session data
            session_data = session.model_dump_json()
            encrypted_data = self.encryption_manager.encrypt(session_data)
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                session_id,
                ttl,
                encrypted_data
            )
            
            # Store reference ID mapping
            await self.redis_client.setex(
                reference_id,
                ttl,
                session_id
            )
            
            logger.info(f"Created session {reference_id} with TTL {ttl}s")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    async def get_session_by_reference_id(self, reference_id: str) -> Optional[SessionState]:
        """Get session by reference ID."""
        try:
            # Get session ID from reference mapping
            session_id = await self.redis_client.get(reference_id)
            if not session_id:
                logger.warning(f"Reference ID {reference_id} not found")
                return None
            
            # Get session data
            encrypted_data = await self.redis_client.get(session_id)
            if not encrypted_data:
                logger.warning(f"Session {session_id} not found")
                return None
            
            # Decrypt and parse session data
            session_data = self.encryption_manager.decrypt(encrypted_data)
            session = SessionState.model_validate_json(session_data)
            
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Refresh TTL
            await self.redis_client.expire(session_id, session.ttl)
            await self.redis_client.expire(reference_id, session.ttl)
            
            logger.info(f"Retrieved session {reference_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session {reference_id}: {str(e)}")
            return None
    
    async def update_session(self, session: SessionState) -> bool:
        """Update session data."""
        try:
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Encrypt and store updated session data
            session_data = session.model_dump_json()
            encrypted_data = self.encryption_manager.encrypt(session_data)
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                session.session_id,
                session.ttl,
                encrypted_data
            )
            
            # Update reference ID mapping TTL
            await self.redis_client.expire(session.reference_id, session.ttl)
            
            logger.info(f"Updated session {session.reference_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session.reference_id}: {str(e)}")
            return False
    
    async def delete_session(self, reference_id: str) -> bool:
        """Delete session by reference ID."""
        try:
            # Get session ID from reference mapping
            session_id = await self.redis_client.get(reference_id)
            if not session_id:
                logger.warning(f"Reference ID {reference_id} not found for deletion")
                return False
            
            # Delete session data and reference mapping
            await self.redis_client.delete(session_id, reference_id)
            
            logger.info(f"Deleted session {reference_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {reference_id}: {str(e)}")
            return False
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        try:
            sessions = []
            
            # Get all session keys
            session_keys = await self.redis_client.keys(f"{self.session_prefix}*")
            
            for session_key in session_keys:
                try:
                    encrypted_data = await self.redis_client.get(session_key)
                    if encrypted_data:
                        session_data = self.encryption_manager.decrypt(encrypted_data)
                        session = SessionState.model_validate_json(session_data)
                        
                        # Get TTL
                        ttl = await self.redis_client.ttl(session_key)
                        
                        sessions.append({
                            "reference_id": session.reference_id,
                            "created_at": session.created_at.isoformat(),
                            "last_accessed": session.last_accessed.isoformat(),
                            "ttl": ttl,
                            "is_active": session.is_active,
                            "agent_status": session.agent_status.value,
                            "connection_status": session.connection_status.value
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing session {session_key}: {str(e)}")
                    continue
            
            logger.info(f"Listed {len(sessions)} active sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing active sessions: {str(e)}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            # Redis automatically handles TTL expiration
            # This method can be used for additional cleanup if needed
            session_keys = await self.redis_client.keys(f"{self.session_prefix}*")
            expired_count = 0
            
            for session_key in session_keys:
                ttl = await self.redis_client.ttl(session_key)
                if ttl <= 0:
                    await self.redis_client.delete(session_key)
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session store statistics."""
        try:
            session_keys = await self.redis_client.keys(f"{self.session_prefix}*")
            reference_keys = await self.redis_client.keys(f"{self.reference_prefix}*")
            
            total_sessions = len(session_keys)
            total_references = len(reference_keys)
            
            # Get memory usage
            memory_info = await self.redis_client.info("memory")
            used_memory = memory_info.get("used_memory_human", "N/A")
            
            stats = {
                "total_sessions": total_sessions,
                "total_references": total_references,
                "used_memory": used_memory,
                "redis_host": settings.redis_host,
                "redis_port": settings.redis_port,
                "session_ttl": settings.session_ttl
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {
                "error": str(e),
                "total_sessions": 0,
                "total_references": 0
            }


# Global session store instance
session_store = SessionStore()


async def get_session_store() -> SessionStore:
    """Get the global session store instance."""
    if not session_store.redis_client:
        await session_store.initialize()
    return session_store 