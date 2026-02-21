"""
Google Drive Authentication Script
Run this once to authenticate your Google Drive account with the bot.
This uses separate credentials from Google Calendar.
"""

from mcps.file_storage_mcp import FileStorageMCP
from utils.logger import get_logger

logger = get_logger(__name__)


def authenticate_drive():
    """Authenticate Google Drive for file storage."""
    print("\n" + "=" * 60)
    print("  Google Drive Authentication for Agentic AI Telebot")
    print("=" * 60)

    mcp = FileStorageMCP()

    print("\n📋 Steps:")
    print("1. A browser window will open")
    print("2. Log in to your Google Drive account")
    print("3. Grant Drive file access permissions")
    print("4. Close the browser when done")
    print("\n" + "=" * 60)

    input("\nPress ENTER to start authentication...")

    try:
        success = mcp.authenticate()
        if success:
            print("\n✅ Google Drive authentication successful!")
            print(f"📁 Token saved to: {mcp.token_path}")
            print("\n🎉 You can now upload files and get Drive links!")
            return True
        else:
            print("\n❌ Authentication failed")
            print("Please check:")
            print("  - credentials/google_drive_credentials.json exists")
            print("  - Google Drive API is enabled in your GCP project")
            print("  - You granted all permissions")
            return False

    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        logger.error("drive_auth_script_error", error=str(e))
        return False


if __name__ == "__main__":
    success = authenticate_drive()

    if success:
        print("\n" + "=" * 60)
        print("✅ Google Drive Setup Complete!")
        print("=" * 60)
        print("\n📱 Next steps:")
        print("1. Make sure your bot is running (python main.py)")
        print("2. Send a document to your Telegram bot")
        print("3. Ask: 'store this file in drive'")
        print("4. Ask: 'give me the drive link'")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Google Drive Authentication Failed")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("  1. Ensure google_drive_credentials.json is in credentials/")
        print("  2. Enable Google Drive API at:")
        print("     https://console.cloud.google.com/apis/library/drive.googleapis.com")
        print("  3. Try running this script again")
        print("=" * 60)
