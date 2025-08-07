from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    """Request model for user queries"""
    query: str
    user_id: Optional[str] = None

class ReasoningStep(BaseModel):
    """Model for individual reasoning steps"""
    step: str
    agent: str
    input: str
    output: str
    timestamp: str

class QueryResponse(BaseModel):
    """Response model with final result and reasoning steps"""
    final_result: str
    reasoning_steps: List[ReasoningStep]
    selected_agent: str
    success: bool
    error_message: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str 