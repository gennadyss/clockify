#!/usr/bin/env python3
"""
Quick Project Task Checker
One-liner utility for fast project task checking
"""

import sys
sys.path.append('.')

from Tasks.Tasks import TaskManager
from Utils.logging import Logger

def quick_check(project_id):
    """Quick check of project tasks without logging noise"""
    logger = Logger('quick_check', console_output=False)  # Silent logging
    task_manager = TaskManager(logger)
    
    try:
        tasks = task_manager.get_tasks_by_project(project_id)
        task_list = tasks.get('items', [])
        
        print(f"Project {project_id} has {len(task_list)} tasks:")
        for i, task in enumerate(task_list, 1):
            print(f"  {i}. {task.get('name', 'Unknown')} (ID: {task.get('id', 'N/A')})")
        
        return task_list
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_check.py <project_id>")
        sys.exit(1)
    
    quick_check(sys.argv[1]) 