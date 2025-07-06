"""
ProjectManager for Clockify project operations
Handles project discovery, filtering, and category management
"""

from typing import Dict, List, Optional, Set, Tuple

from Config.settings import settings

# Using the centralized Utils modules
from Utils.logging import Logger
from Utils.export_data import DataExporter
from Utils.auth import AuthManager
from Utils.api_client import APIClient


class ProjectManager:
    """Manages Clockify projects, categories, and filtering operations"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize ProjectManager
        
        Args:
            logger: Optional logger instance, creates new one if not provided
        """
        self.logger = logger or Logger("project_manager", console_output=True)
        self.exporter = DataExporter(self.logger)
        self.auth_manager = AuthManager(self.logger)
        self.api_client = APIClient(self.logger)
        
        # Cache for projects data
        self._all_projects_cache = None
        self._categories_cache = None
    
    def get_all_projects(self, use_cache: bool = True) -> Dict:
        """
        Get all projects from Clockify workspace using pagination
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            dict: All projects data with pagination information
        """
        if use_cache and self._all_projects_cache is not None:
            self.logger.debug("Using cached projects data")
            return self._all_projects_cache
        
        self.logger.log_step("Getting All Projects with Pagination", "START")
        
        # Get ALL projects using pagination
        projects = self.api_client.get_projects(paginated=True)
        
        # Handle API errors
        if self.api_client.is_error_response(projects):
            error_msg = self.api_client.get_error_message(projects)
            self.logger.error(f"Failed to get projects: {error_msg}")
            return {"items": []}
        
        # Log pagination information
        total_count = projects.get('total_count', len(projects.get('items', [])))
        pages_fetched = projects.get('pages_fetched', 1)
        
        self.logger.info(f"Retrieved {total_count} projects from {pages_fetched} pages")
        
        # Export all projects for human review
        self.exporter.export_to_both_formats(projects, "all_projects")
        
        # Cache the results
        self._all_projects_cache = projects
        
        self.logger.log_step("Getting All Projects with Pagination", "COMPLETE")
        return projects
    
    def extract_categories_from_projects(self, projects: Dict) -> Dict:
        """
        Extract unique categories from project names
        Categories are typically prefixes like 'EXT.FFS', 'INT.DEV', etc.
        
        Args:
            projects: Projects data dictionary
            
        Returns:
            dict: Categories with project counts
        """
        self.logger.log_step("Extracting Categories", "START")
        
        categories_set: Set[str] = set()
        
        for project in projects.get('items', []):
            project_name = project.get('name', '')
            
            # Try to extract category from project name
            # Look for patterns like "CATEGORY.SUBCATEGORY" or "CATEGORY "
            if '.' in project_name:
                # Pattern like "EXT.FFS Something"
                potential_category = project_name.split()[0] if ' ' in project_name else project_name
                if '.' in potential_category:
                    categories_set.add(potential_category)
            elif ' ' in project_name:
                # Pattern like "EXT Something" 
                potential_category = project_name.split()[0]
                if len(potential_category) >= 3:  # Minimum category length
                    categories_set.add(potential_category)
        
        # Convert to format expected by export functions
        categories_list = []
        for cat in sorted(categories_set):
            count = self.count_projects_in_category(projects, cat)
            categories_list.append({
                "category": cat,
                "projects_count": count,
                "example_projects": self.get_example_projects_in_category(projects, cat, limit=3)
            })
        
        categories_data = {"items": categories_list}
        
        self.logger.info(f"Found {len(categories_list)} unique categories")
        
        # Export categories for human review
        self.exporter.export_to_both_formats(categories_data, "all_categories")
        
        # Cache the results
        self._categories_cache = categories_data
        
        self.logger.log_step("Extracting Categories", "COMPLETE")
        return categories_data
    
    def count_projects_in_category(self, projects: Dict, category: str) -> int:
        """Count how many projects belong to a specific category"""
        count = 0
        for project in projects.get('items', []):
            project_name = project.get('name', '')
            if self.project_belongs_to_category(project_name, category):
                count += 1
        return count
    
    def get_example_projects_in_category(self, projects: Dict, category: str, limit: int = 3) -> List[str]:
        """Get example project names for a category"""
        examples = []
        for project in projects.get('items', []):
            project_name = project.get('name', '')
            if self.project_belongs_to_category(project_name, category):
                examples.append(project_name)
                if len(examples) >= limit:
                    break
        return examples
    
    def filter_projects_by_category(self, all_projects: Dict, category: str) -> Dict:
        """
        Filter projects by specific category (e.g., 'EXT.FFS')
        More sophisticated filtering than simple substring match
        
        Args:
            all_projects: All projects data
            category: Category to filter by
            
        Returns:
            dict: Filtered projects data
        """
        self.logger.log_step(f"Filtering Projects by Category: {category}", "START")
        
        filtered_projects = {"items": []}
        
        for project in all_projects.get('items', []):
            project_name = project.get('name', '')
            
            # Check if project belongs to the specified category
            if self.project_belongs_to_category(project_name, category):
                # Add category metadata to project
                project_copy = project.copy()
                project_copy['matched_category'] = category
                project_copy['category_match_method'] = self.get_category_match_method(project_name, category)
                filtered_projects['items'].append(project_copy)
        
        self.logger.info(f"Found {len(filtered_projects['items'])} projects in category '{category}'")
        
        # Export filtered projects
        safe_category_name = category.replace('.', '_').replace(' ', '_')
        self.exporter.export_to_both_formats(filtered_projects, f"projects_category_{safe_category_name}")
        
        self.logger.log_step(f"Filtering Projects by Category: {category}", "COMPLETE")
        return filtered_projects
    
    def project_belongs_to_category(self, project_name: str, category: str) -> bool:
        """
        Determine if a project belongs to a specific category
        More sophisticated than simple substring matching
        
        Args:
            project_name: Name of the project
            category: Category to check against
            
        Returns:
            bool: True if project belongs to category
        """
        if not project_name or not category:
            return False
        
        project_name_lower = project_name.lower()
        category_lower = category.lower()
        
        # Exact match at the beginning
        if project_name_lower.startswith(category_lower + ' '):
            return True
        
        # Category with dot notation (e.g., "EXT.FFS")
        if '.' in category_lower and project_name_lower.startswith(category_lower):
            return True
        
        # Flexible matching for variations
        if category_lower in project_name_lower:
            # Make sure it's not part of another word
            words = project_name_lower.split()
            for word in words:
                if word.startswith(category_lower):
                    return True
        
        return False
    
    def get_category_match_method(self, project_name: str, category: str) -> str:
        """Get the method used to match the project to category"""
        if not project_name or not category:
            return "no_match"
        
        project_name_lower = project_name.lower()
        category_lower = category.lower()
        
        if project_name_lower.startswith(category_lower + ' '):
            return "exact_prefix"
        elif '.' in category_lower and project_name_lower.startswith(category_lower):
            return "dot_notation"
        elif category_lower in project_name_lower:
            return "substring_match"
        
        return "no_match"
    
    def get_projects_by_names(self, project_names: List[str], all_projects: Optional[Dict] = None) -> Dict:
        """
        Get specific projects by their names
        
        Args:
            project_names: List of project names to find
            all_projects: Optional projects data, will fetch if not provided
            
        Returns:
            dict: Found projects data
        """
        if all_projects is None:
            all_projects = self.get_all_projects()
        
        self.logger.log_step(f"Finding {len(project_names)} Specific Projects", "START")
        
        found_projects = {"items": []}
        missing_projects = []
        
        for target_name in project_names:
            found = False
            for project in all_projects.get('items', []):
                if project.get('name', '') == target_name:
                    found_projects['items'].append(project)
                    found = True
                    break
            
            if not found:
                missing_projects.append(target_name)
        
        self.logger.info(f"Found {len(found_projects['items'])} out of {len(project_names)} requested projects")
        
        if missing_projects:
            self.logger.warning(f"Missing projects: {missing_projects}")
        
        # Export found projects
        self.exporter.export_to_both_formats(found_projects, "specific_projects_found")
        
        # Export missing projects list
        if missing_projects:
            missing_data = {"items": [{"missing_project": name} for name in missing_projects]}
            self.exporter.export_to_both_formats(missing_data, "missing_projects")
        
        self.logger.log_step(f"Finding {len(project_names)} Specific Projects", "COMPLETE")
        return found_projects
    
    def get_all_projects_and_categories(self) -> Tuple[Dict, Dict]:
        """
        Get all projects and extract categories in one operation
        
        Returns:
            tuple: (all_projects, categories)
        """
        self.logger.log_step("Getting All Projects and Categories", "START")
        
        # Get all projects
        all_projects = self.get_all_projects()
        
        # Extract categories
        categories = self.extract_categories_from_projects(all_projects)
        
        self.logger.log_step("Getting All Projects and Categories", "COMPLETE")
        return all_projects, categories
    
    def discover_workspace_structure(self) -> Dict:
        """
        Comprehensive discovery of workspace structure
        Returns projects, categories, and statistics
        
        Returns:
            dict: Complete workspace structure data
        """
        self.logger.log_step("Discovering Workspace Structure", "START")
        
        # Get all data
        all_projects, categories = self.get_all_projects_and_categories()
        
        # Generate statistics
        stats = {
            "total_projects": len(all_projects.get('items', [])),
            "total_categories": len(categories.get('items', [])),
            "projects_per_category": {},
            "largest_category": None,
            "smallest_category": None
        }
        
        # Calculate category statistics
        for category_info in categories.get('items', []):
            cat_name = category_info.get('category', '')
            cat_count = category_info.get('projects_count', 0)
            stats["projects_per_category"][cat_name] = cat_count
        
        if stats["projects_per_category"]:
            stats["largest_category"] = max(stats["projects_per_category"], key=stats["projects_per_category"].get)
            stats["smallest_category"] = min(stats["projects_per_category"], key=stats["projects_per_category"].get)
        
        # Compile comprehensive data
        workspace_structure = {
            "discovery_timestamp": self.exporter._generate_timestamp(),
            "statistics": stats,
            "all_projects": all_projects,
            "categories": categories
        }
        
        # Export comprehensive data
        self.exporter.export_to_both_formats(workspace_structure, "workspace_structure_discovery")
        
        self.logger.info(f"Workspace discovery complete: {stats['total_projects']} projects, {stats['total_categories']} categories")
        
        self.logger.log_step("Discovering Workspace Structure", "COMPLETE")
        return workspace_structure
    
    def clear_cache(self):
        """Clear cached project and category data"""
        self._all_projects_cache = None
        self._categories_cache = None
        self.logger.debug("Project cache cleared")
    
    def filter_projects_by_client_id(self, all_projects: Dict, client_id: str) -> Dict:
        """
        Filter projects by specific client ID (category)
        Uses the clientId field in project data
        
        Args:
            all_projects: All projects data
            client_id: Client ID to filter by
            
        Returns:
            dict: Filtered projects data
        """
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id}", "START")
        
        filtered_projects = {"items": []}
        
        for project in all_projects.get('items', []):
            project_client_id = project.get('clientId', '')
            
            # Check if project belongs to the specified client
            if project_client_id == client_id:
                # Add client metadata to project
                project_copy = project.copy()
                project_copy['matched_client_id'] = client_id
                project_copy['filter_method'] = 'client_id'
                filtered_projects['items'].append(project_copy)
        
        self.logger.info(f"Found {len(filtered_projects['items'])} projects for client ID '{client_id}'")
        
        # Export filtered projects
        safe_client_id = client_id.replace('-', '_').replace('.', '_')
        self.exporter.export_to_both_formats(filtered_projects, f"projects_client_{safe_client_id}")
        
        self.logger.log_step(f"Filtering Projects by Client ID: {client_id}", "COMPLETE")
        return filtered_projects
    
    def get_projects_by_client_api(self, client_id: str) -> Dict:
        """
        Get projects filtered by client using API query parameter
        Uses the 'clients' query parameter in the projects endpoint
        
        Args:
            client_id: Client ID to filter by
            
        Returns:
            dict: Projects data filtered by client from API
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
        
        # Log pagination information
        total_count = projects.get('total_count', len(projects.get('items', [])))
        pages_fetched = projects.get('pages_fetched', 1)
        
        self.logger.info(f"Retrieved {total_count} projects for client {client_id} from {pages_fetched} pages")
        
        # Add metadata to projects
        for project in projects.get('items', []):
            project['filtered_by_client_api'] = client_id
            project['filter_method'] = 'api_query'
        
        # Export filtered projects
        safe_client_id = client_id.replace('-', '_').replace('.', '_')
        self.exporter.export_to_both_formats(projects, f"projects_client_api_{safe_client_id}")
        
        self.logger.log_step(f"Getting Projects by Client API: {client_id}", "COMPLETE")
        return projects
    
    def extract_clients_from_projects(self, projects: Dict) -> Dict:
        """
        Extract unique client IDs and names from project data
        This helps identify available categories (clients)
        
        Args:
            projects: Projects data dictionary
            
        Returns:
            dict: Client information with project counts
        """
        self.logger.log_step("Extracting Clients from Projects", "START")
        
        clients_info = {}
        
        for project in projects.get('items', []):
            client_id = project.get('clientId', '')
            client_name = project.get('clientName', 'Unknown Client')
            
            if client_id:
                if client_id not in clients_info:
                    clients_info[client_id] = {
                        "client_id": client_id,
                        "client_name": client_name,
                        "projects_count": 0,
                        "example_projects": []
                    }
                
                clients_info[client_id]["projects_count"] += 1
                if len(clients_info[client_id]["example_projects"]) < 3:
                    clients_info[client_id]["example_projects"].append(project.get('name', 'Unknown Project'))
        
        # Convert to format expected by export functions
        clients_list = list(clients_info.values())
        clients_data = {"items": clients_list}
        
        self.logger.info(f"Found {len(clients_list)} unique clients from projects")
        
        # Export clients for human review
        self.exporter.export_to_both_formats(clients_data, "clients_from_projects")
        
        self.logger.log_step("Extracting Clients from Projects", "COMPLETE")
        return clients_data 