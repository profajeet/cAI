"""
Workflow management and tracing for the Agentic AI Orchestration system.

This module provides the WorkflowManager class that handles workflow
tracing, decision logging, and workflow replay capabilities.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings
from memory.workflow_store import WorkflowStore

console = Console()


class WorkflowManager:
    """
    Manages workflow tracing and decision logging.
    
    This class provides:
    - Workflow step recording
    - Decision-making logs
    - API call tracing
    - Workflow replay support
    """
    
    def __init__(self, settings: Settings):
        """Initialize the workflow manager."""
        self.settings = settings
        self.workflow_store = WorkflowStore(settings)
        
        # Active workflows
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        console.log("🔄 WorkflowManager initialized")
    
    async def start_workflow(
        self, 
        session_id: str,
        workflow_type: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new workflow.
        
        Args:
            session_id: Associated session ID
            workflow_type: Type of workflow
            initial_data: Initial workflow data
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            "workflow_id": workflow_id,
            "session_id": session_id,
            "type": workflow_type,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": [],
            "metadata": initial_data or {},
            "performance_metrics": {
                "total_steps": 0,
                "total_duration": 0,
                "successful_steps": 0,
                "failed_steps": 0
            }
        }
        
        # Store workflow
        await self.workflow_store.save_workflow(workflow_id, workflow)
        
        # Add to active workflows
        self.active_workflows[workflow_id] = workflow
        
        console.log(f"🔄 Started workflow: {workflow_id} ({workflow_type})")
        return workflow_id
    
    async def record_step(
        self, 
        session_id: str,
        step_type: str,
        step_data: Dict[str, Any],
        workflow_id: Optional[str] = None
    ) -> str:
        """
        Record a workflow step.
        
        Args:
            session_id: Associated session ID
            step_type: Type of step
            step_data: Step data
            workflow_id: Optional workflow ID (will create new if not provided)
            
        Returns:
            Step ID
        """
        # Get or create workflow
        if not workflow_id:
            workflow_id = await self._get_or_create_workflow(session_id, step_type)
        
        step_id = str(uuid.uuid4())
        
        step = {
            "step_id": step_id,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "type": step_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": step_data,
            "status": "completed",
            "duration": 0,  # Will be calculated if start_time is provided
            "metadata": {}
        }
        
        # Add step to workflow
        workflow = await self._get_workflow(workflow_id)
        if workflow:
            workflow["steps"].append(step)
            workflow["updated_at"] = datetime.utcnow().isoformat()
            workflow["performance_metrics"]["total_steps"] += 1
            
            # Update performance metrics
            if step_data.get("success", True):
                workflow["performance_metrics"]["successful_steps"] += 1
            else:
                workflow["performance_metrics"]["failed_steps"] += 1
            
            # Save workflow
            await self.workflow_store.save_workflow(workflow_id, workflow)
        
        console.log(f"📝 Recorded step: {step_type} in workflow {workflow_id}")
        return step_id
    
    async def record_decision(
        self,
        session_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        alternatives: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Record a decision-making step.
        
        Args:
            session_id: Associated session ID
            decision_type: Type of decision
            decision_data: Decision data
            alternatives: Alternative options considered
            
        Returns:
            Decision ID
        """
        step_data = {
            "decision_type": decision_type,
            "decision": decision_data,
            "alternatives": alternatives or [],
            "reasoning": decision_data.get("reasoning", ""),
            "confidence": decision_data.get("confidence", 0.0)
        }
        
        return await self.record_step(session_id, "decision", step_data)
    
    async def record_api_call(
        self,
        session_id: str,
        api_name: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration: float
    ) -> str:
        """
        Record an API call.
        
        Args:
            session_id: Associated session ID
            api_name: Name of the API
            request_data: Request data
            response_data: Response data
            duration: Call duration in seconds
            
        Returns:
            API call ID
        """
        step_data = {
            "api_name": api_name,
            "request": request_data,
            "response": response_data,
            "duration": duration,
            "status": "success" if response_data.get("success", True) else "error",
            "error": response_data.get("error")
        }
        
        return await self.record_step(session_id, "api_call", step_data)
    
    async def record_tool_usage(
        self,
        session_id: str,
        tool_name: str,
        tool_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> str:
        """
        Record tool usage.
        
        Args:
            session_id: Associated session ID
            tool_name: Name of the tool
            tool_data: Tool input data
            result: Tool result
            
        Returns:
            Tool usage ID
        """
        step_data = {
            "tool_name": tool_name,
            "input": tool_data,
            "output": result,
            "success": result.get("success", True),
            "error": result.get("error")
        }
        
        return await self.record_step(session_id, "tool_usage", step_data)
    
    async def get_workflow_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get workflow trace for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of workflow steps
        """
        workflows = await self.workflow_store.get_workflows_by_session(session_id)
        
        all_steps = []
        for workflow in workflows:
            all_steps.extend(workflow.get("steps", []))
        
        # Sort by timestamp
        all_steps.sort(key=lambda x: x.get("timestamp", ""))
        
        return all_steps
    
    async def get_workflow_summary(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow summary.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow summary or None if not found
        """
        workflow = await self.workflow_store.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        steps = workflow.get("steps", [])
        
        summary = {
            "workflow_id": workflow_id,
            "session_id": workflow.get("session_id"),
            "type": workflow.get("type"),
            "status": workflow.get("status"),
            "created_at": workflow.get("created_at"),
            "updated_at": workflow.get("updated_at"),
            "total_steps": len(steps),
            "performance_metrics": workflow.get("performance_metrics", {}),
            "step_types": self._get_step_type_counts(steps),
            "duration": self._calculate_workflow_duration(workflow)
        }
        
        return summary
    
    async def replay_workflow(
        self, 
        workflow_id: str,
        replay_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Replay a workflow.
        
        Args:
            workflow_id: Workflow ID to replay
            replay_options: Replay options
            
        Returns:
            Replay results
        """
        workflow = await self.workflow_store.get_workflow(workflow_id)
        
        if not workflow:
            return {"error": "Workflow not found"}
        
        replay_results = {
            "workflow_id": workflow_id,
            "replay_started": datetime.utcnow().isoformat(),
            "steps_replayed": 0,
            "steps_skipped": 0,
            "errors": [],
            "results": []
        }
        
        steps = workflow.get("steps", [])
        
        for step in steps:
            try:
                result = await self._replay_step(step, replay_options)
                replay_results["results"].append(result)
                replay_results["steps_replayed"] += 1
                
            except Exception as e:
                replay_results["errors"].append({
                    "step_id": step.get("step_id"),
                    "error": str(e)
                })
        
        replay_results["replay_completed"] = datetime.utcnow().isoformat()
        
        console.log(f"🔄 Replayed workflow {workflow_id}: {replay_results['steps_replayed']} steps")
        
        return replay_results
    
    async def _get_or_create_workflow(
        self, 
        session_id: str, 
        step_type: str
    ) -> str:
        """Get existing workflow or create a new one."""
        # Check for active workflow for this session
        for workflow_id, workflow in self.active_workflows.items():
            if workflow.get("session_id") == session_id and workflow.get("status") == "active":
                return workflow_id
        
        # Create new workflow
        workflow_type = f"session_{step_type}"
        return await self.start_workflow(session_id, workflow_type)
    
    async def _get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        # Check active workflows first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Load from storage
        workflow = await self.workflow_store.get_workflow(workflow_id)
        
        if workflow:
            self.active_workflows[workflow_id] = workflow
        
        return workflow
    
    def _get_step_type_counts(self, steps: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get counts of step types."""
        counts = {}
        for step in steps:
            step_type = step.get("type", "unknown")
            counts[step_type] = counts.get(step_type, 0) + 1
        return counts
    
    def _calculate_workflow_duration(self, workflow: Dict[str, Any]) -> Optional[float]:
        """Calculate workflow duration."""
        try:
            created_at = datetime.fromisoformat(workflow["created_at"])
            updated_at = datetime.fromisoformat(workflow["updated_at"])
            duration = (updated_at - created_at).total_seconds()
            return duration
        except Exception:
            return None
    
    async def _replay_step(
        self, 
        step: Dict[str, Any], 
        replay_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Replay a single workflow step."""
        step_type = step.get("type")
        step_data = step.get("data", {})
        
        result = {
            "step_id": step.get("step_id"),
            "type": step_type,
            "original_data": step_data,
            "replay_result": None,
            "success": False
        }
        
        try:
            if step_type == "api_call":
                result["replay_result"] = await self._replay_api_call(step_data)
            elif step_type == "tool_usage":
                result["replay_result"] = await self._replay_tool_usage(step_data)
            elif step_type == "decision":
                result["replay_result"] = await self._replay_decision(step_data)
            else:
                result["replay_result"] = {"message": "Step type not supported for replay"}
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _replay_api_call(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replay an API call."""
        # This would implement actual API call replay
        # For now, return the original data
        return {
            "api_name": step_data.get("api_name"),
            "request": step_data.get("request"),
            "response": step_data.get("response"),
            "duration": step_data.get("duration"),
            "replayed": True
        }
    
    async def _replay_tool_usage(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replay a tool usage."""
        # This would implement actual tool replay
        # For now, return the original data
        return {
            "tool_name": step_data.get("tool_name"),
            "input": step_data.get("input"),
            "output": step_data.get("output"),
            "replayed": True
        }
    
    async def _replay_decision(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replay a decision."""
        # This would implement decision replay logic
        # For now, return the original data
        return {
            "decision_type": step_data.get("decision_type"),
            "decision": step_data.get("decision"),
            "alternatives": step_data.get("alternatives"),
            "replayed": True
        }
    
    async def cleanup_old_workflows(self, days: int = 30) -> int:
        """
        Clean up old workflows.
        
        Args:
            days: Number of days to keep workflows
            
        Returns:
            Number of workflows cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = await self.workflow_store.delete_old_workflows(cutoff_date)
            
            console.log(f"🧹 Cleaned up {deleted_count} old workflows")
            return deleted_count
            
        except Exception as e:
            console.log(f"❌ Error cleaning up workflows: {e}")
            return 0
    
    async def export_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Export workflow data.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Exported workflow data or None if not found
        """
        workflow = await self.workflow_store.get_workflow(workflow_id)
        
        if not workflow:
            return None
        
        export_data = {
            "workflow_id": workflow["workflow_id"],
            "session_id": workflow["session_id"],
            "type": workflow["type"],
            "status": workflow["status"],
            "created_at": workflow["created_at"],
            "updated_at": workflow["updated_at"],
            "steps": workflow["steps"],
            "metadata": workflow["metadata"],
            "performance_metrics": workflow["performance_metrics"],
            "exported_at": datetime.utcnow().isoformat()
        }
        
        return export_data
    
    async def shutdown(self):
        """Shutdown the workflow manager."""
        # Save all active workflows
        for workflow_id, workflow in self.active_workflows.items():
            await self.workflow_store.save_workflow(workflow_id, workflow)
        
        console.log("🔄 WorkflowManager shutdown complete") 