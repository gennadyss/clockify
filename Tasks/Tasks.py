"""
Task Manager for Clockify API operations
Based on https://docs.clockify.me/#tag/Task
Enhanced with pagination support to retrieve all data
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from Config.settings import settings
from Utils.api_client import APIClient
from Utils.logging import Logger
from Utils.export_data import DataExporter


class TaskManager:
    """Manages Clockify tasks and task-related operations with pagination support"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize TaskManager with enhanced API client
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger("task_manager")
        self.api_client = APIClient(self.logger)
        self.exporter = DataExporter(self.logger)
        self.workspace_id = settings.clockify_workspace_id
    
    def get_projects_by_category(self, category: str) -> Dict:
        """
        Get all projects by category (e.g., 'EXT.FFS') using pagination
        
        Args:
            category: Category filter string
            
        Returns:
            dict: Projects data with pagination information
        """
        self.logger.debug(f"Getting projects by category: {category}")
        
        # Get ALL projects using pagination
        projects = self.api_client.get_projects(paginated=True)
        
        # Filter projects by category if specified
        if category:
            filtered_items = []
            for project in projects.get('items', []):
                project_name = project.get('name', '')
                if category.lower() in project_name.lower():
                    filtered_items.append(project)
            
            filtered_projects = {
                "items": filtered_items,
                "total_count": len(filtered_items),
                "original_total": projects.get('total_count', 0),
                "filter_applied": category
            }
            
            self.logger.info(f"Filtered {len(filtered_items)} projects matching category '{category}' from {projects.get('total_count', 0)} total projects")
            return filtered_projects
        
        self.logger.info(f"Retrieved {projects.get('total_count', 0)} projects")
        return projects
    
    def get_tasks_by_project(self, project_id: str) -> Dict:
        """
        Get all tasks for a specific project using pagination
        
        Args:
            project_id: ID of the project
            
        Returns:
            dict: Tasks data with pagination information
        """
        self.logger.debug(f"Getting tasks for project: {project_id}")
        
        # Get ALL tasks for the project using pagination
        tasks = self.api_client.get_project_tasks(project_id, paginated=True)
        
        self.logger.info(f"Retrieved {tasks.get('total_count', 0)} tasks for project {project_id}")
        return tasks
    
    def get_tasks_by_name(self, task_name: str) -> Dict:
        """
        Get tasks by name across all projects using pagination
        
        Args:
            task_name: Name or partial name of tasks to find
            
        Returns:
            dict: Matching tasks with project information
        """
        self.logger.debug(f"Searching for tasks by name: {task_name}")
        
        # First get all projects
        projects = self.get_projects_by_category("")
        
        matching_tasks = {"items": []}
        total_projects_searched = 0
        
        for project in projects.get('items', []):
            project_id = project.get('id')
            project_name = project.get('name', '')
            
            # Get all tasks for this project
            tasks = self.get_tasks_by_project(project_id)
            total_projects_searched += 1
            
            # Filter tasks by name
            for task in tasks.get('items', []):
                if task_name.lower() in task.get('name', '').lower():
                    # Add project information to task
                    task_copy = task.copy()
                    task_copy['project_name'] = project_name
                    task_copy['project_id'] = project_id
                    matching_tasks['items'].append(task_copy)
        
        # Add summary information
        matching_tasks.update({
            "total_count": len(matching_tasks['items']),
            "projects_searched": total_projects_searched,
            "search_term": task_name
        })
        
        self.logger.info(f"Found {len(matching_tasks['items'])} tasks matching '{task_name}' across {total_projects_searched} projects")
        return matching_tasks
    
    def get_task_by_id(self, project_id: str, task_id: str) -> Dict:
        """
        Get a specific task by ID
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            dict: Task data
        """
        self.logger.debug(f"Getting task {task_id} from project {project_id}")
        
        endpoint = f"/projects/{project_id}/tasks/{task_id}"
        result = self.api_client.get_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Retrieved task {task_id}")
        
        return result
    
    def create_task(self, project_id: str, task_data: Dict) -> Dict:
        """
        Create a new task in a project
        
        Args:
            project_id: ID of the project
            task_data: Task data to create
            
        Returns:
            dict: Created task data
        """
        self.logger.debug(f"Creating task in project {project_id}")
        
        endpoint = f"/projects/{project_id}/tasks"
        result = self.api_client.post_workspace_data(endpoint, task_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Created task: {task_data.get('name', 'Unknown')}")
        
        return result
    
    def update_task(self, project_id: str, task_id: str, task_data: Dict) -> Dict:
        """
        Update an existing task
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            task_data: Updated task data
            
        Returns:
            dict: Updated task data
        """
        self.logger.debug(f"Updating task {task_id} in project {project_id}")
        
        endpoint = f"/projects/{project_id}/tasks/{task_id}"
        result = self.api_client.put_workspace_data(endpoint, task_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Updated task {task_id}")
        
        return result
    
    def delete_task(self, project_id: str, task_id: str) -> Dict:
        """
        Delete a task
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            dict: Deletion result
        """
        self.logger.debug(f"Deleting task {task_id} from project {project_id}")
        
        endpoint = f"/projects/{project_id}/tasks/{task_id}"
        result = self.api_client.delete_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Deleted task {task_id}")
        
        return result
    
    def get_task_access_permissions(self, project_id: str, task_id: str) -> Dict:
        """
        Get access permissions for a task
        Note: This endpoint might not exist in the actual Clockify API
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            dict: Access permissions data
        """
        self.logger.debug(f"Getting access permissions for task {task_id}")
        
        endpoint = f"/projects/{project_id}/tasks/{task_id}/permissions"
        result = self.api_client.get_workspace_data(endpoint)
        
        return result
    
    def update_task_access_permissions(self, project_id: str, task_id: str, permissions: Dict) -> Dict:
        """
        Update access permissions for a task
        Note: This endpoint might not exist in the actual Clockify API
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            permissions: Permission data
            
        Returns:
            dict: Updated permissions data
        """
        self.logger.debug(f"Updating access permissions for task {task_id}")
        
        endpoint = f"/projects/{project_id}/tasks/{task_id}/permissions"
        result = self.api_client.put_workspace_data(endpoint, permissions)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Updated permissions for task {task_id}")
        
        return result
    
    def grant_task_access(self, project_id: str, task_id: str, user_ids: List[str], group_ids: List[str]) -> Dict:
        """
        Grant access to a task for specific users and groups
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            user_ids: List of user IDs to grant access
            group_ids: List of group IDs to grant access
            
        Returns:
            dict: Access grant result
        """
        self.logger.debug(f"Granting access to task {task_id} for {len(user_ids)} users and {len(group_ids)} groups")
        
        permissions = {
            "allowedUsers": user_ids,
            "allowedGroups": group_ids,
            "accessType": "RESTRICTED"
        }
        
        result = self.update_task_access_permissions(project_id, task_id, permissions)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Granted access to task {task_id}")
        
        return result
    
    def revoke_task_access(self, project_id: str, task_id: str, user_ids: List[str], group_ids: List[str]) -> Dict:
        """
        Revoke access to a task for specific users and groups
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            user_ids: List of user IDs to revoke access
            group_ids: List of group IDs to revoke access
            
        Returns:
            dict: Access revocation result
        """
        self.logger.debug(f"Revoking access to task {task_id} for {len(user_ids)} users and {len(group_ids)} groups")
        
        permissions = {
            "deniedUsers": user_ids,
            "deniedGroups": group_ids,
            "accessType": "RESTRICTED"
        }
        
        result = self.update_task_access_permissions(project_id, task_id, permissions)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Revoked access to task {task_id}")
        
        return result
    
    def export_tasks_to_csv(self, tasks: Dict, filename: str) -> None:
        """
        Export tasks data to CSV file in Export folder
        
        Args:
            tasks: Tasks data to export
            filename: Base filename for export
        """
        try:
            csv_file = self.exporter.export_to_csv(tasks, filename)
            if csv_file:
                print(f"Tasks exported to CSV: {csv_file}")
            else:
                print("CSV export failed - no data or invalid format")
        except Exception as e:
            error_msg = f"CSV export failed: {e}"
            self.logger.error(error_msg)
            print(error_msg)
    
    def export_tasks_to_json(self, tasks: Dict, filename: str) -> None:
        """
        Export tasks data to JSON file in Export folder
        
        Args:
            tasks: Tasks data to export
            filename: Base filename for export
        """
        try:
            json_file = self.exporter.export_to_json(tasks, filename)
            print(f"Tasks exported to JSON: {json_file}")
        except Exception as e:
            error_msg = f"JSON export failed: {e}"
            self.logger.error(error_msg)
            print(error_msg)
    
    def get_all_projects(self) -> Dict:
        """
        Get all projects in the workspace using pagination
        
        Returns:
            dict: All projects data with pagination information
        """
        self.logger.debug("Getting all projects")
        
        # Use the enhanced API client with pagination
        projects = self.api_client.get_projects(paginated=True)
        
        self.logger.info(f"Retrieved {projects.get('total_count', 0)} projects from {projects.get('pages_fetched', 0)} pages")
        return projects
    
    def get_pagination_info(self, endpoint_type: str) -> Dict:
        """
        Get pagination information for different endpoint types
        
        Args:
            endpoint_type: Type of endpoint ('projects', 'tasks', etc.)
            
        Returns:
            dict: Pagination information
        """
        if endpoint_type == 'projects':
            endpoint = f"/workspaces/{self.workspace_id}/projects"
        elif endpoint_type == 'tasks':
            # Need a project ID for tasks - this is just for analysis
            endpoint = f"/workspaces/{self.workspace_id}/projects/sample/tasks"
        else:
            return {"error": f"Unknown endpoint type: {endpoint_type}"}
        
        return self.api_client.get_pagination_info(endpoint) 