# File Storage MCP Documentation

## Overview

The **File Storage MCP** provides seamless file upload and management capabilities, allowing the bot to accept documents from users, store them securely, and generate shareable Google Drive links.

## Features

- ✅ **Upload Files**: Upload local files to Google Drive
- ✅ **List Files**: View all stored files
- ✅ **Delete Files**: Remove files from storage
- ✅ **Get Links**: Generate shareable Google Drive links
- ✅ **Share Files**: Share files with specific users via email

## Installation

The File Storage MCP is automatically initialized when the agent starts. It imports:

```python
from mcps.file_storage_mcp import FileStorageMCP, FileStorageInput
```

## API Reference

### Actions

#### 1. **upload**
Upload a file to Google Drive.

**Parameters:**
- `file_path` (required): Local path to the file
- `file_name` (optional): Name for the file in storage (defaults to original filename)
- `folder_id` (optional): Google Drive folder ID for organization

**Example:**
```json
{
  "action": "upload",
  "file_path": "C:\\Documents\\report.pdf",
  "file_name": "Q1_Report.pdf"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "drive_file_123_456789",
    "file_name": "Q1_Report.pdf",
    "file_size": 2048576,
    "drive_link": "https://drive.google.com/file/d/drive_file_123_456789/view"
  },
  "message": "File 'Q1_Report.pdf' uploaded successfully"
}
```

#### 2. **list**
List all files in storage.

**Parameters:**
- None required

**Example:**
```json
{
  "action": "list"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "file_name": "report.pdf",
        "file_size": 1024576,
        "modified": "2024-01-15T10:30:00"
      }
    ],
    "count": 1
  },
  "message": "Found 1 files in storage"
}
```

#### 3. **delete**
Delete a file from storage.

**Parameters:**
- `file_id` (required): Google Drive file ID

**Example:**
```json
{
  "action": "delete",
  "file_id": "drive_file_123_456789"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "deleted_count": 1
  },
  "message": "Deleted 1 file(s)"
}
```

#### 4. **get_link**
Generate a shareable Google Drive link.

**Parameters:**
- `file_id` (required): Google Drive file ID

**Example:**
```json
{
  "action": "get_link",
  "file_id": "drive_file_123_456789"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "drive_file_123_456789",
    "drive_link": "https://drive.google.com/file/d/drive_file_123_456789/view"
  },
  "message": "Drive link: https://drive.google.com/file/d/drive_file_123_456789/view"
}
```

#### 5. **share**
Share a file with another user.

**Parameters:**
- `file_id` (required): Google Drive file ID
- `share_with` (required): Email address to share with
- `access_level` (optional): "viewer", "commenter", or "editor" (defaults to "viewer")

**Example:**
```json
{
  "action": "share",
  "file_id": "drive_file_123_456789",
  "share_with": "colleague@example.com",
  "access_level": "editor"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "drive_file_123_456789",
    "shared_with": "colleague@example.com",
    "access_level": "editor"
  },
  "message": "File shared with colleague@example.com"
}
```

## User Interaction Examples

### Example 1: Upload a Resume
```
User: "Upload my resume to Google Drive"
Bot: "I can help you upload your resume. What's the path to your resume file?"
User: "It's at C:\Users\John\Documents\resume.pdf"
Bot: "✅ Done! I've uploaded your resume to Google Drive.
      Here's the shareable link: https://drive.google.com/file/d/[file_id]/view"
```

### Example 2: Share a Document
```
User: "Share the project proposal with sarah@company.com"
Bot: "I'll share the project proposal with sarah@company.com. 
     Should she be able to view only, comment, or edit the document?"
User: "She can edit it"
Bot: "✅ Done! The project proposal is now shared with Sarah as an editor."
```

### Example 3: List Uploaded Files
```
User: "Show me what files I've uploaded"
Bot: "Here are your uploaded files:
      1. resume.pdf (2.1 MB) - modified Jan 15
      2. portfolio.zip (15.3 MB) - modified Jan 12
      3. cover_letter.docx (850 KB) - modified Jan 10"
```

## Configuration

### Storage Directory
Files are stored locally in: `storage/files/`

The directory structure:
```
storage/
├── files/
│   ├── drive_file_123_456789_resume.pdf
│   ├── drive_file_123_456790_portfolio.zip
│   └── ...
```

### Google Drive Integration

For full Google Drive integration:

1. **Ensure credentials are configured:**
   ```python
   credentials_file = "credentials/google_credentials.json"
   ```

2. **The MCP will automatically:**
   - Load existing credentials
   - Refresh expired tokens
   - Create shareable links

## Error Handling

The File Storage MCP includes robust error handling:

### File Not Found
```json
{
  "status": "failure",
  "message": "File not found: C:\\path\\to\\missing.pdf",
  "error": "File not found"
}
```

### Missing Required Parameters
```json
{
  "status": "failure",
  "message": "File path is required",
  "error": "Missing file_path"
}
```

### Upload Errors
```json
{
  "status": "failure",
  "message": "Failed to upload file",
  "error": "Permission denied or disk space exceeded"
}
```

## Logging

All file operations are logged with:
- User ID
- File name and size
- Operation type
- Timestamps
- Errors (if any)

Example log entries:
```
file_storage_uploaded - user_id=123, file_name=resume.pdf, file_id=drive_file_123, file_size=2048
file_storage_deleted - user_id=123, file_id=drive_file_123
file_storage_shared - user_id=123, file_id=drive_file_456, share_with=colleague@example.com
```

## Security Considerations

1. **Access Control**: Each user's files are tracked by user_id
2. **Local Storage**: Files are stored locally with unique identifiers
3. **Sharing Permissions**: Granular control over access levels (viewer, commenter, editor)
4. **Credentials Management**: Google credentials are kept separate in `credentials/` directory

## Integration with Agent

The File Storage MCP is integrated into the agent's executor and can be triggered through:

1. **Natural language**: "Upload my file", "Share this document"
2. **Direct API calls**: Using `FileStorageInput` parameters
3. **Planner suggestions**: Automatically recommended when file operations are needed

## Capabilities

The MCP registers the following capabilities:

| Capability | Description | Parameters |
|------------|-------------|-----------|
| `upload` | Upload a file to Google Drive | `file_path`, `file_name`, `folder_id` |
| `list` | List files in storage | None |
| `delete` | Delete a file | `file_id` |
| `get_link` | Get shareable link | `file_id` |
| `share` | Share with user | `file_id`, `share_with`, `access_level` |

## Future Enhancements

Planned features for future versions:

- [ ] Folder organization and management
- [ ] File versioning and history
- [ ] Document scanning and OCR
- [ ] File preview in chat
- [ ] Automatic file organization by date/type
- [ ] Storage quota management
- [ ] File search and filtering
- [ ] Bulk operations

## Troubleshooting

### Google Drive Service Not Initializing

**Problem**: "file_storage_drive_initialization_failed"

**Solution**: 
1. Check that Google credentials are properly configured
2. Verify the credentials file exists at `credentials/google_credentials.json`
3. Ensure Google Drive API is enabled in your Google Cloud project

### Files Not Found After Upload

**Problem**: Uploaded files can't be listed or retrieved

**Solution**:
1. Check that the local storage directory exists: `storage/files/`
2. Verify file permissions on the storage directory
3. Check available disk space

### Permission Denied When Sharing

**Problem**: Unable to share files with specific users

**Solution**:
1. Verify the email address is correct
2. Ensure the user has a valid Google account
3. Check your Google Drive sharing settings

---

**Last Updated**: January 2024
**Version**: 1.0.0
