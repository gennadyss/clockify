"""
ExpenseManager - Comprehensive expense management for Clockify API

This module provides complete expense management functionality including:
- Creating, reading, updating, and deleting expenses
- Expense validation and data formatting
- Bulk expense operations
- Export and reporting capabilities
- Integration with Clockify workspace and project structures

Author: Auto-generated for Clockify Expense Management
Based on: https://docs.clockify.me/#tag/Expense
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.api_client import APIClient
from Utils.logging import Logger
from Utils.export_data import DataExporter
from Utils.file_utils import FileUtils


class ExpenseManager:
    """
    Comprehensive expense management for Clockify API
    
    Provides full CRUD operations for expenses, including:
    - Creating new expenses
    - Retrieving expense data
    - Updating existing expenses
    - Deleting expenses
    - Bulk operations and reporting
    """
    
    def __init__(self, logger: Logger = None):
        """
        Initialize ExpenseManager
        
        Args:
            logger: Logger instance for tracking operations
        """
        self.logger = logger or Logger("ExpenseManager", console_output=True)
        self.api_client = APIClient(logger=self.logger)
        self.data_exporter = DataExporter(logger=self.logger)
        self.file_utils = FileUtils(logger=self.logger)
        
        # Expense data cache
        self._expense_cache = {}
        self._workspace_cache = {}
        
        self.logger.info("ExpenseManager initialized successfully")

    def get_all_expenses(self, workspace_id: str, user_id: str = None, project_id: str = None,
                        start_date: str = None, end_date: str = None, page_size: int = 50) -> Dict[str, Any]:
        """
        Retrieve all expenses for a workspace or user
        
        Args:
            workspace_id: Clockify workspace ID
            user_id: Optional user ID to filter expenses
            project_id: Optional project ID to filter expenses
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            page_size: Number of expenses per page (max 50)
            
        Returns:
            Dict containing expense data and metadata
        """
        try:
            self.logger.info(f"Retrieving expenses for workspace: {workspace_id}")
            
            # Build endpoint URL
            if user_id:
                endpoint = f"/workspaces/{workspace_id}/user/{user_id}/expenses"
            else:
                endpoint = f"/workspaces/{workspace_id}/expenses"
            
            # Build query parameters
            params = {
                "page-size": min(page_size, 50)  # Ensure max 50 per API limits
            }
            
            if project_id:
                params["project"] = project_id
            if start_date:
                params["start"] = start_date
            if end_date:
                params["end"] = end_date
                
            # Make API request
            response = self.api_client.get(endpoint, params=params)
            
            # Check if response contains an error
            if self.api_client.is_error_response(response):
                error_msg = self.api_client.get_error_message(response)
                self.logger.error(f"Failed to retrieve expenses: {error_msg}")
                return {
                    'expenses': [],
                    'total_count': 0,
                    'workspace_id': workspace_id,
                    'success': False,
                    'error': error_msg
                }
            else:
                # Successful response - Clockify returns expense list directly
                expenses_data = response if isinstance(response, list) else []
                
                result = {
                    'expenses': expenses_data,
                    'total_count': len(expenses_data),
                    'workspace_id': workspace_id,
                    'user_id': user_id,
                    'project_id': project_id,
                    'filters_applied': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'project_id': project_id
                    },
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
                
                self.logger.info(f"Retrieved {len(expenses_data)} expenses successfully")
                return result
                
        except Exception as e:
            self.logger.error(f"Error retrieving expenses: {str(e)}")
            return {
                'expenses': [],
                'total_count': 0,
                'workspace_id': workspace_id,
                'success': False,
                'error': str(e)
            }

    def get_expense_by_id(self, workspace_id: str, expense_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific expense by ID
        
        Args:
            workspace_id: Clockify workspace ID
            expense_id: Expense ID to retrieve
            
        Returns:
            Dict containing expense data
        """
        try:
            self.logger.info(f"Retrieving expense {expense_id} from workspace {workspace_id}")
            
            endpoint = f"/workspaces/{workspace_id}/expenses/{expense_id}"
            response = self.api_client.get(endpoint)
            
            if response.get('success'):
                expense_data = response.get('data')
                
                result = {
                    'expense': expense_data,
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
                
                self.logger.info(f"Retrieved expense {expense_id} successfully")
                return result
            else:
                self.logger.error(f"Failed to retrieve expense {expense_id}: {response.get('error')}")
                return {
                    'expense': None,
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'success': False,
                    'error': response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            self.logger.error(f"Error retrieving expense {expense_id}: {str(e)}")
            return {
                'expense': None,
                'workspace_id': workspace_id,
                'expense_id': expense_id,
                'success': False,
                'error': str(e)
            }

    def create_expense(self, workspace_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new expense using the Clockify API
        
        Args:
            workspace_id: Clockify workspace ID
            expense_data: Expense data dictionary containing required fields
            
        Returns:
            Dict containing created expense data
        """
        try:
            self.logger.info(f"Creating new expense in workspace {workspace_id}")
            
            # Validate required expense fields for Clockify API
            required_fields = ['amount', 'categoryId', 'date', 'projectId', 'userId']
            for field in required_fields:
                if field not in expense_data:
                    raise ValueError(f"Required field '{field}' missing from expense data")
            
            # Prepare form data for multipart/form-data request
            form_data = {
                'amount': str(expense_data['amount']),
                'categoryId': expense_data['categoryId'],
                'date': expense_data['date'],  # Should be ISO format: 2020-01-01T00:00:00Z
                'projectId': expense_data['projectId'],
                'userId': expense_data['userId']
            }
            
            # Add optional fields
            if 'billable' in expense_data:
                form_data['billable'] = str(expense_data['billable']).lower()
            if 'notes' in expense_data:
                form_data['notes'] = expense_data['notes']
            if 'taskId' in expense_data:
                form_data['taskId'] = expense_data['taskId']
            
            # Handle file upload - REQUIRED by Clockify API
            files = {}
            if 'receipt_file' in expense_data and expense_data['receipt_file']:
                files['file'] = expense_data['receipt_file']
            else:
                # Use /dev/null since we know it works with curl
                files['file'] = ('receipt.txt', open('/dev/null', 'rb'))
            
            endpoint = f"/workspaces/{workspace_id}/expenses"
            
            response = self.api_client.post(endpoint, data=form_data, files=files)
            
            if 'error' in response:
                self.logger.error(f"Failed to create expense: {response['error']}")
                return {
                    'success': False,
                    'error': response['error'],
                    'workspace_id': workspace_id,
                    'expense_data': expense_data,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            result = {
                'success': True,
                'expense': response,
                'workspace_id': workspace_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Created expense successfully: {response.get('id', 'Unknown ID')}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to create expense: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'workspace_id': workspace_id,
                'expense_data': expense_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def update_expense(self, workspace_id: str, expense_id: str, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing expense
        
        Args:
            workspace_id: Clockify workspace ID
            expense_id: Expense ID to update
            expense_data: Updated expense data
            
        Returns:
            Dict containing updated expense data
        """
        try:
            self.logger.info(f"Updating expense {expense_id} in workspace {workspace_id}")
            
            # Format expense data
            formatted_expense = self._format_expense_data(expense_data)
            
            endpoint = f"/workspaces/{workspace_id}/expenses/{expense_id}"
            response = self.api_client.put(endpoint, data=formatted_expense)
            
            if response.get('success'):
                updated_expense = response.get('data')
                
                result = {
                    'expense': updated_expense,
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
                
                self.logger.info(f"Updated expense {expense_id} successfully")
                return result
            else:
                self.logger.error(f"Failed to update expense {expense_id}: {response.get('error')}")
                return {
                    'expense': None,
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'success': False,
                    'error': response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            self.logger.error(f"Error updating expense {expense_id}: {str(e)}")
            return {
                'expense': None,
                'workspace_id': workspace_id,
                'expense_id': expense_id,
                'success': False,
                'error': str(e)
            }

    def delete_expense(self, workspace_id: str, expense_id: str) -> Dict[str, Any]:
        """
        Delete an expense
        
        Args:
            workspace_id: Clockify workspace ID
            expense_id: Expense ID to delete
            
        Returns:
            Dict containing deletion result
        """
        try:
            self.logger.info(f"Deleting expense {expense_id} from workspace {workspace_id}")
            
            endpoint = f"/workspaces/{workspace_id}/expenses/{expense_id}"
            response = self.api_client.delete(endpoint)
            
            if response.get('success'):
                result = {
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'deleted_at': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
                
                self.logger.info(f"Deleted expense {expense_id} successfully")
                return result
            else:
                self.logger.error(f"Failed to delete expense {expense_id}: {response.get('error')}")
                return {
                    'workspace_id': workspace_id,
                    'expense_id': expense_id,
                    'success': False,
                    'error': response.get('error', 'Unknown error')
                }
                
        except Exception as e:
            self.logger.error(f"Error deleting expense {expense_id}: {str(e)}")
            return {
                'workspace_id': workspace_id,
                'expense_id': expense_id,
                'success': False,
                'error': str(e)
            }

    def bulk_create_expenses(self, workspace_id: str, expenses_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple expenses in bulk
        
        Args:
            workspace_id: Clockify workspace ID
            expenses_list: List of expense data dictionaries
            
        Returns:
            Dict containing bulk creation results
        """
        try:
            self.logger.info(f"Creating {len(expenses_list)} expenses in bulk for workspace {workspace_id}")
            
            created_expenses = []
            failed_expenses = []
            
            for i, expense_data in enumerate(expenses_list):
                try:
                    result = self.create_expense(workspace_id, expense_data)
                    if result.get('success'):
                        created_expenses.append(result['expense'])
                        self.logger.debug(f"Bulk creation {i+1}/{len(expenses_list)}: Success")
                    else:
                        failed_expenses.append({
                            'index': i,
                            'expense_data': expense_data,
                            'error': result.get('error')
                        })
                        self.logger.warning(f"Bulk creation {i+1}/{len(expenses_list)}: Failed - {result.get('error')}")
                        
                except Exception as e:
                    failed_expenses.append({
                        'index': i,
                        'expense_data': expense_data,
                        'error': str(e)
                    })
                    self.logger.warning(f"Bulk creation {i+1}/{len(expenses_list)}: Exception - {str(e)}")
            
            result = {
                'workspace_id': workspace_id,
                'total_attempted': len(expenses_list),
                'total_created': len(created_expenses),
                'total_failed': len(failed_expenses),
                'created_expenses': created_expenses,
                'failed_expenses': failed_expenses,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'success': len(created_expenses) > 0
            }
            
            self.logger.info(f"Bulk creation completed: {len(created_expenses)}/{len(expenses_list)} successful")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in bulk expense creation: {str(e)}")
            return {
                'workspace_id': workspace_id,
                'total_attempted': len(expenses_list),
                'total_created': 0,
                'total_failed': len(expenses_list),
                'created_expenses': [],
                'failed_expenses': [{'error': str(e), 'expense_data': exp} for exp in expenses_list],
                'success': False,
                'error': str(e)
            }

    def export_expenses(self, workspace_id: str, output_format: str = "json", 
                       filename: str = None, **filter_kwargs) -> Dict[str, Any]:
        """
        Export expenses to file
        
        Args:
            workspace_id: Clockify workspace ID
            output_format: Export format (json, csv, xlsx)
            filename: Optional custom filename
            **filter_kwargs: Additional filters for expense retrieval
            
        Returns:
            Dict containing export results
        """
        try:
            self.logger.info(f"Exporting expenses for workspace {workspace_id} in {output_format} format")
            
            # Get expenses data
            expenses_result = self.get_all_expenses(workspace_id, **filter_kwargs)
            
            if not expenses_result.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to retrieve expenses: {expenses_result.get('error')}"
                }
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"expenses_export_{workspace_id}_{timestamp}"
            
            # Export data
            export_result = self.data_exporter.export_data(
                data=expenses_result['expenses'],
                filename=filename,
                format=output_format,
                metadata={
                    'workspace_id': workspace_id,
                    'export_type': 'expenses',
                    'total_expenses': expenses_result['total_count'],
                    'filters_applied': expenses_result.get('filters_applied', {}),
                    'exported_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            self.logger.info(f"Exported {expenses_result['total_count']} expenses to {export_result.get('filepath')}")
            return export_result
            
        except Exception as e:
            self.logger.error(f"Error exporting expenses: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _format_expense_data(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format expense data for Clockify API
        
        Args:
            expense_data: Raw expense data
            
        Returns:
            Formatted expense data for API submission
        """
        formatted = {}
        
        # Required fields
        if 'amount' in expense_data:
            # Ensure amount is formatted correctly (Clockify expects amount in cents)
            amount = expense_data['amount']
            if isinstance(amount, (int, float)):
                formatted['amount'] = int(amount * 100) if isinstance(amount, float) else amount
            else:
                formatted['amount'] = amount
                
        if 'description' in expense_data:
            formatted['description'] = str(expense_data['description'])
        
        # Optional fields
        optional_fields = [
            'projectId', 'taskId', 'tagIds', 'billable', 'invoiced',
            'customFields', 'category', 'receipt', 'date', 'currency', 'userEmail'
        ]
        
        for field in optional_fields:
            if field in expense_data:
                formatted[field] = expense_data[field]
        
        # Format date if provided
        if 'date' in expense_data and expense_data['date']:
            if isinstance(expense_data['date'], str):
                formatted['date'] = expense_data['date']
            elif isinstance(expense_data['date'], datetime):
                formatted['date'] = expense_data['date'].isoformat()
        
        return formatted

    def get_expense_categories(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get available expense categories for a workspace
        
        Args:
            workspace_id: Clockify workspace ID
            
        Returns:
            Dict containing expense categories
        """
        try:
            self.logger.info(f"Retrieving expense categories for workspace {workspace_id}")
            
            endpoint = f"/workspaces/{workspace_id}/expenses/categories"
            response = self.api_client.get(endpoint)
            
            # Check if response contains an error
            if self.api_client.is_error_response(response):
                error_msg = self.api_client.get_error_message(response)
                self.logger.warning(f"Could not retrieve expense categories: {error_msg}")
                return {
                    'categories': [],
                    'total_count': 0,
                    'workspace_id': workspace_id,
                    'success': False,
                    'error': error_msg
                }
            else:
                # Successful response - Clockify returns categories in 'categories' field
                categories = response.get('categories', []) if response else []
                
                result = {
                    'categories': categories,
                    'total_count': len(categories),
                    'workspace_id': workspace_id,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
                
                self.logger.info(f"Retrieved {len(categories)} expense categories")
                return result
                
        except Exception as e:
            self.logger.error(f"Error retrieving expense categories: {str(e)}")
            return {
                'categories': [],
                'total_count': 0,
                'workspace_id': workspace_id,
                'success': False,
                'error': str(e)
            }

    def get_expense_summary(self, workspace_id: str, **filter_kwargs) -> Dict[str, Any]:
        """
        Get expense summary statistics
        
        Args:
            workspace_id: Clockify workspace ID
            **filter_kwargs: Additional filters for expense analysis
            
        Returns:
            Dict containing expense summary data
        """
        try:
            self.logger.info(f"Generating expense summary for workspace {workspace_id}")
            
            # Get all expenses
            expenses_result = self.get_all_expenses(workspace_id, **filter_kwargs)
            
            if not expenses_result.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to retrieve expenses: {expenses_result.get('error')}"
                }
            
            expenses = expenses_result['expenses']
            
            # Calculate summary statistics
            total_amount = 0
            billable_amount = 0
            non_billable_amount = 0
            category_breakdown = {}
            project_breakdown = {}
            
            for expense in expenses:
                amount = expense.get('amount', 0)
                if isinstance(amount, (int, float)):
                    total_amount += amount
                    
                    if expense.get('billable', False):
                        billable_amount += amount
                    else:
                        non_billable_amount += amount
                
                # Category breakdown
                category = expense.get('category', 'Uncategorized')
                category_breakdown[category] = category_breakdown.get(category, 0) + amount
                
                # Project breakdown
                project_id = expense.get('projectId', 'No Project')
                project_breakdown[project_id] = project_breakdown.get(project_id, 0) + amount
            
            summary = {
                'workspace_id': workspace_id,
                'total_expenses': len(expenses),
                'total_amount': total_amount,
                'billable_amount': billable_amount,
                'non_billable_amount': non_billable_amount,
                'category_breakdown': category_breakdown,
                'project_breakdown': project_breakdown,
                'filters_applied': expenses_result.get('filters_applied', {}),
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'success': True
            }
            
            self.logger.info(f"Generated expense summary: {len(expenses)} expenses, total: {total_amount}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating expense summary: {str(e)}")
            return {
                'workspace_id': workspace_id,
                'success': False,
                'error': str(e)
            } 