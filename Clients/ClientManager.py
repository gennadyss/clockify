"""
ClientManager for Clockify Client operations
Handles client discovery, management, and project filtering by client (category)
Based on https://docs.clockify.me/#tag/Client

In Clockify web interface, Clients are used as Categories for organizing projects.
"""

from typing import Dict, List, Optional, Set, Tuple

from Config.settings import settings

# Using the centralized Utils modules
from Utils.logging import Logger
from Utils.export_data import DataExporter
from Utils.auth import AuthManager
from Utils.api_client import APIClient


class ClientManager:
    """Manages Clockify clients (categories) and client-based project filtering operations"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize ClientManager
        
        Args:
            logger: Optional logger instance, creates new one if not provided
        """
        self.logger = logger or Logger("client_manager", console_output=True)
        self.exporter = DataExporter(self.logger)
        self.auth_manager = AuthManager(self.logger)
        self.api_client = APIClient(self.logger)
        
        # Cache for clients data
        self._all_clients_cache = None
    
    def get_all_clients(self, use_cache: bool = True) -> Dict:
        """
        Get all clients from Clockify workspace using pagination
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            dict: All clients data with pagination information
        """
        if use_cache and self._all_clients_cache is not None:
            self.logger.debug("Using cached clients data")
            return self._all_clients_cache
        
        self.logger.log_step("Getting All Clients with Pagination", "START")
        
        # Get clients using API client with pagination
        clients = self.api_client.get_clients(paginated=True)
        
        # Handle API errors
        if self.api_client.is_error_response(clients):
            error_msg = self.api_client.get_error_message(clients)
            self.logger.error(f"Failed to get clients: {error_msg}")
            return {"items": []}
        
        # Log pagination information
        total_count = clients.get('total_count', len(clients.get('items', [])))
        pages_fetched = clients.get('pages_fetched', 1)
        
        self.logger.info(f"Retrieved {total_count} clients from {pages_fetched} pages")
        
        # Export all clients for human review
        self.exporter.export_to_both_formats(clients, "all_clients")
        
        # Cache the results
        self._all_clients_cache = clients
        
        self.logger.log_step("Getting All Clients with Pagination", "COMPLETE")
        return clients
    
    def get_client_by_id(self, client_id: str) -> Dict:
        """
        Get a specific client by ID
        
        Args:
            client_id: Client ID to retrieve
            
        Returns:
            dict: Client data
        """
        self.logger.debug(f"Getting client by ID: {client_id}")
        
        endpoint = f"/clients/{client_id}"
        result = self.api_client.get_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Retrieved client {client_id}")
        
        return result
    
    def get_client_by_name(self, client_name: str) -> Optional[Dict]:
        """
        Get a client by name
        
        Args:
            client_name: Name of the client to find
            
        Returns:
            dict or None: Client data if found, None otherwise
        """
        self.logger.debug(f"Searching for client by name: {client_name}")
        
        all_clients = self.get_all_clients()
        for client in all_clients.get('items', []):
            if client.get('name', '').lower() == client_name.lower():
                self.logger.info(f"Found client by name: {client_name}")
                return client
        
        self.logger.warning(f"Client not found by name: {client_name}")
        return None
    
    def filter_projects_by_client_id(self, projects: Dict, client_id: str) -> Dict:
        """
        Filter projects by specific client ID (category)
        
        Args:
            projects: All projects data
            client_id: Client ID to filter by
            
        Returns:
            dict: Filtered projects data
        """
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id}", "START")
        
        filtered_projects = {"items": []}
        
        for project in projects.get('items', []):
            project_client_id = project.get('clientId', '')
            
            if project_client_id == client_id:
                # Add client metadata to project
                project_copy = project.copy()
                project_copy['filtered_by_client'] = client_id
                filtered_projects['items'].append(project_copy)
        
        self.logger.info(f"Found {len(filtered_projects['items'])} projects for client '{client_id}'")
        
        # Export filtered projects
        safe_client_name = client_id.replace('-', '_')
        self.exporter.export_to_both_formats(filtered_projects, f"projects_client_{safe_client_name}")
        
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id}", "COMPLETE")
        return filtered_projects
    
    def filter_projects_by_client_name(self, projects: Dict, client_name: str, all_clients: Optional[Dict] = None) -> Dict:
        """
        Filter projects by client name (category name)
        
        Args:
            projects: All projects data
            client_name: Client name to filter by
            all_clients: Optional clients data
            
        Returns:
            dict: Filtered projects data
        """
        if all_clients is None:
            all_clients = self.get_all_clients()
        
        # Find client ID by name
        client_id = None
        for client in all_clients.get('items', []):
            if client.get('name', '').lower() == client_name.lower():
                client_id = client.get('id', '')
                break
        
        if not client_id:
            self.logger.warning(f"Client '{client_name}' not found")
            return {"items": []}
        
        return self.filter_projects_by_client_id(projects, client_id)
    
    def get_projects_by_client_api(self, client_id: str) -> Dict:
        """
        Get projects filtered by client using API query parameter
        Uses the 'clients' query parameter in the projects endpoint
        
        Args:
            client_id: Client ID to filter by
            
        Returns:
            dict: Projects data filtered by client
        """
        self.logger.log_step(f"Getting Projects by Client API: {client_id}", "START")
        
        # Use the clients query parameter to filter projects
        params = {"clients": client_id}
        projects = self.api_client.get_projects(params=params, paginated=True)
        
        # Handle API errors
        if self.api_client.is_error_response(projects):
            error_msg = self.api_client.get_error_message(projects)
            self.logger.error(f"Failed to get projects by client: {error_msg}")
            return {"items": []}
        
        # Log results
        total_count = projects.get('total_count', len(projects.get('items', [])))
        pages_fetched = projects.get('pages_fetched', 1)
        
        self.logger.info(f"Retrieved {total_count} projects for client {client_id} from {pages_fetched} pages")
        
        # Export filtered projects
        safe_client_name = client_id.replace('-', '_')
        self.exporter.export_to_both_formats(projects, f"projects_by_client_api_{safe_client_name}")
        
        self.logger.log_step(f"Getting Projects by Client API: {client_id}", "COMPLETE")
        return projects
    
    def get_clients_summary(self, all_clients: Optional[Dict] = None, all_projects: Optional[Dict] = None) -> Dict:
        """
        Get summary of clients with project counts
        
        Args:
            all_clients: Optional clients data
            all_projects: Optional projects data
            
        Returns:
            dict: Clients summary with project counts
        """
        self.logger.log_step("Creating Clients Summary", "START")
        
        if all_clients is None:
            all_clients = self.get_all_clients()
        
        # If projects not provided, we'll get counts via API calls
        summary = {"items": []}
        
        for client in all_clients.get('items', []):
            client_id = client.get('id', '')
            client_name = client.get('name', '')
            
            # Get project count for this client
            if all_projects:
                # Count from provided projects data
                project_count = sum(1 for project in all_projects.get('items', []) 
                                  if project.get('clientId') == client_id)
            else:
                # Get count via API
                client_projects = self.get_projects_by_client_api(client_id)
                project_count = client_projects.get('total_count', len(client_projects.get('items', [])))
            
            client_summary = {
                "client_id": client_id,
                "client_name": client_name,
                "project_count": project_count,
                "archived": client.get('archived', False),
                "note": client.get('note', ''),
                "workspaceId": client.get('workspaceId', '')
            }
            
            summary['items'].append(client_summary)
        
        # Sort by project count (descending)
        summary['items'].sort(key=lambda x: x['project_count'], reverse=True)
        
        # Add total summary
        summary.update({
            "total_clients": len(summary['items']),
            "total_projects_across_clients": sum(item['project_count'] for item in summary['items']),
            "clients_with_projects": len([item for item in summary['items'] if item['project_count'] > 0])
        })
        
        self.logger.info(f"Created summary for {summary['total_clients']} clients")
        
        # Export summary
        self.exporter.export_to_both_formats(summary, "clients_summary")
        
        self.logger.log_step("Creating Clients Summary", "COMPLETE")
        return summary
    
    def create_client(self, client_data: Dict) -> Dict:
        """
        Create a new client (category)
        
        Args:
            client_data: Client data to create
            
        Returns:
            dict: Created client data
        """
        self.logger.debug(f"Creating client: {client_data.get('name', 'Unknown')}")
        
        endpoint = "/clients"
        result = self.api_client.post_workspace_data(endpoint, client_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Created client: {client_data.get('name', 'Unknown')}")
            # Clear cache since we added a new client
            self._all_clients_cache = None
        
        return result
    
    def update_client(self, client_id: str, client_data: Dict) -> Dict:
        """
        Update an existing client (category)
        
        Args:
            client_id: ID of the client to update
            client_data: Updated client data
            
        Returns:
            dict: Updated client data
        """
        self.logger.debug(f"Updating client: {client_id}")
        
        endpoint = f"/clients/{client_id}"
        result = self.api_client.put_workspace_data(endpoint, client_data)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Updated client {client_id}")
            # Clear cache since we updated a client
            self._all_clients_cache = None
        
        return result
    
    def delete_client(self, client_id: str) -> Dict:
        """
        Delete a client (category)
        
        Args:
            client_id: ID of the client to delete
            
        Returns:
            dict: Deletion result
        """
        self.logger.debug(f"Deleting client: {client_id}")
        
        endpoint = f"/clients/{client_id}"
        result = self.api_client.delete_workspace_data(endpoint)
        
        if not self.api_client.is_error_response(result):
            self.logger.info(f"Deleted client {client_id}")
            # Clear cache since we deleted a client
            self._all_clients_cache = None
        
        return result
    
    def discover_client_structure(self) -> Dict:
        """
        Discover and analyze the complete client structure in the workspace
        
        Returns:
            dict: Complete client structure analysis
        """
        self.logger.log_step("Discovering Client Structure", "START")
        
        # Get all clients and projects
        all_clients = self.get_all_clients()
        
        # Get clients summary with project counts
        clients_summary = self.get_clients_summary(all_clients)
        
        # Create comprehensive structure
        structure = {
            "clients": all_clients,
            "clients_summary": clients_summary,
            "discovery_metadata": {
                "total_clients": len(all_clients.get('items', [])),
                "clients_with_projects": clients_summary.get('clients_with_projects', 0),
                "total_projects_across_clients": clients_summary.get('total_projects_across_clients', 0)
            }
        }
        
        # Export complete structure
        self.exporter.export_to_both_formats(structure, "client_structure_discovery")
        
        self.logger.log_step("Discovering Client Structure", "COMPLETE")
        return structure
    
    def clear_cache(self):
        """Clear all cached client data"""
        self._all_clients_cache = None
        self.logger.debug("Client cache cleared") 