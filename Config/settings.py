"""
Configuration Settings Module
Centralized configuration management for the Clockify integration
"""

import os
from dotenv import load_dotenv
from typing import Optional

class Settings:
    def __init__(self):
        load_dotenv()
        
        # Clockify Configuration
        self.clockify_api_key = os.getenv('CLOCKIFY_API_KEY')
        self.clockify_workspace_id = os.getenv('CLOCKIFY_WORKSPACE_ID')
        self.clockify_base_url = "https://api.clockify.me/api/v1"
        
        # Application Configuration
        self.output_file = "TimeEntries.csv"
        
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_vars = {
            'CLOCKIFY_API_KEY': self.clockify_api_key,
            'CLOCKIFY_WORKSPACE_ID': self.clockify_workspace_id
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        
        if missing_vars:
            print("Missing required environment variables:")
            for var in missing_vars:
                print(f"  - {var}")
            return False
            
        return True

# Global settings instance
settings = Settings()
