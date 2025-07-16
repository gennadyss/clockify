"""
CSVExpenseUploader - CSV-based expense upload for Clockify

This module provides comprehensive CSV upload functionality for expenses including:
- CSV file parsing and validation
- Data mapping and transformation
- Schema validation and error handling
- Bulk upload with progress tracking
- Detailed reporting and export capabilities

Supported CSV Format:
Required columns: amount, description
Optional columns: date, project_id, project_name, category, billable, tags, currency, receipt

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


class CSVExpenseUploader:
    """
    CSV-based expense upload manager for Clockify
    
    Provides comprehensive CSV upload functionality including:
    - File parsing and validation
    - Data transformation and mapping
    - Bulk upload with error handling
    - Progress tracking and reporting
    """
    
    # CSV column mappings
    REQUIRED_COLUMNS = ['amount', 'description']
    OPTIONAL_COLUMNS = [
        'date', 'project_id', 'project_name', 'category', 
        'billable', 'tags', 'currency', 'receipt', 'task_id'
    ]
    ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    
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
        self.data_exporter = DataExporter(logger=self.logger)
        self.file_utils = FileUtils(logger=self.logger)
        
        # Upload tracking
        self._upload_stats = {}
        self._project_cache = {}
        
        self.logger.info("CSVExpenseUploader initialized successfully")

    def upload_from_csv(self, csv_file_path: str, workspace_id: str, 
                       dry_run: bool = False, chunk_size: int = 50,
                       column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload expenses from a CSV file
        
        Args:
            csv_file_path: Path to the CSV file
            workspace_id: Clockify workspace ID
            dry_run: If True, validate only without uploading
            chunk_size: Number of expenses to upload in each batch
            column_mapping: Custom column name mappings
            
        Returns:
            Dict containing upload results and statistics
        """
        try:
            self.logger.info(f"Starting CSV expense upload from {csv_file_path}")
            self.logger.info(f"Workspace: {workspace_id}, Dry run: {dry_run}")
            
            # Step 1: Validate file exists
            if not self.file_utils.file_exists(csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
            
            # Step 2: Parse CSV file
            parsed_data = self._parse_csv_file(csv_file_path, column_mapping)
            if not parsed_data['success']:
                return parsed_data
            
            raw_expenses = parsed_data['data']
            self.logger.info(f"Parsed {len(raw_expenses)} expense records from CSV")
            
            # Step 3: Validate and transform data
            validation_result = self._validate_and_transform_data(raw_expenses, workspace_id)
            if not validation_result['success']:
                return validation_result
            
            valid_expenses = validation_result['valid_expenses']
            validation_errors = validation_result['validation_errors']
            
            self.logger.info(f"Validation completed: {len(valid_expenses)} valid, {len(validation_errors)} errors")
            
            # Step 4: If dry run, return validation results
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
            
            # Step 5: Upload expenses in chunks
            upload_result = self._upload_expenses_in_chunks(
                workspace_id, valid_expenses, chunk_size
            )
            
            # Step 6: Generate comprehensive results
            final_result = {
                'success': upload_result['success'],
                'workspace_id': workspace_id,
                'csv_file_path': csv_file_path,
                'total_records_in_csv': len(raw_expenses),
                'valid_records': len(valid_expenses),
                'invalid_records': len(validation_errors),
                'validation_errors': validation_errors,
                'upload_results': upload_result,
                'processed_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Step 7: Export results
            self._export_upload_results(final_result)
            
            self.logger.info(f"CSV upload completed: {upload_result.get('total_created', 0)} expenses created")
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
            
            # Apply column mapping if provided
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # Normalize column names (lowercase, replace spaces with underscores)
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
            
            # Check for required columns
            missing_columns = []
            for col in self.REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f"Missing required columns: {missing_columns}",
                    'available_columns': list(df.columns),
                    'required_columns': self.REQUIRED_COLUMNS
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
                'columns_found': list(df.columns)
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing CSV file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_and_transform_data(self, raw_expenses: List[Dict], workspace_id: str) -> Dict[str, Any]:
        """
        Validate and transform expense data
        
        Args:
            raw_expenses: Raw expense data from CSV
            workspace_id: Clockify workspace ID
            
        Returns:
            Dict containing validation results
        """
        try:
            self.logger.info(f"Validating and transforming {len(raw_expenses)} expense records")
            
            valid_expenses = []
            validation_errors = []
            
            # Cache projects for validation
            projects_result = self.project_manager.get_all_projects(workspace_id)
            if projects_result.get('success'):
                projects = projects_result.get('projects', [])
                self._project_cache[workspace_id] = {
                    proj['id']: proj for proj in projects
                }
                project_name_to_id = {
                    proj['name'].lower(): proj['id'] for proj in projects
                }
            else:
                self.logger.warning("Could not load projects for validation")
                self._project_cache[workspace_id] = {}
                project_name_to_id = {}
            
            for i, raw_expense in enumerate(raw_expenses):
                try:
                    # Validate and transform individual expense
                    transformed_expense = self._validate_single_expense(
                        raw_expense, i, workspace_id, project_name_to_id
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
                                workspace_id: str, project_name_to_id: Dict) -> Dict[str, Any]:
        """
        Validate and transform a single expense record
        
        Args:
            raw_expense: Raw expense data
            row_index: Row index for error reporting
            workspace_id: Clockify workspace ID
            project_name_to_id: Project name to ID mapping
            
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
                    
                    if amount <= 0:
                        errors.append("Amount must be greater than 0")
                    else:
                        expense_data['amount'] = amount
                        
                except (ValueError, InvalidOperation):
                    errors.append(f"Invalid amount format: {amount_raw}")
            
            # Description validation
            description = raw_expense.get('description')
            if not description or description.strip() == '':
                errors.append("Description is required")
            else:
                expense_data['description'] = str(description).strip()
            
            # Optional field validation and transformation
            
            # Date validation
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
                            expense_data['date'] = parsed_date.isoformat()
                        else:
                            errors.append(f"Invalid date format: {date_raw}")
                    else:
                        # Assume it's already a datetime
                        expense_data['date'] = date_raw.isoformat() if hasattr(date_raw, 'isoformat') else str(date_raw)
                except Exception as e:
                    errors.append(f"Date parsing error: {str(e)}")
            
            # Project validation
            project_id = raw_expense.get('project_id')
            project_name = raw_expense.get('project_name')
            
            if project_id and project_id != '':
                # Validate project_id exists
                if workspace_id in self._project_cache and project_id in self._project_cache[workspace_id]:
                    expense_data['projectId'] = project_id
                else:
                    errors.append(f"Project ID not found: {project_id}")
            elif project_name and project_name != '':
                # Try to resolve project name to ID
                project_name_lower = project_name.lower().strip()
                if project_name_lower in project_name_to_id:
                    expense_data['projectId'] = project_name_to_id[project_name_lower]
                else:
                    errors.append(f"Project name not found: {project_name}")
            
            # Category
            category = raw_expense.get('category')
            if category and category != '':
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
            
            # Task ID
            task_id = raw_expense.get('task_id')
            if task_id and task_id != '':
                expense_data['taskId'] = str(task_id).strip()
            
            # Receipt
            receipt = raw_expense.get('receipt')
            if receipt and receipt != '':
                expense_data['receipt'] = str(receipt).strip()
            
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

    def generate_csv_template(self, output_path: str = None) -> Dict[str, Any]:
        """
        Generate a CSV template file for expense uploads
        
        Args:
            output_path: Optional custom output path
            
        Returns:
            Dict containing template generation result
        """
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"expense_upload_template_{timestamp}.csv"
            
            # Sample data for template - all rows must have the same fields
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
            
            self.logger.info(f"CSV template generated: {output_path}")
            
            return {
                'success': True,
                'template_path': output_path,
                'columns_included': list(template_data[0].keys()) if template_data else [],
                'sample_rows': len(template_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating CSV template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 