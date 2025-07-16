"""
Expenses Module for Clockify API Integration

This module provides comprehensive expense management functionality for Clockify,
including creating, reading, updating, and deleting expenses through the Clockify API.

Components:
- ExpenseManager: Main expense management class with CRUD operations
- Expense data models and validation
- Integration with Utils modules for API client, logging, and file operations

Based on Clockify API documentation: https://docs.clockify.me/#tag/Expense
"""

from .ExpenseManager import ExpenseManager

__all__ = ['ExpenseManager'] 