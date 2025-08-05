"""
Workflow storage for the Agentic AI Orchestration system.

This module provides the WorkflowStore class that handles workflow
persistence and storage.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rich.console import Console

from config.settings import Settings

console = Console()


class WorkflowStore:
    """
    Handles workflow persistence and storage.
    
    This class provides:
    - Workflow storage and retrieval
    - Workflow listing and management
    - Workflow cleanup
    """
    
    def __init__(self, settings: Settings):
        """Initialize the workflow store."""
        self.settings = settings
        self.storage_dir = "data/workflows"
        
        # Create storage directory
        os.makedirs(self.storage_dir, exist_ok=True)
        
        console.log("💾 WorkflowStore initialized")
    
    async def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> bool:
        """
        Save workflow data to storage.
        
        Args:
            workflow_id: Workflow ID
            workflow_data: Workflow data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{workflow_id}.json")
            
            # Save to file
            with open(filename, "w") as f:
                json.dump(workflow_data, f, indent=2)
            
            return True
            
        except Exception as e:
            console.log(f"❌ Error saving workflow {workflow_id}: {e}")
            return False
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow data from storage.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data or None if not found
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{workflow_id}.json")
            
            # Check if file exists
            if not os.path.exists(filename):
                return None
            
            # Load from file
            with open(filename, "r") as f:
                workflow_data = json.load(f)
            
            return workflow_data
            
        except Exception as e:
            console.log(f"❌ Error loading workflow {workflow_id}: {e}")
            return None
    
    async def get_workflows_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all workflows for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of workflows for the session
        """
        try:
            workflows = []
            
            # List all workflow files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    workflow_id = filename[:-5]  # Remove .json extension
                    
                    # Load workflow data
                    workflow_data = await self.get_workflow(workflow_id)
                    
                    if workflow_data and workflow_data.get("session_id") == session_id:
                        workflows.append(workflow_data)
            
            # Sort by creation time
            workflows.sort(key=lambda x: x.get("created_at", ""))
            
            return workflows
            
        except Exception as e:
            console.log(f"❌ Error getting workflows for session {session_id}: {e}")
            return []
    
    async def list_workflows(
        self, 
        session_id: Optional[str] = None,
        workflow_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List workflows from storage.
        
        Args:
            session_id: Optional session ID to filter by
            workflow_type: Optional workflow type to filter by
            limit: Maximum number of workflows to return
            
        Returns:
            List of workflow summaries
        """
        try:
            workflows = []
            
            # List all workflow files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    workflow_id = filename[:-5]  # Remove .json extension
                    
                    # Load workflow data
                    workflow_data = await self.get_workflow(workflow_id)
                    
                    if workflow_data:
                        # Apply filters
                        if session_id and workflow_data.get("session_id") != session_id:
                            continue
                        
                        if workflow_type and workflow_data.get("type") != workflow_type:
                            continue
                        
                        workflows.append(workflow_data)
            
            # Sort by creation time
            workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return workflows[:limit]
            
        except Exception as e:
            console.log(f"❌ Error listing workflows: {e}")
            return []
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete workflow from storage.
        
        Args:
            workflow_id: Workflow ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filename
            filename = os.path.join(self.storage_dir, f"{workflow_id}.json")
            
            # Check if file exists
            if not os.path.exists(filename):
                return False
            
            # Delete file
            os.remove(filename)
            
            console.log(f"🗑️ Deleted workflow: {workflow_id}")
            return True
            
        except Exception as e:
            console.log(f"❌ Error deleting workflow {workflow_id}: {e}")
            return False
    
    async def delete_old_workflows(self, cutoff_date: datetime) -> int:
        """
        Delete old workflows.
        
        Args:
            cutoff_date: Cutoff date for deletion
            
        Returns:
            Number of workflows deleted
        """
        try:
            deleted_count = 0
            
            # List all workflow files
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    workflow_id = filename[:-5]
                    
                    # Load workflow data
                    workflow_data = await self.get_workflow(workflow_id)
                    
                    if workflow_data:
                        # Check creation time
                        created_at = workflow_data.get("created_at")
                        if created_at:
                            try:
                                workflow_date = datetime.fromisoformat(created_at)
                                if workflow_date < cutoff_date:
                                    # Delete old workflow
                                    if await self.delete_workflow(workflow_id):
                                        deleted_count += 1
                            except Exception:
                                # Skip workflows with invalid dates
                                pass
            
            console.log(f"🧹 Deleted {deleted_count} old workflows")
            return deleted_count
            
        except Exception as e:
            console.log(f"❌ Error deleting old workflows: {e}")
            return 0
    
    async def get_workflow_stats(self) -> Dict[str, Any]:
        """
        Get workflow storage statistics.
        
        Returns:
            Workflow storage statistics
        """
        try:
            total_workflows = 0
            total_size = 0
            workflow_types = {}
            
            # Count workflows and calculate size
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    total_workflows += 1
                    
                    filepath = os.path.join(self.storage_dir, filename)
                    total_size += os.path.getsize(filepath)
                    
                    # Count by type
                    workflow_id = filename[:-5]
                    workflow_data = await self.get_workflow(workflow_id)
                    if workflow_data:
                        workflow_type = workflow_data.get("type", "unknown")
                        workflow_types[workflow_type] = workflow_types.get(workflow_type, 0) + 1
            
            return {
                "total_workflows": total_workflows,
                "total_size_bytes": total_size,
                "workflow_types": workflow_types,
                "storage_directory": self.storage_dir
            }
            
        except Exception as e:
            console.log(f"❌ Error getting workflow stats: {e}")
            return {
                "total_workflows": 0,
                "total_size_bytes": 0,
                "workflow_types": {},
                "storage_directory": self.storage_dir
            }
    
    async def search_workflows(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search workflows by content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching workflows
        """
        try:
            results = []
            query_lower = query.lower()
            
            # Search through all workflows
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    workflow_id = filename[:-5]
                    workflow_data = await self.get_workflow(workflow_id)
                    
                    if workflow_data:
                        # Search in workflow data
                        workflow_str = json.dumps(workflow_data).lower()
                        if query_lower in workflow_str:
                            results.append({
                                "workflow_id": workflow_id,
                                "workflow_data": workflow_data,
                                "match_score": workflow_str.count(query_lower)
                            })
            
            # Sort by match score
            results.sort(key=lambda x: x["match_score"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            console.log(f"❌ Error searching workflows: {e}")
            return []
    
    async def export_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Export workflow data.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Exported workflow data or None if not found
        """
        workflow_data = await self.get_workflow(workflow_id)
        
        if not workflow_data:
            return None
        
        # Add export metadata
        export_data = {
            "workflow_id": workflow_id,
            "exported_at": datetime.utcnow().isoformat(),
            "workflow_data": workflow_data
        }
        
        return export_data
    
    async def import_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """
        Import workflow data.
        
        Args:
            workflow_data: Workflow data to import
            
        Returns:
            New workflow ID
        """
        import uuid
        
        # Generate new workflow ID
        new_workflow_id = str(uuid.uuid4())
        
        # Extract workflow data
        original_workflow = workflow_data.get("workflow_data", {})
        
        # Update workflow data
        imported_workflow = {
            **original_workflow,
            "workflow_id": new_workflow_id,
            "imported_at": datetime.utcnow().isoformat(),
            "original_workflow_id": original_workflow.get("workflow_id")
        }
        
        # Save workflow
        await self.save_workflow(new_workflow_id, imported_workflow)
        
        console.log(f"📥 Imported workflow as: {new_workflow_id}")
        return new_workflow_id 