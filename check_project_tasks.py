#!/usr/bin/env python3
"""
Check Project Tasks Script
Quick utility to check tasks for a specific Clockify project ID
"""

import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.append('.')

from Tasks.Tasks import TaskManager
from Projects.ProjectManager import ProjectManager
from Utils.logging import Logger
from Utils.export_data import DataExporter

def check_project_tasks(project_id, export_data=False, detailed=False):
    """
    Check tasks for a specific project ID
    
    Args:
        project_id: Clockify project ID
        export_data: Whether to export data to files
        detailed: Whether to show detailed task information
    """
    print(f"🔍 Checking tasks for project: {project_id}")
    print("=" * 60)
    
    # Initialize managers
    logger = Logger('project_tasks_check', console_output=True)
    task_manager = TaskManager(logger)
    project_manager = ProjectManager(logger)
    
    try:
        # Get project details first
        print("📁 Getting project details...")
        all_projects = project_manager.get_all_projects()
        
        project_info = None
        for project in all_projects.get('items', []):
            if project.get('id') == project_id:
                project_info = project
                break
        
        if project_info:
            print(f"   Project Name: {project_info.get('name', 'Unknown')}")
            print(f"   Client ID: {project_info.get('clientId', 'N/A')}")
            print(f"   Color: {project_info.get('color', 'N/A')}")
            print(f"   Archived: {project_info.get('archived', False)}")
            print()
        else:
            print("   ⚠️  Project not found in workspace")
            print()
        
        # Get tasks for this project
        print("📋 Getting tasks...")
        tasks = task_manager.get_tasks_by_project(project_id)
        
        task_count = len(tasks.get('items', []))
        print(f"   Found {task_count} tasks")
        print()
        
        if task_count > 0:
            print("📝 Task List:")
            for i, task in enumerate(tasks.get('items', []), 1):
                task_name = task.get('name', 'Unknown')
                task_id = task.get('id', 'N/A')
                
                if detailed:
                    print(f"   {i}. {task_name}")
                    print(f"      ID: {task_id}")
                    print(f"      Project ID: {task.get('projectId', 'N/A')}")
                    print(f"      Status: {task.get('status', 'N/A')}")
                    print(f"      Assignee IDs: {task.get('assigneeIds', [])}")
                    print(f"      User Group IDs: {task.get('userGroupIds', [])}")
                    print(f"      Estimate: {task.get('estimate', 'N/A')}")
                    print(f"      Duration: {task.get('duration', 'N/A')}")
                    print()
                else:
                    print(f"   {i}. {task_name} (ID: {task_id})")
        
        # Export data if requested
        if export_data:
            print("💾 Exporting data...")
            exporter = DataExporter(logger)
            
            # Export tasks
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exporter.export_to_json(tasks, f"project_{project_id}_tasks_{timestamp}")
            exporter.export_to_csv(tasks, f"project_{project_id}_tasks_{timestamp}")
            
            # Export project info if available
            if project_info:
                project_data = {"items": [project_info]}
                exporter.export_to_json(project_data, f"project_{project_id}_info_{timestamp}")
            
            print("   ✅ Data exported to Export/ folder")
        
        print()
        print("✅ Task check completed!")
        return tasks
        
    except Exception as e:
        print(f"❌ Error checking project tasks: {str(e)}")
        return None

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Check tasks for a specific Clockify project')
    parser.add_argument('project_id', help='Clockify project ID')
    parser.add_argument('--export', action='store_true', help='Export data to files')
    parser.add_argument('--detailed', action='store_true', help='Show detailed task information')
    
    args = parser.parse_args()
    
    check_project_tasks(args.project_id, args.export, args.detailed)

if __name__ == "__main__":
    main() 