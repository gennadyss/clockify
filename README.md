# Clockify Management Suite

Comprehensive management system for Clockify.app operations including task access restriction and expense management.

## 🎯 Objectives

### **Primary**: Task Access Restriction Management
Make bulk access restrictions for tasks across all projects in a specific client (category) for multiple groups.

**Note**: In Clockify web interface, **Clients are used as Categories** for organizing projects. This project uses the [Clockify Client API](https://docs.clockify.me/#tag/Client) to filter projects by client (category).

### **Secondary**: Expense Management
Comprehensive CSV-based expense upload and management with intelligent name-to-ID resolution for projects, tasks, and categories.

## 🔧 Core Features

### **1. Task Access Management**
- **Grant Access** to authorized users/groups for specific tasks
- **Remove Access** from restricted groups for sensitive tasks  
- **Bulk Operations** across multiple projects and tasks
- **Client-based Filtering** to target specific project categories

### **2. Expense Management**
- **CSV Upload** with intelligent parsing and validation
- **Name Resolution** for projects, tasks, categories, and users
- **Flexible Format Support** for different CSV structures
- **Dry Run Validation** to test before uploading
- **Bulk Processing** with chunked uploads for performance

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
│   └── settings.py            # Environment settings
├── Utils/                      # Shared utilities
│   ├── __init__.py
│   ├── api_client.py          # Enhanced Clockify API client with pagination
│   ├── auth.py                # Authentication management
│   ├── export_data.py         # Data export utilities
│   ├── file_utils.py          # File operations
│   └── logging.py             # Centralized logging
├── Tasks/                      # Task management
│   ├── __init__.py
│   └── Tasks.py               # Task operations with pagination
├── Users/                      # User management
│   ├── __init__.py
│   └── UserManager.py         # User/group operations with pagination
├── Groups/                     # Group management
│   ├── __init__.py
│   └── Groups.py              # Group operations and management
├── Projects/                   # Project management
│   ├── __init__.py
│   └── ProjectManager.py      # Project operations and client-based filtering
├── Clients/                    # Client management (Categories)
│   ├── __init__.py
│   └── ClientManager.py       # Client operations based on Clockify API
├── Expenses/                   # Expense management
│   ├── __init__.py
│   └── ExpenseManager.py      # Complete expense CRUD operations
├── UploadExpenses/             # CSV-based expense upload
│   ├── __init__.py
│   └── CSVExpenseUploader.py  # Intelligent CSV parsing and upload
├── TasksAccessRestriction/     # Main access management logic
│   ├── __init__.py
│   └── TasksAccessManager.py  # Core access restriction logic
├── Export/                     # Generated files (auto-created)
│   ├── expense_upload_*.json  # Expense upload results
│   ├── all_projects_*.json    # Project exports with timestamps
│   ├── validation_errors_*.csv # Upload validation errors
│   └── ... (other exports)    # All generated JSON/CSV files
├── logs/                       # Application logs (auto-created)
│   └── *.log                  # Timestamped log files
├── main.py                     # Main execution script with multiple processes
├── requirements.txt            # Python dependencies
├── env_template.txt            # Environment template
├── README.md                   # This file
└── USAGE.md                    # Detailed usage guide
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
CLOCKIFY_WORKSPACE_ID=your_workspace_id_here
APPROVE_CHANGES=false  # Set to true to apply changes (default: false for safety)
DEBUG=true            # Set to true for detailed logging
```

### **3. Usage Examples**

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

#### **Expense Upload**
```bash
# Generate CSV template
python main.py upload-expenses --generate-template

# Validate CSV without uploading (dry run)
python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv" --dry-run

# Upload expenses
python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv"

# Upload with default user email
python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv" --user-email "user@example.com"

# Custom chunk size for large files
python main.py upload-expenses --workspace-id "xyz789" --csv-file "expenses.csv" --chunk-size 25
```

#### **Module Demonstrations**
```bash
# Explore all modules and their capabilities
python main.py demo
```

## 📄 CSV Format Support

### **Expense Upload Formats**

#### **Format 1: Project/Task/Category Names**
```csv
Date,Project,Task,Amount,Category,user_email
6/1/2025,Repare.Schonhoft.PanCan.PBMC,NGS Reagents and Lab Operations Cost,1345.85,NGS Reagents,john@company.com
6/1/2025,LigoChem.Slocum.PanCan.TROP2,IMG Reagents and Lab Operations Cost,934.20,IMG Reagents,
```

#### **Format 2: Traditional Description-Based**
```csv
amount,description,date,project_name,category,billable,currency
25.50,Business lunch with client,2024-01-15,Project Alpha,Meals,Yes,USD
15.00,Taxi to office,2024-01-16,,Transportation,No,USD
```

### **Supported Columns**
- **Required**: `amount` + (`description` OR `project`+`task`+`category`)
- **Optional**: `date`, `project_id`, `project_name`, `category`, `billable`, `tags`, `currency`, `receipt`, `task_id`, `user_email`

### **Smart Features**
- **Name Resolution**: Automatically converts project/task/category names to IDs
- **Flexible Date Formats**: Supports multiple date patterns
- **Boolean Parsing**: "Yes/No", "True/False", "1/0" for billable field
- **Duplicate Column Handling**: Automatically renames duplicate columns
- **Validation**: Comprehensive error checking with detailed reports

## 🔧 Enhanced Features

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

- **All exports** automatically saved to `Export/` folder
- **All logs** automatically saved to `logs/` folder  
- **Timestamped filenames** for version tracking
- **Both JSON and CSV** formats for maximum compatibility
- **Validation error reports** exported for review and correction

## 🎯 Use Cases

1. **Bulk Task Access Management**: Manage permissions across hundreds of projects and tasks
2. **Expense Data Migration**: Import expenses from external systems via CSV
3. **Project Organization**: Analyze and reorganize project structures by client
4. **Compliance Reporting**: Generate audit trails for access control changes
5. **Data Integration**: Integrate Clockify with other business systems

## 📖 Additional Resources

- **USAGE.md**: Detailed usage guide with examples
- **Export/ folder**: Review generated reports and data exports
- **logs/ folder**: Monitor operation logs and troubleshoot issues
- **Clockify API docs**: https://docs.clockify.me/ for API reference