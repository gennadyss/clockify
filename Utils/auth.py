"""
Authentication and Configuration Utilities
Centralized authentication and configuration validation functionality
"""

import os
from typing import Dict, List, Optional, Tuple
from Config.settings import settings
from .logging import Logger
from .api_client import APIClient


class AuthManager:
    """Manages authentication and configuration validation"""
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize AuthManager
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger()
        self.api_client = None
    
    def validate_environment_variables(self) -> Tuple[bool, List[str]]:
        """
        Validate required environment variables
        
        Returns:
            tuple: (is_valid, list_of_missing_vars)
        """
        required_vars = {
            'CLOCKIFY_API_KEY': settings.clockify_api_key,
            'CLOCKIFY_WORKSPACE_ID': settings.clockify_workspace_id
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        
        if missing_vars:
            self.logger.log_configuration("Environment Variables", "INVALID")
            self.logger.error("Missing required environment variables:")
            for var in missing_vars:
                self.logger.error(f"  - {var}")
            return False, missing_vars
        
        self.logger.log_configuration("Environment Variables", "VALID")
        return True, []
    
    def validate_api_credentials(self) -> bool:
        """
        Validate API credentials by making a test request
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            # Create API client if not exists
            if not self.api_client:
                self.api_client = APIClient(self.logger)
            
            # Test connection
            if self.api_client.validate_connection():
                self.logger.log_configuration("API Credentials", "VALID")
                return True
            else:
                self.logger.log_configuration("API Credentials", "INVALID")
                return False
                
        except Exception as e:
            self.logger.error(f"API credential validation failed: {e}")
            self.logger.log_configuration("API Credentials", "INVALID")
            return False
    
    def validate_configuration(self) -> bool:
        """
        Comprehensive configuration validation
        
        Returns:
            bool: True if all configuration is valid
        """
        self.logger.info("🔍 Validating configuration...")
        
        # Check environment variables
        env_valid, missing_vars = self.validate_environment_variables()
        if not env_valid:
            return False
        
        # Check API credentials
        api_valid = self.validate_api_credentials()
        if not api_valid:
            return False
        
        # Check application settings
        app_valid = self.validate_application_settings()
        if not app_valid:
            return False
        
        self.logger.info("✅ All configuration validation passed!")
        return True
    
    def validate_application_settings(self) -> bool:
        """
        Validate application-specific settings
        
        Returns:
            bool: True if application settings are valid
        """
        try:
            # Check if APPROVE_CHANGES is set and is boolean-like
            approve_changes = os.getenv('APPROVE_CHANGES', 'false').lower()
            if approve_changes not in ['true', 'false']:
                self.logger.warning("APPROVE_CHANGES should be 'true' or 'false'")
            
            # Check debug setting
            debug = os.getenv('DEBUG', 'true').lower()
            if debug not in ['true', 'false']:
                self.logger.warning("DEBUG should be 'true' or 'false'")
            
            # Validate workspace ID format (if needed)
            if len(settings.clockify_workspace_id) < 10:
                self.logger.warning("Workspace ID seems unusually short")
            
            self.logger.log_configuration("Application Settings", "VALID")
            return True
            
        except Exception as e:
            self.logger.error(f"Application settings validation failed: {e}")
            self.logger.log_configuration("Application Settings", "INVALID")
            return False
    
    def get_user_permissions(self) -> Dict:
        """
        Get current user permissions and role information
        
        Returns:
            dict: User permissions and role data
        """
        try:
            if not self.api_client:
                self.api_client = APIClient(self.logger)
            
            # Get current user info
            user_info = self.api_client.get("/user")
            
            if not self.api_client.is_error_response(user_info):
                self.logger.debug(f"Current user: {user_info.get('name', 'Unknown')}")
                return user_info
            else:
                self.logger.error("Failed to get user permissions")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting user permissions: {e}")
            return {}
    
    def check_required_permissions(self, required_permissions: List[str]) -> bool:
        """
        Check if current user has required permissions
        
        Args:
            required_permissions: List of required permission names
            
        Returns:
            bool: True if user has all required permissions
        """
        try:
            user_info = self.get_user_permissions()
            if not user_info:
                return False
            
            # This would need to be adapted based on actual Clockify permission structure
            user_permissions = user_info.get('permissions', [])
            
            missing_permissions = [perm for perm in required_permissions 
                                 if perm not in user_permissions]
            
            if missing_permissions:
                self.logger.warning(f"Missing permissions: {missing_permissions}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
    
    def get_workspace_info(self) -> Dict:
        """
        Get detailed workspace information
        
        Returns:
            dict: Workspace information
        """
        try:
            if not self.api_client:
                self.api_client = APIClient(self.logger)
            
            workspace_info = self.api_client.get_workspace_info()
            
            if not self.api_client.is_error_response(workspace_info):
                self.logger.debug(f"Workspace: {workspace_info.get('name', 'Unknown')}")
                return workspace_info
            else:
                self.logger.error("Failed to get workspace information")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting workspace info: {e}")
            return {}
    
    def validate_workspace_access(self) -> bool:
        """
        Validate that user has access to the configured workspace
        
        Returns:
            bool: True if workspace access is valid
        """
        try:
            workspace_info = self.get_workspace_info()
            
            if workspace_info and workspace_info.get('id') == settings.clockify_workspace_id:
                self.logger.log_configuration("Workspace Access", "VALID")
                return True
            else:
                self.logger.log_configuration("Workspace Access", "INVALID")
                return False
                
        except Exception as e:
            self.logger.error(f"Workspace access validation failed: {e}")
            self.logger.log_configuration("Workspace Access", "INVALID")
            return False
    
    def is_changes_approved(self) -> bool:
        """
        Check if changes are approved via environment variable
        
        Returns:
            bool: True if changes are approved
        """
        approved = os.getenv('APPROVE_CHANGES', 'false').lower() == 'true'
        
        if approved:
            self.logger.warning("⚠️  CHANGES ARE APPROVED - Real modifications will be made!")
        else:
            self.logger.info("ℹ️  Running in dry-run mode - no actual changes will be made")
        
        return approved
    
    def get_configuration_summary(self) -> Dict:
        """
        Get a summary of current configuration
        
        Returns:
            dict: Configuration summary
        """
        return {
            "api_key_configured": bool(settings.clockify_api_key),
            "workspace_id_configured": bool(settings.clockify_workspace_id),
            "changes_approved": self.is_changes_approved(),
            "debug_mode": os.getenv('DEBUG', 'true').lower() == 'true',
            "base_url": settings.clockify_base_url,
            "workspace_id": settings.clockify_workspace_id
        } 