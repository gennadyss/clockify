#!/usr/bin/env python3
"""
Main execution script for Clockify bulk access restriction management.
This script serves as the entry point for the application.

Enhanced with domain-specific modules:
- Projects: Project discovery and client-based category management
- Clients: Client management for project categorization (based on https://docs.clockify.me/#tag/Client)
- Utils: Shared utilities for logging, export, API client, etc.

Note: In Clockify web interface, Clients are used as Categories for organizing projects.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TasksAccessRestriction.TasksAccessManager import TasksAccessManager
from Projects.ProjectManager import ProjectManager
from Clients.ClientManager import ClientManager
from Utils.logging import Logger


def main(client_id: str = None, client_name: str = None, project_id: str = None, project_name: str = None):
    """
    Main execution function
    
    Args:
        client_id: Client ID to filter projects by
        client_name: Client name to filter projects by (alternative to client_id)
        project_id: Specific project ID to process (takes precedence over client filtering)
        project_name: Specific project name to process (alternative to project_id)
    """
    print("🕐 Starting Clockify Access Management")
    print("=" * 50)
    
    # Priority: project_id > project_name > client_id > client_name > all projects
    target_project_id = None
    target_client_id = None
    
    if project_id:
        print(f"Processing specific project ID: {project_id}")
        target_project_id = project_id
    elif project_name:
        print(f"Processing specific project name: {project_name}")
        print("🔍 Looking up project ID from name...")
        # We'll need to resolve the project name to ID
        target_project_id = resolve_project_name_to_id(project_name)
        if not target_project_id:
            print(f"❌ Project with name '{project_name}' not found!")
            sys.exit(1)
        print(f"✅ Found project ID: {target_project_id}")
    elif client_id:
        print(f"Filtering projects by client ID: {client_id}")
        target_client_id = client_id
    elif client_name:
        print(f"Filtering projects by client name: {client_name}")
        print("🔍 Looking up client ID from name...")
        # We'll need to resolve the client name to ID
        target_client_id = resolve_client_name_to_id(client_name)
        if not target_client_id:
            print(f"❌ Client with name '{client_name}' not found!")
            sys.exit(1)
        print(f"✅ Found client ID: {target_client_id}")
    else:
        print("Processing all projects (no filters specified)")
    
    # Create and run the access manager
    access_manager = TasksAccessManager()
    
    # If we have a client_id, we need to set up the manager to filter by client
    if target_client_id:
        # Set the client filter in the access manager
        access_manager.client_filter_id = target_client_id
        success = access_manager.run_access_restrictions()
    elif target_project_id:
        success = access_manager.run_access_restrictions(project_id=target_project_id)
    else:
        success = access_manager.run_access_restrictions()
    
    if success:
        print("\n🕐 Clockify Access Management completed successfully")
    else:
        print("\n🕐 Clockify Access Management completed with errors")
        sys.exit(1)


def resolve_project_name_to_id(project_name: str) -> str:
    """
    Resolve project name to project ID
    
    Args:
        project_name: Name of the project to find
        
    Returns:
        str: Project ID if found, None otherwise
    """
    try:
        logger = Logger("project_resolver", console_output=True)
        project_manager = ProjectManager(logger)
        
        # Get all projects
        all_projects = project_manager.get_all_projects()
        
        # Search for project by name (case-insensitive)
        for project in all_projects.get('items', []):
            if project.get('name', '').lower() == project_name.lower():
                return project.get('id')
        
        return None
        
    except Exception as e:
        print(f"❌ Error resolving project name: {e}")
        return None


def resolve_client_name_to_id(client_name: str) -> str:
    """
    Resolve client name to client ID
    
    Args:
        client_name: Name of the client to find
        
    Returns:
        str: Client ID if found, None otherwise
    """
    try:
        logger = Logger("client_resolver", console_output=True)
        client_manager = ClientManager(logger)
        
        # Get all clients
        all_clients = client_manager.get_all_clients()
        
        # Search for client by name (case-insensitive)
        for client in all_clients.get('items', []):
            if client.get('name', '').lower() == client_name.lower():
                return client.get('id')
        
        return None
        
    except Exception as e:
        print(f"❌ Error resolving client name: {e}")
        return None


def demonstrate_new_modules():
    """Demonstrate the new domain-specific modules"""
    print("🔍 Demonstrating New Domain-Specific Modules")
    print("=" * 60)
    
    # Initialize shared logger
    logger = Logger("demo", console_output=True)
    
    # Demonstrate ProjectManager
    print("\n📁 Projects Module Demonstration:")
    project_manager = ProjectManager(logger)
    
    # Discover workspace structure
    workspace_structure = project_manager.discover_workspace_structure()
    print(f"   - Found {workspace_structure['statistics']['total_projects']} projects")
    print(f"   - Found {workspace_structure['statistics']['total_categories']} categories")
    
    # Demonstrate ClientManager
    print("\n🏢 Clients Module Demonstration:")
    client_manager = ClientManager(logger)
    
    # Discover client structure
    client_structure = client_manager.discover_client_structure()
    print(f"   - Found {client_structure['discovery_metadata']['total_clients']} clients")
    print(f"   - Found {client_structure['discovery_metadata']['clients_with_projects']} clients with projects")
    print(f"   - Total projects across clients: {client_structure['discovery_metadata']['total_projects_across_clients']}")
    
    print("\n✅ Module demonstration completed!")
    print("📊 Check the exported files for detailed results.")
    print("ℹ️  Note: In Clockify web interface, Clients are used as Categories for organizing projects.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clockify Access Management')
    parser.add_argument('--demo', action='store_true', 
                       help='Run demonstration of new modules')
    
    # Client filtering options
    parser.add_argument('--client-id', type=str, 
                       help='Client ID to filter projects by')
    parser.add_argument('--client-name', type=str,
                       help='Client name to filter projects by (alternative to --client-id)')
    
    # Project targeting options
    parser.add_argument('--project-id', type=str,
                       help='Specific project ID to process (takes precedence over client filtering)')
    parser.add_argument('--project-name', type=str,
                       help='Specific project name to process (alternative to --project-id)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.client_id and args.client_name:
        print("❌ Error: Cannot specify both --client-id and --client-name")
        sys.exit(1)
    
    if args.project_id and args.project_name:
        print("❌ Error: Cannot specify both --project-id and --project-name")
        sys.exit(1)
    
    if args.demo:
        demonstrate_new_modules()
    else:
        main(args.client_id, args.client_name, args.project_id, args.project_name) 