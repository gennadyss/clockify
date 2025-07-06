#project
That project for support Clockify.app.

##Objective
Make a bulk-access-restriction for tasks for all projects in a specific client (category) for several groups. 
Find all projects with a specific client ID.

**Note**: In Clockify web interface, **Clients are used as Categories** for organizing projects. This project uses the [Clockify Client API](https://docs.clockify.me/#tag/Client) to filter projects by client (category).

###First
Use Objective and give access only to:
- Role: Admins
- User name: Ekaterina Postovalova, Lev Bedniagin, Alina Mulyukina, Anastasiya Terenteva, Tatiana Vasilyeva, Anastasiya Tarabarova, Lile Kontselidze, Alexandra Boiko
- Group: RPMHS.RPMG: Research Projects Management Group

For every projects in specified client (category) add access to tasks:
-NGS Reagents and Lab Operations Cost
-ISP Reagents and Lab Operations Cost
-IMG Reagents and Lab Operations Cost
-RepGen Dry operations
-Pipeline Dry Operations
-Contingencies (other variant of the same task Contingencies (30%))

###Second
Use Objective and Remove access to tasks:
-NGS Dry Operations
-ISP Dry Operations
-IMG Dry Operations
-PM Dry Operations

From the groups:
US.LAB.RND
US.LAB.CLIN
US.QAREG
US.HR
Eric White
Artur Baisangurov
Tina Barsoumian
US.LAB.RND.NGS
US.LAB.RND.ISP
US.LAB.RND.PATH
US.LAB.CLIN.NGS
US.LAB.CLIN.PATH
US.LAB.RND.OP.BSP

Create for every step 

#
Description of project

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
│   └── Users.py               # User/group operations with pagination
├── Projects/                   # Project management
│   ├── __init__.py
│   └── ProjectManager.py      # Project operations and client-based filtering
├── Clients/                    # Client management (Categories)
│   ├── __init__.py
│   └── ClientManager.py       # Client operations based on https://docs.clockify.me/#tag/Client
├── TasksAccessRestriction/     # Main access management logic
│   ├── __init__.py
│   └── TasksAccessManager.py  # Core access restriction logic
├── Export/                     # Generated files (auto-created)
│   ├── all_projects_*.json    # Project exports with timestamps
│   ├── all_clients_*.csv      # Client exports (categories)
│   └── ... (other exports)    # All generated JSON/CSV files
├── logs/                       # Application logs (auto-created)
│   └── *.log                  # Timestamped log files
├── main.py                     # Main execution script
├── requirements.txt            # Python dependencies
├── env_template.txt            # Environment template
├── README.md                   # This file
└── USAGE.md                    # Detailed usage guide
```

### **File Organization**
- **All exports** automatically saved to `Export/` folder
- **All logs** automatically saved to `logs/` folder  
- **Timestamped filenames** for version tracking
- **Both JSON and CSV** formats for flexibility

## Configuration
### Environment Variables (.env) 

Download every intermediate data to json (for next code) and CSV (for human reading).
Don't change or upload data without approved by human. Add specific parameter.
Use SomeClockifyApiTag how template for all tag folders.  

## 🔧 Configuration

Create a `.env` file in the project root with your Clockify credentials:

```bash
CLOCKIFY_API_KEY=your_api_key_here
CLOCKIFY_WORKSPACE_ID=your_workspace_id_here
APPROVE_CHANGES=false  # Set to true to apply changes (default: false for safety)
DEBUG=true            # Set to true for detailed logging
```

## 🚀 Enhanced Features

### **Complete Data Retrieval with Pagination**
Based on the [Clockify API documentation](https://docs.clockify.me/), all GET functions now support pagination to ensure you get **ALL** your data, not just the first page:

- **Automatic pagination** for all list endpoints
- **Maximum page size (5000)** for efficient data retrieval
- **Progress logging** to track pagination status
- **Complete data coverage** across all projects, tasks, users, and groups

**Before**: Only first 50 items returned ❌  
**After**: ALL items retrieved automatically ✅

### **Robust Error Handling**
- API connection validation
- Rate limit detection
- Comprehensive error logging
- Graceful failure handling

### **Data Export & Auditing**
- JSON and CSV export formats
- Timestamped file names
- Comprehensive data logging
- Human-readable audit trails

## �� Project Structure