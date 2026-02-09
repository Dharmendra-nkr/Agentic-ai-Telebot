# File Storage MCP - Integration Guide

## Quick Start

The File Storage MCP is now fully integrated with your Agentic AI bot! You can immediately start using it.

## How It Works

### Auto-Detection
When you send a message like:
- "Upload my report"
- "Save this file to Drive" 
- "Share the document with someone"
- "Show me my files"
- "Delete that old file"

The bot automatically:
1. **Recognizes** the file operation intent
2. **Asks** for any missing information (file path, recipient email, etc.)
3. **Executes** the operation using FileStorageMCP
4. **Returns** the result with shareable links or confirmations

### File Flow

```
User Message
    ↓
Agent Planner (detects file operation intent)
    ↓
Executor → FileStorageMCP
    ↓
Action: upload/list/delete/share/get_link
    ↓
Response with Drive link or confirmation
```

## Usage Examples

### 1. Upload a File

```
You: "Please upload my presentation.pptx from Desktop"
Bot: "I'll upload your presentation to Google Drive. Give me a moment..."
Bot: "✅ Done! Your presentation is now in Google Drive.
     Shareable link: https://drive.google.com/file/d/[id]/view"
```

### 2. List Your Files

```
You: "What files do I have uploaded?"
Bot: "You have 3 files uploaded:
      1. presentation.pptx (5.2 MB) - uploaded Jan 15
      2. report.pdf (2.1 MB) - uploaded Jan 14
      3. data.xlsx (1.8 MB) - uploaded Jan 12"
```

### 3. Share a File

```
You: "Share my report with john@company.com"
Bot: "I'll share your report with John. What access level?
      - View only (default)
      - Comment
      - Edit"
You: "Edit"
Bot: "✅ Done! The report is now shared with John as an editor."
```

### 4. Get a Shareable Link

```
You: "Give me a link to my data file"
Bot: "Here's the shareable link for your data:
      https://drive.google.com/file/d/[id]/view"
```

### 5. Delete a File

```
You: "Delete my old presentation"
Bot: "I found 'presentation.pptx' from Jan 15. 
      Are you sure you want to delete it?"
You: "Yes"
Bot: "✅ Deleted! The file has been removed from storage."
```

## File Path Examples

### On Windows
```
C:\Users\YourName\Documents\file.pdf
C:\Users\YourName\Desktop\presentation.pptx
```

### On Mac/Linux
```
/Users/YourName/Documents/file.pdf
/home/username/Desktop/presentation.pptx
```

## Features

| Feature | Status | Example |
|---------|--------|---------|
| Upload files | ✅ Ready | "Upload my resume" |
| List files | ✅ Ready | "Show me all files" |
| Delete files | ✅ Ready | "Delete old_file.pdf" |
| Get links | ✅ Ready | "Give me link to report" |
| Share files | ✅ Ready | "Share with john@email.com" |
| Google Drive sync | 🔄 In progress | Automatic sync |
| Folder organization | 📋 Planned | Coming soon |
| File preview | 📋 Planned | Coming soon |

## Behind the Scenes

### What Happens When You Upload

1. **User provides file path**: "C:\Documents\resume.pdf"
2. **MCP validates**: Checks file exists and is readable
3. **File is stored**: Copied to `storage/files/` with unique ID
4. **Google Drive link generated**: File ID creates shareable URL
5. **Response sent**: Links and confirmations returned to user

### Storage Structure

```
storage/
└── files/
    ├── drive_file_0_123_resume.pdf
    ├── drive_file_1_456_presentation.pptx
    └── drive_file_2_789_report.pdf
```

Each file gets a unique ID: `drive_file_{user_id}_{timestamp}_{filename}`

## Error Recovery

If something goes wrong:

```
You: "Upload my file"
Bot: "I found the file, but encountered an error during upload.
      This might be due to:
      - Network connectivity
      - Insufficient disk space
      - File permission issues
      
      Would you like me to try again?"
```

## Privacy & Security

- **Local Storage**: Files stored safely in `storage/files/`
- **User Isolation**: Each user's files are tracked separately
- **Sharing Control**: You decide who gets access and what level
- **No Auto-Share**: Files are never shared without your permission

## Tips & Tricks

### Organize by Naming
```
You: "Upload resume_2024_v2.pdf and call it resume_latest.pdf"
Bot: "Done! File saved as 'resume_latest.pdf' for easy access."
```

### Batch Share
```
You: "Share all my files with the team@company.com"
Bot: "I'll share all 3 of your files. What access level?"
```

### Get Links for All Files
```
You: "Give me links to everything I've uploaded"
Bot: "Here are your files and links:
      1. resume.pdf → [link]
      2. portfolio.zip → [link]
      3. cover_letter.docx → [link]"
```

## Troubleshooting

### "File not found"
- Check the file path is correct
- Verify the file exists on your system
- Use quotes if path has spaces: `"C:\My Documents\file.pdf"`

### "Permission denied"
- File might be open in another program
- You might not have read permissions
- Try closing the file and retrying

### "Share failed"
- Double-check the email address
- Ensure the email belongs to a valid Google account
- Try a different access level

## Developer Notes

### How It's Integrated

1. **Executor** (`agent/executor.py`):
   - Initializes FileStorageMCP
   - Registers with MCP registry
   - Routes file operations

2. **Planner** (`agent/planner.py`):
   - Detects file operation intents
   - Creates action steps for file operations
   - Provides context to the LLM

3. **Prompts** (`agent/prompts.py`):
   - Includes file storage examples
   - Guides LLM behavior for file operations
   - Provides few-shot examples

### Key Files

- `mcps/file_storage_mcp.py` - Main MCP implementation
- `mcps/__init__.py` - Exports FileStorageMCP
- `agent/executor.py` - Integration point
- `FILE_STORAGE_MCP.md` - Full documentation

## Next Steps

1. **Start using it**: Send file-related messages to the bot
2. **Test uploads**: Try uploading different file types
3. **Share files**: Use the share feature with colleagues
4. **Provide feedback**: Share feature requests or improvements

## Need Help?

- Check [FILE_STORAGE_MCP.md](FILE_STORAGE_MCP.md) for detailed API reference
- Review examples above for common use cases
- Check logs in `logs/` for detailed operation history

## What's Coming

Future versions will include:
- 📁 Folder organization
- 🔄 Automatic organization by file type/date
- 👀 File previews in chat
- 🔍 Search and filtering
- 📊 Storage quota management
- ⏱️ File versioning and rollback

---

**Ready to use!** Start uploading and sharing files now.
