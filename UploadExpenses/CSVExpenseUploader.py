"""
CSVExpenseUploader - CSV-based expense upload for Clockify

This module provides comprehensive CSV upload functionality for expenses including:
- CSV file parsing and validation
- Data mapping and transformation with name-to-ID resolution
- Project name to ID resolution
- Task name to ID resolution  
- Category name to ID resolution
- Schema validation and error handling
- Bulk upload with progress tracking
- Detailed reporting and export capabilities

Supported CSV Format:
Required columns: amount, description OR amount, project (name), task (name), category (name)
Optional columns: date, project_id, project_name, category, billable, tags, currency, receipt, task_id

Author: Auto-generated for Clockify Expense CSV Upload
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from decimal import Decimal, InvalidOperation

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.api_client import APIClient
from Utils.logging import Logger
from Utils.export_data import DataExporter
from Utils.file_utils import FileUtils
from Expenses.ExpenseManager import ExpenseManager
from Projects.ProjectManager import ProjectManager
from Tasks.Tasks import TaskManager


class CSVExpenseUploader:
    """
    CSV-based expense upload manager for Clockify
    
    Provides comprehensive CSV upload functionality including:
    - File parsing and validation
    - Data transformation and mapping with name-to-ID resolution
    - Project, Task, and Category name resolution
    - Bulk upload with error handling
    - Progress tracking and reporting
    """
    
    # CSV column mappings
    REQUIRED_COLUMNS = ['amount']  # Either description OR project+task+category
    ALTERNATIVE_REQUIRED = [
        ['description'], 
        ['project', 'task', 'category']  # For the new format
    ]
    OPTIONAL_COLUMNS = [
        'date', 'project_id', 'project_name', 'category', 
        'billable', 'tags', 'currency', 'receipt', 'task_id', 'description',
        'user_email'  # User email field
    ]
    
    # Data type mappings
    BOOLEAN_COLUMNS = ['billable']
    NUMERIC_COLUMNS = ['amount']
    DATE_COLUMNS = ['date']
    
    def __init__(self, logger: Logger = None):
        """
        Initialize CSVExpenseUploader
        
        Args:
            logger: Logger instance for tracking operations
        """
        self.logger = logger or Logger("CSVExpenseUploader", console_output=True)
        self.api_client = APIClient(logger=self.logger)
        self.expense_manager = ExpenseManager(logger=self.logger)
        self.project_manager = ProjectManager(logger=self.logger)
        self.task_manager = TaskManager(logger=self.logger)
        self.data_exporter = DataExporter(logger=self.logger)
        self.file_utils = FileUtils(logger=self.logger)
        
        # Upload tracking
        self._upload_stats = {}
        
        # Caching for name-to-ID resolution
        self._project_cache = {}
        self._task_cache = {}
        self._category_cache = {}
        self._user_cache = {}
        self._project_name_to_id = {}
        self._task_name_to_id = {}
        self._category_name_to_id = {}
        self._user_email_to_id = {}
        
        self.logger.info("CSVExpenseUploader initialized successfully")

    def _validate_user_in_workspace(self, user_email: str, workspace_id: str) -> Dict[str, Any]:
        """
        Validate that a user exists in the specified workspace
        
        Args:
            user_email: Email of the user to validate
            workspace_id: Clockify workspace ID
            
        Returns:
            Dict containing validation result and suggestions
        """
        try:
            self.logger.info(f"Validating user {user_email} exists in workspace {workspace_id}")
            
            # Get all users in workspace
            from Users.Users import UserManager
            user_manager = UserManager(logger=self.logger)
            users_result = user_manager.get_all_users()
            
            if self.api_client.is_error_response(users_result):
                return {
                    'valid': False,
                    'error': f"Failed to fetch users from workspace: {self.api_client.get_error_message(users_result)}"
                }
            
            users = users_result.get('items', [])
            if not users:
                return {
                    'valid': False,
                    'error': "No users found in workspace"
                }
            
            # Check if the email exists (case-insensitive)
            user_email_lower = user_email.lower().strip()
            existing_emails = [user.get('email', '').lower().strip() for user in users if user.get('email')]
            
            if user_email_lower not in existing_emails:
                # Suggest similar emails
                suggested_users = []
                for user in users[:10]:  # Limit to first 10 users
                    if user.get('email') and user.get('name'):
                        suggested_users.append({
                            'email': user['email'],
                            'name': user['name'],
                            'id': user['id']
                        })
                
                return {
                    'valid': False,
                    'error': f"User '{user_email}' not found in workspace. Please check the email address or use one of the suggested users below.",
                    'suggested_users': suggested_users
                }
            
            self.logger.info(f"User {user_email} validated successfully")
            return {
                'valid': True,
                'user_email': user_email
            }
            
        except Exception as e:
            self.logger.error(f"Error validating user {user_email}: {str(e)}")
            return {
                'valid': False,
                'error': f"Error validating user: {str(e)}"
            }

    def upload_from_csv(self, csv_file_path: str, workspace_id: str, 
                       dry_run: bool = False, chunk_size: int = 50,
                       column_mapping: Dict[str, str] = None,
                       default_user_email: str = None) -> Dict[str, Any]:
        """
        Upload expenses from a CSV file
        
        Args:
            csv_file_path: Path to the CSV file
            workspace_id: Clockify workspace ID
            dry_run: If True, validate only without uploading
            chunk_size: Number of expenses to upload in each batch
            column_mapping: Custom column name mappings
            default_user_email: Default user email to assign to expenses if not specified in CSV
            
        Returns:
            Dict containing upload results and statistics
        """
        try:
            self.logger.info(f"Starting CSV expense upload from {csv_file_path}")
            self.logger.info(f"Workspace: {workspace_id}, Dry run: {dry_run}")
            
            # Step 1: Validate file exists
            if not self.file_utils.file_exists(csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
            
            # Step 2: Validate user exists in workspace if specified
            if default_user_email:
                user_validation = self._validate_user_in_workspace(default_user_email, workspace_id)
                if not user_validation['valid']:
                    return {
                        'success': False,
                        'error': user_validation['error'],
                        'available_users': user_validation.get('suggested_users', []),
                        'workspace_id': workspace_id,
                        'processed_at': datetime.now(timezone.utc).isoformat()
                    }
                    
            # Step 3: Pre-load caches for name resolution
            self._load_name_resolution_caches(workspace_id)
            
            # Step 3: Parse CSV file
            parsed_data = self._parse_csv_file(csv_file_path, column_mapping)
            if not parsed_data['success']:
                return parsed_data
            
            raw_expenses = parsed_data['data']
            self.logger.info(f"Parsed {len(raw_expenses)} expense records from CSV")
            
            # Step 4: Validate and transform data
            validation_result = self._validate_and_transform_data(raw_expenses, workspace_id, default_user_email)
            if not validation_result['success']:
                return validation_result
            
            valid_expenses = validation_result['valid_expenses']
            validation_errors = validation_result['validation_errors']
            
            self.logger.info(f"Validation completed: {len(valid_expenses)} valid, {len(validation_errors)} errors")
            
            # Step 5: If dry run, return validation results
            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'total_records': len(raw_expenses),
                    'valid_records': len(valid_expenses),
                    'invalid_records': len(validation_errors),
                    'validation_errors': validation_errors,
                    'sample_valid_expense': valid_expenses[0] if valid_expenses else None,
                    'workspace_id': workspace_id,
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }
            
            # Step 6: Upload expenses in chunks
            upload_result = self._upload_expenses_in_chunks(
                workspace_id, valid_expenses, chunk_size
            )
            
            # Step 7: Generate comprehensive results
            final_result = {
                'success': upload_result.get('success', False),
                'total_records_in_csv': len(raw_expenses),
                'valid_records': len(valid_expenses),
                'invalid_records': len(validation_errors),
                'validation_errors': validation_errors,
                'total_created': upload_result.get('total_created', 0),
                'total_failed': upload_result.get('total_failed', 0),
                'created_expenses': upload_result.get('created_expenses', []),
                'failed_expenses': upload_result.get('failed_expenses', []),
                'chunk_results': upload_result.get('chunk_results', []),
                'workspace_id': workspace_id,
                'csv_file_path': csv_file_path,
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'upload_summary': {
                    'total_processed': len(valid_expenses),
                    'successful_uploads': upload_result.get('total_created', 0),
                    'failed_uploads': upload_result.get('total_failed', 0),
                    'success_rate': (upload_result.get('total_created', 0) / len(valid_expenses) * 100) if valid_expenses else 0
                }
            }
            
            # Export results (optional)
            try:
                self._export_upload_results(final_result)
            except Exception as e:
                self.logger.warning(f"Failed to export validation results: {e}")
            
            self.logger.info(f"CSV validation completed: {len(valid_expenses)} valid expenses (upload not supported)")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error in CSV expense upload: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'workspace_id': workspace_id,
                'csv_file_path': csv_file_path,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }

    def _load_name_resolution_caches(self, workspace_id: str) -> None:
        """
        Pre-load caches for name-to-ID resolution
        
        Args:
            workspace_id: Clockify workspace ID
        """
        try:
            self.logger.info("Loading name resolution caches...")
            
            # Load users cache
            self.logger.info("Loading users cache...")
            from Users.Users import UserManager
            user_manager = UserManager(logger=self.logger)
            users_result = user_manager.get_all_users()
            if users_result.get('items'):
                users = users_result.get('items', [])
                self._user_cache[workspace_id] = {
                    user['id']: user for user in users
                }
                self._user_email_to_id[workspace_id] = {
                    user['email'].lower().strip(): user['id'] 
                    for user in users if user.get('email')
                }
                self.logger.info(f"Cached {len(users)} users")
            else:
                self.logger.warning("Could not load users for caching")
                self._user_cache[workspace_id] = {}
                self._user_email_to_id[workspace_id] = {}
            
            # Load projects cache
            self.logger.info("Loading projects cache...")
            projects_result = self.project_manager.get_all_projects()
            if projects_result.get('items'):
                projects = projects_result.get('items', [])
                self._project_cache[workspace_id] = {
                    proj['id']: proj for proj in projects
                }
                self._project_name_to_id[workspace_id] = {
                    proj['name'].lower().strip(): proj['id'] for proj in projects
                }
                self.logger.info(f"Cached {len(projects)} projects")
            else:
                self.logger.warning("Could not load projects for caching")
                self._project_cache[workspace_id] = {}
                self._project_name_to_id[workspace_id] = {}
            
            # Load tasks cache - use lazy loading approach to avoid timeout
            self.logger.info("Loading tasks cache...")
            all_tasks = {}
            task_name_to_data = {}
            
            # Get list of projects
            projects = list(self._project_cache.get(workspace_id, {}).values())
            total_projects = len(projects)
            self.logger.info(f"Found {total_projects} projects. Using lazy task loading to prevent timeout...")
            
            # Initialize empty task caches (will be populated on-demand)
            self._task_cache[workspace_id] = all_tasks
            self._task_name_to_id[workspace_id] = task_name_to_data
            self.logger.info(f"Initialized task cache for lazy loading from {total_projects} projects")
            
            # Load categories cache
            self.logger.info("Loading categories cache...")
            categories_result = self.expense_manager.get_expense_categories(workspace_id)
            if categories_result.get('success') and categories_result.get('categories'):
                categories = categories_result.get('categories', [])
                self._category_cache[workspace_id] = {
                    cat.get('id'): cat for cat in categories if cat.get('id')
                }
                self._category_name_to_id[workspace_id] = {
                    cat.get('name', '').lower().strip(): cat.get('id') 
                    for cat in categories if cat.get('name') and cat.get('id')
                }
                self.logger.info(f"Cached {len(categories)} expense categories")
            else:
                self.logger.warning("Could not load expense categories for caching")
                self._category_cache[workspace_id] = {}
                self._category_name_to_id[workspace_id] = {}
            
            self.logger.info("Name resolution caches loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading name resolution caches: {str(e)}")
            # Initialize empty caches to prevent errors
            for cache_type in ['_project_cache', '_task_cache', '_category_cache', '_user_cache',
                             '_project_name_to_id', '_task_name_to_id', '_category_name_to_id', '_user_email_to_id']:
                if not hasattr(self, cache_type):
                    setattr(self, cache_type, {})
                if workspace_id not in getattr(self, cache_type):
                    getattr(self, cache_type)[workspace_id] = {}

    def _parse_csv_file(self, csv_file_path: str, column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Parse CSV file and extract expense data
        
        Args:
            csv_file_path: Path to CSV file
            column_mapping: Custom column mappings
            
        Returns:
            Dict containing parsed data or error information
        """
        try:
            self.logger.info(f"Parsing CSV file: {csv_file_path}")
            
            # Read CSV with pandas for better error handling
            try:
                df = pd.read_csv(csv_file_path)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to read CSV file: {str(e)}"
                }
            
            # Check if file is empty
            if df.empty:
                return {
                    'success': False,
                    'error': "CSV file is empty"
                }
            
            # Handle duplicate column names (like duplicate "Date" columns)
            original_columns = list(df.columns)
            seen_columns = {}
            new_columns = []
            
            for col in original_columns:
                if col in seen_columns:
                    seen_columns[col] += 1
                    new_col = f"{col}_{seen_columns[col]}"
                    new_columns.append(new_col)
                    self.logger.info(f"Renamed duplicate column '{col}' to '{new_col}'")
                else:
                    seen_columns[col] = 0
                    new_columns.append(col)
            
            df.columns = new_columns
            
            # Apply column mapping if provided
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # Normalize column names (lowercase, replace spaces with underscores)
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
            
            # Special handling for the format shown in the example CSV
            # Map columns to standardized names
            column_mappings = {
                'project': 'project_name',
                'task': 'task_name', 
                'category': 'category_name'
            }
            
            df = df.rename(columns=column_mappings)
            
            # Check for required columns - either traditional or new format
            has_traditional_format = all(col in df.columns for col in ['amount', 'description'])
            has_new_format = all(col in df.columns for col in ['amount', 'project_name', 'task_name', 'category_name'])
            
            if not has_traditional_format and not has_new_format:
                return {
                    'success': False,
                    'error': f"CSV must have either [amount, description] OR [amount, project_name, task_name, category_name]",
                    'available_columns': list(df.columns),
                    'required_traditional': ['amount', 'description'],
                    'required_new_format': ['amount', 'project_name', 'task_name', 'category_name']
                }
            
            # Convert DataFrame to list of dictionaries
            expenses_data = df.to_dict('records')
            
            # Clean up NaN values
            for expense in expenses_data:
                for key, value in expense.items():
                    if pd.isna(value):
                        expense[key] = None
            
            self.logger.info(f"Successfully parsed {len(expenses_data)} records from CSV")
            return {
                'success': True,
                'data': expenses_data,
                'total_records': len(expenses_data),
                'columns_found': list(df.columns),
                'format_detected': 'new_format' if has_new_format else 'traditional'
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing CSV file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_and_transform_data(self, raw_expenses: List[Dict], workspace_id: str, 
                                   default_user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate and transform expense data
        
        Args:
            raw_expenses: Raw expense data from CSV
            workspace_id: Clockify workspace ID
            default_user_email: Default user email to assign to expenses if not specified in CSV
            
        Returns:
            Dict containing validation results
        """
        try:
            self.logger.info(f"Validating and transforming {len(raw_expenses)} expense records")
            
            valid_expenses = []
            validation_errors = []
            
            for i, raw_expense in enumerate(raw_expenses):
                try:
                    # Validate and transform individual expense
                    transformed_expense = self._validate_single_expense(
                        raw_expense, i, workspace_id, default_user_email
                    )
                    
                    if transformed_expense['valid']:
                        valid_expenses.append(transformed_expense['expense_data'])
                    else:
                        validation_errors.append({
                            'row_index': i + 1,  # 1-based index for users
                            'raw_data': raw_expense,
                            'errors': transformed_expense['errors']
                        })
                        
                except Exception as e:
                    validation_errors.append({
                        'row_index': i + 1,
                        'raw_data': raw_expense,
                        'errors': [f"Validation exception: {str(e)}"]
                    })
            
            result = {
                'success': True,
                'valid_expenses': valid_expenses,
                'validation_errors': validation_errors,
                'total_processed': len(raw_expenses),
                'total_valid': len(valid_expenses),
                'total_invalid': len(validation_errors)
            }
            
            self.logger.info(f"Validation completed: {len(valid_expenses)} valid, {len(validation_errors)} invalid")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in data validation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_single_expense(self, raw_expense: Dict, row_index: int, 
                                workspace_id: str, default_user_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate and transform a single expense record
        
        Args:
            raw_expense: Raw expense data
            row_index: Row index for error reporting
            workspace_id: Clockify workspace ID
            default_user_email: Default user email to assign to expenses if not specified in CSV
            
        Returns:
            Dict containing validation result
        """
        errors = []
        expense_data = {}
        
        try:
            # Validate required fields
            
            # Amount validation
            amount_raw = raw_expense.get('amount')
            if amount_raw is None or amount_raw == '':
                errors.append("Amount is required")
            else:
                try:
                    if isinstance(amount_raw, str):
                        # Clean amount string (remove currency symbols, commas)
                        amount_clean = amount_raw.replace('$', '').replace(',', '').strip()
                        amount = float(amount_clean)
                    else:
                        amount = float(amount_raw)
                    
                    if amount < 0:  # Allow 0 amounts as per the example CSV
                        errors.append("Amount cannot be negative")
                    else:
                        expense_data['amount'] = amount
                        
                except (ValueError, InvalidOperation):
                    errors.append(f"Invalid amount format: {amount_raw}")
            
            # Description validation - required unless we have project+task+category
            description = raw_expense.get('description')
            project_name = raw_expense.get('project_name')
            task_name = raw_expense.get('task_name')
            category_name = raw_expense.get('category_name')
            
            # Check if we have the new format (project+task+category)
            has_new_format_data = all([project_name, task_name, category_name])
            
            if not description and not has_new_format_data:
                errors.append("Description is required when project/task/category are not provided")
            elif description:
                expense_data['description'] = str(description).strip()
            elif has_new_format_data:
                # Generate description from project+task+category
                expense_data['description'] = f"{task_name} - {category_name} ({project_name})"
            
            # Project name resolution - REQUIRED by Clockify API
            if project_name and project_name.strip():
                project_id = self._resolve_project_name_to_id(workspace_id, project_name.strip())
                if project_id:
                    expense_data['projectId'] = project_id
                else:
                    errors.append(f"Project name not found: {project_name}")
            else:
                errors.append("Project name is required - must match a Clockify project name")
            
            # Task name resolution
            if task_name and task_name.strip() and project_name and project_name.strip():
                task_id = self._resolve_task_name_to_id(workspace_id, task_name.strip(), project_name.strip())
                if task_id:
                    expense_data['taskId'] = task_id
                else:
                    errors.append(f"Task name '{task_name}' not found in project '{project_name}'")
            
            # Category name resolution - REQUIRED by Clockify API
            if category_name and category_name.strip():
                category_id = self._resolve_category_name_to_id(workspace_id, category_name.strip())
                if category_id:
                    expense_data['categoryId'] = category_id
                else:
                    errors.append(f"Category name not found in Clockify categories: {category_name}")
            else:
                errors.append("Category name is required - must match a Clockify expense category")
            
            # Optional field validation and transformation
            
            # Date validation - handle the first date column
            date_raw = raw_expense.get('date')
            if date_raw and date_raw != '':
                try:
                    if isinstance(date_raw, str):
                        # Try multiple date formats
                        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                        parsed_date = None
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date_raw, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if parsed_date:
                            expense_data['date'] = parsed_date.isoformat() + 'Z'
                        else:
                            errors.append(f"Invalid date format: {date_raw}")
                    else:
                        # Assume it's already a datetime
                        date_str = date_raw.isoformat() if hasattr(date_raw, 'isoformat') else str(date_raw)
                        if not date_str.endswith('Z'):
                            date_str += 'Z'
                        expense_data['date'] = date_str
                except Exception as e:
                    errors.append(f"Date parsing error: {str(e)}")
            
            # Handle existing project_id if provided
            project_id = raw_expense.get('project_id')
            if project_id and project_id != '' and 'projectId' not in expense_data:
                # Validate project_id exists
                if workspace_id in self._project_cache and project_id in self._project_cache[workspace_id]:
                    expense_data['projectId'] = project_id
                else:
                    errors.append(f"Project ID not found: {project_id}")
            
            # Category (as free text if no category_name was provided)
            category = raw_expense.get('category')
            if category and category != '' and 'categoryId' not in expense_data and 'category' not in expense_data:
                expense_data['category'] = str(category).strip()
            
            # Billable
            billable_raw = raw_expense.get('billable')
            if billable_raw is not None and billable_raw != '':
                if isinstance(billable_raw, bool):
                    expense_data['billable'] = billable_raw
                elif isinstance(billable_raw, str):
                    billable_lower = billable_raw.lower().strip()
                    if billable_lower in ['true', '1', 'yes', 'y', 'billable']:
                        expense_data['billable'] = True
                    elif billable_lower in ['false', '0', 'no', 'n', 'non-billable']:
                        expense_data['billable'] = False
                    else:
                        errors.append(f"Invalid billable value: {billable_raw}")
                else:
                    expense_data['billable'] = bool(billable_raw)
            
            # Currency
            currency = raw_expense.get('currency')
            if currency and currency != '':
                expense_data['currency'] = str(currency).strip().upper()
            
            # Tags (assuming comma-separated)
            tags_raw = raw_expense.get('tags')
            if tags_raw and tags_raw != '':
                if isinstance(tags_raw, str):
                    tags = [tag.strip() for tag in tags_raw.split(',') if tag.strip()]
                    if tags:
                        expense_data['tagIds'] = tags  # Note: This might need tag ID resolution
                else:
                    expense_data['tagIds'] = tags_raw
            
            # Task ID (if provided directly)
            task_id = raw_expense.get('task_id')
            if task_id and task_id != '' and 'taskId' not in expense_data:
                expense_data['taskId'] = str(task_id).strip()
            
            # Receipt
            receipt = raw_expense.get('receipt')
            if receipt and receipt != '':
                expense_data['receipt'] = str(receipt).strip()
            
            # User email/ID resolution - required by Clockify API
            user_email = raw_expense.get('user_email')
            if user_email and user_email != '':
                user_id = self._resolve_user_email_to_id(workspace_id, user_email.strip())
                if user_id:
                    expense_data['userId'] = user_id
                    expense_data['userEmail'] = str(user_email).strip()
                else:
                    errors.append(f"User email not found: {user_email}")
            elif default_user_email:
                user_id = self._resolve_user_email_to_id(workspace_id, default_user_email)
                if user_id:
                    expense_data['userId'] = user_id
                    expense_data['userEmail'] = default_user_email
                else:
                    errors.append(f"Default user email not found: {default_user_email}")
            else:
                errors.append("User email is required - provide in CSV or as default_user_email parameter")
            
            # Set ISO date format if date exists
            if 'date' in expense_data:
                # Ensure date is in ISO format required by Clockify API
                try:
                    if isinstance(expense_data['date'], str):
                        # Try to parse and reformat to ensure ISO format
                        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                            try:
                                parsed_date = datetime.strptime(expense_data['date'], fmt)
                                expense_data['date'] = parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                                break
                            except ValueError:
                                continue
                        else:
                            # If no format worked, try to append time if missing
                            if 'T' not in expense_data['date']:
                                expense_data['date'] = expense_data['date'] + 'T00:00:00Z'
                except Exception as e:
                    errors.append(f"Date formatting error: {str(e)}")
            else:
                # Use current date if not provided
                expense_data['date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Ensure required notes field for API
            if 'description' in expense_data:
                expense_data['notes'] = expense_data['description']  # API uses 'notes' field
            
            # Final validation: Check all API required fields are present
            api_required_fields = ['amount', 'categoryId', 'date', 'projectId', 'userId']
            for field in api_required_fields:
                if field not in expense_data:
                    errors.append(f"Missing required field for Clockify API: {field}")
            
            return {
                'valid': len(errors) == 0,
                'expense_data': expense_data,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'valid': False,
                'expense_data': {},
                'errors': [f"Validation error: {str(e)}"]
            }

    def _resolve_project_name_to_id(self, workspace_id: str, project_name: str) -> Optional[str]:
        """
        Resolve project name to project ID
        
        Args:
            workspace_id: Clockify workspace ID
            project_name: Project name to resolve
            
        Returns:
            Project ID if found, None otherwise
        """
        try:
            project_name_lower = project_name.lower().strip()
            name_to_id_map = self._project_name_to_id.get(workspace_id, {})
            return name_to_id_map.get(project_name_lower)
        except Exception as e:
            self.logger.warning(f"Error resolving project name '{project_name}': {str(e)}")
            return None

    def _resolve_task_name_to_id(self, workspace_id: str, task_name: str, project_name: str) -> Optional[str]:
        """
        Resolve task name to task ID within a specific project
        
        Args:
            workspace_id: Clockify workspace ID
            task_name: Task name to resolve
            project_name: Project name for context
            
        Returns:
            Task ID if found, None otherwise
        """
        try:
            task_name_lower = task_name.lower().strip()
            project_name_lower = project_name.lower().strip()
            
            task_name_to_data_map = self._task_name_to_id.get(workspace_id, {})
            
            # First try with project-specific key (most accurate) from existing cache
            composite_key = f"{project_name_lower}::{task_name_lower}"
            task_data = task_name_to_data_map.get(composite_key)
            
            if task_data:
                return task_data.get('id')
            
            # Fallback: try task name only from existing cache
            task_data = task_name_to_data_map.get(task_name_lower)
            if task_data:
                # Verify it's in the right project
                if task_data.get('project_name', '').lower().strip() == project_name_lower:
                    return task_data.get('id')
                else:
                    self.logger.warning(f"Task '{task_name}' found but in different project: {task_data.get('project_name')}")
            
            # Lazy loading: if not found in cache, try to load tasks for this specific project
            project_id = self._resolve_project_name_to_id(workspace_id, project_name)
            if project_id:
                self.logger.info(f"Lazy loading tasks for project '{project_name}' to resolve task '{task_name}'")
                try:
                    tasks_result = self.task_manager.get_tasks_by_project(project_id)
                    project_tasks = tasks_result.get('items', [])
                    
                    # Add these tasks to the cache
                    for task in project_tasks:
                        task_id = task.get('id')
                        task_name_cached = task.get('name', '').lower().strip()
                        
                        # Store task data with project context
                        task_data = {
                            'id': task_id,
                            'name': task.get('name', ''),
                            'project_id': project_id,
                            'project_name': project_name
                        }
                        
                        self._task_cache[workspace_id][task_id] = task_data
                        
                        # Create mapping for name resolution
                        composite_key = f"{project_name_lower}::{task_name_cached}"
                        self._task_name_to_id[workspace_id][composite_key] = task_data
                        
                        # Also store by task name only (may not be unique)
                        if task_name_cached not in self._task_name_to_id[workspace_id]:
                            self._task_name_to_id[workspace_id][task_name_cached] = task_data
                    
                    # Now try to resolve again with the newly cached data
                    composite_key = f"{project_name_lower}::{task_name_lower}"
                    task_data = self._task_name_to_id[workspace_id].get(composite_key)
                    if task_data:
                        self.logger.info(f"Task '{task_name}' found via lazy loading")
                        return task_data.get('id')
                    
                except Exception as e:
                    self.logger.warning(f"Failed to lazy load tasks for project {project_id}: {str(e)}")
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error resolving task name '{task_name}' in project '{project_name}': {str(e)}")
            return None

    def _resolve_category_name_to_id(self, workspace_id: str, category_name: str) -> Optional[str]:
        """
        Resolve category name to category ID
        
        Args:
            workspace_id: Clockify workspace ID
            category_name: Category name to resolve
            
        Returns:
            Category ID if found, None otherwise
        """
        try:
            category_name_lower = category_name.lower().strip()
            name_to_id_map = self._category_name_to_id.get(workspace_id, {})
            return name_to_id_map.get(category_name_lower)
        except Exception as e:
            self.logger.warning(f"Error resolving category name '{category_name}': {str(e)}")
            return None

    def _resolve_user_email_to_id(self, workspace_id: str, user_email: str) -> Optional[str]:
        """
        Resolve user email to user ID
        
        Args:
            workspace_id: Clockify workspace ID
            user_email: User email to resolve
            
        Returns:
            User ID if found, None otherwise
        """
        try:
            user_email_lower = user_email.lower().strip()
            email_to_id_map = self._user_email_to_id.get(workspace_id, {})
            return email_to_id_map.get(user_email_lower)
        except Exception as e:
            self.logger.warning(f"Error resolving user email '{user_email}': {str(e)}")
            return None

    def _upload_expenses_in_chunks(self, workspace_id: str, valid_expenses: List[Dict], 
                                  chunk_size: int) -> Dict[str, Any]:
        """
        Upload expenses in chunks for better performance and error handling
        
        Args:
            workspace_id: Clockify workspace ID
            valid_expenses: List of validated expense data
            chunk_size: Number of expenses per chunk
            
        Returns:
            Dict containing upload results
        """
        try:
            self.logger.info(f"Uploading {len(valid_expenses)} expenses in chunks of {chunk_size}")
            
            total_created = 0
            total_failed = 0
            all_created_expenses = []
            all_failed_expenses = []
            chunk_results = []
            
            # Process expenses in chunks
            for i in range(0, len(valid_expenses), chunk_size):
                chunk = valid_expenses[i:i + chunk_size]
                chunk_number = (i // chunk_size) + 1
                total_chunks = ((len(valid_expenses) - 1) // chunk_size) + 1
                
                self.logger.info(f"Processing chunk {chunk_number}/{total_chunks} ({len(chunk)} expenses)")
                
                try:
                    # Use bulk create from ExpenseManager
                    chunk_result = self.expense_manager.bulk_create_expenses(workspace_id, chunk)
                    
                    chunk_created = chunk_result.get('total_created', 0)
                    chunk_failed = chunk_result.get('total_failed', 0)
                    
                    total_created += chunk_created
                    total_failed += chunk_failed
                    
                    all_created_expenses.extend(chunk_result.get('created_expenses', []))
                    all_failed_expenses.extend(chunk_result.get('failed_expenses', []))
                    
                    chunk_results.append({
                        'chunk_number': chunk_number,
                        'chunk_size': len(chunk),
                        'created': chunk_created,
                        'failed': chunk_failed,
                        'success': chunk_result.get('success', False)
                    })
                    
                    self.logger.info(f"Chunk {chunk_number} completed: {chunk_created} created, {chunk_failed} failed")
                    
                except Exception as e:
                    self.logger.error(f"Error in chunk {chunk_number}: {str(e)}")
                    total_failed += len(chunk)
                    chunk_results.append({
                        'chunk_number': chunk_number,
                        'chunk_size': len(chunk),
                        'created': 0,
                        'failed': len(chunk),
                        'success': False,
                        'error': str(e)
                    })
            
            upload_result = {
                'success': total_created > 0,
                'total_attempted': len(valid_expenses),
                'total_created': total_created,
                'total_failed': total_failed,
                'created_expenses': all_created_expenses,
                'failed_expenses': all_failed_expenses,
                'chunk_results': chunk_results,
                'upload_completed_at': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(f"Upload completed: {total_created}/{len(valid_expenses)} expenses created")
            return upload_result
            
        except Exception as e:
            self.logger.error(f"Error in chunked upload: {str(e)}")
            return {
                'success': False,
                'total_attempted': len(valid_expenses),
                'total_created': 0,
                'total_failed': len(valid_expenses),
                'error': str(e)
            }

    def _export_upload_results(self, upload_result: Dict[str, Any]) -> None:
        """
        Export upload results to file for review
        
        Args:
            upload_result: Complete upload result data
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_id = upload_result.get('workspace_id', 'unknown')
            
            # Export main results
            filename = f"expense_upload_results_{workspace_id}_{timestamp}"
            
            export_result = self.data_exporter.export_data(
                data=upload_result,
                filename=filename,
                format="json",
                metadata={
                    'export_type': 'expense_upload_results',
                    'workspace_id': workspace_id,
                    'exported_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            self.logger.info(f"Upload results exported to: {export_result.get('filepath')}")
            
            # Also export validation errors if any
            validation_errors = upload_result.get('validation_errors', [])
            if validation_errors:
                errors_filename = f"expense_upload_validation_errors_{workspace_id}_{timestamp}"
                self.data_exporter.export_data(
                    data=validation_errors,
                    filename=errors_filename,
                    format="csv",
                    metadata={
                        'export_type': 'validation_errors',
                        'workspace_id': workspace_id,
                        'total_errors': len(validation_errors)
                    }
                )
                self.logger.info(f"Validation errors exported to CSV for review")
            
        except Exception as e:
            self.logger.warning(f"Failed to export upload results: {str(e)}")

    def generate_csv_template(self, output_path: str = None, template_format: str = "new") -> Dict[str, Any]:
        """
        Generate a CSV template file for expense uploads
        
        Args:
            output_path: Optional custom output path
            template_format: "new" for project/task/category format, "traditional" for description format
            
        Returns:
            Dict containing template generation result
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"expense_upload_template_{template_format}_{timestamp}.csv"
            
            if template_format == "new":
                # Template for the new format with project/task/category names
                template_data = [
                    {
                        'date': '6/1/2025',
                        'project': 'Repare.Schonhoft.PanCan.PBMC',
                        'task': 'NGS Reagents and Lab Operations Cost',
                        'amount': 1345.85,
                        'category': 'NGS Reagents',
                        'user_email': 'john.doe@company.com'
                    },
                    {
                        'date': '6/1/2025',
                        'project': 'LigoChem.Slocum.PanCan.TROP2',
                        'task': 'IMG Reagents and Lab Operations Cost',
                        'amount': 934.20,
                        'category': 'IMG Reagents'
                    }
                ]
            else:
                # Traditional template format
                template_data = [
                    {
                        'amount': 25.50,
                        'description': 'Business lunch with client',
                        'date': '2024-01-15',
                        'project_id': '',
                        'project_name': 'Project Alpha',
                        'category': 'Meals',
                        'billable': 'true',
                        'currency': 'USD',
                        'tags': 'client,meal',
                        'task_id': '',
                        'receipt': 'receipt_001.pdf'
                    },
                    {
                        'amount': 15.00,
                        'description': 'Taxi to office',
                        'date': '2024-01-16',
                        'project_id': 'abc123',
                        'project_name': '',
                        'category': 'Transportation',
                        'billable': 'false',
                        'currency': 'USD',
                        'tags': 'transportation',
                        'task_id': '',
                        'receipt': ''
                    }
                ]
            
            # Write template CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if template_data:
                    writer = csv.DictWriter(csvfile, fieldnames=template_data[0].keys())
                    writer.writeheader()
                    writer.writerows(template_data)
            
            self.logger.info(f"CSV template ({template_format} format) generated: {output_path}")
            
            return {
                'success': True,
                'template_path': output_path,
                'template_format': template_format,
                'columns_included': list(template_data[0].keys()) if template_data else [],
                'sample_rows': len(template_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating CSV template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 