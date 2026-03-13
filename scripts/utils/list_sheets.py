#!/usr/bin/env python3
"""
List Available Sheets
Shows all spreadsheets accessible to your service account credentials.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os


def list_available_sheets():
    """List all spreadsheets accessible with the current credentials."""
    
    try:
        # Setup credentials
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_path = "credentials.json"
        if not os.path.exists(creds_path):
            raise FileNotFoundError("credentials.json not found in current directory")
        
        print("📝 Loading credentials...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        
        print("🔗 Authorizing with Google Sheets API...")
        client = gspread.authorize(creds)
        
        print("📊 Fetching accessible spreadsheets...\n")
        spreadsheets = client.openall()
        
        if not spreadsheets:
            print("❌ No spreadsheets found")
            print("   Make sure the service account has been shared access to your sheets\n")
            return
        
        print(f"✅ Found {len(spreadsheets)} spreadsheet(s):\n")
        for i, sheet in enumerate(spreadsheets, 1):
            print(f"   {i}. {sheet.title}")
            print(f"      ID: {sheet.id}")
        
        print("\n" + "=" * 60)
        print("👉 Copy the sheet name (the title) you want to use and")
        print("   update it in test_connection.py at line 37:")
        print("   sheet_name = \"<your_sheet_name>\"")
        print("=" * 60)
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("   Ensure credentials.json is in the project root")
        return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("📋 Remote Worker - List Available Sheets")
    print("=" * 60)
    print()
    
    list_available_sheets()
