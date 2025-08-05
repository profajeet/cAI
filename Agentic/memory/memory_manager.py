"""
Memory management for the Agentic AI Orchestration system.

This module provides the MemoryManager class that handles memory
storage, retrieval, and management.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings

console = Console()


class MemoryManager:
    """
    Manages memory storage and retrieval.
    
    This class provides:
    - Memory storage and retrieval
    - Context management
    - Knowledge persistence
    - Memory cleanup and optimization
    """
    
    def __init__(self, settings: Settings):
        """Initialize the memory manager."""
        self.settings = settings
        
        # Memory storage
        self.memory_store: Dict[str, Any] = {}
        
        # Context cache
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        
        # Knowledge base
        self.knowledge_base: Dict[str, Any] = {}
        
        console.log("🧠 MemoryManager initialized")
    
    async def store_memory(
        self, 
        key: str, 
        data: Any, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store data in memory.
        
        Args:
            key: Memory key
            data: Data to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            memory_entry = {
                "data": data,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
                "access_count": 0,
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            self.memory_store[key] = memory_entry
            
            console.log(f"🧠 Stored memory: {key}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error storing memory {key}: {e}")
            return False
    
    async def retrieve_memory(self, key: str) -> Optional[Any]:
        """
        Retrieve data from memory.
        
        Args:
            key: Memory key
            
        Returns:
            Stored data or None if not found
        """
        if key not in self.memory_store:
            return None
        
        memory_entry = self.memory_store[key]
        
        # Update access statistics
        memory_entry["access_count"] += 1
        memory_entry["last_accessed"] = datetime.utcnow().isoformat()
        
        return memory_entry["data"]
    
    async def store_context(
        self, 
        session_id: str, 
        context_data: Dict[str, Any]
    ) -> bool:
        """
        Store context for a session.
        
        Args:
            session_id: Session ID
            context_data: Context data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if session_id not in self.context_cache:
                self.context_cache[session_id] = {}
            
            # Merge context data
            self.context_cache[session_id].update(context_data)
            
            # Add timestamp
            self.context_cache[session_id]["last_updated"] = datetime.utcnow().isoformat()
            
            console.log(f"🧠 Stored context for session: {session_id}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error storing context for session {session_id}: {e}")
            return False
    
    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get context for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Context data
        """
        return self.context_cache.get(session_id, {})
    
    async def store_knowledge(
        self, 
        domain: str, 
        knowledge_data: Dict[str, Any]
    ) -> bool:
        """
        Store knowledge in the knowledge base.
        
        Args:
            domain: Knowledge domain
            knowledge_data: Knowledge data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if domain not in self.knowledge_base:
                self.knowledge_base[domain] = {}
            
            # Add timestamp
            knowledge_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Store knowledge
            self.knowledge_base[domain].update(knowledge_data)
            
            console.log(f"🧠 Stored knowledge in domain: {domain}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error storing knowledge in domain {domain}: {e}")
            return False
    
    async def get_knowledge(self, domain: str) -> Dict[str, Any]:
        """
        Get knowledge from a domain.
        
        Args:
            domain: Knowledge domain
            
        Returns:
            Knowledge data
        """
        return self.knowledge_base.get(domain, {})
    
    async def store_action_results(
        self, 
        session_id: str, 
        action_results: Dict[str, Any]
    ) -> bool:
        """
        Store action results in memory.
        
        Args:
            session_id: Session ID
            action_results: Action results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"action_results_{session_id}"
            
            # Get existing results
            existing_results = await self.retrieve_memory(key) or {}
            
            # Merge new results
            existing_results.update(action_results)
            
            # Store updated results
            await self.store_memory(key, existing_results, {
                "session_id": session_id,
                "type": "action_results"
            })
            
            return True
            
        except Exception as e:
            console.log(f"❌ Error storing action results for session {session_id}: {e}")
            return False
    
    async def get_action_results(self, session_id: str) -> Dict[str, Any]:
        """
        Get action results for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Action results
        """
        key = f"action_results_{session_id}"
        return await self.retrieve_memory(key) or {}
    
    async def search_memory(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memory for relevant entries.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        results = []
        query_lower = query.lower()
        
        for key, entry in self.memory_store.items():
            # Simple text search
            if (query_lower in key.lower() or 
                query_lower in str(entry["data"]).lower()):
                
                results.append({
                    "key": key,
                    "data": entry["data"],
                    "metadata": entry["metadata"],
                    "timestamp": entry["timestamp"],
                    "access_count": entry["access_count"]
                })
        
        # Sort by relevance (access count and recency)
        results.sort(key=lambda x: (
            x["access_count"], 
            x["timestamp"]
        ), reverse=True)
        
        return results[:limit]
    
    async def cleanup_old_memory(self, days: int = 30) -> int:
        """
        Clean up old memory entries.
        
        Args:
            days: Number of days to keep memory
            
        Returns:
            Number of entries cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleaned_count = 0
            
            keys_to_remove = []
            
            for key, entry in self.memory_store.items():
                entry_date = datetime.fromisoformat(entry["timestamp"])
                if entry_date < cutoff_date:
                    keys_to_remove.append(key)
            
            # Remove old entries
            for key in keys_to_remove:
                del self.memory_store[key]
                cleaned_count += 1
            
            console.log(f"🧹 Cleaned up {cleaned_count} old memory entries")
            return cleaned_count
            
        except Exception as e:
            console.log(f"❌ Error cleaning up memory: {e}")
            return 0
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Memory statistics
        """
        total_entries = len(self.memory_store)
        total_contexts = len(self.context_cache)
        total_knowledge_domains = len(self.knowledge_base)
        
        # Calculate total size (rough estimate)
        total_size = 0
        for entry in self.memory_store.values():
            total_size += len(str(entry))
        
        stats = {
            "total_memory_entries": total_entries,
            "total_contexts": total_contexts,
            "total_knowledge_domains": total_knowledge_domains,
            "estimated_size_bytes": total_size,
            "most_accessed": self._get_most_accessed_entries(),
            "recent_entries": self._get_recent_entries()
        }
        
        return stats
    
    def _get_most_accessed_entries(self) -> List[Dict[str, Any]]:
        """Get most accessed memory entries."""
        entries = []
        
        for key, entry in self.memory_store.items():
            entries.append({
                "key": key,
                "access_count": entry["access_count"],
                "last_accessed": entry["last_accessed"]
            })
        
        # Sort by access count
        entries.sort(key=lambda x: x["access_count"], reverse=True)
        
        return entries[:5]
    
    def _get_recent_entries(self) -> List[Dict[str, Any]]:
        """Get recent memory entries."""
        entries = []
        
        for key, entry in self.memory_store.items():
            entries.append({
                "key": key,
                "timestamp": entry["timestamp"],
                "access_count": entry["access_count"]
            })
        
        # Sort by timestamp
        entries.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return entries[:5]
    
    async def export_memory(self) -> Dict[str, Any]:
        """
        Export all memory data.
        
        Returns:
            Exported memory data
        """
        export_data = {
            "memory_store": self.memory_store,
            "context_cache": self.context_cache,
            "knowledge_base": self.knowledge_base,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return export_data
    
    async def import_memory(self, memory_data: Dict[str, Any]) -> bool:
        """
        Import memory data.
        
        Args:
            memory_data: Memory data to import
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "memory_store" in memory_data:
                self.memory_store.update(memory_data["memory_store"])
            
            if "context_cache" in memory_data:
                self.context_cache.update(memory_data["context_cache"])
            
            if "knowledge_base" in memory_data:
                self.knowledge_base.update(memory_data["knowledge_base"])
            
            console.log("📥 Imported memory data successfully")
            return True
            
        except Exception as e:
            console.log(f"❌ Error importing memory data: {e}")
            return False
    
    async def clear_memory(self, memory_type: Optional[str] = None):
        """
        Clear memory.
        
        Args:
            memory_type: Type of memory to clear (None for all)
        """
        if memory_type is None:
            self.memory_store.clear()
            self.context_cache.clear()
            self.knowledge_base.clear()
            console.log("🧹 Cleared all memory")
        elif memory_type == "memory_store":
            self.memory_store.clear()
            console.log("🧹 Cleared memory store")
        elif memory_type == "context_cache":
            self.context_cache.clear()
            console.log("🧹 Cleared context cache")
        elif memory_type == "knowledge_base":
            self.knowledge_base.clear()
            console.log("🧹 Cleared knowledge base")
    
    async def shutdown(self):
        """Shutdown the memory manager."""
        console.log("🔄 Shutting down MemoryManager...")
        
        # Save memory to persistent storage if needed
        # This could be implemented to save to disk/database
        
        console.log("✅ MemoryManager shutdown complete") 