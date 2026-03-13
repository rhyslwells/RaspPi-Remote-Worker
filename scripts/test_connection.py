#!/usr/bin/env python3
"""
Test Connection Script
Tests the connection to the Google Sheet and logs a test entry to the Log sheet.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os


def test_sheet_connection():
    """Test connection to Google Sheet and log a test entry."""
    
    try:
        # Setup credentials
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get credentials file path (supports running from different directories)
        creds_path = "credentials.json"
        if not os.path.exists(creds_path):
            raise FileNotFoundError("credentials.json not found in current directory")
        
        print("📝 Loading credentials...")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        
        print("🔗 Authorizing with Google Sheets API...")
        client = gspread.authorize(creds)
        
        # Try to open the sheet
        print("📊 Opening spreadsheet...")
        sheet_name = "RaspPI-Remote-Worker"  # Your actual spreadsheet name
        workbook = client.open(sheet_name)
        
        # Get or create the Log sheet
        print("📋 Accessing Log sheet...")
        try:
            log_sheet = workbook.worksheet("Log")
        except gspread.exceptions.WorksheetNotFound:
            print("   ⚠️  Log sheet not found, creating one...")
            log_sheet = workbook.add_worksheet(title="Log", rows=1000, cols=5)
            # Add header row
            log_sheet.append_row(["Timestamp", "Script", "Status", "Message", "Details"])
        
        # Prepare log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        script_name = "test_connection.py"
        status = "SUCCESS"
        message = "Connection test successful"
        details = "Test entry from test_connection.py script"
        
        print("✍️  Appending log entry...")
        log_sheet.append_row([timestamp, script_name, status, message, details])
        
        print("\n✅ Connection test SUCCESSFUL!")
        print(f"   Logged entry: {timestamp} | {script_name} | {status}")
        print(f"   Spreadsheet: RaspPI-Remote-Worker → Log worksheet")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("   Ensure credentials.json is in the project root")
        return False
    
    except gspread.exceptions.SpreadsheetNotFound as e:
        print(f"\n❌ ERROR: Could not find spreadsheet")
        print(f"   Make sure 'Your_Sheet_Name' exists and the service account has access")
        print(f"   Details: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Remote Worker - Connection Test")
    print("=" * 60)
    print()
    
    success = test_sheet_connection()
    
    print()
    print("=" * 60)
    exit(0 if success else 1)
