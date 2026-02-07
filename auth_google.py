"""
Google Calendar Authentication Script
Run this once to authenticate your Google account with the bot.
"""

from utils.google_calendar_helper import GoogleCalendarClient
from utils.logger import get_logger

logger = get_logger(__name__)

def authenticate_user(user_id: int):
    """
    Authenticate a user with Google Calendar.
    
    Args:
        user_id: Telegram user ID
    """
    print(f"\n🔐 Starting Google Calendar authentication for user {user_id}...")
    print("=" * 60)
    
    client = GoogleCalendarClient(user_id)
    
    print("\n📋 Steps:")
    print("1. A browser window will open")
    print("2. Log in to your Google account")
    print("3. Grant calendar permissions")
    print("4. Close the browser when done")
    print("\n" + "=" * 60)
    
    input("\nPress ENTER to start authentication...")
    
    try:
        if client.authenticate():
            print("\n✅ Authentication successful!")
            print(f"📁 Token saved to: {client.token_path}")
            print("\n🎉 You can now create events and they will sync to Google Calendar!")
            return True
        else:
            print("\n❌ Authentication failed")
            print("Please check:")
            print("  - credentials/google_credentials.json exists")
            print("  - Google Calendar API is enabled")
            print("  - You granted all permissions")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        logger.error("auth_script_error", error=str(e), user_id=user_id)
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Google Calendar Authentication for Agentic AI Telebot")
    print("=" * 60)
    
    # Get user ID from input
    user_id_input = input("\nEnter your Telegram User ID (e.g., 1852635471): ").strip()
    
    try:
        user_id = int(user_id_input)
    except ValueError:
        print("❌ Invalid user ID. Please enter a number.")
        exit(1)
    
    success = authenticate_user(user_id)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Setup Complete!")
        print("=" * 60)
        print("\n📱 Next steps:")
        print("1. Make sure your bot is running (python main.py)")
        print("2. Send a message in Telegram to create an event")
        print("3. Check your Google Calendar to verify sync")
        print("\nExample: 'Schedule a meeting tomorrow at 3 PM'")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Authentication Failed")
        print("=" * 60)
        print("\nPlease check the error messages above and try again.")
        print("See google_calendar_setup_guide.md for detailed instructions.")
