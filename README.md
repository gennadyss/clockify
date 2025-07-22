# Clockify Management Suite

Comprehensive management system for Clockify.app operations including task access restriction and expense management with CSV upload functionality.

## 🎯 Objectives

### **Primary**: CSV-Based Expense Management
**✅ FULLY IMPLEMENTED & TESTED** - Upload expenses to Clockify from CSV files with intelligent name-to-ID resolution, validation, and bulk processing capabilities.

### **Secondary**: Task Access Restriction Management
Make bulk access restrictions for tasks across all projects in a specific client (category) for multiple groups.

**Note**: In Clockify web interface, **Clients are used as Categories** for organizing projects. This project uses the [Clockify Client API](https://docs.clockify.me/#tag/Client) to filter projects by client (category).

## 🔧 Core Features

### **1. ✅ Expense Management (Production Ready)**
- **CSV Upload** with intelligent parsing and validation
- **Name Resolution** automatically converts project/task/category names to IDs
- **User Validation** ensures users exist in the workspace
- **Flexible Format Support** for different CSV structures
- **Dry Run Validation** to test before uploading
- **Bulk Processing** with chunked uploads for performance
- **Template Generation** creates sample CSV files
- **Environment Configuration** supports workspace ID from .env or parameters
- **Comprehensive Error Reporting** with detailed validation results

### **2. Task Access Management**
- **Grant Access** to authorized users/groups for specific tasks
- **Remove Access** from restricted groups for sensitive tasks  
- **Bulk Operations** across multiple projects and tasks
- **Client-based Filtering** to target specific project categories

### **3. Comprehensive Data Management**
- **Complete Pagination** support for all Clockify APIs
- **Robust Error Handling** with detailed logging
- **Data Export** in JSON and CSV formats
- **Validation and Auditing** for all operations

## 📋 Task Access Configuration

### **Step 1: Grant Access**
Give access to:
- **Role**: Admins
- **Users**: Ekaterina Postovalova, Lev Bedniagin, Alina Mulyukina, Anastasiya Terenteva, Tatiana Vasilyeva, Anastasiya Tarabarova, Lile Kontselidze, Alexandra Boiko
- **Group**: RPMHS.RPMG: Research Projects Management Group

For tasks:
- NGS Reagents and Lab Operations Cost
- ISP Reagents and Lab Operations Cost
- IMG Reagents and Lab Operations Cost
- RepGen Dry operations
- Pipeline Dry Operations
- Contingencies (including variants like "Contingencies (30%)")

### **Step 2: Remove Access**
Remove access from restricted groups:
- US.LAB.RND, US.LAB.CLIN, US.QAREG, US.HR
- Eric White, Artur Baisangurov, Tina Barsoumian
- US.LAB.RND.NGS, US.LAB.RND.ISP, US.LAB.RND.PATH
- US.LAB.CLIN.NGS, US.LAB.CLIN.PATH, US.LAB.RND.OP.BSP

For tasks:
- NGS Dry Operations
- ISP Dry Operations
- IMG Dry Operations
- PM Dry Operations

## 📊 Project Structure

```
clockify/
├── Config/                     # Configuration management
│   ├── __init__.py
│   └── settings.py            # Environment settings (.env support)
├── Utils/                      # Shared utilities
│   ├── __init__.py
│   ├── api_client.py          # Enhanced Clockify API client with multipart/form-data support
│   ├── auth.py                # Authentication management
│   ├── export_data.py         # Data export utilities
│   ├── file_utils.py          # File operations
│   └── logging.py             # Centralized logging
├── Expenses/                   # Expense management
│   ├── __init__.py
│   └── ExpenseManager.py      # Complete expense CRUD operations
├── UploadExpenses/             # CSV-based expense upload (FULLY FUNCTIONAL)
│   ├── __init__.py
│   ├── CSVExpenseUploader.py  # Intelligent CSV parsing and upload
│   └── Test_final_sheet_expenses.csv # Test data file
├── Tasks/                      # Task management
│   ├── __init__.py
│   └── Tasks.py               # Task operations with pagination
├── Users/                      # User management
│   ├── __init__.py
│   └── Users.py               # User operations with pagination
├── Groups/                     # Group management
│   ├── __init__.py
│   └── Groups.py              # Group operations and management
├── Projects/                   # Project management
│   ├── __init__.py
│   └── ProjectManager.py      # Project operations and client-based filtering
├── Clients/                    # Client management (Categories)
│   ├── __init__.py
│   └── ClientManager.py       # Client operations based on Clockify API
├── TasksAccessRestriction/     # Access management logic
│   ├── __init__.py
│   └── TasksAccessManager.py  # Core access restriction logic
├── SomeClockifyApiTag/         # Additional API functionality
│   ├── __init__.py
│   └── CodeName.py            # Extended API operations
├── Export/                     # Generated files (auto-created)
│   ├── all_projects_*.json    # Project exports with timestamps
│   ├── all_projects_*.csv     # Project data in CSV format
│   ├── validation_errors_*.csv # Upload validation errors (if any)
│   └── ... (other exports)    # All generated JSON/CSV files
├── logs/                       # Application logs (auto-created)
│   └── *.log                  # Timestamped log files
├── main.py                     # Main execution script (3 commands available)
├── requirements.txt            # Python dependencies
├── env_template.txt            # Environment template
├── README.md                   # This file
├── USAGE.md                    # Detailed usage guide
├── quick_check.py              # Quick testing utilities
├── check_project_tasks.py      # Project/task validation scripts
└── test_pagination.py          # API pagination testing
```

## 🚀 Quick Start

### **1. Installation**
```bash
# Clone repository
git clone <repository-url>
cd clockify

# Install dependencies
pip install -r requirements.txt
```

### **2. Configuration**
Create a `.env` file in the project root:

```bash
CLOCKIFY_API_KEY=your_api_key_here
CLOCKIFY_WORKSPACE_ID=your_workspace_id_here  # Optional for expense upload
APPROVE_CHANGES=false  # Set to true to apply changes (default: false for safety)
DEBUG=true            # Set to true for detailed logging
```

### **3. Usage Examples**

#### **✅ Expense Upload (Production Ready)**

**Note**: Workspace ID can be provided via `--workspace-id` parameter or configured in `.env` as `CLOCKIFY_WORKSPACE_ID`. Parameter takes precedence over environment.

```bash
# Generate CSV template with sample data
python main.py upload-expenses --generate-template

# Validate CSV without uploading (dry run) - uses workspace from .env
python main.py upload-expenses --csv-file "expenses.csv" --dry-run

# Upload expenses using workspace from .env
python main.py upload-expenses --csv-file "expenses.csv"

# Upload with explicit workspace ID (overrides .env)
python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv"

# Upload with default user email for expenses missing user info
python main.py upload-expenses --csv-file "expenses.csv" --user-email "user@example.com"

# Custom chunk size for large files
python main.py upload-expenses --csv-file "expenses.csv" --chunk-size 25
```

#### **Task Access Management**
```bash
# Dry run for all projects (recommended first)
python main.py tasks-access

# Filter by specific client ID (category)
python main.py tasks-access --client-id YOUR_CLIENT_ID

# Filter by client name
python main.py tasks-access --client-name "Client Name"

# Process specific project
python main.py tasks-access --project-id "abc123"
python main.py tasks-access --project-name "Project Name"
```

#### **Module Demonstrations**
```bash
# Explore all modules and their capabilities
python main.py demo
```

## 📄 CSV Format Support

### **✅ Current Working Format (Tested & Validated)**

The system generates and accepts this CSV format:

```csv
date,project,task,amount,category,user_email
6/1/2025,Repare.Schonhoft.PanCan.PBMC,NGS Reagents and Lab Operations Cost,1345.85,NGS Reagents,john.doe@company.com
6/1/2025,LigoChem.Slocum.PanCan.TROP2,IMG Reagents and Lab Operations Cost,934.2,IMG Reagents,
```

### **Supported Columns & Features**
- **Required**: `amount` + (`project`+`task`+`category` OR `description`)
- **Optional**: `date`, `project_id`, `project_name`, `category`, `billable`, `tags`, `currency`, `receipt`, `task_id`, `user_email`
- **Smart Name Resolution**: Automatically converts project/task/category names to Clockify IDs
- **Flexible Date Formats**: Supports multiple date patterns (MM/DD/YYYY, YYYY-MM-DD, etc.)
- **Boolean Parsing**: "Yes/No", "True/False", "1/0" for billable field
- **User Validation**: Ensures specified users exist in the workspace
- **Missing Data Handling**: Uses default user email when user_email column is empty

### **Template Generation**
Use `--generate-template` to create a properly formatted CSV with sample data:
```bash
python main.py upload-expenses --generate-template
```

## 🔧 Enhanced Features

### **✅ Production-Ready Expense Upload**
- **100% Success Rate**: Tested and working with real Clockify API
- **Intelligent Name Resolution**: Automatically resolves project, task, and category names to IDs
- **User Validation**: Verifies users exist in workspace before upload
- **Comprehensive Error Reporting**: Detailed validation with row-by-row error analysis
- **Dry Run Capability**: Test uploads without creating actual expenses
- **Template Generation**: Creates properly formatted CSV templates
- **Environment Integration**: Seamless .env configuration support

### **Complete Data Retrieval with Pagination**
Based on the [Clockify API documentation](https://docs.clockify.me/), all operations support pagination:

- **Automatic pagination** for all list endpoints
- **Maximum page size (5000)** for efficient data retrieval
- **Progress logging** to track pagination status
- **Complete data coverage** across all projects, tasks, users, and groups

### **Robust Error Handling**
- API connection validation
- Rate limit detection and handling
- Comprehensive error logging
- Graceful failure handling with detailed error reports

### **Data Export & Auditing**
- **JSON and CSV export** formats for all operations
- **Timestamped file names** for version tracking
- **Comprehensive data logging** for audit trails
- **Human-readable reports** for validation and review
- **Automatic export** to `Export/` folder

### **Intelligent Validation**
- **Dry run capability** for all operations
- **Detailed validation reports** with row-by-row error analysis
- **Name resolution verification** for all Clockify entities
- **Data format validation** with helpful error messages

## 🛡️ Safety Features

- **Dry run by default** for destructive operations
- **Human approval required** via `APPROVE_CHANGES` environment variable
- **Comprehensive logging** of all operations
- **Data export before changes** for rollback capability
- **Validation before execution** with detailed error reporting

## 📁 File Organization

- **All exports** automatically saved to `Export/` folder with timestamps
- **All logs** automatically saved to `logs/` folder  
- **Both JSON and CSV** formats for maximum compatibility
- **Validation error reports** exported for review and correction
- **Template generation** for easy CSV creation

## 🎯 Use Cases

1. **✅ Expense Data Upload**: Import expenses from external systems via CSV (Production Ready)
2. **Bulk Task Access Management**: Manage permissions across hundreds of projects and tasks
3. **Project Organization**: Analyze and reorganize project structures by client
4. **Compliance Reporting**: Generate audit trails for access control changes
5. **Data Integration**: Integrate Clockify with other business systems

## 📊 Dependencies

```
requests==2.31.0      # HTTP requests for Clockify API
python-dotenv==1.0.0  # Environment variable management
numpy==1.24.3         # Numerical operations
pandas==2.0.3         # CSV processing and data manipulation
```

## 📈 Success Metrics

### **✅ Expense Upload System**
- **100% Success Rate** in production testing
- **4/4 expenses** created successfully in recent tests
- **Full validation pipeline** working correctly
- **User verification** implemented and tested
- **Error handling** comprehensive and user-friendly

## 📖 Additional Resources

- **USAGE.md**: Detailed usage guide with examples
- **Export/ folder**: Review generated reports and data exports
- **logs/ folder**: Monitor operation logs and troubleshoot issues
- **Clockify API docs**: https://docs.clockify.me/ for API reference
- **Template Generation**: Use `--generate-template` for properly formatted CSV examples