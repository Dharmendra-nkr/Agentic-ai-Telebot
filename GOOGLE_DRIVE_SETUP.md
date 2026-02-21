# 🔐 Google Drive Connection Setup Guide

## Quick Setup (5 minutes)

Follow these steps to connect your Google Drive account to the File Storage MCP.

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a Project"** at the top
3. Click **"NEW PROJECT"**
4. Enter project name: **"Agentic AI DW"**
5. Click **"CREATE"**
6. Wait for project creation (1-2 minutes)

---

## Step 2: Enable Google Drive API

1. In Google Cloud Console, search for **"Google Drive API"**
2. Click on it
3. Click **"ENABLE"**
4. Wait for it to enable

---

## Step 3: Create OAuth 2.0 Credentials

1. Go to **"Credentials"** (left sidebar)
2. Click **"+ CREATE CREDENTIALS"** at top
3. Choose **"OAuth client ID"**
4. If prompted, click **"CONFIGURE CONSENT SCREEN"** first:
   - Choose **"External"**
   - Fill in app name: **"Agentic AI Bot"**
   - Add your email
   - Click **"SAVE AND CONTINUE"** for each step
   - Skip optional sections
5. Back to credentials, click **"+ CREATE CREDENTIALS"** again
6. Choose **"OAuth client ID"**
7. Application type: **"Desktop application"**
8. Name: **"Agentic AI Desktop"**
9. Click **"CREATE"**

---

## Step 4: Download the Credentials File

1. Click the download icon (⬇️) next to your OAuth 2.0 credential
2. This downloads a JSON file
3. Rename it to: **`google_drive_credentials.json`**

---

## Step 5: Place Credentials in Your Project

1. In your project folder, create a **`credentials`** folder if it doesn't exist:
   ```
   Agentic_AI_DW/
   └── credentials/
   ```

2. Move the `google_drive_credentials.json` file there:
   ```
   Agentic_AI_DW/
   └── credentials/
       ├── nkrd_google_credentials.json (for Calendar)
       └── google_drive_credentials.json (for Drive - NEW!)
   ```

---

## Step 6: First Time Authentication

Run your bot/code once:
```bash
python main.py
```

1. A browser window will open asking you to **log in to Google**
2. Sign in with your Google account
3. Click **"Allow"** to give permission
4. The token will be saved automatically

That's it! ✅

---

## ✅ Verification

After setup, you should see in logs:
```
file_storage_drive_service_initialized
```

This means Google Drive is connected! 🎉

---

## 🧪 Test It

Once connected, try:
```
Bot: "Upload my test file"
```

You should get a Google Drive link!

---

## 🐛 Troubleshooting

### "file_storage_drive_initialization_failed"
- **Check**: Is `google_drive_credentials.json` in `credentials/` folder?
- **Check**: Did you enable Google Drive API?
- **Check**: Is credentials file valid JSON?

### "file_storage_no_valid_credentials"
- **Check**: File path is correct
- **Check**: You completed the authentication step
- **Try**: Delete the credentials file and redo authentication

### "Permission denied"
- **Check**: You allowed permissions in the browser
- **Check**: Your Google account has Drive access
- **Try**: Re-authenticate by deleting credentials and running again

---

## 📁 Final Setup Check

Your folder structure should look like:
```
Agentic_AI_DW/
├── mcps/
│   ├── file_storage_mcp.py
│   └── ...
├── agent/
│   └── ...
├── credentials/
│   ├── nkrd_google_credentials.json  ← Calendar credentials
│   └── google_drive_credentials.json  ← Drive credentials (NEW!)
├── storage/
│   └── files/  ← Files will be stored here
├── main.py
└── ...
```

---

## 🎯 What Happens Next

Once connected:
1. ✅ Files upload to your personal Google Drive
2. ✅ Shareable links are generated automatically
3. ✅ You can share files with others
4. ✅ All synced automatically

---

## 🔒 Security Notes

- ✅ Credentials stored **locally only**
- ✅ Never shared with anyone
- ✅ Can revoke access anytime from Google Account
- ✅ Token auto-refreshes when needed

---

## 💡 Tips

### To Revoke Access Anytime
1. Go to [Google Account](https://myaccount.google.com/)
2. Go to **"Security"** → **"Your connections to third-party apps"**
3. Find **"Agentic AI Desktop"**
4. Click and remove access

### To Switch Google Accounts
1. Delete the `credentials/google_drive_credentials.json` file
2. Run the bot again
3. Sign in with different account

### To Get a New Credentials File
1. Go back to Google Cloud Console
2. Create a new OAuth credential
3. Download and replace the file

---

## 📞 Need Help?

- **Stuck on authentication?** Check Step 6
- **Can't find Google Drive API?** Search for it by name
- **Credentials not working?** Re-run authentication from scratch
- **Check logs** for detailed error messages

---

## ✨ You're All Set!

Once `google_credentials.json` is in place, your bot can:
- 📤 Upload files
- 🔗 Generate links
- 👥 Share files
- 📋 Manage storage
- ❌ Delete files

**Ready?** Move on to using the File Storage MCP!

Start with the bot: **"Upload my file"** 🚀

---

**Setup Time**: ~5 minutes
**Difficulty**: Easy
**Status**: Ready when you complete the steps above
