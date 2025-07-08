"""
Group Manager for Clockify API operations
Download and manage Clockify User Groups with all information
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


class GroupManager:
    """Manages Clockify user groups and group-related operations with pagination support"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize GroupManager with enhanced API client
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger("group_manager")
        self.api_client = APIClient(self.logger)
        self.exporter = DataExporter(self.logger)
        self.workspace_id = settings.clockify_workspace_id
    
    def get_all_groups(self) -> Dict:
        """
        Get all user groups in the workspace using pagination
        
        Returns:
            dict: All groups data with pagination information
        """
        self.logger.debug("Getting all user groups")
        
        # Use the enhanced API client with pagination
        groups = self.api_client.get_user_groups(paginated=True)
        
        self.logger.info(f"Retrieved {groups.get('total_count', 0)} user groups from {groups.get('pages_fetched', 0)} pages")
        return groups
    
    def get_group_by_id(self, group_id: str) -> Dict:
        """
        Get a specific group by ID
        
        Args:
            group_id: ID of the group
            
        Returns:
            dict: Group data
        """
        self.logger.debug(f"Getting group by ID: {group_id}")
        
        endpoint = f"/user-groups/{group_id}"
        result = self.api_client.get_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Retrieved group {group_id}")
        
        return result
    
    def get_group_by_name(self, group_name: str) -> Optional[Dict]:
        """
        Get a group by name
        
        Args:
            group_name: Name of the group to find
            
        Returns:
            dict or None: Group data if found, None otherwise
        """
        self.logger.debug(f"Searching for group by name: {group_name}")
        
        all_groups = self.get_all_groups()
        for group in all_groups.get('items', []):
            if group.get('name', '').lower() == group_name.lower():
                self.logger.info(f"Found group by name: {group_name}")
                return group
        
        self.logger.warning(f"Group not found by name: {group_name}")
        return None
    
    def get_group_members(self, group_id: str) -> Dict:
        """
        Get all members of a specific group
        
        Args:
            group_id: ID of the group
            
        Returns:
            dict: Group members data
        """
        self.logger.debug(f"Getting members for group: {group_id}")
        
        endpoint = f"/user-groups/{group_id}/users"
        result = self.api_client.get_workspace_data(endpoint)
        
        return result
    
    def create_user_group(self, group_data: Dict) -> Dict:
        """
        Create a new user group
        
        Args:
            group_data: Group data to create
            
        Returns:
            dict: Created group data
        """
        self.logger.debug(f"Creating user group: {group_data.get('name', 'Unknown')}")
        
        endpoint = "/user-groups"
        result = self.api_client.post_workspace_data(endpoint, group_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Created user group: {group_data.get('name', 'Unknown')}")
        
        return result
    
    def update_user_group(self, group_id: str, group_data: Dict) -> Dict:
        """
        Update an existing user group
        
        Args:
            group_id: ID of the group to update
            group_data: Updated group data
            
        Returns:
            dict: Updated group data
        """
        self.logger.debug(f"Updating user group: {group_id}")
        
        endpoint = f"/user-groups/{group_id}"
        result = self.api_client.put_workspace_data(endpoint, group_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Updated user group {group_id}")
        
        return result
    
    def delete_user_group(self, group_id: str) -> Dict:
        """
        Delete a user group
        
        Args:
            group_id: ID of the group to delete
            
        Returns:
            dict: Deletion result
        """
        self.logger.debug(f"Deleting user group: {group_id}")
        
        endpoint = f"/user-groups/{group_id}"
        result = self.api_client.delete_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Deleted user group {group_id}")
        
        return result
    
    def add_user_to_group(self, group_id: str, user_id: str) -> Dict:
        """
        Add a user to a group
        
        Args:
            group_id: ID of the group
            user_id: ID of the user to add
            
        Returns:
            dict: Operation result
        """
        self.logger.debug(f"Adding user {user_id} to group {group_id}")
        
        endpoint = f"/user-groups/{group_id}/users"
        data = {"userIds": [user_id]}
        result = self.api_client.post_workspace_data(endpoint, data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Added user {user_id} to group {group_id}")
        
        return result
    
    def remove_user_from_group(self, group_id: str, user_id: str) -> Dict:
        """
        Remove a user from a group
        
        Args:
            group_id: ID of the group
            user_id: ID of the user to remove
            
        Returns:
            dict: Operation result
        """
        self.logger.debug(f"Removing user {user_id} from group {group_id}")
        
        endpoint = f"/user-groups/{group_id}/users/{user_id}"
        result = self.api_client.delete_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Removed user {user_id} from group {group_id}")
        
        return result
    
    def get_user_groups(self, user_id: str) -> Dict:
        """
        Get groups that a user belongs to
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: User groups data
        """
        self.logger.debug(f"Getting groups for user: {user_id}")
        
        endpoint = f"/users/{user_id}/groups"
        result = self.api_client.get_workspace_data(endpoint)
        
        return result
    
    def find_groups_by_names(self, group_names: List[str]) -> Dict:
        """
        Find groups by a list of names using pagination
        
        Args:
            group_names: List of group names to find
            
        Returns:
            dict: Found groups data with search information
        """
        self.logger.debug(f"Finding groups by names: {group_names}")
        
        all_groups = self.get_all_groups()
        found_groups = {"items": []}
        missing_groups = []
        
        for group_name in group_names:
            found = False
            for group in all_groups.get('items', []):
                if group_name.lower() in group.get('name', '').lower():
                    found_groups['items'].append(group)
                    found = True
                    break
            
            if not found:
                missing_groups.append(group_name)
        
        # Add search metadata
        found_groups.update({
            "total_count": len(found_groups['items']),
            "searched_names": group_names,
            "missing_names": missing_groups,
            "total_groups_searched": all_groups.get('total_count', 0)
        })
        
        self.logger.info(f"Found {len(found_groups['items'])} groups out of {len(group_names)} searched names")
        if missing_groups:
            self.logger.warning(f"Missing groups: {missing_groups}")
        
        return found_groups
    
    def export_groups_to_csv(self, groups: Dict, filename: str) -> None:
        """
        Export groups data to CSV file in Export folder
        
        Args:
            groups: Groups data to export
            filename: Base filename for export
        """
        try:
            csv_file = self.exporter.export_to_csv(groups, filename)
            if csv_file:
                print(f"Groups exported to CSV: {csv_file}")
            else:
                print("CSV export failed - no data or invalid format")
        except Exception as e:
            error_msg = f"CSV export failed: {e}"
            self.logger.error(error_msg)
            print(error_msg)
    
    def export_groups_to_json(self, groups: Dict, filename: str) -> None:
        """
        Export groups data to JSON file in Export folder
        
        Args:
            groups: Groups data to export
            filename: Base filename for export
        """
        try:
            json_file = self.exporter.export_to_json(groups, filename)
            print(f"Groups exported to JSON: {json_file}")
        except Exception as e:
            error_msg = f"JSON export failed: {e}"
            self.logger.error(error_msg)
            print(error_msg)
    
    def get_groups_by_names(self, group_names: List[str]) -> Dict:
        """
        Get groups by exact name matches (case-insensitive)
        
        Args:
            group_names: List of group names to find
            
        Returns:
            dict: Found groups data with search information
        """
        self.logger.debug(f"Getting groups by exact names: {group_names}")
        
        all_groups = self.get_all_groups()
        found_groups = {"items": []}
        missing_groups = []
        
        for group_name in group_names:
            found = False
            for group in all_groups.get('items', []):
                if group.get('name', '').lower() == group_name.lower():
                    found_groups['items'].append(group)
                    found = True
                    break
            
            if not found:
                missing_groups.append(group_name)
        
        # Add search metadata
        found_groups.update({
            "total_count": len(found_groups['items']),
            "searched_names": group_names,
            "missing_names": missing_groups,
            "total_groups_searched": all_groups.get('total_count', 0)
        })
        
        self.logger.info(f"Found {len(found_groups['items'])} groups out of {len(group_names)} searched names")
        if missing_groups:
            self.logger.warning(f"Missing groups: {missing_groups}")
        
        return found_groups
    
    def get_group_members_with_details(self, group_id: str) -> Dict:
        """
        Get detailed information about all members of a specific group
        
        Args:
            group_id: ID of the group
            
        Returns:
            dict: Detailed group members data
        """
        self.logger.debug(f"Getting detailed members for group: {group_id}")
        
        # Get basic group members
        members = self.get_group_members(group_id)
        
        # Get group details
        group_details = self.get_group_by_id(group_id)
        
        # Combine data
        result = {
            "group_id": group_id,
            "group_name": group_details.get('name', 'Unknown'),
            "members": members,
            "member_count": len(members.get('items', [])) if isinstance(members.get('items'), list) else 0
        }
        
        self.logger.info(f"Retrieved detailed members for group {group_id}: {result['member_count']} members")
        return result
    
    def bulk_add_users_to_group(self, group_id: str, user_ids: List[str]) -> Dict:
        """
        Add multiple users to a group in a single operation
        
        Args:
            group_id: ID of the group
            user_ids: List of user IDs to add
            
        Returns:
            dict: Operation result
        """
        self.logger.debug(f"Adding {len(user_ids)} users to group {group_id}")
        
        endpoint = f"/user-groups/{group_id}/users"
        data = {"userIds": user_ids}
        result = self.api_client.post_workspace_data(endpoint, data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Added {len(user_ids)} users to group {group_id}")
        
        return result
    
    def get_groups_summary(self) -> Dict:
        """
        Get a summary of all groups with member counts
        
        Returns:
            dict: Groups summary data
        """
        self.logger.debug("Getting groups summary")
        
        all_groups = self.get_all_groups()
        summary = {
            "total_groups": all_groups.get('total_count', 0),
            "groups": []
        }
        
        for group in all_groups.get('items', []):
            group_id = group.get('id')
            group_name = group.get('name', 'Unknown')
            
            # Get member count for each group
            members = self.get_group_members(group_id)
            member_count = len(members.get('items', [])) if isinstance(members.get('items'), list) else 0
            
            summary['groups'].append({
                "id": group_id,
                "name": group_name,
                "member_count": member_count
            })
        
        self.logger.info(f"Generated summary for {summary['total_groups']} groups")
        return summary 