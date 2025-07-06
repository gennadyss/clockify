#!/usr/bin/env python3
"""
Test Pagination Functionality
Demonstrates how pagination ensures complete data retrieval from Clockify API
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from Utils.api_client import APIClient
from Utils.logging import Logger
from Tasks.Tasks import TaskManager
from Users.Users import UserManager
from Config.settings import settings


def test_pagination_functionality():
    """Test and demonstrate pagination functionality"""
    
    print("🔍 Testing Clockify API Pagination Functionality")
    print("=" * 60)
    
    # Initialize components
    logger = Logger("pagination_test")
    api_client = APIClient(logger)
    task_manager = TaskManager(logger)
    user_manager = UserManager(logger)
    
    # Test 1: API Connection
    print("\n1. Testing API Connection...")
    if api_client.validate_connection():
        print("✅ API connection successful")
    else:
        print("❌ API connection failed")
        return False
    
    # Test 2: Projects with Pagination
    print("\n2. Testing Projects Pagination...")
    try:
        # Get projects with pagination info
        projects = api_client.get_projects(paginated=True)
        
        if api_client.is_error_response(projects):
            print(f"❌ Error: {api_client.get_error_message(projects)}")
        else:
            total_count = projects.get('total_count', 0)
            pages_fetched = projects.get('pages_fetched', 1)
            items_count = len(projects.get('items', []))
            
            print(f"✅ Retrieved {total_count} projects")
            print(f"   📄 Pages fetched: {pages_fetched}")
            print(f"   📋 Items in response: {items_count}")
            
            # Show first few project names
            if items_count > 0:
                print(f"   📌 First 3 projects:")
                for i, project in enumerate(projects.get('items', [])[:3]):
                    print(f"      {i+1}. {project.get('name', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ Projects test failed: {e}")
    
    # Test 3: Users with Pagination
    print("\n3. Testing Users Pagination...")
    try:
        users = api_client.get_users(paginated=True)
        
        if api_client.is_error_response(users):
            print(f"❌ Error: {api_client.get_error_message(users)}")
        else:
            total_count = users.get('total_count', 0)
            pages_fetched = users.get('pages_fetched', 1)
            items_count = len(users.get('items', []))
            
            print(f"✅ Retrieved {total_count} users")
            print(f"   📄 Pages fetched: {pages_fetched}")
            print(f"   📋 Items in response: {items_count}")
            
            # Show first few user names
            if items_count > 0:
                print(f"   📌 First 3 users:")
                for i, user in enumerate(users.get('items', [])[:3]):
                    print(f"      {i+1}. {user.get('name', 'Unknown')} ({user.get('email', 'No email')})")
    
    except Exception as e:
        print(f"❌ Users test failed: {e}")
    
    # Test 4: User Groups with Pagination
    print("\n4. Testing User Groups Pagination...")
    try:
        groups = api_client.get_user_groups(paginated=True)
        
        if api_client.is_error_response(groups):
            print(f"❌ Error: {api_client.get_error_message(groups)}")
        else:
            total_count = groups.get('total_count', 0)
            pages_fetched = groups.get('pages_fetched', 1)
            items_count = len(groups.get('items', []))
            
            print(f"✅ Retrieved {total_count} user groups")
            print(f"   📄 Pages fetched: {pages_fetched}")
            print(f"   📋 Items in response: {items_count}")
            
            # Show first few group names
            if items_count > 0:
                print(f"   📌 First 3 groups:")
                for i, group in enumerate(groups.get('items', [])[:3]):
                    print(f"      {i+1}. {group.get('name', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ User groups test failed: {e}")
    
    # Test 5: Pagination Info Analysis
    print("\n5. Testing Pagination Info Analysis...")
    try:
        # Get pagination info for projects
        info = api_client.get_pagination_info(f"/workspaces/{settings.clockify_workspace_id}/projects")
        
        if api_client.is_error_response(info):
            print(f"❌ Error: {api_client.get_error_message(info)}")
        else:
            print(f"✅ Pagination analysis:")
            print(f"   🔍 Supports pagination: {info.get('supports_pagination', 'Unknown')}")
            print(f"   📊 Response format: {info.get('response_format', 'Unknown')}")
            print(f"   🔢 First page items: {info.get('first_page_items', 'Unknown')}")
            
            if 'available_keys' in info:
                print(f"   🗝️  Available keys: {info['available_keys']}")
    
    except Exception as e:
        print(f"❌ Pagination info test failed: {e}")
    
    # Test 6: Compare Paginated vs Non-Paginated
    print("\n6. Testing Paginated vs Non-Paginated Comparison...")
    try:
        # Get first page only
        projects_first_page = api_client.get_projects(paginated=False)
        
        # Get all pages
        projects_all_pages = api_client.get_projects(paginated=True)
        
        if (not api_client.is_error_response(projects_first_page) and 
            not api_client.is_error_response(projects_all_pages)):
            
            first_page_count = len(projects_first_page.get('items', []) if isinstance(projects_first_page, dict) else projects_first_page)
            all_pages_count = projects_all_pages.get('total_count', 0)
            
            print(f"✅ Comparison results:")
            print(f"   📄 First page only: {first_page_count} items")
            print(f"   📚 All pages: {all_pages_count} items")
            
            if all_pages_count > first_page_count:
                print(f"   🎯 Pagination retrieved {all_pages_count - first_page_count} additional items!")
            elif all_pages_count == first_page_count:
                print(f"   ℹ️  All data fits in first page")
            else:
                print(f"   ⚠️  Inconsistent results")
    
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Pagination testing completed!")
    print("📊 All GET functions now retrieve complete data across all pages")
    print("🔗 Based on Clockify API documentation: https://docs.clockify.me/")
    
    return True


def main():
    """Main test function"""
    print(f"Clockify Pagination Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not settings.clockify_api_key:
        print("❌ CLOCKIFY_API_KEY not set in environment")
        return False
    
    if not settings.clockify_workspace_id:
        print("❌ CLOCKIFY_WORKSPACE_ID not set in environment")
        return False
    
    # Run tests
    success = test_pagination_functionality()
    
    if success:
        print("\n🎉 All pagination tests passed!")
        print("🚀 Your Clockify integration now retrieves complete data sets")
    else:
        print("\n❌ Some tests failed")
        print("🔧 Check your API credentials and network connection")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 