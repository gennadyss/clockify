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
from Groups.Groups import GroupManager

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
        self.group_manager = GroupManager(self.logger)
        
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
            "Contingencies"
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
            #added from Admin Role
            "Anastasia Shvyrkova",
            "Anastasiya Makarova",
            "Dionysus Tech",
            "Gennady Sidelnikov",
            "Grace Goyette",
            "Lyudmila Kolomys",
            "Melanie Sinclair",
            "Melissa Olsson",
            "Vladimir Saturchenko"
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
        
        # Initialize data storage for united files
        self.authorized_tasks_data = {}
        self.restricted_tasks_data = {}
        self.authorized_tasks_count = 0
        self.restricted_tasks_count = 0
    
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
    
    def authorized_users_by_role(self, role: str = "Admin") -> List[str]:
        """
        Get authorized users by role using Clockify User API
        Based on https://docs.clockify.me/#tag/User
        
        Args:
            role: User role to filter by (default: "Admin")
            
        Returns:
            List[str]: List of user names with the specified role
        """
        self.logger.log_step(f"Getting Authorized Users by Role: {role} - Using UserManager", "START")
        
        try:
            # Get all users from workspace using UserManager
            all_users = self.user_manager.get_all_users()
            
            # Filter users by role
            users_with_role = {"items": []}
            user_names = []
            
            for user in all_users.get('items', []):
                user_role = user.get('role', '').upper()
                target_role = role.upper()
                
                # Check if user has the specified role
                if user_role == target_role:
                    user_name = user.get('name', '')
                    user_email = user.get('email', '')
                    
                    # Add user to filtered list
                    user_copy = user.copy()
                    user_copy['filtered_by_role'] = role
                    users_with_role['items'].append(user_copy)
                    
                    # Add user name to return list
                    if user_name:
                        user_names.append(user_name)
                    
                    self.logger.info(f"Found user with role {role}: {user_name} ({user_email})")
            
            # Log statistics
            total_users = len(all_users.get('items', []))
            users_with_role_count = len(users_with_role['items'])
            
            self.logger.info(f"Found {users_with_role_count} users with role '{role}' out of {total_users} total users")
            
            # Export the filtered users for auditing
            self.export_data_to_files(users_with_role, f"authorized_users_by_role_{role.lower()}")
            
            # Also export all users for reference
            self.export_data_to_files(all_users, "all_users_workspace")
            
            self.logger.log_step(f"Getting Authorized Users by Role: {role} - Using UserManager", "COMPLETE")
            return user_names
            
        except Exception as e:
            self.logger.error(f"Error getting users by role {role}: {e}")
            self.logger.log_step(f"Getting Authorized Users by Role: {role} - Using UserManager", "ERROR")
            return []
    
    def step_one_grant_access(self, client_id: str = None, role: str = "Admin") -> bool:
        """
        Step 1: Grant access to authorized tasks by updating userGroupIds and assigneeIds
        New logic: Pattern matching for authorized_tasks, update with authorized_groups and authorized_users
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
            role: User role to include in authorized users (default: "Admin")
        """
        self.logger.log_step("STEP 1: Granting Access to Authorized Tasks", "START")
        
        # Get all projects and filter by client ID if specified
        all_projects, all_clients = self.get_all_projects_and_clients()
        
        if client_id:
            filtered_projects = self.filter_projects_by_client_id(all_projects, client_id)
            self.logger.info(f"Processing {len(filtered_projects.get('items', []))} projects for client ID {client_id}")
        else:
            filtered_projects = all_projects
            self.logger.info(f"Processing {len(filtered_projects.get('items', []))} projects")
        
        self.export_data_to_files(filtered_projects, "filtered_projects_step1")
        
        # Step 1: Get authorized users by role and combine with hardcoded users
        role_based_users = self.authorized_users_by_role(role)
        all_authorized_users = list(set(self.authorized_users + role_based_users))
        
        self.logger.info(f"Total authorized users: {len(all_authorized_users)}")
        self.logger.info(f"  - Hardcoded users: {len(self.authorized_users)}")
        self.logger.info(f"  - Role-based users ({role}): {len(role_based_users)}")
        
        # Step 2: Get authorized user IDs from names
        self.logger.info("Getting authorized user IDs...")
        all_users = self.user_manager.get_all_users()
        authorized_user_ids = []
        
        for user in all_users.get('items', []):
            user_name = user.get('name', '')
            user_id = user.get('id', '')
            
            if user_name in all_authorized_users and user_id:
                authorized_user_ids.append(user_id)
                self.logger.info(f"Found authorized user: {user_name} (ID: {user_id})")
        
        self.logger.info(f"Resolved {len(authorized_user_ids)} authorized user IDs")
        
        # Step 3: Get authorized group IDs from names
        self.logger.info("Getting authorized group IDs...")
        authorized_groups_details = self.group_manager.get_groups_by_names(self.authorized_groups)
        authorized_group_ids = [group.get('id') for group in authorized_groups_details.get('items', []) if group.get('id')]
        
        self.logger.info(f"Resolved {len(authorized_group_ids)} authorized group IDs")
        for group in authorized_groups_details.get('items', []):
            group_name = group.get('name', '')
            group_id = group.get('id', '')
            self.logger.info(f"Found authorized group: {group_name} (ID: {group_id})")
        
        # Step 4: Find tasks matching authorized task patterns from filtered projects
        authorized_tasks_data = {}
        total_authorized_tasks = 0
        total_tasks_updated = 0
        
        for authorized_task_pattern in self.authorized_tasks:
            matching_tasks = {"items": []}
            
            # Search in filtered projects
            for project in filtered_projects.get('items', []):
                project_id = project.get('id')
                project_name = project.get('name', '')
                
                project_tasks = self.task_manager.get_tasks_by_project(project_id)
                
                # Use pattern matching for task names (not exact matching)
                for task in project_tasks.get('items', []):
                    task_name = task.get('name', '')
                    
                    # Pattern matching: check if authorized_task_pattern is in task_name
                    # This handles cases like "Contingencies" matching "Contingencies (30%)"
                    if authorized_task_pattern.lower() in task_name.lower():
                        # Add project information to task
                        task_copy = task.copy()
                        task_copy['project_name'] = project_name
                        task_copy['project_id'] = project_id
                        task_copy['matched_authorized_task'] = authorized_task_pattern
                        matching_tasks['items'].append(task_copy)
                        total_authorized_tasks += 1
            
            authorized_tasks_data[authorized_task_pattern] = matching_tasks
        
        self.logger.info(f"Found {total_authorized_tasks} authorized tasks across filtered projects")
        
        # Store authorized tasks data for later merging
        self.authorized_tasks_data = authorized_tasks_data
        self.authorized_tasks_count = total_authorized_tasks
        
        # Export task data for review
        self.exporter.export_multiple_datasets(authorized_tasks_data, "authorized_tasks_by_pattern")
        
        # Create summary of all authorized tasks
        authorized_tasks_summary = {"items": []}
        for pattern, task_data in authorized_tasks_data.items():
            for task in task_data.get('items', []):
                task['task_type'] = 'authorized'
                authorized_tasks_summary['items'].append(task)
        
        self.export_data_to_files(authorized_tasks_summary, "all_authorized_tasks")
        
        # Export user and group information for review
        user_group_info_summary = {
            "authorized_users": all_users.get('items', []),
            "authorized_groups": authorized_groups_details.get('items', []),
            "authorized_user_ids": authorized_user_ids,
            "authorized_group_ids": authorized_group_ids,
            "summary": {
                "total_authorized_users": len(authorized_user_ids),
                "total_authorized_groups": len(authorized_group_ids),
                "hardcoded_users": len(self.authorized_users),
                "role_based_users": len(role_based_users)
            }
        }
        self.export_data_to_files(user_group_info_summary, "step1_user_group_analysis")
        
        if not self.auth_manager.is_changes_approved():
            self.logger.warning("⚠️  Changes not approved. Set APPROVE_CHANGES=true to apply changes.")
            self.logger.info("✅ Step 1 data collection completed successfully (dry-run mode)")
            self.logger.log_step("STEP 1: Granting Access to Authorized Tasks", "COMPLETE")
            return True  # Return True for data collection success
        
        # Step 5: Update task userGroupIds and assigneeIds using the updateTask API
        self.logger.info("Updating task userGroupIds and assigneeIds...")
        
        for pattern, task_data in authorized_tasks_data.items():
            for task in task_data.get('items', []):
                project_id = task.get('project_id')
                task_id = task.get('id')
                current_user_group_ids = task.get('userGroupIds', [])
                current_assignee_ids = task.get('assigneeIds', [])
                
                if project_id and task_id:
                    # Prepare update data - update both userGroupIds and assigneeIds
                    update_data = {
                        "userGroupIds": authorized_group_ids,
                        "assigneeIds": authorized_user_ids
                    }
                    
                    self.logger.info(f"Updating task '{task.get('name')}' (ID: {task_id}) in project {project_id}")
                    self.logger.debug(f"Current userGroupIds: {current_user_group_ids}")
                    self.logger.debug(f"New userGroupIds: {authorized_group_ids}")
                    self.logger.debug(f"Current assigneeIds: {current_assignee_ids}")
                    self.logger.debug(f"New assigneeIds: {authorized_user_ids}")
                    
                    # Update the task using the TaskManager's update_task method
                    result = self.task_manager.update_task(project_id, task_id, update_data)
                    
                    if not self.task_manager.api_client.is_error_response(result):
                        total_tasks_updated += 1
                        self.logger.info(f"Successfully updated task {task_id} with {len(authorized_group_ids)} groups and {len(authorized_user_ids)} users")
                    else:
                        error_msg = self.task_manager.api_client.get_error_message(result)
                        self.logger.error(f"Failed to update task {task_id}: {error_msg}")
                else:
                    self.logger.warning(f"Missing project_id or task_id for task: {task.get('name', 'Unknown')}")
        
        # Log final summary
        self.logger.info(f"✅ Step 1 completed:")
        self.logger.info(f"   📊 Total authorized tasks found: {total_authorized_tasks}")
        self.logger.info(f"   🔧 Tasks successfully updated: {total_tasks_updated}")
        self.logger.info(f"   👥 Users processed: {len(authorized_user_ids)} authorized users")
        self.logger.info(f"   🏷️  Groups processed: {len(authorized_group_ids)} authorized groups")
        
        self.logger.log_access_operation("GRANT", f"{total_tasks_updated} tasks with userGroupIds and assigneeIds", total_tasks_updated > 0)
        
        self.logger.log_step("STEP 1: Granting Access to Authorized Tasks", "COMPLETE")
        return True
    
    def step_two_remove_access(self, client_id: str = None) -> bool:
        """
        Step 2: Remove access to specific tasks from restricted groups
        New logic: Get all groups, remove restricted groups, update task userGroupIds
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
        """
        self.logger.log_step("STEP 2: Removing Access from Restricted Tasks", "START")
        
        # Get all projects and filter by client ID if specified
        all_projects, _ = self.get_all_projects_and_clients()
        
        if client_id:
            filtered_projects = self.filter_projects_by_client_id(all_projects, client_id)
            self.logger.info(f"Processing {len(filtered_projects.get('items', []))} projects for client ID {client_id}")
        else:
            filtered_projects = all_projects
            self.logger.info(f"Processing {len(filtered_projects.get('items', []))} projects")
        
        # Step 1: Get all groups from Clockify
        self.logger.info("Getting all groups from Clockify...")
        all_groups = self.group_manager.get_all_groups()
        all_group_ids = [group.get('id') for group in all_groups.get('items', []) if group.get('id')]
        
        self.logger.info(f"Found {len(all_group_ids)} total groups in Clockify")
        
        # Step 2: Remove restricted groups from the list
        self.logger.info("Removing restricted groups from the list...")
        restricted_groups_details = self.group_manager.get_groups_by_names(self.restricted_groups)
        restricted_group_ids = [group.get('id') for group in restricted_groups_details.get('items', []) if group.get('id')]
        
        self.logger.info(f"Found {len(restricted_group_ids)} restricted groups to remove")
        
        # Create final list of allowed groups (all groups - restricted groups)
        allowed_group_ids = [group_id for group_id in all_group_ids if group_id not in restricted_group_ids]
        
        self.logger.info(f"Final allowed groups count: {len(allowed_group_ids)} (removed {len(restricted_group_ids)} restricted groups)")
        
        # Step 3: Find tasks matching the restricted task names from filtered projects
        restricted_tasks_data = {}
        total_restricted_tasks = 0
        total_tasks_updated = 0
        
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
        
        # Store restricted tasks data for later merging
        self.restricted_tasks_data = restricted_tasks_data
        self.restricted_tasks_count = total_restricted_tasks
        
        # Export task data for review
        self.exporter.export_multiple_datasets(restricted_tasks_data, "restricted_tasks_by_name")
        
        # Create summary of all restricted tasks
        restricted_tasks_summary = {"items": []}
        for task_name, task_data in restricted_tasks_data.items():
            for task in task_data.get('items', []):
                task['task_type'] = 'restricted'
                restricted_tasks_summary['items'].append(task)
        
        self.export_data_to_files(restricted_tasks_summary, "all_restricted_tasks")
        
        # Export group information for review
        group_info_summary = {
            "all_groups": all_groups.get('items', []),
            "restricted_groups": restricted_groups_details.get('items', []),
            "allowed_group_ids": allowed_group_ids,
            "restricted_group_ids": restricted_group_ids,
            "summary": {
                "total_groups": len(all_group_ids),
                "restricted_groups": len(restricted_group_ids),
                "allowed_groups": len(allowed_group_ids)
            }
        }
        self.export_data_to_files(group_info_summary, "step2_group_analysis")
        
        if not self.auth_manager.is_changes_approved():
            self.logger.warning("⚠️  Changes not approved. Set APPROVE_CHANGES=true to apply changes.")
            self.logger.info("✅ Step 2 data collection completed successfully (dry-run mode)")
            self.logger.log_step("STEP 2: Removing Access from Restricted Tasks", "COMPLETE")
            return True  # Return True for data collection success
        
        # Step 4: Update task userGroupIds with the final list of allowed groups
        self.logger.info("Updating task userGroupIds with allowed groups...")
        
        for task_name, task_data in restricted_tasks_data.items():
            for task in task_data.get('items', []):
                project_id = task.get('project_id')
                task_id = task.get('id')
                current_user_group_ids = task.get('userGroupIds', [])
                
                if project_id and task_id:
                    # Prepare update data - only update userGroupIds field
                    update_data = {
                        "userGroupIds": allowed_group_ids
                    }
                    
                    self.logger.info(f"Updating task '{task.get('name')}' (ID: {task_id}) in project {project_id}")
                    self.logger.debug(f"Current userGroupIds: {current_user_group_ids}")
                    self.logger.debug(f"New userGroupIds: {allowed_group_ids}")
                    
                    # Update the task using the TaskManager's update_task method
                    result = self.task_manager.update_task(project_id, task_id, update_data)
                    
                    if not self.task_manager.api_client.is_error_response(result):
                        total_tasks_updated += 1
                        self.logger.info(f"Successfully updated task {task_id} with {len(allowed_group_ids)} allowed groups")
                    else:
                        error_msg = self.task_manager.api_client.get_error_message(result)
                        self.logger.error(f"Failed to update task {task_id}: {error_msg}")
                else:
                    self.logger.warning(f"Missing project_id or task_id for task: {task.get('name', 'Unknown')}")
        
        # Log final summary
        self.logger.info(f"✅ Step 2 completed:")
        self.logger.info(f"   📊 Total restricted tasks found: {total_restricted_tasks}")
        self.logger.info(f"   🔧 Tasks successfully updated: {total_tasks_updated}")
        self.logger.info(f"   👥 Groups processed: {len(all_group_ids)} total, {len(restricted_group_ids)} restricted, {len(allowed_group_ids)} allowed")
        
        self.logger.log_access_operation("UPDATE", f"{total_tasks_updated} tasks with userGroupIds", total_tasks_updated > 0)
        
        self.logger.log_step("STEP 2: Removing Access from Restricted Tasks", "COMPLETE")
        return True
    
    def create_united_task_files(self, client_id: str = None) -> bool:
        """
        Create united files that merge authorized and restricted tasks data
        This provides a comprehensive view of all task access management
        
        Args:
            client_id: Client ID used for filtering (for filename context)
        """
        self.logger.log_step("Creating United Task Files", "START")
        
        try:
            # Check if we have data from both steps
            if not hasattr(self, 'authorized_tasks_data') or not hasattr(self, 'restricted_tasks_data'):
                self.logger.warning("⚠️  Missing task data. Ensure both Step 1 and Step 2 have been executed.")
                return False
            
            # Create united summary with all tasks
            united_tasks_summary = {"items": []}
            
            # Add all authorized tasks
            for project_key, project_tasks in self.authorized_tasks_data.items():
                for task in project_tasks.get('items', []):
                    task_copy = task.copy()
                    task_copy['task_type'] = 'authorized'
                    task_copy['data_source'] = 'step_1_grant_access'
                    united_tasks_summary['items'].append(task_copy)
            
            # Add all restricted tasks
            for task_name, task_data in self.restricted_tasks_data.items():
                for task in task_data.get('items', []):
                    task_copy = task.copy()
                    task_copy['task_type'] = 'restricted'
                    task_copy['data_source'] = 'step_2_remove_access'
                    united_tasks_summary['items'].append(task_copy)
            
            # Create statistics summary
            stats_summary = {
                "summary": {
                    "total_tasks": len(united_tasks_summary['items']),
                    "authorized_tasks": self.authorized_tasks_count,
                    "restricted_tasks": self.restricted_tasks_count,
                    "client_id_filter": client_id if client_id else "all_projects",
                    "projects_with_authorized_tasks": len(self.authorized_tasks_data),
                    "restricted_task_types": len(self.restricted_tasks_data)
                },
                "authorized_tasks_by_project": self.authorized_tasks_data,
                "restricted_tasks_by_name": self.restricted_tasks_data
            }
            
            # Generate filename suffix
            filename_suffix = f"client_{client_id}" if client_id else "all_projects"
            
            # Export united files
            self.export_data_to_files(united_tasks_summary, f"united_all_tasks_{filename_suffix}")
            self.export_data_to_files(stats_summary, f"united_task_statistics_{filename_suffix}")
            
            # Create detailed breakdown by project
            united_by_project = {}
            
            # Group authorized tasks by project
            for project_key, project_tasks in self.authorized_tasks_data.items():
                if project_key not in united_by_project:
                    united_by_project[project_key] = {"items": []}
                for task in project_tasks.get('items', []):
                    task_copy = task.copy()
                    task_copy['task_type'] = 'authorized'
                    united_by_project[project_key]['items'].append(task_copy)
            
            # Add restricted tasks to their respective projects
            for task_name, task_data in self.restricted_tasks_data.items():
                for task in task_data.get('items', []):
                    project_key = f"{task.get('project_name', 'Unknown')} ({task.get('project_id', 'N/A')})"
                    if project_key not in united_by_project:
                        united_by_project[project_key] = {"items": []}
                    task_copy = task.copy()
                    task_copy['task_type'] = 'restricted'
                    united_by_project[project_key]['items'].append(task_copy)
            
            # Export united breakdown by project
            self.exporter.export_multiple_datasets(united_by_project, f"united_tasks_by_project_{filename_suffix}")
            
            # Log summary statistics
            self.logger.info(f"✅ United files created successfully:")
            self.logger.info(f"   📊 Total tasks processed: {len(united_tasks_summary['items'])}")
            self.logger.info(f"   ✅ Authorized tasks: {self.authorized_tasks_count}")
            self.logger.info(f"   🚫 Restricted tasks: {self.restricted_tasks_count}")
            self.logger.info(f"   📁 Projects with authorized tasks: {len(self.authorized_tasks_data)}")
            self.logger.info(f"   🔒 Restricted task types: {len(self.restricted_tasks_data)}")
            
            self.logger.log_step("Creating United Task Files", "COMPLETE")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating united task files: {e}")
            self.logger.log_step("Creating United Task Files", "ERROR")
            return False
    
    def get_authorized_groups_details(self) -> Dict:
        """
        Get detailed information about authorized groups using GroupManager
        
        Returns:
            dict: Authorized groups data with member information
        """
        self.logger.log_step("Getting Authorized Groups Details - Using GroupManager", "START")
        
        try:
            # Get groups by names using the new GroupManager
            authorized_groups_data = self.group_manager.get_groups_by_names(self.authorized_groups)
            
            # Get detailed member information for each found group
            detailed_groups = {"items": []}
            
            for group in authorized_groups_data.get('items', []):
                group_id = group.get('id')
                group_details = self.group_manager.get_group_members_with_details(group_id)
                detailed_groups['items'].append(group_details)
            
            # Add metadata
            detailed_groups.update({
                "total_authorized_groups": len(detailed_groups['items']),
                "configured_groups": self.authorized_groups,
                "found_groups": [g.get('group_name') for g in detailed_groups['items']],
                "missing_groups": authorized_groups_data.get('missing_names', [])
            })
            
            # Export the data
            self.export_data_to_files(detailed_groups, "authorized_groups_details")
            
            self.logger.info(f"Retrieved details for {len(detailed_groups['items'])} authorized groups")
            self.logger.log_step("Getting Authorized Groups Details - Using GroupManager", "COMPLETE")
            
            return detailed_groups
            
        except Exception as e:
            self.logger.error(f"Error getting authorized groups details: {e}")
            self.logger.log_step("Getting Authorized Groups Details - Using GroupManager", "ERROR")
            return {"items": [], "error": str(e)}
    
    def get_restricted_groups_details(self) -> Dict:
        """
        Get detailed information about restricted groups using GroupManager
        
        Returns:
            dict: Restricted groups data with member information
        """
        self.logger.log_step("Getting Restricted Groups Details - Using GroupManager", "START")
        
        try:
            # Get groups by names using the new GroupManager
            restricted_groups_data = self.group_manager.get_groups_by_names(self.restricted_groups)
            
            # Get detailed member information for each found group
            detailed_groups = {"items": []}
            
            for group in restricted_groups_data.get('items', []):
                group_id = group.get('id')
                group_details = self.group_manager.get_group_members_with_details(group_id)
                detailed_groups['items'].append(group_details)
            
            # Add metadata
            detailed_groups.update({
                "total_restricted_groups": len(detailed_groups['items']),
                "configured_groups": self.restricted_groups,
                "found_groups": [g.get('group_name') for g in detailed_groups['items']],
                "missing_groups": restricted_groups_data.get('missing_names', [])
            })
            
            # Export the data
            self.export_data_to_files(detailed_groups, "restricted_groups_details")
            
            self.logger.info(f"Retrieved details for {len(detailed_groups['items'])} restricted groups")
            self.logger.log_step("Getting Restricted Groups Details - Using GroupManager", "COMPLETE")
            
            return detailed_groups
            
        except Exception as e:
            self.logger.error(f"Error getting restricted groups details: {e}")
            self.logger.log_step("Getting Restricted Groups Details - Using GroupManager", "ERROR")
            return {"items": [], "error": str(e)}
    
    def get_groups_access_summary(self) -> Dict:
        """
        Get a comprehensive summary of group access configuration using GroupManager
        
        Returns:
            dict: Complete group access summary
        """
        self.logger.log_step("Getting Groups Access Summary - Using GroupManager", "START")
        
        try:
            # Get all groups summary
            all_groups_summary = self.group_manager.get_groups_summary()
            
            # Get authorized and restricted groups details
            authorized_details = self.get_authorized_groups_details()
            restricted_details = self.get_restricted_groups_details()
            
            # Create comprehensive summary
            summary = {
                "total_groups_in_workspace": all_groups_summary.get('total_groups', 0),
                "authorized_groups": {
                    "configured_count": len(self.authorized_groups),
                    "found_count": authorized_details.get('total_authorized_groups', 0),
                    "missing_groups": authorized_details.get('missing_groups', []),
                    "details": authorized_details.get('items', [])
                },
                "restricted_groups": {
                    "configured_count": len(self.restricted_groups),
                    "found_count": restricted_details.get('total_restricted_groups', 0),
                    "missing_groups": restricted_details.get('missing_groups', []),
                    "details": restricted_details.get('items', [])
                },
                "all_groups": all_groups_summary.get('groups', [])
            }
            
            # Export the comprehensive summary
            self.export_data_to_files(summary, "groups_access_summary")
            
            self.logger.info("Generated comprehensive groups access summary")
            self.logger.log_step("Getting Groups Access Summary - Using GroupManager", "COMPLETE")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting groups access summary: {e}")
            self.logger.log_step("Getting Groups Access Summary - Using GroupManager", "ERROR")
            return {"error": str(e)}
    
    def validate_user_group_access(self, user_id: str) -> Dict:
        """
        Validate a user's group membership against authorized/restricted groups
        
        Args:
            user_id: ID of the user to validate
            
        Returns:
            dict: User's group access validation result
        """
        self.logger.debug(f"Validating group access for user: {user_id}")
        
        try:
            # Get user's groups using UserManager (this should stay in UserManager)
            user_groups = self.user_manager.get_user_groups(user_id)
            
            # Get authorized and restricted group details
            authorized_groups = self.get_authorized_groups_details()
            restricted_groups = self.get_restricted_groups_details()
            
            # Check user's membership in authorized/restricted groups
            user_authorized_groups = []
            user_restricted_groups = []
            
            for user_group in user_groups.get('items', []):
                user_group_name = user_group.get('name', '')
                
                # Check against authorized groups
                for auth_group in authorized_groups.get('items', []):
                    if auth_group.get('group_name', '').lower() == user_group_name.lower():
                        user_authorized_groups.append(user_group_name)
                
                # Check against restricted groups  
                for rest_group in restricted_groups.get('items', []):
                    if rest_group.get('group_name', '').lower() == user_group_name.lower():
                        user_restricted_groups.append(user_group_name)
            
            # Determine access status
            access_status = "ALLOWED"  # Default
            if user_restricted_groups and not user_authorized_groups:
                access_status = "RESTRICTED"
            elif user_authorized_groups:
                access_status = "AUTHORIZED"
            elif not user_authorized_groups and not user_restricted_groups:
                access_status = "NEUTRAL"
            
            validation_result = {
                "user_id": user_id,
                "access_status": access_status,
                "authorized_groups_membership": user_authorized_groups,
                "restricted_groups_membership": user_restricted_groups,
                "total_user_groups": len(user_groups.get('items', [])),
                "all_user_groups": [g.get('name') for g in user_groups.get('items', [])]
            }
            
            self.logger.info(f"User {user_id} access status: {access_status}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating user group access: {e}")
            return {"user_id": user_id, "error": str(e), "access_status": "ERROR"}
    
    def run_access_restrictions(self, client_id: str = None, role: str = "Admin") -> bool:
        """
        Execute both access restriction steps
        
        Args:
            client_id: Client ID to filter projects by (if None, uses all projects)
            role: User role to include in authorized users (default: "Admin")
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
        
        # Generate groups access summary using the new GroupManager
        self.logger.info("🔍 Generating groups access summary using GroupManager...")
        groups_summary = self.get_groups_access_summary()
        self.logger.info(f"📊 Groups Summary: {groups_summary.get('total_groups_in_workspace', 0)} total groups")
        self.logger.info(f"✅ Authorized groups found: {groups_summary.get('authorized_groups', {}).get('found_count', 0)}")
        self.logger.info(f"🚫 Restricted groups found: {groups_summary.get('restricted_groups', {}).get('found_count', 0)}")
        
        try:
            # Execute Step 1
            success_step1 = self.step_one_grant_access(client_id, role)
            
            # Execute Step 2
            success_step2 = self.step_two_remove_access(client_id)
            
            # Create united files if both steps completed
            success_united = False
            if success_step1 and success_step2:
                success_united = self.create_united_task_files(client_id)
                self.logger.info("✅ Both steps completed successfully!")
                if success_united:
                    self.logger.info("✅ United task files created successfully!")
                else:
                    self.logger.warning("⚠️  United task files creation had issues.")
                return success_united
            else:
                self.logger.warning("⚠️  Some steps completed with warnings or were skipped.")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error occurred: {e}")
            return False 