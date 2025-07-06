"""
TasksAccessManager for Clockify bulk access restriction management.
This module handles the two main objectives:
1. Give access only to specific roles, users, and groups for certain tasks
2. Remove access to certain tasks from specific groups

Enhanced version using centralized Utils modules for better maintainability.
"""

import os
import sys
from typing import Dict, List, Optional, Set, Tuple

from Config.settings import settings
from Tasks.Tasks import TaskManager
from Users.Users import UserManager

# Using the centralized Utils modules
from Utils.logging import Logger
from Utils.export_data import DataExporter
from Utils.auth import AuthManager
from Utils.api_client import APIClient

# Using the domain-specific modules
from Projects.ProjectManager import ProjectManager
from Clients.ClientManager import ClientManager


class TasksAccessManager:
    """Main class for managing Clockify task access restrictions"""
    
    def __init__(self):
        # Initialize utilities for better logging, export, and validation
        self.logger = Logger("tasks_access", console_output=True)
        self.logger.create_log_file_for_session("access_management")
        
        self.exporter = DataExporter(self.logger)
        self.auth_manager = AuthManager(self.logger)
        self.api_client = APIClient(self.logger)
        
        # Initialize managers
        self.task_manager = TaskManager(self.logger)
        self.user_manager = UserManager(self.logger)
        
        # Initialize domain-specific managers
        self.project_manager = ProjectManager(self.logger)
        self.client_manager = ClientManager(self.logger)
        
        # Define the authorized tasks within EXT.FFS projects from README
        self.authorized_tasks = [
            "NGS Reagents and Lab Operations Cost",
            "ISP Reagents and Lab Operations Cost", 
            "IMG Reagents and Lab Operations Cost",
            "RepGen Dry operations",
            "Pipeline Dry Operations",
            "Contingencies (other variant of the same task Contingencies (30%))"
        ]
        
        self.restricted_tasks = [
            "NGS Dry Operations",
            "ISP Dry Operations", 
            "IMG Dry Operations",
            "PM Dry Operations"
        ]
        
        # Authorized users and groups
        self.authorized_users = [
            "Ekaterina Postovalova",
            "Lev Bedniagin", 
            "Alina Mulyukina",
            "Anastasiya Terenteva",
            "Tatiana Vasilyeva",
            "Anastasiya Tarabarova",
            "Lile Kontselidze",
            "Alexandra Boiko"
        ]
        
        self.authorized_groups = [
            "RPMHS.RPMG: Research Projects Management Group"
        ]
        
        self.restricted_groups = [
            "US.LAB.RND",
            "US.LAB.CLIN",
            "US.QAREG",
            "US.HR",
            "Eric White",
            "Artur Baisangurov",
            "Tina Barsoumian",
            "US.LAB.RND.NGS",
            "US.LAB.RND.ISP",
            "US.LAB.RND.PATH",
            "US.LAB.CLIN.NGS",
            "US.LAB.CLIN.PATH",
            "US.LAB.RND.OP.BSP"
        ]
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present"""
        return self.auth_manager.validate_configuration()
    
    def export_data_to_files(self, data: Dict, filename_prefix: str) -> None:
        """Export data to both JSON and CSV formats using DataExporter"""
        self.exporter.export_to_both_formats(data, filename_prefix)
    
    def get_all_projects_and_clients(self) -> Tuple[Dict, Dict]:
        """
        Step 0: Get ALL projects and extract all unique clients (categories)
        As required by README.md - find all projects first, then extract clients
        """
        self.logger.log_step("Getting All Projects and Clients - Using ProjectManager", "START")
        
        # Get all projects using the dedicated ProjectManager
        all_projects = self.project_manager.get_all_projects()
        
        # Extract clients from projects
        clients = self.project_manager.extract_clients_from_projects(all_projects)
        
        self.logger.log_step("Getting All Projects and Clients - Using ProjectManager", "COMPLETE")
        return all_projects, clients
    
    def filter_projects_by_client_id(self, all_projects: Dict, client_id: str) -> Dict:
        """
        Filter projects by specific client ID (category)
        Using the dedicated ProjectManager for client-based filtering
        """
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id} - Using ProjectManager", "START")
        
        # Use the ProjectManager for client-based filtering
        filtered_projects = self.project_manager.filter_projects_by_client_id(all_projects, client_id)
        
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id} - Using ProjectManager", "COMPLETE")
        return filtered_projects
    
    def get_projects_by_client_api(self, client_id: str) -> Dict:
        """
        Get projects filtered by client using API query parameter
        Using the dedicated ProjectManager for API-based filtering
        """
        self.logger.log_step(f"Getting Projects by Client API: {client_id} - Using ProjectManager", "START")
        
        # Use the ProjectManager for API-based client filtering
        filtered_projects = self.project_manager.get_projects_by_client_api(client_id)
        
        self.logger.log_step(f"Getting Projects by Client API: {client_id} - Using ProjectManager", "COMPLETE")
        return filtered_projects
    
    def step_one_grant_access(self, client_id: str = None) -> bool:
        """
        Step 1: Grant access only to authorized roles, users, and groups
        for specific authorized tasks within ALL projects in specified client category
        Following README.md requirements
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
        """
        self.logger.log_step("STEP 1: Granting Access to Authorized Tasks", "START")
        
        # First, get all projects and clients
        all_projects, all_clients = self.get_all_projects_and_clients()
        
        # Filter projects by client ID if specified
        if client_id:
            filtered_projects = self.filter_projects_by_client_id(all_projects, client_id)
            self.logger.info(f"Found {len(filtered_projects.get('items', []))} projects for client ID {client_id}")
        else:
            filtered_projects = all_projects
            self.logger.info(f"Using all {len(filtered_projects.get('items', []))} projects")
        
        self.export_data_to_files(filtered_projects, "filtered_projects_step1")
        
        # Find authorized tasks within each filtered project
        authorized_tasks_data = {}
        total_authorized_tasks = 0
        
        for project in filtered_projects.get('items', []):
            project_id = project.get('id')
            project_name = project.get('name', '')
            
            # Get all tasks for this project
            project_tasks = self.task_manager.get_tasks_by_project(project_id)
            
            # Find authorized tasks within this project
            authorized_tasks_in_project = {"items": []}
            
            for task in project_tasks.get('items', []):
                task_name = task.get('name', '')
                
                # Check if this task is in our authorized tasks list
                for authorized_task in self.authorized_tasks:
                    if authorized_task.lower() in task_name.lower() or task_name.lower() in authorized_task.lower():
                        # Add project information to task
                        task_copy = task.copy()
                        task_copy['project_name'] = project_name
                        task_copy['project_id'] = project_id
                        task_copy['matched_authorized_task'] = authorized_task
                        authorized_tasks_in_project['items'].append(task_copy)
                        total_authorized_tasks += 1
                        break
            
            if authorized_tasks_in_project['items']:
                authorized_tasks_data[f"{project_name} ({project_id})"] = authorized_tasks_in_project
        
        self.logger.info(f"Found {total_authorized_tasks} authorized tasks across {len(authorized_tasks_data)} projects")
        self.exporter.export_multiple_datasets(authorized_tasks_data, "authorized_tasks_by_project")
        
        # Create summary of authorized tasks
        authorized_tasks_summary = {"items": []}
        for project_key, project_tasks in authorized_tasks_data.items():
            for task in project_tasks.get('items', []):
                authorized_tasks_summary['items'].append(task)
        
        self.export_data_to_files(authorized_tasks_summary, "all_authorized_tasks")
        
        if not self.auth_manager.is_changes_approved():
            self.logger.warning("⚠️  Changes not approved. Set APPROVE_CHANGES=true to apply changes.")
            return False
        
        # Apply access restrictions (placeholder - implement actual API calls)
        self.logger.log_access_operation("GRANT", f"{total_authorized_tasks} authorized tasks", True)
        # TODO: Implement actual Clockify API calls to modify task access
        
        self.logger.log_step("STEP 1: Granting Access to Authorized Tasks", "COMPLETE")
        return True
    
    def step_two_remove_access(self, client_id: str = None) -> bool:
        """
        Step 2: Remove access to specific tasks from restricted groups
        Search for restricted tasks in projects filtered by client ID
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
        """
        self.logger.log_step("STEP 2: Removing Access from Restricted Tasks", "START")
        
        # Get all projects and filter by client ID if specified
        all_projects, _ = self.get_all_projects_and_clients()
        
        if client_id:
            filtered_projects = self.filter_projects_by_client_id(all_projects, client_id)
            self.logger.info(f"Searching for restricted tasks in {len(filtered_projects.get('items', []))} projects for client ID {client_id}")
        else:
            filtered_projects = all_projects
            self.logger.info(f"Searching for restricted tasks in {len(filtered_projects.get('items', []))} projects")
        
        # Get all tasks matching the restricted task names from filtered projects
        restricted_tasks_data = {}
        total_restricted_tasks = 0
        
        for task_name in self.restricted_tasks:
            matching_tasks = {"items": []}
            
            # Search in filtered projects
            for project in filtered_projects.get('items', []):
                project_id = project.get('id')
                project_name = project.get('name', '')
                
                project_tasks = self.task_manager.get_tasks_by_project(project_id)
                
                # Filter tasks by name
                for task in project_tasks.get('items', []):
                    if task_name.lower() in task.get('name', '').lower():
                        # Add project information to task
                        task_copy = task.copy()
                        task_copy['project_name'] = project_name
                        task_copy['project_id'] = project_id
                        task_copy['matched_restricted_task'] = task_name
                        matching_tasks['items'].append(task_copy)
                        total_restricted_tasks += 1
            
            restricted_tasks_data[task_name] = matching_tasks
        
        self.logger.info(f"Found {total_restricted_tasks} restricted tasks across filtered projects")
        self.exporter.export_multiple_datasets(restricted_tasks_data, "restricted_tasks_by_name")
        
        # Create summary of all restricted tasks
        restricted_tasks_summary = {"items": []}
        for task_name, task_data in restricted_tasks_data.items():
            for task in task_data.get('items', []):
                restricted_tasks_summary['items'].append(task)
        
        self.export_data_to_files(restricted_tasks_summary, "all_restricted_tasks")
        
        if not self.auth_manager.is_changes_approved():
            self.logger.warning("⚠️  Changes not approved. Set APPROVE_CHANGES=true to apply changes.")
            return False
        
        # Apply access removal (placeholder - implement actual API calls)
        self.logger.log_access_operation("REVOKE", f"{total_restricted_tasks} restricted tasks", True)
        # TODO: Implement actual Clockify API calls to remove task access
        
        self.logger.log_step("STEP 2: Removing Access from Restricted Tasks", "COMPLETE")
        return True
    
    def run_access_restrictions(self, client_id: str = None) -> bool:
        """
        Execute both access restriction steps
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
        """
        self.logger.info("🕐 Starting Clockify Access Management")
        self.logger.info("=" * 50)
        
        if client_id:
            self.logger.info(f"Filtering projects by client ID: {client_id}")
        else:
            self.logger.info("Processing all projects (no client filter)")
        
        # Comprehensive validation using AuthManager
        if not self.validate_configuration():
            return False
        
        # Log configuration summary
        config_summary = self.auth_manager.get_configuration_summary()
        self.logger.info(f"Configuration Summary: {config_summary}")
        
        try:
            # Execute Step 1
            success_step1 = self.step_one_grant_access(client_id)
            
            # Execute Step 2
            success_step2 = self.step_two_remove_access(client_id)
            
            if success_step1 and success_step2:
                self.logger.info("✅ Both steps completed successfully!")
                return True
            else:
                self.logger.warning("⚠️  Some steps completed with warnings or were skipped.")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error occurred: {e}")
            return False 