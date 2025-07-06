# Clockify Access Management - Usage Guide

**Note**: In Clockify web interface, **Clients are used as Categories** for organizing projects. This project uses the [Clockify Client API](https://docs.clockify.me/#tag/Client) to filter projects by client (category).

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure Environment**
- Copy `env_template.txt` to `.env`
- Configure your Clockify credentials:
  ```env
  CLOCKIFY_API_KEY=your_api_key_here
  CLOCKIFY_WORKSPACE_ID=your_workspace_id_here
  APPROVE_CHANGES=false
  DEBUG=true
  ```

### 3. **Run the Application**
```bash
# Dry run for all projects (recommended first)
python main.py

# Filter by specific client ID (category)
python main.py --client-id YOUR_CLIENT_ID

# Apply changes (after reviewing dry run results)
# Set APPROVE_CHANGES=true in .env, then:
python main.py --client-id YOUR_CLIENT_ID
```

## 📁 Project Structure

```
Clockify/
├── main.py                    # Entry point
├── Projects/                  # Project discovery and management
│   ├── __init__.py
│   └── ProjectManager.py     # Project operations and client-based filtering
├── Clients/                   # Client management (Categories)
│   ├── __init__.py
│   └── ClientManager.py      # Client operations based on https://docs.clockify.me/#tag/Client
├── TasksAccessRestriction/    # Core access management
│   ├── __init__.py
│   └── TasksAccessManager.py # Main access logic
├── Utils/                     # Centralized utilities
│   ├── __init__.py
│   ├── export_data.py        # Data export (JSON/CSV)
│   ├── logging.py           # Structured logging
│   ├── auth.py              # Authentication & validation
│   ├── api_client.py        # Centralized API communication
│   └── file_utils.py        # File operations
├── Config/                   # Configuration management
│   ├── __init__.py
│   └── settings.py          # Configuration settings
├── Tasks/                    # Task operations
│   ├── __init__.py
│   └── Tasks.py             # Task management
├── Users/                    # User & group management
│   ├── __init__.py
│   └── Users.py             # User operations
├── SomeClockifyApiTag/      # Template for new endpoints
│   ├── __init__.py
│   └── CodeName.py          # Template file
└── logs/                    # Generated log files
```

## 🎯 What the Application Does

### **Step 1: Grant Access to Authorized Tasks**
- Finds ALL projects in specified client (category) or processes all projects if no client specified
- Within each filtered project, finds authorized tasks:
  - NGS Reagents and Lab Operations Cost
  - ISP Reagents and Lab Operations Cost  
  - IMG Reagents and Lab Operations Cost
  - RepGen Dry operations
  - Pipeline Dry Operations
  - Contingencies
- Grants access to these specific tasks only to authorized users and groups

### **Step 2: Remove Access from Restricted Tasks**
- Searches filtered projects for restricted tasks:
  - NGS Dry Operations
  - ISP Dry Operations
  - IMG Dry Operations
  - PM Dry Operations
- Removes access to these specific tasks from restricted groups

### **Client-Based Filtering**
- Uses `--client-id` parameter to filter projects by specific client (category)
- If no client ID specified, processes all projects
- Leverages [Clockify Client API](https://docs.clockify.me/#tag/Client) for efficient filtering

## 🛠️ Using the Domain-Specific Modules

### **Projects Module (Projects/ProjectManager.py)**
```python
from Projects.ProjectManager import ProjectManager
from Utils.logging import Logger

logger = Logger()
project_manager = ProjectManager(logger)

# Get all projects and extract clients from them
all_projects = project_manager.get_all_projects()
clients = project_manager.extract_clients_from_projects(all_projects)

# Filter projects by client ID (category)
filtered_projects = project_manager.filter_projects_by_client_id(all_projects, "client_id")

# Get projects by client using API query parameter
api_filtered_projects = project_manager.get_projects_by_client_api("client_id")

# Get specific projects by name
target_projects = ["NGS Reagents and Lab Operations Cost", "ISP Reagents and Lab Operations Cost"]
found_projects = project_manager.get_projects_by_names(target_projects)

# Discover complete workspace structure
workspace_structure = project_manager.discover_workspace_structure()
print(f"Found {workspace_structure['statistics']['total_projects']} projects")
```

### **Clients Module (Clients/ClientManager.py)**
```python
from Clients.ClientManager import ClientManager
from Utils.logging import Logger

logger = Logger()
client_manager = ClientManager(logger)

# Get all clients (categories)
all_clients = client_manager.get_all_clients()

# Get specific client by ID or name
client = client_manager.get_client_by_id("client_id")
client = client_manager.get_client_by_name("Client Name")

# Get projects for specific client using API
projects = client_manager.get_projects_by_client_api("client_id")

# Filter projects by client ID
filtered_projects = client_manager.filter_projects_by_client_id(all_projects, "client_id")

# Get summary of clients with project counts
summary = client_manager.get_clients_summary()

# Discover complete client structure
client_structure = client_manager.discover_client_structure()
print(f"Found {client_structure['discovery_metadata']['total_clients']} clients")
```

## 🛠️ Using the Utils Modules

### **Logging (Utils/logging.py)**
```python
from Utils.logging import Logger

# Create logger
logger = Logger("my_module", console_output=True)
logger.create_log_file_for_session("my_session")

# Use different log levels
logger.info("Process started")
logger.warning("This is a warning")
logger.error("Error occurred")

# Specialized logging
logger.log_step("Data Processing", "START")
logger.log_api_request("GET", "/projects", 200)
logger.log_export("data.json", 150)
logger.log_access_operation("GRANT", "user123", True)
```

### **Data Export (Utils/export_data.py)**
```python
from Utils.export_data import DataExporter
from Utils.logging import Logger

logger = Logger()
exporter = DataExporter(logger)

# Export to both JSON and CSV
data = {"items": [{"id": 1, "name": "Project A"}]}
exporter.export_to_both_formats(data, "projects")

# Export multiple datasets
datasets = {
    "users": {"items": [...]},
    "projects": {"items": [...]}
}
exporter.export_multiple_datasets(datasets, "workspace_data")
```

### **Authentication & Configuration (Utils/auth.py)**
```python
from Utils.auth import AuthManager
from Utils.logging import Logger

logger = Logger()
auth_manager = AuthManager(logger)

# Validate configuration
if auth_manager.validate_configuration():
    print("Configuration is valid")

# Check if changes are approved
if auth_manager.is_changes_approved():
    print("Changes will be applied")
else:
    print("Running in dry-run mode")

# Get configuration summary
config = auth_manager.get_configuration_summary()
print(f"Config: {config}")
```

### **API Client (Utils/api_client.py)**
```python
from Utils.api_client import APIClient
from Utils.logging import Logger

logger = Logger()
api_client = APIClient(logger)

# Validate connection
if api_client.validate_connection():
    print("API connection successful")

# Get data using convenience methods
projects = api_client.get_projects()
users = api_client.get_users()
groups = api_client.get_user_groups()

# Make custom requests
endpoint = "/workspaces/workspace_id/custom-endpoint"
response = api_client.get(endpoint)
```

### **File Operations (Utils/file_utils.py)**
```python
from Utils.file_utils import FileUtils
from Utils.logging import Logger

logger = Logger()
file_utils = FileUtils(logger)

# JSON operations
data = {"key": "value"}
file_utils.write_json_file(data, "output.json")
loaded_data = file_utils.read_json_file("output.json")

# File management
backup_path = file_utils.create_backup("important_file.json")
file_utils.copy_file("source.txt", "destination.txt")

# Directory operations
files = file_utils.list_files_in_directory("data/", "*.json")
cleaned = file_utils.cleanup_old_files("logs/", "*.log", max_age_days=7)
```

## 🔧 Configuration Options

### **Environment Variables**
- `CLOCKIFY_API_KEY`: Your Clockify API key
- `CLOCKIFY_WORKSPACE_ID`: Your workspace ID
- `APPROVE_CHANGES`: Set to `true` to apply changes (default: `false`)
- `DEBUG`: Set to `true` for detailed logging (default: `true`)

### **Pagination Support**
All GET functions now support pagination to ensure complete data retrieval:

#### **Automatic Pagination**
Based on [Clockify API documentation](https://docs.clockify.me/), all list endpoints support pagination with:
- `page` parameter (default: 1)
- `page-size` parameter (default: 50, max: 5000)

Our implementation:
- **Automatically fetches ALL pages** by default
- Uses **maximum page size (5000)** for efficiency
- **Logs pagination progress** for transparency
- **Caches results** to avoid redundant API calls

#### **Supported Endpoints with Pagination**
- **Projects**: `get_projects()` - Gets all projects across all pages
- **Tasks**: `get_project_tasks()` - Gets all tasks for a project
- **Users**: `get_users()` - Gets all workspace users
- **User Groups**: `get_user_groups()` - Gets all user groups
- **Clients**: `get_clients()` - Gets all clients
- **Tags**: `get_tags()` - Gets all tags
- **Time Entries**: `get_time_entries()` - Gets all time entries
- **Custom Fields**: `get_custom_fields()` - Gets all custom fields

#### **Pagination Control**
```python
# Get all data (recommended - default behavior)
projects = api_client.get_projects(paginated=True)

# Get only first page (faster but incomplete)
projects = api_client.get_projects(paginated=False)

# Custom pagination with limits
projects = api_client.get_paginated_data("/projects", max_pages=5)

# Check pagination info without fetching all data
info = api_client.get_pagination_info("/workspaces/123/projects")
```

#### **Pagination Logging**
When pagination is active, you'll see logs like:
```
DEBUG: Starting paginated request for /workspaces/123/projects with page_size=5000
DEBUG: Page 1: fetched 5000 items (total: 5000)
DEBUG: Page 2: fetched 2543 items (total: 7543)
INFO: Paginated request complete: 7543 items from 2 pages
```

### **Safety Features**
- **Dry-run mode**: Default behavior, no changes applied
- **Comprehensive validation**: Environment, API, and configuration checks
- **Detailed logging**: All operations logged to files with timestamps
- **Data export**: All data exported before operations for review

## 📁 Output Files

All generated files are automatically organized in the **Export** folder for better file management:

### **File Structure**
```
clockify/
├── Export/                              # All generated files
│   ├── all_projects_YYYYMMDD_HHMMSS.json
│   ├── all_projects_YYYYMMDD_HHMMSS.csv
│   ├── all_categories_YYYYMMDD_HHMMSS.json
│   ├── all_categories_YYYYMMDD_HHMMSS.csv
│   ├── ext_ffs_projects_YYYYMMDD_HHMMSS.json
│   ├── ext_ffs_projects_YYYYMMDD_HHMMSS.csv
│   └── ... (other timestamped files)
├── logs/                               # Application logs
└── main.py                             # Main execution script
```

### **Generated File Types**

#### **Project Data Files**
- `all_projects_*.json/csv` - Complete list of all projects in workspace
- `all_clients_*.json/csv` - Extracted clients (categories) with project counts
- `projects_client_[CLIENT_ID]_*.json/csv` - Projects filtered by specific client ID
- `ext_ffs_projects_*.json/csv` - Target projects for access management

#### **Task Data Files**
- `all_authorized_tasks_*.json/csv` - Tasks that should have restricted access
- `target_project_tasks_*.json/csv` - Tasks from specific target projects
- `restricted_tasks_by_name_*.json/csv` - Tasks found by restricted name patterns
- `all_restricted_tasks_*.json/csv` - Combined restricted tasks data

#### **User Data Files**
- `authorized_users_*.json/csv` - Users who should have access
- `authorized_groups_*.json/csv` - Groups who should have access
- `restricted_users_*.json/csv` - Users whose access should be removed
- `restricted_groups_*.json/csv` - Groups whose access should be removed

#### **System Files**
- `workspace_structure_discovery_*.json` - Complete workspace analysis
- `client_structure_discovery_*.json` - Client system analysis (categories)

### **File Organization Benefits**
- ✅ **Centralized Location**: All exports in one folder
- ✅ **Timestamped Files**: Automatic versioning with YYYYMMDD_HHMMSS format
- ✅ **Multiple Formats**: Both JSON (detailed) and CSV (tabular) formats
- ✅ **Easy Cleanup**: Simple to archive or clean old files
- ✅ **Version Control**: Export folder excluded from git (see `.gitignore`)

### **File Management Commands**
```bash
# List all export files
ls -la Export/

# Find recent files (last 24 hours)
find Export/ -name "*.json" -mtime -1

# Clean old files (older than 30 days)
find Export/ -name "*.json" -mtime +30 -delete
find Export/ -name "*.csv" -mtime +30 -delete

# Archive exports by date
mkdir -p Archive/$(date +%Y-%m)
mv Export/*$(date +%Y%m%d)* Archive/$(date +%Y-%m)/
```

## 🎨 Extending the Application

### **Adding New API Endpoints**
1. Copy `SomeClockifyApiTag/` folder
2. Rename to match API tag (e.g., `Reports/`, `TimeEntries/`)
3. Update class names and endpoints
4. Use the Utils modules for consistency:
   ```python
   from Utils import Logger, DataExporter, APIClient
   
   class MyNewManager:
       def __init__(self):
           self.logger = Logger("my_manager")
           self.exporter = DataExporter(self.logger)
           self.api_client = APIClient(self.logger)
   ```

### **Creating Custom Utilities**
Add new utility modules to the `Utils/` folder:
```python
# Utils/my_custom_utils.py
from .logging import Logger

class MyCustomUtils:
    def __init__(self, logger=None):
        self.logger = logger or Logger()
    
    def my_custom_function(self):
        self.logger.info("Custom function executed")
```

Update `Utils/__init__.py`:
```python
from .my_custom_utils import MyCustomUtils
__all__ = [..., 'MyCustomUtils']
```

## 🔍 Troubleshooting

### **Configuration Issues**
```bash
# Check configuration
python -c "from Utils.auth import AuthManager; AuthManager().validate_configuration()"
```

### **API Connection Issues**
```bash
# Test API connection
python -c "from Utils.api_client import APIClient; APIClient().validate_connection()"
```

### **Common Issues**
1. **Missing environment variables**: Check `.env` file exists and has correct values
2. **API key invalid**: Verify API key in Clockify settings
3. **Workspace ID incorrect**: Check workspace ID in Clockify URL
4. **Permission errors**: Ensure API key has sufficient permissions
5. **Network issues**: Check internet connection and firewall settings

### **Debug Mode**
Set `DEBUG=true` in `.env` for detailed logging:
```env
DEBUG=true
```

## 📈 Best Practices

### **Development Workflow**
1. **Always run dry-run first** to review planned changes
2. **Check exported data files** before applying changes
3. **Review log files** for any warnings or errors
4. **Use version control** for configuration changes
5. **Test with small datasets** before full deployment

### **Code Organization**
- Use Utils modules for common functionality
- Keep business logic in domain-specific modules
- Implement proper error handling and logging
- Export data for audit trails
- Follow the established patterns

### **Production Deployment**
1. Test thoroughly in development environment
2. Backup existing configuration
3. Run with `APPROVE_CHANGES=false` first
4. Review all exported data
5. Monitor logs during execution
6. Have rollback plan ready

## 🆘 Support

For issues or questions:
1. Check the log files in `logs/` directory
2. Review exported data files
3. Verify configuration with validation methods
4. Check Clockify API documentation for endpoint changes

The Utils modules provide comprehensive logging and error handling to help diagnose issues quickly.

## 🎯 Demo Mode

### **Running the Demo**
The application now includes a demo mode to showcase the new domain-specific modules:

```bash
# Run the demo to see Projects and Clients modules in action
python main.py --demo
```

### **What the Demo Does**
1. **Projects Module Demo**:
   - Discovers all projects in the workspace
   - Extracts and categorizes all project categories
   - Generates comprehensive statistics
   - Exports all data for review

2. **Clients Module Demo**:
- Discovers all clients in the workspace (categories)
- Gets projects for each client using Clockify API
- Generates client summaries with project counts
   - Calculates totals and statistics

### **Demo Output**
The demo generates timestamped files:
- `workspace_structure_discovery_YYYYMMDD_HHMMSS.json/csv` - Complete workspace structure
- `client_structure_discovery_YYYYMMDD_HHMMSS.json/csv` - Complete client structure
- `all_projects_YYYYMMDD_HHMMSS.json/csv` - All projects data
- `all_categories_YYYYMMDD_HHMMSS.json/csv` - All project categories (legacy)
- `all_clients_YYYYMMDD_HHMMSS.json/csv` - All clients data
- `clients_summary_YYYYMMDD_HHMMSS.json/csv` - Client summaries with project counts

### **Example Usage**
```bash
# Run normal access management
python main.py

# Run demo to explore workspace structure
python main.py --demo

# Get help
python main.py --help
```

This demo mode is perfect for:
- Exploring your Clockify workspace structure
- Understanding project and client (category) organization
- Testing the new modules without affecting access permissions
- Generating comprehensive reports for analysis 