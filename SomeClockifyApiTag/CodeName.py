"""
Template Manager for Clockify API operations
Based on https://docs.clockify.me/#tag/*

This is a template file. Replace 'SomeClockifyApiTag' and 'SomeClockifyApiManager' 
with the actual API tag name and manager class name.
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from Config.settings import settings


class SomeClockifyApiManager:
    """
    Template class for managing Clockify API operations
    Replace this with the actual API tag functionality
    """
    
    def __init__(self):
        self.base_url = settings.clockify_base_url
        self.api_key = settings.clockify_api_key
        self.workspace_id = settings.clockify_workspace_id
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """Make a request to the Clockify API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {"error": str(e)}
    
    def get_all_items(self) -> Dict:
        """
        Template method to get all items for this API tag
        Replace with actual endpoint
        """
        endpoint = f"/workspaces/{self.workspace_id}/some-endpoint"
        return self._make_request(endpoint)
    
    def get_item_by_id(self, item_id: str) -> Dict:
        """
        Template method to get a specific item by ID
        Replace with actual endpoint
        """
        endpoint = f"/workspaces/{self.workspace_id}/some-endpoint/{item_id}"
        return self._make_request(endpoint)
    
    def create_item(self, item_data: Dict) -> Dict:
        """
        Template method to create a new item
        Replace with actual endpoint
        """
        endpoint = f"/workspaces/{self.workspace_id}/some-endpoint"
        return self._make_request(endpoint, method='POST', data=item_data)
    
    def update_item(self, item_id: str, item_data: Dict) -> Dict:
        """
        Template method to update an existing item
        Replace with actual endpoint
        """
        endpoint = f"/workspaces/{self.workspace_id}/some-endpoint/{item_id}"
        return self._make_request(endpoint, method='PUT', data=item_data)
    
    def delete_item(self, item_id: str) -> Dict:
        """
        Template method to delete an item
        Replace with actual endpoint
        """
        endpoint = f"/workspaces/{self.workspace_id}/some-endpoint/{item_id}"
        return self._make_request(endpoint, method='DELETE')
    
    def export_to_csv(self, data: Dict, filename: str) -> None:
        """Export data to CSV file"""
        try:
            df = pd.DataFrame(data.get('items', []))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{filename}_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"Data exported to CSV: {csv_filename}")
        except Exception as e:
            print(f"CSV export failed: {e}")
    
    def export_to_json(self, data: Dict, filename: str) -> None:
        """Export data to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"{filename}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data exported to JSON: {json_filename}")
        except Exception as e:
            print(f"JSON export failed: {e}")
    
    def batch_export(self, data: Dict, filename_prefix: str) -> None:
        """Export data to both JSON and CSV formats"""
        self.export_to_json(data, filename_prefix)
        self.export_to_csv(data, filename_prefix) 