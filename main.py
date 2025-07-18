#!/usr/bin/env python3
"""
Main execution script for Clockify management suite.
This script serves as the entry point for multiple Clockify management processes.

Available Processes:
- TasksAccess: Bulk access restriction management for tasks
- UploadExpenses: CSV-based expense upload and management
- Demo: Demonstration of domain-specific modules

Enhanced with domain-specific modules:
- Projects: Project discovery and client-based category management
- Clients: Client management for project categorization (based on https://docs.clockify.me/#tag/Client)
- Expenses: Comprehensive expense management (based on https://docs.clockify.me/#tag/Expense)
- UploadExpenses: CSV upload functionality for expenses
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
from Expenses.ExpenseManager import ExpenseManager
from UploadExpenses.CSVExpenseUploader import CSVExpenseUploader
from Utils.logging import Logger


def main_tasks_access(client_id: str = None, client_name: str = None, project_id: str = None, project_name: str = None):
    """
    Main execution function for Tasks Access Management
    
    Args:
        client_id: Client ID to filter projects by
        client_name: Client name to filter projects by (alternative to client_id)
        project_id: Specific project ID to process (takes precedence over client filtering)
        project_name: Specific project name to process (alternative to project_id)
    """
    print("🕐 Starting Clockify Tasks Access Management")
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
        print("\n🕐 Clockify Tasks Access Management completed successfully")
    else:
        print("\n🕐 Clockify Tasks Access Management completed with errors")
        sys.exit(1)


def main_upload_expenses(workspace_id: str, csv_file: str, dry_run: bool = False, 
                        chunk_size: int = 50, generate_template: bool = False,
                        user_email: str = None):
    """
    Main execution function for Expense Upload
    
    Args:
        workspace_id: Clockify workspace ID
        csv_file: Path to CSV file containing expenses
        dry_run: If True, validate only without uploading
        chunk_size: Number of expenses to upload in each batch
        generate_template: If True, generate a CSV template and exit
        user_email: Default user email to assign to expenses if not specified in CSV
    """
    print("💰 Starting Clockify Expense Upload")
    print("=" * 50)
    
    try:
        # Initialize uploader
        logger = Logger("expense_upload", console_output=True)
        uploader = CSVExpenseUploader(logger=logger)
        
        # Generate template if requested
        if generate_template:
            print("📄 Generating CSV template...")
            template_result = uploader.generate_csv_template()
            
            if template_result.get('success'):
                print(f"✅ CSV template generated: {template_result['template_path']}")
                print(f"📊 Template includes {template_result['sample_rows']} sample rows")
                print(f"📋 Columns: {', '.join(template_result['columns_included'])}")
                return
            else:
                print(f"❌ Failed to generate template: {template_result.get('error')}")
                sys.exit(1)
        
        # Validate required parameters
        if not workspace_id:
            print("❌ Workspace ID is required for expense upload")
            sys.exit(1)
        
        if not csv_file:
            print("❌ CSV file path is required for expense upload")
            sys.exit(1)
        
        print(f"📋 Workspace ID: {workspace_id}")
        print(f"📄 CSV File: {csv_file}")
        print(f"🔍 Dry Run: {dry_run}")
        print(f"📦 Chunk Size: {chunk_size}")
        
        # Perform upload
        result = uploader.upload_from_csv(
            csv_file_path=csv_file,
            workspace_id=workspace_id,
            dry_run=dry_run,
            chunk_size=chunk_size,
            default_user_email=user_email
        )
        
        # Report results
        if result.get('success'):
            if dry_run:
                print(f"\n✅ Dry run completed successfully")
                print(f"📊 Total records: {result['total_records']}")
                print(f"✅ Valid records: {result['valid_records']}")
                print(f"❌ Invalid records: {result['invalid_records']}")
                
                if result['invalid_records'] > 0:
                    print(f"\n⚠️  Found {result['invalid_records']} validation errors:")
                    for error in result['validation_errors'][:5]:  # Show first 5 errors
                        print(f"   Row {error['row_index']}: {', '.join(error['errors'])}")
                    if len(result['validation_errors']) > 5:
                        print(f"   ... and {len(result['validation_errors']) - 5} more errors")
                
                print(f"\n📝 Review validation results and fix any errors before uploading")
            else:
                upload_results = result['upload_results']
                print(f"\n✅ Upload completed successfully")
                print(f"📊 Total CSV records: {result['total_records_in_csv']}")
                print(f"✅ Valid records: {result['valid_records']}")
                print(f"❌ Invalid records: {result['invalid_records']}")
                print(f"💰 Expenses created: {upload_results['total_created']}")
                print(f"❌ Upload failures: {upload_results['total_failed']}")
                
                if result['invalid_records'] > 0:
                    print(f"\n⚠️  Validation errors prevented {result['invalid_records']} records from being processed")
                
                if upload_results['total_failed'] > 0:
                    print(f"\n⚠️  {upload_results['total_failed']} expenses failed to upload")
        else:
            print(f"\n❌ Upload failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        print(f"\n💰 Clockify Expense Upload completed")
        
    except Exception as e:
        print(f"\n❌ Error in expense upload: {str(e)}")
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


def main():
    """Main dispatcher function that routes to appropriate process handlers"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clockify Management Suite - Multiple processes for Clockify automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tasks Access Management
  python main.py tasks-access --client-name "EXT.FFS"
  python main.py tasks-access --project-id "abc123"
  
  # Expense Upload
  python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv"
  python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv" --dry-run
  python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv" --user-email "user@example.com"
  python main.py upload-expenses --generate-template
  
  # Module Demonstration
  python main.py demo
        """
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='process', help='Available processes')
    
    # Tasks Access Management subcommand
    tasks_parser = subparsers.add_parser(
        'tasks-access', 
        help='Bulk access restriction management for tasks'
    )
    tasks_parser.add_argument('--client-id', type=str, 
                             help='Client ID to filter projects by')
    tasks_parser.add_argument('--client-name', type=str,
                             help='Client name to filter projects by (alternative to --client-id)')
    tasks_parser.add_argument('--project-id', type=str,
                             help='Specific project ID to process (takes precedence over client filtering)')
    tasks_parser.add_argument('--project-name', type=str,
                             help='Specific project name to process (alternative to --project-id)')
    
    # Expense Upload subcommand
    expenses_parser = subparsers.add_parser(
        'upload-expenses', 
        help='CSV-based expense upload and management'
    )
    expenses_parser.add_argument('--workspace-id', type=str, required=False,
                                help='Clockify workspace ID (required unless --generate-template)')
    expenses_parser.add_argument('--csv-file', type=str, required=False,
                                help='Path to CSV file containing expenses (required unless --generate-template)')
    expenses_parser.add_argument('--dry-run', action='store_true',
                                help='Validate CSV data without uploading to Clockify')
    expenses_parser.add_argument('--chunk-size', type=int, default=50,
                                help='Number of expenses to upload in each batch (default: 50)')
    expenses_parser.add_argument('--generate-template', action='store_true',
                                help='Generate a CSV template file and exit')
    expenses_parser.add_argument('--user-email', type=str, required=False,
                                help='Default user email to assign to expenses if not specified in CSV')
    
    # Demo subcommand
    demo_parser = subparsers.add_parser(
        'demo', 
        help='Demonstrate domain-specific modules'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    if args.process == 'tasks-access':
        # Validate arguments for tasks access
        if args.client_id and args.client_name:
            print("❌ Error: Cannot specify both --client-id and --client-name")
            sys.exit(1)
        
        if args.project_id and args.project_name:
            print("❌ Error: Cannot specify both --project-id and --project-name")
            sys.exit(1)
        
        main_tasks_access(args.client_id, args.client_name, args.project_id, args.project_name)
        
    elif args.process == 'upload-expenses':
        # Validate arguments for expense upload
        if not args.generate_template:
            if not args.workspace_id:
                print("❌ Error: --workspace-id is required (unless using --generate-template)")
                sys.exit(1)
            
            if not args.csv_file:
                print("❌ Error: --csv-file is required (unless using --generate-template)")
                sys.exit(1)
        
        main_upload_expenses(
            workspace_id=args.workspace_id,
            csv_file=args.csv_file,
            dry_run=args.dry_run,
            chunk_size=args.chunk_size,
            generate_template=args.generate_template,
            user_email=args.user_email
        )
        
    elif args.process == 'demo':
        demonstrate_new_modules()
        
    else:
        # No subcommand provided, show help
        parser.print_help()
        print("\n❌ Error: Please specify a process to run")
        print("Available processes: tasks-access, upload-expenses, demo")
        sys.exit(1)


if __name__ == "__main__":
    main() 