#!/usr/bin/env python3
"""
Test the expense upload with the July data CSV
"""

import os
import sys

# Add the parent directory to the path to access Utils and other modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from Utils.logging import Logger
from UploadExpenses.CSVExpenseUploader import CSVExpenseUploader
from Config.settings import settings

def test_expense_upload():
    """Test the expense upload with July data"""
    
    logger = Logger("TestExpenseUpload", console_output=True)
    logger.info("Testing expense upload with July data...")
    
    # Initialize CSV uploader
    uploader = CSVExpenseUploader(logger=logger)
    
    # Test parameters
    workspace_id = settings.clockify_workspace_id
    csv_file = "/Users/gennadyss/Development/bgReps/clockify/UploadExpenses/Test_final_sheet_expenses_July_data.csv"
    user_email = "dionysus_tech@bostongene.com"
    
    logger.info(f"Testing with:")
    logger.info(f"  CSV File: {csv_file}")
    logger.info(f"  Workspace: {workspace_id}")
    logger.info(f"  User Email: {user_email}")
    
    # Test dry run first
    result = uploader.upload_from_csv(
        csv_file_path=csv_file,
        workspace_id=workspace_id,
        dry_run=True,  # Dry run to test validation
        default_user_email=user_email
    )
    
    logger.info(f"Upload result: {result.get('success', False)}")
    
    if result.get('success'):
        logger.info("✅ Expense upload validation passed!")
        logger.info(f"Total records: {result.get('total_records', 0)}")
        logger.info(f"Valid records: {result.get('valid_records', 0)}")
        logger.info(f"Invalid records: {result.get('invalid_records', 0)}")
        
        if result.get('invalid_records', 0) > 0:
            logger.warning("Some validation errors found:")
            for error in result.get('validation_errors', [])[:3]:
                logger.warning(f"  Row {error.get('row_index')}: {error.get('errors')}")
        
        return True
    else:
        logger.error(f"❌ Expense upload failed: {result.get('error')}")
        
        # Show user suggestions if available
        if 'available_users' in result and result['available_users']:
            logger.info("Available users in workspace:")
            for user in result['available_users'][:5]:
                logger.info(f"  - {user.get('email', 'No email')} ({user.get('name', 'No name')})")
        
        return False

if __name__ == "__main__":
    success = test_expense_upload()
    if not success:
        print("\n❌ Expense upload test failed")
        sys.exit(1)
    else:
        print("\n✅ Expense upload test passed")