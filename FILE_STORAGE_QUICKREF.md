# File Storage MCP - Quick Reference

## 🚀 Quick Start

### Import
```python
from mcps import FileStorageMCP, FileStorageInput

# Or from registry
from mcps import get_mcp
file_storage = get_mcp("FileStorageMCP")
```

### Basic Usage
```python
# Create input
input_data = FileStorageInput(
    action="upload",
    file_path="C:\\Documents\\file.pdf"
)

# Execute
result = await file_storage.execute(input_data, user_id=123)

# Check result
if result.status == MCPStatus.SUCCESS:
    file_id = result.data["file_id"]
    drive_link = result.data["drive_link"]
```

## 📋 Available Actions

### 1. Upload File
```python
FileStorageInput(
    action="upload",
    file_path="C:\\Documents\\resume.pdf",
    file_name="resume_2024.pdf"  # optional
)
```
**Returns**: file_id, file_name, file_size, drive_link

### 2. List Files
```python
FileStorageInput(action="list")
```
**Returns**: List of files with names, sizes, modification times

### 3. Delete File
```python
FileStorageInput(
    action="delete",
    file_id="drive_file_123_456"
)
```
**Returns**: deleted_count

### 4. Get Link
```python
FileStorageInput(
    action="get_link",
    file_id="drive_file_123_456"
)
```
**Returns**: file_id, drive_link

### 5. Share File
```python
FileStorageInput(
    action="share",
    file_id="drive_file_123_456",
    share_with="user@example.com",
    access_level="editor"  # viewer, commenter, editor
)
```
**Returns**: file_id, shared_with, access_level

## 🔧 Integration Points

### In Executor
```python
# In agent/executor.py
from mcps.file_storage_mcp import FileStorageMCP, FileStorageInput

class AgentExecutor:
    def __init__(self, db, scheduler=None):
        self.file_storage_mcp = FileStorageMCP()
        self.registry.register(self.file_storage_mcp)
    
    async def _execute_tool(self, tool_name, parameters, user_id):
        if tool_name == "FileStorageMCP":
            input_data = FileStorageInput(**parameters)
        # ... execute ...
```

### In Planner
```python
# Files are automatically suggested when:
# - User mentions "upload", "file", "document"
# - User asks to "share" something
# - User wants to "download" or "get link"

# The planner will create steps like:
{
    "step": 1,
    "action": "Upload file",
    "tool": "FileStorageMCP",
    "parameters": {
        "action": "upload",
        "file_path": "user_provided_path"
    }
}
```

## 📊 MCP Response Format

```python
MCPOutput(
    status=MCPStatus.SUCCESS,  # or FAILURE
    message="Human readable message",
    data={},  # Action-specific data
    error=None,  # If status=FAILURE
    metadata={  # Useful info for logging
        "file_id": "drive_file_...",
        "drive_link": "https://..."
    }
)
```

## 🛡️ Error Handling

```python
# Always check status
if result.status == MCPStatus.SUCCESS:
    # Use result.data
    pass
elif result.status == MCPStatus.FAILURE:
    # result.error contains error message
    logger.error(f"File storage error: {result.error}")
```

## 📁 File Paths

### Windows
- `C:\\Users\\Name\\Documents\\file.pdf`
- `D:\\Projects\\document.docx`
- `C:\\Desktop\\image.png`

### Mac/Linux
- `/Users/name/Documents/file.pdf`
- `/home/user/Projects/document.docx`
- `~/Desktop/image.png`

## 🎯 Use Cases

### Resume Sharing
```python
# Upload resume
upload = FileStorageInput(
    action="upload",
    file_path="C:\\Documents\\resume.pdf"
)

# Get link
link = FileStorageInput(
    action="get_link",
    file_id=result.data["file_id"]
)

# Share with company
share = FileStorageInput(
    action="share",
    file_id=result.data["file_id"],
    share_with="hr@company.com",
    access_level="viewer"
)
```

### Project Collaboration
```python
# Upload files
files = ["report.pdf", "data.xlsx", "presentation.pptx"]

# Share with team
for file_id in file_ids:
    share = FileStorageInput(
        action="share",
        file_id=file_id,
        share_with="team@company.com",
        access_level="editor"
    )
```

### File Management
```python
# List all files
list_op = FileStorageInput(action="list")

# Get links to all files
for file in result.data["files"]:
    link_op = FileStorageInput(
        action="get_link",
        file_id=file["file_id"]
    )

# Delete old files
delete_op = FileStorageInput(
    action="delete",
    file_id=old_file_id
)
```

## 🔍 Logging

All operations are logged:
```
file_storage_uploaded - user_id=123, file_name=resume.pdf
file_storage_shared - user_id=123, share_with=user@example.com
file_storage_deleted - user_id=123, file_id=...
file_storage_error - error=File not found
```

Check logs at: `logs/`

## 🧪 Testing

### Test Upload
```python
input_data = FileStorageInput(
    action="upload",
    file_path="test_file.txt"
)
result = await mcp.execute(input_data, user_id=1)
assert result.status == MCPStatus.SUCCESS
assert "file_id" in result.data
```

### Test List
```python
input_data = FileStorageInput(action="list")
result = await mcp.execute(input_data, user_id=1)
assert result.status == MCPStatus.SUCCESS
assert "files" in result.data
```

### Test Share
```python
input_data = FileStorageInput(
    action="share",
    file_id="drive_file_1_123",
    share_with="test@example.com",
    access_level="viewer"
)
result = await mcp.execute(input_data, user_id=1)
assert result.status == MCPStatus.SUCCESS
```

## 📚 Full Documentation

- **User Guide**: [FILE_STORAGE_INTEGRATION.md](FILE_STORAGE_INTEGRATION.md)
- **API Reference**: [FILE_STORAGE_MCP.md](FILE_STORAGE_MCP.md)
- **Implementation**: [FILE_STORAGE_IMPLEMENTATION.md](FILE_STORAGE_IMPLEMENTATION.md)

## 🎓 Key Classes

### FileStorageMCP
Main MCP class that handles all file operations
- `async execute(input_data, user_id)` - Execute action
- `get_capabilities()` - List available operations
- `get_description()` - Get MCP description

### FileStorageInput
Input validation using Pydantic
- `action` - Required: upload, list, delete, get_link, share
- `file_path` - For upload, local file path
- `file_name` - For upload, optional custom name
- `file_id` - For operations on existing files
- `share_with` - For share, email address
- `access_level` - For share, permission level

### MCPOutput
Response object from all operations
- `status` - SUCCESS or FAILURE
- `message` - Human readable message
- `data` - Operation results
- `error` - Error message if failed
- `metadata` - Additional info

## ⚙️ Configuration

### Credentials
Store at: `credentials/google_credentials.json`

### Storage
Local files stored at: `storage/files/`

### Logging
Check: `logs/` directory

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| File not found | Check file path and quotes |
| Permission denied | File in use, try closing it |
| Share failed | Verify email is valid |
| Drive not initialized | Check google_credentials.json |

## 💡 Tips

1. **Always check status**: `if result.status == MCPStatus.SUCCESS`
2. **Use relative paths**: Easier to handle in logs
3. **Validate file paths**: Check file exists before actions
4. **Batch operations**: Share multiple files at once
5. **Cache links**: Reuse links instead of regenerating

## 📞 Support

- Check logs for detailed errors
- Review FILE_STORAGE_MCP.md for API details
- See FILE_STORAGE_INTEGRATION.md for user examples
- Review FILE_STORAGE_IMPLEMENTATION.md for architecture

---

**Quick Reference v1.0**
Updated: January 2024
