"""
UploadExpenses Module for Clockify Expense CSV Import

This module provides comprehensive CSV upload functionality for expenses,
including file parsing, validation, transformation, and bulk upload to Clockify.

Components:
- CSVExpenseUploader: Main CSV upload manager with validation and processing
- Data validation and transformation utilities
- Error handling and reporting
- Integration with Expenses module and Utils

Features:
- CSV file parsing and validation
- Data mapping and transformation
- Bulk expense creation
- Progress tracking and error reporting
- Export of upload results

Usage:
    from UploadExpenses import CSVExpenseUploader
    
    uploader = CSVExpenseUploader()
    result = uploader.upload_from_csv("expenses.csv", workspace_id="123")
"""

from .CSVExpenseUploader import CSVExpenseUploader

__all__ = ['CSVExpenseUploader'] 