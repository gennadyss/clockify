"""
API Client Utilities
Centralized Clockify API communication functionality
Enhanced with pagination support for complete data retrieval
"""

import requests
from typing import Dict, List, Optional, Any, Union
from Config.settings import settings
from .logging import Logger


class APIClient:
    """Centralized API client for Clockify communication with pagination support"""
    
    # Default pagination settings based on Clockify API documentation
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 5000
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize API client
        
        Args:
            logger: Optional logger instance
        """
        self.base_url = settings.clockify_base_url
        self.api_key = settings.clockify_api_key
        self.workspace_id = settings.clockify_workspace_id
        self.logger = logger or Logger()
        
        # Standard headers for all requests
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Clockify API
        
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method (GET, POST, PUT, DELETE)
            data: JSON data for POST/PUT requests
            params: Query parameters
            
        Returns:
            dict: API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        self.logger.log_api_request(method, endpoint)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            self.logger.log_api_request(method, endpoint, response.status_code)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {e}"
            self.logger.error(error_msg)
            return {"error": str(e)}
    
    def get_paginated_data(self, endpoint: str, params: Optional[Dict] = None, 
                          page_size: int = None, max_pages: int = None) -> Dict:
        """
        Get all data from a paginated endpoint
        
        Args:
            endpoint: API endpoint
            params: Base query parameters
            page_size: Items per page (default: MAX_PAGE_SIZE for efficiency)
            max_pages: Maximum pages to fetch (None = all pages)
            
        Returns:
            dict: Combined data from all pages
        """
        if params is None:
            params = {}
        
        # Use maximum page size for efficiency
        if page_size is None:
            page_size = self.MAX_PAGE_SIZE
        
        # Start with first page
        page = 1
        all_items = []
        total_pages_fetched = 0
        
        self.logger.debug(f"Starting paginated request for {endpoint} with page_size={page_size}")
        
        while True:
            # Prepare parameters for this page
            page_params = params.copy()
            page_params.update({
                'page': page,
                'page-size': page_size
            })
            
            # Make the request
            response = self._make_request(endpoint, 'GET', params=page_params)
            
            # Check for errors
            if self.is_error_response(response):
                self.logger.error(f"Error fetching page {page}: {self.get_error_message(response)}")
                break
            
            # Handle different response formats
            if isinstance(response, list):
                # Direct list response
                page_items = response
            elif isinstance(response, dict):
                # Object response - look for common array keys
                page_items = response.get('items', response.get('data', response.get('results', [])))
            else:
                # Unknown format
                page_items = []
            
            # Add items from this page
            if isinstance(page_items, list):
                all_items.extend(page_items)
                items_count = len(page_items)
            else:
                # Single item response
                all_items.append(page_items)
                items_count = 1
            
            total_pages_fetched += 1
            self.logger.debug(f"Page {page}: fetched {items_count} items (total: {len(all_items)})")
            
            # Check if we should continue
            if (items_count < page_size or  # Last page (partial results)
                items_count == 0 or          # No more items
                (max_pages and total_pages_fetched >= max_pages)):  # Hit max pages limit
                break
            
            page += 1
        
        self.logger.info(f"Paginated request complete: {len(all_items)} items from {total_pages_fetched} pages")
        
        # Return in consistent format
        return {"items": all_items, "total_count": len(all_items), "pages_fetched": total_pages_fetched}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request"""
        return self._make_request(endpoint, 'GET', params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make POST request"""
        return self._make_request(endpoint, 'POST', data=data, params=params)
    
    def put(self, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make PUT request"""
        return self._make_request(endpoint, 'PUT', data=data, params=params)
    
    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make DELETE request"""
        return self._make_request(endpoint, 'DELETE', params=params)
    
    # Workspace-specific convenience methods
    def get_workspace_endpoint(self, path: str) -> str:
        """Generate workspace-specific endpoint"""
        return f"/workspaces/{self.workspace_id}{path}"
    
    def get_workspace_data(self, path: str, params: Optional[Dict] = None) -> Dict:
        """GET request to workspace endpoint"""
        endpoint = self.get_workspace_endpoint(path)
        return self.get(endpoint, params)
    
    def get_workspace_data_paginated(self, path: str, params: Optional[Dict] = None, 
                                   page_size: int = None, max_pages: int = None) -> Dict:
        """GET request to workspace endpoint with pagination support"""
        endpoint = self.get_workspace_endpoint(path)
        return self.get_paginated_data(endpoint, params, page_size, max_pages)
    
    def post_workspace_data(self, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """POST request to workspace endpoint"""
        endpoint = self.get_workspace_endpoint(path)
        return self.post(endpoint, data, params)
    
    def put_workspace_data(self, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """PUT request to workspace endpoint"""
        endpoint = self.get_workspace_endpoint(path)
        return self.put(endpoint, data, params)
    
    def delete_workspace_data(self, path: str, params: Optional[Dict] = None) -> Dict:
        """DELETE request to workspace endpoint"""
        endpoint = self.get_workspace_endpoint(path)
        return self.delete(endpoint, params)
    
    # Enhanced Clockify API endpoints with pagination support
    def get_projects(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get all projects in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Projects data
        """
        if paginated:
            return self.get_workspace_data_paginated("/projects", params)
        else:
            return self.get_workspace_data("/projects", params)
    
    def get_project_tasks(self, project_id: str, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get tasks for a specific project
        
        Args:
            project_id: ID of the project
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Tasks data
        """
        if paginated:
            return self.get_workspace_data_paginated(f"/projects/{project_id}/tasks", params)
        else:
            return self.get_workspace_data(f"/projects/{project_id}/tasks", params)
    
    def get_users(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get all users in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Users data
        """
        if paginated:
            return self.get_workspace_data_paginated("/users", params)
        else:
            return self.get_workspace_data("/users", params)
    
    def get_user_groups(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get all user groups in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: User groups data
        """
        if paginated:
            return self.get_workspace_data_paginated("/user-groups", params)
        else:
            return self.get_workspace_data("/user-groups", params)
    
    def get_clients(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get all clients in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Clients data
        """
        if paginated:
            return self.get_workspace_data_paginated("/clients", params)
        else:
            return self.get_workspace_data("/clients", params)
    
    def get_tags(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get all tags in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Tags data
        """
        if paginated:
            return self.get_workspace_data_paginated("/tags", params)
        else:
            return self.get_workspace_data("/tags", params)
    
    def get_time_entries(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get time entries for workspace
        
        Args:
            params: Additional query parameters (user-id, start, end, etc.)
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Time entries data
        """
        if paginated:
            return self.get_workspace_data_paginated("/time-entries", params)
        else:
            return self.get_workspace_data("/time-entries", params)
    
    def get_custom_fields(self, params: Optional[Dict] = None, paginated: bool = True) -> Dict:
        """
        Get custom fields in workspace
        
        Args:
            params: Additional query parameters
            paginated: Whether to fetch all pages (True) or just first page (False)
            
        Returns:
            dict: Custom fields data
        """
        if paginated:
            return self.get_workspace_data_paginated("/custom-fields", params)
        else:
            return self.get_workspace_data("/custom-fields", params)
    
    def get_workspace_info(self) -> Dict:
        """Get workspace information"""
        return self.get(f"/workspaces/{self.workspace_id}")
    
    def validate_connection(self) -> bool:
        """
        Validate API connection and credentials
        
        Returns:
            bool: True if connection is valid
        """
        try:
            result = self.get_workspace_info()
            if "error" not in result:
                self.logger.info("✅ API connection validated successfully")
                return True
            else:
                self.logger.error("❌ API connection validation failed")
                return False
        except Exception as e:
            self.logger.error(f"❌ API connection validation failed: {e}")
            return False
    
    def check_rate_limits(self) -> bool:
        """
        Check if we're hitting rate limits
        
        Returns:
            bool: True if rate limits are okay
        """
        # This could be enhanced to track actual rate limit headers
        # For now, just validate connection
        return self.validate_connection()
    
    def is_error_response(self, response: Dict) -> bool:
        """Check if response contains an error"""
        return "error" in response
    
    def get_error_message(self, response: Dict) -> str:
        """Extract error message from response"""
        if self.is_error_response(response):
            return response.get("error", "Unknown error")
        return ""
    
    def batch_request(self, requests: List[Dict]) -> List[Dict]:
        """
        Execute multiple API requests
        
        Args:
            requests: List of request dictionaries with 'endpoint', 'method', 'data', 'params' keys
            
        Returns:
            list: List of response dictionaries
        """
        results = []
        
        for request in requests:
            endpoint = request.get('endpoint')
            method = request.get('method', 'GET')
            data = request.get('data')
            params = request.get('params')
            
            result = self._make_request(endpoint, method, data, params)
            results.append(result)
        
        return results
    
    def get_pagination_info(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Get pagination information for an endpoint without fetching all data
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            dict: Pagination information
        """
        # Get first page to analyze pagination
        page_params = (params or {}).copy()
        page_params.update({
            'page': 1,
            'page-size': 1  # Minimal page size for analysis
        })
        
        response = self._make_request(endpoint, 'GET', params=page_params)
        
        if self.is_error_response(response):
            return {"error": self.get_error_message(response)}
        
        # Try to determine total count and pagination info
        if isinstance(response, list):
            # Direct list response - can't determine total without fetching all
            return {
                "supports_pagination": True,
                "first_page_items": len(response),
                "estimated_total": "unknown (list response)"
            }
        elif isinstance(response, dict):
            return {
                "supports_pagination": True,
                "first_page_items": len(response.get('items', response.get('data', []))),
                "response_format": type(response).__name__,
                "available_keys": list(response.keys()) if isinstance(response, dict) else []
            }
        
        return {"supports_pagination": False} 