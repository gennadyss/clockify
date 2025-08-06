#!/usr/bin/env python3
"""
CSV Format Validation Script for Clockify Expense Upload

This script validates the July data CSV file against the reference format
from Test_final_sheet_expenses.csv to ensure compatibility with the expense
upload system.
"""

import pandas as pd
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the parent directory to the path to access Utils and other modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from Utils.logging import Logger

class CSVFormatValidator:
    """Validates CSV files against expected expense upload format"""
    
    def __init__(self, logger: Logger = None):
        self.logger = logger or Logger("CSVFormatValidator", console_output=True)
        
        # Expected format based on Test_final_sheet_expenses.csv
        self.expected_columns = {
            'Date': str,
            'Project': str, 
            'Task': str,
            'Amount': float,
            'Category': str,
            'billable': str  # Should be 'Yes' or 'No'
        }
        
        # Optional columns that may appear
        self.optional_columns = {
            'Note': str
        }
        
        # Valid billable values
        self.valid_billable_values = ['Yes', 'No', 'yes', 'no', 'YES', 'NO']
        
        # Date format patterns to try
        self.date_formats = [
            '%m/%d/%Y',    # 11/30/2025
            '%d/%m/%Y',    # 31/07/2025  
            '%Y-%m-%d',    # 2025-11-30
            '%m-%d-%Y',    # 11-30-2025
        ]

    def validate_csv_file(self, csv_file_path: str, reference_file_path: str = None) -> Dict[str, Any]:
        """
        Validate CSV file format and content
        
        Args:
            csv_file_path: Path to CSV file to validate
            reference_file_path: Optional path to reference CSV file
            
        Returns:
            Dict containing validation results
        """
        try:
            self.logger.info(f"Starting validation of: {csv_file_path}")
            
            # Check if file exists
            if not os.path.exists(csv_file_path):
                return {
                    'valid': False,
                    'error': f"CSV file not found: {csv_file_path}"
                }
            
            # Read the CSV file
            try:
                df = pd.read_csv(csv_file_path)
            except Exception as e:
                return {
                    'valid': False,
                    'error': f"Failed to read CSV file: {str(e)}"
                }
            
            # Initialize validation results
            validation_results = {
                'valid': True,
                'file_path': csv_file_path,
                'total_rows': len(df),
                'columns_found': list(df.columns),
                'issues': [],
                'warnings': [],
                'data_summary': {}
            }
            
            # Validate structure
            structure_issues = self._validate_structure(df)
            validation_results['issues'].extend(structure_issues)
            
            # Validate data content
            content_issues, warnings = self._validate_content(df)
            validation_results['issues'].extend(content_issues)
            validation_results['warnings'].extend(warnings)
            
            # Generate data summary
            validation_results['data_summary'] = self._generate_data_summary(df)
            
            # Overall validation result
            validation_results['valid'] = len(validation_results['issues']) == 0
            
            # Compare with reference file if provided
            if reference_file_path and os.path.exists(reference_file_path):
                comparison_results = self._compare_with_reference(df, reference_file_path)
                validation_results['reference_comparison'] = comparison_results
            
            self.logger.info(f"Validation completed. Valid: {validation_results['valid']}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error during validation: {str(e)}")
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}"
            }

    def _validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate CSV structure (columns, headers)"""
        issues = []
        
        # Check for required columns
        missing_columns = []
        for col in self.expected_columns.keys():
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check for unexpected columns
        expected_and_optional = set(self.expected_columns.keys()) | set(self.optional_columns.keys())
        unexpected_columns = [col for col in df.columns if col not in expected_and_optional]
        
        if unexpected_columns:
            issues.append(f"Unexpected columns found: {unexpected_columns}")
        
        # Check for empty dataframe
        if df.empty:
            issues.append("CSV file is empty")
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
            issues.append(f"Duplicate column names found: {set(duplicates)}")
        
        return issues

    def _validate_content(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Validate CSV content (data types, values, formats)"""
        issues = []
        warnings = []
        
        for index, row in df.iterrows():
            row_num = index + 2  # +2 because index is 0-based and we have header
            
            # Validate Date column
            if 'Date' in df.columns:
                date_value = row['Date']
                if pd.isna(date_value) or date_value == '':
                    issues.append(f"Row {row_num}: Date is empty")
                else:
                    date_parsed = self._parse_date(str(date_value))
                    if not date_parsed:
                        issues.append(f"Row {row_num}: Invalid date format '{date_value}'. Expected formats: MM/DD/YYYY or DD/MM/YYYY")
            
            # Validate Project column
            if 'Project' in df.columns:
                project_value = row['Project']
                if pd.isna(project_value) or str(project_value).strip() == '':
                    issues.append(f"Row {row_num}: Project name is empty")
                elif len(str(project_value).strip()) < 3:
                    warnings.append(f"Row {row_num}: Project name is very short: '{project_value}'")
            
            # Validate Task column
            if 'Task' in df.columns:
                task_value = row['Task']
                if pd.isna(task_value) or str(task_value).strip() == '':
                    issues.append(f"Row {row_num}: Task name is empty")
                elif len(str(task_value).strip()) < 3:
                    warnings.append(f"Row {row_num}: Task name is very short: '{task_value}'")
            
            # Validate Amount column
            if 'Amount' in df.columns:
                amount_value = row['Amount']
                if pd.isna(amount_value) or amount_value == '':
                    issues.append(f"Row {row_num}: Amount is empty")
                else:
                    try:
                        amount_float = float(amount_value)
                        if amount_float < 0:
                            issues.append(f"Row {row_num}: Amount cannot be negative: {amount_value}")
                        elif amount_float == 0:
                            warnings.append(f"Row {row_num}: Amount is zero: {amount_value}")
                    except (ValueError, TypeError):
                        issues.append(f"Row {row_num}: Invalid amount format: '{amount_value}'. Must be a number.")
            
            # Validate Category column
            if 'Category' in df.columns:
                category_value = row['Category']
                if pd.isna(category_value) or str(category_value).strip() == '':
                    issues.append(f"Row {row_num}: Category is empty")
                elif len(str(category_value).strip()) < 2:
                    warnings.append(f"Row {row_num}: Category name is very short: '{category_value}'")
            
            # Validate billable column
            if 'billable' in df.columns:
                billable_value = row['billable']
                if pd.isna(billable_value) or str(billable_value).strip() == '':
                    issues.append(f"Row {row_num}: Billable value is empty")
                elif str(billable_value).strip() not in self.valid_billable_values:
                    issues.append(f"Row {row_num}: Invalid billable value '{billable_value}'. Must be 'Yes' or 'No'")
        
        return issues, warnings

    def _parse_date(self, date_str: str) -> bool:
        """Try to parse date string with multiple formats"""
        if not date_str:
            return False
            
        for fmt in self.date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False

    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the data"""
        summary = {
            'total_rows': len(df),
            'columns': list(df.columns)
        }
        
        # Amount statistics
        if 'Amount' in df.columns:
            try:
                amounts = pd.to_numeric(df['Amount'], errors='coerce')
                summary['amount_stats'] = {
                    'total': float(amounts.sum()),
                    'average': float(amounts.mean()),
                    'min': float(amounts.min()),
                    'max': float(amounts.max()),
                    'count': int(amounts.count())
                }
            except Exception as e:
                summary['amount_stats'] = f"Error calculating amount stats: {str(e)}"
        
        # Project distribution
        if 'Project' in df.columns:
            project_counts = df['Project'].value_counts()
            summary['project_distribution'] = {
                'unique_projects': int(project_counts.count()),
                'top_projects': project_counts.head(10).to_dict()
            }
        
        # Category distribution
        if 'Category' in df.columns:
            category_counts = df['Category'].value_counts()
            summary['category_distribution'] = {
                'unique_categories': int(category_counts.count()),
                'categories': category_counts.to_dict()
            }
        
        # Billable distribution
        if 'billable' in df.columns:
            billable_counts = df['billable'].value_counts()
            summary['billable_distribution'] = billable_counts.to_dict()
        
        # Date range
        if 'Date' in df.columns:
            valid_dates = []
            for date_str in df['Date'].dropna():
                parsed_date = None
                for fmt in self.date_formats:
                    try:
                        parsed_date = datetime.strptime(str(date_str), fmt)
                        break
                    except ValueError:
                        continue
                if parsed_date:
                    valid_dates.append(parsed_date)
            
            if valid_dates:
                summary['date_range'] = {
                    'earliest': min(valid_dates).strftime('%Y-%m-%d'),
                    'latest': max(valid_dates).strftime('%Y-%m-%d'),
                    'unique_dates': len(set(valid_dates))
                }
        
        return summary

    def _compare_with_reference(self, df: pd.DataFrame, reference_file_path: str) -> Dict[str, Any]:
        """Compare current CSV with reference file"""
        try:
            ref_df = pd.read_csv(reference_file_path)
            
            comparison = {
                'reference_file': reference_file_path,
                'structure_match': True,
                'differences': []
            }
            
            # Compare columns
            current_cols = set(df.columns)
            reference_cols = set(ref_df.columns)
            
            if current_cols != reference_cols:
                comparison['structure_match'] = False
                
                missing_in_current = reference_cols - current_cols
                extra_in_current = current_cols - reference_cols
                
                if missing_in_current:
                    comparison['differences'].append(f"Missing columns: {list(missing_in_current)}")
                
                if extra_in_current:
                    comparison['differences'].append(f"Extra columns: {list(extra_in_current)}")
            
            # Compare data types and formats
            common_cols = current_cols & reference_cols
            for col in common_cols:
                # Sample some values to check format consistency
                current_sample = df[col].dropna().head(5).astype(str).tolist()
                ref_sample = ref_df[col].dropna().head(5).astype(str).tolist()
                
                if col == 'Date':
                    # Check date format patterns
                    current_patterns = [self._detect_date_pattern(d) for d in current_sample]
                    ref_patterns = [self._detect_date_pattern(d) for d in ref_sample]
                    
                    if set(current_patterns) != set(ref_patterns):
                        comparison['differences'].append(f"Date format differs in {col}: current uses {set(current_patterns)}, reference uses {set(ref_patterns)}")
            
            return comparison
            
        except Exception as e:
            return {
                'reference_file': reference_file_path,
                'error': f"Failed to compare with reference: {str(e)}"
            }

    def _detect_date_pattern(self, date_str: str) -> str:
        """Detect the pattern of a date string"""
        for fmt in self.date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return fmt
            except ValueError:
                continue
        return "unknown"

    def print_validation_report(self, validation_results: Dict[str, Any]) -> None:
        """Print a formatted validation report"""
        print("\n" + "="*60)
        print("CSV VALIDATION REPORT")
        print("="*60)
        
        print(f"\nFile: {validation_results.get('file_path', 'Unknown')}")
        print(f"Total Rows: {validation_results.get('total_rows', 0)}")
        print(f"Columns Found: {validation_results.get('columns_found', [])}")
        
        # Overall status
        is_valid = validation_results.get('valid', False)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"\nValidation Status: {status}")
        
        # Issues
        issues = validation_results.get('issues', [])
        if issues:
            print(f"\n🔴 ISSUES FOUND ({len(issues)}):")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        # Warnings
        warnings = validation_results.get('warnings', [])
        if warnings:
            print(f"\n🟡 WARNINGS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        # Data Summary
        data_summary = validation_results.get('data_summary', {})
        if data_summary:
            print(f"\n📊 DATA SUMMARY:")
            
            # Amount stats
            amount_stats = data_summary.get('amount_stats')
            if isinstance(amount_stats, dict):
                print(f"  Total Amount: ${amount_stats.get('total', 0):,.2f}")
                print(f"  Average Amount: ${amount_stats.get('average', 0):,.2f}")
                print(f"  Amount Range: ${amount_stats.get('min', 0):,.2f} - ${amount_stats.get('max', 0):,.2f}")
            
            # Project info
            project_dist = data_summary.get('project_distribution', {})
            if project_dist:
                print(f"  Unique Projects: {project_dist.get('unique_projects', 0)}")
            
            # Category info
            category_dist = data_summary.get('category_distribution', {})
            if category_dist:
                print(f"  Unique Categories: {category_dist.get('unique_categories', 0)}")
                print(f"  Categories: {list(category_dist.get('categories', {}).keys())}")
            
            # Date range
            date_range = data_summary.get('date_range')
            if date_range:
                print(f"  Date Range: {date_range.get('earliest')} to {date_range.get('latest')}")
        
        # Reference comparison
        ref_comparison = validation_results.get('reference_comparison')
        if ref_comparison:
            print(f"\n🔍 REFERENCE COMPARISON:")
            print(f"  Reference File: {ref_comparison.get('reference_file')}")
            match = ref_comparison.get('structure_match', False)
            print(f"  Structure Match: {'✅ Yes' if match else '❌ No'}")
            
            differences = ref_comparison.get('differences', [])
            if differences:
                print(f"  Differences:")
                for diff in differences:
                    print(f"    - {diff}")
        
        print("\n" + "="*60)


def main():
    """Main function to run CSV validation"""
    
    # File paths - now relative to current directory since we're in UploadExpenses/
    july_csv = "Test_final_sheet_expenses_July_data.csv"
    reference_csv = "Test_final_sheet_expenses.csv"
    
    # Initialize validator
    logger = Logger("CSVValidator", console_output=True)
    validator = CSVFormatValidator(logger=logger)
    
    # Validate the July CSV file
    print("Validating July expenses CSV file...")
    validation_results = validator.validate_csv_file(july_csv, reference_csv)
    
    # Print detailed report
    validator.print_validation_report(validation_results)
    
    # Summary
    if validation_results.get('valid'):
        print("\n✅ The July CSV file is VALID and ready for upload!")
    else:
        print("\n❌ The July CSV file has issues that need to be fixed before upload.")
        print("\nRecommendations:")
        print("1. Fix all issues listed above")
        print("2. Ensure date format consistency")
        print("3. Verify all required fields are present")
        print("4. Check that project/task/category names match Clockify exactly")

if __name__ == "__main__":
    main()