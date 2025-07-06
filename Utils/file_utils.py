"""
File Utilities
Common file operations and utility functions
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from .logging import Logger


class FileUtils:
    """Utility class for file operations"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize FileUtils
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger()
    
    @staticmethod
    def ensure_directory_exists(directory_path: Union[str, Path]) -> bool:
        """
        Ensure directory exists, create if it doesn't
        
        Args:
            directory_path: Path to directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix.lower()
    
    @staticmethod
    def get_filename_without_extension(filename: str) -> str:
        """Get filename without extension"""
        return Path(filename).stem
    
    @staticmethod
    def generate_timestamped_filename(base_name: str, extension: str = ".txt") -> str:
        """
        Generate filename with timestamp
        
        Args:
            base_name: Base name for file
            extension: File extension (include dot)
            
        Returns:
            str: Timestamped filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}{extension}"
    
    def read_json_file(self, file_path: Union[str, Path]) -> Optional[Dict]:
        """
        Read JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            dict: JSON data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.debug(f"Read JSON file: {file_path}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to read JSON file {file_path}: {e}")
            return None
    
    def write_json_file(self, data: Dict, file_path: Union[str, Path], 
                       pretty: bool = True) -> bool:
        """
        Write data to JSON file
        
        Args:
            data: Data to write
            file_path: Path for output file
            pretty: Whether to format JSON prettily
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure directory exists
            self.ensure_directory_exists(Path(file_path).parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            self.logger.debug(f"Written JSON file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write JSON file {file_path}: {e}")
            return False
    
    def read_text_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Read text file
        
        Args:
            file_path: Path to text file
            
        Returns:
            str: File content or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.debug(f"Read text file: {file_path}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to read text file {file_path}: {e}")
            return None
    
    def write_text_file(self, content: str, file_path: Union[str, Path]) -> bool:
        """
        Write content to text file
        
        Args:
            content: Text content to write
            file_path: Path for output file
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure directory exists
            self.ensure_directory_exists(Path(file_path).parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Written text file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write text file {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()
    
    def get_file_size(self, file_path: Union[str, Path]) -> Optional[int]:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
            
        Returns:
            int: File size in bytes or None if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return None
    
    def get_file_modification_time(self, file_path: Union[str, Path]) -> Optional[datetime]:
        """
        Get file modification time
        
        Args:
            file_path: Path to file
            
        Returns:
            datetime: Modification time or None if file doesn't exist
        """
        try:
            timestamp = Path(file_path).stat().st_mtime
            return datetime.fromtimestamp(timestamp)
        except Exception:
            return None
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete file
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if successful
        """
        try:
            Path(file_path).unlink()
            self.logger.debug(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copy file
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure destination directory exists
            self.ensure_directory_exists(Path(destination).parent)
            
            shutil.copy2(source, destination)
            self.logger.debug(f"Copied file: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file {source} -> {destination}: {e}")
            return False
    
    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Move file
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure destination directory exists
            self.ensure_directory_exists(Path(destination).parent)
            
            shutil.move(source, destination)
            self.logger.debug(f"Moved file: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file {source} -> {destination}: {e}")
            return False
    
    def list_files_in_directory(self, directory: Union[str, Path], 
                               pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        List files in directory
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            list: List of file paths
        """
        try:
            directory_path = Path(directory)
            if recursive:
                files = list(directory_path.rglob(pattern))
            else:
                files = list(directory_path.glob(pattern))
            
            # Filter to only files (not directories)
            files = [f for f in files if f.is_file()]
            
            self.logger.debug(f"Found {len(files)} files in {directory}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    def cleanup_old_files(self, directory: Union[str, Path], 
                         pattern: str = "*", max_age_days: int = 7) -> int:
        """
        Clean up old files in directory
        
        Args:
            directory: Directory path
            pattern: File pattern to match
            max_age_days: Maximum age in days
            
        Returns:
            int: Number of files deleted
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            files = self.list_files_in_directory(directory, pattern)
            
            deleted_count = 0
            for file_path in files:
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                except Exception:
                    continue
            
            self.logger.info(f"Cleaned up {deleted_count} old files from {directory}")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Failed to cleanup files in {directory}: {e}")
            return 0
    
    def get_directory_size(self, directory: Union[str, Path]) -> int:
        """
        Get total size of directory
        
        Args:
            directory: Directory path
            
        Returns:
            int: Total size in bytes
        """
        try:
            total_size = 0
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception as e:
            self.logger.error(f"Failed to get directory size {directory}: {e}")
            return 0
    
    def create_backup(self, file_path: Union[str, Path], 
                     backup_suffix: str = ".backup") -> Optional[Path]:
        """
        Create backup of file
        
        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file
            
        Returns:
            Path: Backup file path or None if failed
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = source_path.with_suffix(f"{backup_suffix}_{timestamp}")
            
            if self.copy_file(source_path, backup_path):
                return backup_path
            return None
        except Exception as e:
            self.logger.error(f"Failed to create backup of {file_path}: {e}")
            return None 