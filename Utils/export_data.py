"""
Data Export Utilities
Centralized functionality for exporting data to JSON and CSV formats
Files are generated in the Export folder for better organization
"""

import json
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from .logging import Logger


class DataExporter:
    """Utility class for exporting data to various formats"""
    
    def __init__(self, logger: Optional[Logger] = None, export_folder: str = "Export"):
        """
        Initialize DataExporter
        
        Args:
            logger: Optional logger instance
            export_folder: Folder to store exported files (default: "Export")
        """
        self.logger = logger or Logger()
        self.export_folder = export_folder
        self._ensure_export_folder_exists()
    
    def _ensure_export_folder_exists(self):
        """Ensure the export folder exists"""
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder, exist_ok=True)
            self.logger.info(f"Created export folder: {self.export_folder}")
    
    def _generate_timestamp(self) -> str:
        """Generate timestamp for filenames"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _get_file_path(self, filename: str) -> str:
        """Get full file path in export folder"""
        return os.path.join(self.export_folder, filename)
    
    def export_to_json(self, data: Dict, filename: str, include_timestamp: bool = True) -> str:
        """
        Export data to JSON file in Export folder
        
        Args:
            data: Dictionary data to export
            filename: Base filename (without extension)
            include_timestamp: Whether to include timestamp in filename
            
        Returns:
            str: Full filename of created file
        """
        try:
            if include_timestamp:
                timestamp = self._generate_timestamp()
                json_filename = f"{filename}_{timestamp}.json"
            else:
                json_filename = f"{filename}.json"
            
            # Create full path in Export folder
            full_path = self._get_file_path(json_filename)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data exported to JSON: {full_path}")
            return full_path
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            raise
    
    def export_to_csv(self, data: Dict, filename: str, include_timestamp: bool = True) -> Optional[str]:
        """
        Export data to CSV file in Export folder
        
        Args:
            data: Dictionary data to export (must have 'items' key with list of records)
            filename: Base filename (without extension)
            include_timestamp: Whether to include timestamp in filename
            
        Returns:
            str: Full filename of created file, or None if export failed
        """
        try:
            if not isinstance(data, dict) or 'items' not in data:
                self.logger.warning("Data format not suitable for CSV export (missing 'items' key)")
                return None
            
            df = pd.DataFrame(data['items'])
            if df.empty:
                self.logger.warning("No data to export to CSV")
                return None
            
            if include_timestamp:
                timestamp = self._generate_timestamp()
                csv_filename = f"{filename}_{timestamp}.csv"
            else:
                csv_filename = f"{filename}.csv"
            
            # Create full path in Export folder
            full_path = self._get_file_path(csv_filename)
            
            df.to_csv(full_path, index=False)
            self.logger.info(f"Data exported to CSV: {full_path}")
            return full_path
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            return None
    
    def export_to_both_formats(self, data: Dict, filename_prefix: str, include_timestamp: bool = True) -> Dict[str, str]:
        """
        Export data to both JSON and CSV formats in Export folder
        
        Args:
            data: Dictionary data to export
            filename_prefix: Base filename prefix (without extension)
            include_timestamp: Whether to include timestamp in filename
            
        Returns:
            dict: Dictionary with 'json' and 'csv' keys containing filenames
        """
        results = {}
        
        # Export to JSON
        json_file = self.export_to_json(data, filename_prefix, include_timestamp)
        results['json'] = json_file
        
        # Export to CSV
        csv_file = self.export_to_csv(data, filename_prefix, include_timestamp)
        if csv_file:
            results['csv'] = csv_file
        
        return results
    
    def export_multiple_datasets(self, datasets: Dict[str, Dict], base_filename: str, 
                                include_timestamp: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Export multiple datasets with different suffixes to Export folder
        
        Args:
            datasets: Dictionary where keys are suffixes and values are data dictionaries
            base_filename: Base filename prefix
            include_timestamp: Whether to include timestamp in filename
            
        Returns:
            dict: Nested dictionary with dataset names and their exported filenames
        """
        results = {}
        
        for suffix, data in datasets.items():
            filename = f"{base_filename}_{suffix}" if suffix else base_filename
            results[suffix] = self.export_to_both_formats(data, filename, include_timestamp)
        
        return results
    
    def export_list_data(self, data: List[Dict], filename: str, include_timestamp: bool = True) -> Dict[str, str]:
        """
        Export list data by wrapping it in 'items' key to Export folder
        
        Args:
            data: List of dictionaries to export
            filename: Base filename (without extension)
            include_timestamp: Whether to include timestamp in filename
            
        Returns:
            dict: Dictionary with 'json' and 'csv' keys containing filenames
        """
        wrapped_data = {"items": data}
        return self.export_to_both_formats(wrapped_data, filename, include_timestamp)
    
    def validate_export_data(self, data: Any) -> bool:
        """
        Validate data format for export
        
        Args:
            data: Data to validate
            
        Returns:
            bool: True if data is valid for export
        """
        if not isinstance(data, dict):
            self.logger.warning("Data must be a dictionary")
            return False
        
        if 'items' in data and not isinstance(data['items'], list):
            self.logger.warning("'items' key must contain a list")
            return False
        
        return True
    
    def get_export_folder(self) -> str:
        """Get the current export folder path"""
        return self.export_folder
    
    def set_export_folder(self, folder: str):
        """
        Set a new export folder
        
        Args:
            folder: New export folder path
        """
        self.export_folder = folder
        self._ensure_export_folder_exists()
        self.logger.info(f"Export folder changed to: {folder}")
    
    def list_exported_files(self) -> List[str]:
        """
        List all files in the export folder
        
        Returns:
            list: List of filenames in export folder
        """
        if not os.path.exists(self.export_folder):
            return []
        
        files = []
        for file in os.listdir(self.export_folder):
            if file.endswith(('.json', '.csv')):
                files.append(os.path.join(self.export_folder, file))
        
        return sorted(files)
    
    def clean_old_exports(self, days_old: int = 30):
        """
        Remove export files older than specified days
        
        Args:
            days_old: Number of days old to consider for cleanup
        """
        if not os.path.exists(self.export_folder):
            return
        
        import time
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        removed_count = 0
        
        for file in os.listdir(self.export_folder):
            if file.endswith(('.json', '.csv')):
                file_path = os.path.join(self.export_folder, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        self.logger.info(f"Removed old export file: {file}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove file {file}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old export files")
        else:
            self.logger.info("No old export files to clean up") 