"""
Context-aware task understanding and analysis.

This module provides the ContextManager class that analyzes user input
to understand intent, extract entities, and determine required actions.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console

from config.settings import Settings

console = Console()


class ContextManager:
    """
    Manages context-aware task understanding and analysis.
    
    This class provides:
    - Intent recognition
    - Entity extraction
    - Context analysis
    - Task breakdown
    """
    
    def __init__(self, settings: Settings):
        """Initialize the context manager."""
        self.settings = settings
        
        # Intent patterns
        self.intent_patterns = {
            "file_operation": [
                r"(load|read|write|save|copy|move|delete)\s+(?:the\s+)?(?:file|files)\s+(.+?)(?:\s+into\s+(.+))?",
                r"(upload|download)\s+(?:the\s+)?(?:file|files)\s+(.+?)",
                r"open\s+(?:the\s+)?(?:file|files)\s+(.+)",
                r"create\s+(?:a\s+)?(?:new\s+)?(?:file|directory|folder)\s+(.+)",
            ],
            "database_operation": [
                r"(load|insert|update|delete|query|select)\s+(?:data|records|rows)\s+(?:from|into|in)\s+(.+?)(?:\s+database)?",
                r"connect\s+to\s+(?:the\s+)?(?:database|db)\s+(.+)",
                r"create\s+(?:a\s+)?(?:new\s+)?(?:table|database)\s+(.+)",
                r"backup\s+(?:the\s+)?(?:database|db)\s+(.+)",
            ],
            "api_operation": [
                r"(call|invoke|request|get|post|put|delete)\s+(?:the\s+)?(?:api|endpoint|service)\s+(.+)",
                r"fetch\s+(?:data|information)\s+from\s+(.+)",
                r"send\s+(?:a\s+)?(?:request|message)\s+to\s+(.+)",
            ],
            "mcp_operation": [
                r"(use|connect\s+to|call)\s+(?:the\s+)?(?:mcp\s+)?(?:server|service)\s+(.+)",
                r"activate\s+(?:the\s+)?(?:mcp\s+)?(?:server|service)\s+(.+)",
                r"run\s+(?:the\s+)?(?:mcp\s+)?(?:server|service)\s+(.+)",
            ],
            "general_query": [
                r"(what|how|when|where|why|can\s+you|please)\s+(.+)",
                r"(help|assist|support)\s+(?:me\s+)?(?:with\s+)?(.+)",
            ],
            "system_operation": [
                r"(start|stop|restart|check\s+status)\s+(?:the\s+)?(?:system|service|server)\s+(.+)",
                r"(configure|setup|install)\s+(?:the\s+)?(?:system|service|server)\s+(.+)",
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            "file_paths": [
                r"([\/\\][\w\-\.\/\\]+\.\w+)",
                r"([A-Za-z]:[\/\\][\w\-\.\/\\]+)",
                r"(\w+\.\w+)",
            ],
            "database_names": [
                r"(?:database|db)\s+([\w\-_]+)",
                r"table\s+([\w\-_]+)",
                r"schema\s+([\w\-_]+)",
            ],
            "urls": [
                r"(https?:\/\/[^\s]+)",
                r"(www\.[^\s]+)",
            ],
            "mcp_servers": [
                r"(?:mcp\s+)?(?:server|service)\s+([\w\-_]+)",
                r"([\w\-_]+)\s+(?:mcp\s+)?(?:server|service)",
            ],
            "api_endpoints": [
                r"(?:api|endpoint)\s+([\/\w\-_]+)",
                r"([\/\w\-_]+)\s+(?:api|endpoint)",
            ]
        }
        
        console.log("🧠 ContextManager initialized")
    
    async def analyze_input(
        self, 
        user_input: str, 
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user input to understand intent and extract entities.
        
        Args:
            user_input: The user's input text
            session: Current session data
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Normalize input
            normalized_input = self._normalize_input(user_input)
            
            # Detect intent
            intent = await self._detect_intent(normalized_input)
            
            # Extract entities
            entities = await self._extract_entities(normalized_input, intent)
            
            # Analyze context
            context = await self._analyze_context(session, intent, entities)
            
            # Determine confidence
            confidence = self._calculate_confidence(intent, entities, context)
            
            # Build analysis result
            analysis = {
                "original_input": user_input,
                "normalized_input": normalized_input,
                "intent": intent,
                "entities": entities,
                "context": context,
                "confidence": confidence,
                "timestamp": self._get_timestamp()
            }
            
            console.log(f"🔍 Context analysis: {intent.get('type', 'unknown')} intent detected")
            
            return analysis
            
        except Exception as e:
            console.log(f"❌ Error in context analysis: {e}")
            return {
                "original_input": user_input,
                "intent": {"type": "unknown", "confidence": 0.0},
                "entities": {},
                "context": {},
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _normalize_input(self, user_input: str) -> str:
        """Normalize user input for better analysis."""
        # Convert to lowercase
        normalized = user_input.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove punctuation that might interfere with pattern matching
        normalized = re.sub(r'[^\w\s\/\\\-_\.:]', ' ', normalized)
        
        return normalized
    
    async def _detect_intent(self, normalized_input: str) -> Dict[str, Any]:
        """Detect the intent of the user input."""
        best_match = None
        best_confidence = 0.0
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, normalized_input, re.IGNORECASE)
                if match:
                    confidence = self._calculate_pattern_confidence(
                        pattern, match, normalized_input
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            "type": intent_type,
                            "confidence": confidence,
                            "pattern": pattern,
                            "match": match.group(0),
                            "groups": match.groups()
                        }
        
        if best_match:
            return best_match
        else:
            return {
                "type": "general_query",
                "confidence": 0.1,
                "pattern": None,
                "match": None,
                "groups": ()
            }
    
    async def _extract_entities(
        self, 
        normalized_input: str, 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract entities from the user input."""
        entities = {}
        
        # Extract based on intent type
        if intent.get("type") == "file_operation":
            entities["file_paths"] = self._extract_file_paths(normalized_input)
            entities["operations"] = self._extract_file_operations(normalized_input)
            
        elif intent.get("type") == "database_operation":
            entities["database"] = self._extract_database_info(normalized_input)
            entities["operations"] = self._extract_database_operations(normalized_input)
            
        elif intent.get("type") == "api_operation":
            entities["api_endpoints"] = self._extract_api_endpoints(normalized_input)
            entities["operations"] = self._extract_api_operations(normalized_input)
            
        elif intent.get("type") == "mcp_operation":
            entities["mcp_server"] = self._extract_mcp_server(normalized_input)
            entities["operations"] = self._extract_mcp_operations(normalized_input)
        
        # Extract general entities
        entities["urls"] = self._extract_urls(normalized_input)
        entities["keywords"] = self._extract_keywords(normalized_input)
        
        return entities
    
    async def _analyze_context(
        self, 
        session: Dict[str, Any], 
        intent: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze the context based on session history and current intent."""
        context = {
            "session_history": len(session.get("messages", [])),
            "previous_intents": self._get_previous_intents(session),
            "user_preferences": session.get("context", {}).get("preferences", {}),
            "current_task": self._identify_current_task(session, intent),
            "required_clarification": self._needs_clarification(intent, entities)
        }
        
        return context
    
    def _calculate_confidence(
        self, 
        intent: Dict[str, Any], 
        entities: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the analysis."""
        base_confidence = intent.get("confidence", 0.0)
        
        # Adjust based on entity extraction
        if entities:
            entity_confidence = min(1.0, len(entities) * 0.2)
            base_confidence = (base_confidence + entity_confidence) / 2
        
        # Adjust based on context
        if context.get("session_history", 0) > 0:
            base_confidence += 0.1
        
        # Adjust based on clarification needs
        if context.get("required_clarification"):
            base_confidence -= 0.2
        
        return min(1.0, max(0.0, base_confidence))
    
    def _calculate_pattern_confidence(
        self, 
        pattern: str, 
        match: re.Match, 
        input_text: str
    ) -> float:
        """Calculate confidence for a pattern match."""
        # Base confidence from pattern complexity
        base_confidence = 0.5
        
        # Adjust based on match length vs input length
        match_ratio = len(match.group(0)) / len(input_text)
        base_confidence += match_ratio * 0.3
        
        # Adjust based on pattern specificity
        if "\\" in pattern or "/" in pattern:
            base_confidence += 0.2  # File paths are specific
        
        if "database" in pattern or "db" in pattern:
            base_confidence += 0.2  # Database operations are specific
        
        return min(1.0, base_confidence)
    
    def _extract_file_paths(self, text: str) -> List[str]:
        """Extract file paths from text."""
        paths = []
        for pattern in self.entity_patterns["file_paths"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            paths.extend(matches)
        return list(set(paths))
    
    def _extract_file_operations(self, text: str) -> List[str]:
        """Extract file operations from text."""
        operations = []
        file_ops = ["load", "read", "write", "save", "copy", "move", "delete", "upload", "download", "open", "create"]
        
        for op in file_ops:
            if op in text:
                operations.append(op)
        
        return operations
    
    def _extract_database_info(self, text: str) -> Dict[str, Any]:
        """Extract database information from text."""
        db_info = {}
        
        # Extract database name
        for pattern in self.entity_patterns["database_names"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                db_info["name"] = match.group(1)
                break
        
        # Extract database type
        db_types = ["postgresql", "mysql", "sqlite", "mongodb", "redis"]
        for db_type in db_types:
            if db_type in text:
                db_info["type"] = db_type
                break
        
        return db_info
    
    def _extract_database_operations(self, text: str) -> List[str]:
        """Extract database operations from text."""
        operations = []
        db_ops = ["load", "insert", "update", "delete", "query", "select", "connect", "create", "backup"]
        
        for op in db_ops:
            if op in text:
                operations.append(op)
        
        return operations
    
    def _extract_api_endpoints(self, text: str) -> List[str]:
        """Extract API endpoints from text."""
        endpoints = []
        for pattern in self.entity_patterns["api_endpoints"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            endpoints.extend(matches)
        return list(set(endpoints))
    
    def _extract_api_operations(self, text: str) -> List[str]:
        """Extract API operations from text."""
        operations = []
        api_ops = ["call", "invoke", "request", "get", "post", "put", "delete", "fetch", "send"]
        
        for op in api_ops:
            if op in text:
                operations.append(op)
        
        return operations
    
    def _extract_mcp_server(self, text: str) -> Optional[str]:
        """Extract MCP server name from text."""
        for pattern in self.entity_patterns["mcp_servers"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_mcp_operations(self, text: str) -> List[str]:
        """Extract MCP operations from text."""
        operations = []
        mcp_ops = ["use", "connect", "call", "activate", "run"]
        
        for op in mcp_ops:
            if op in text:
                operations.append(op)
        
        return operations
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        urls = []
        for pattern in self.entity_patterns["urls"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)
        return list(set(urls))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction - could be enhanced with NLP
        words = text.split()
        keywords = [word for word in words if len(word) > 3]
        return keywords[:10]  # Limit to top 10 keywords
    
    def _get_previous_intents(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get previous intents from session history."""
        intents = []
        messages = session.get("messages", [])
        
        for message in messages[-5:]:  # Last 5 messages
            if message.get("role") == "user":
                # This would need to be enhanced to store intent analysis
                # For now, return basic info
                intents.append({
                    "timestamp": message.get("timestamp"),
                    "content": message.get("content")[:50] + "..." if len(message.get("content", "")) > 50 else message.get("content", "")
                })
        
        return intents
    
    def _identify_current_task(self, session: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Identify the current task based on session and intent."""
        task = {
            "type": intent.get("type", "unknown"),
            "description": intent.get("match", ""),
            "in_progress": False,
            "steps_completed": 0,
            "total_steps": 1
        }
        
        # Check if this is a continuation of a previous task
        if session.get("context", {}).get("current_task"):
            previous_task = session["context"]["current_task"]
            if previous_task.get("type") == intent.get("type"):
                task["in_progress"] = True
                task["steps_completed"] = previous_task.get("steps_completed", 0)
        
        return task
    
    def _needs_clarification(self, intent: Dict[str, Any], entities: Dict[str, Any]) -> bool:
        """Determine if the input needs clarification."""
        # Check for missing required entities based on intent
        if intent.get("type") == "file_operation":
            if not entities.get("file_paths"):
                return True
        
        elif intent.get("type") == "database_operation":
            if not entities.get("database", {}).get("name"):
                return True
        
        elif intent.get("type") == "mcp_operation":
            if not entities.get("mcp_server"):
                return True
        
        return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() 