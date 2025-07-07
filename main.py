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


def main(client_id: str = None, role: str = "Admin"):
    """
    Main execution function
    
    Args:
        client_id: Client ID to filter projects by (if None, uses all projects)
        role: User role to include in authorized users (default: "Admin")
    """
    print("🕐 Starting Clockify Access Management")
    print("=" * 50)
    
    if client_id:
        print(f"Filtering projects by client ID: {client_id}")
    else:
        print("Processing all projects (no client filter)")
    
    if role:
        print(f"Including users with role: {role}")
    
    # Create and run the access manager
    access_manager = TasksAccessManager()
    success = access_manager.run_access_restrictions(client_id, role)
    
    if success:
        print("\n🕐 Clockify Access Management completed successfully")
    else:
        print("\n🕐 Clockify Access Management completed with errors")
        sys.exit(1)


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
    parser.add_argument('--client-id', type=str, 
                       help='Client ID to filter projects by (if not specified, uses all projects)')
    parser.add_argument('--role', type=str, default='Admin',
                       help='User role to include in authorized users (default: Admin)')
    
    args = parser.parse_args()
    
    if args.demo:
        demonstrate_new_modules()
    else:
        main(args.client_id, args.role) 