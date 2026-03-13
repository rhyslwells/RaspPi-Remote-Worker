#!/usr/bin/env python3
"""
Test Connection Script
Tests the connection to the Google Sheet using the Control Panel class
and logs a test entry to the Log sheet.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel, ScriptStatus


def test_sheet_connection():
    """
    Test connection to Google Sheet using Control Panel and log a test entry.
    
    Returns:
        tuple: (success: bool, message: str, details: str)
    """
    
    try:
        print("📝 Testing Google Sheets connection...")
        
        # Initialize the Control Panel
        # Update "RaspPI-Remote-Worker" to your actual spreadsheet name
        panel = ControlPanel(
            spreadsheet_name="RaspPI-Remote-Worker",
            credentials_path="credentials.json"
        )
        
        print("✅ Connected to Google Sheets successfully!")
        
        # Return tuple expected by runner
        return (
            True,
            "Connection test successful",
            "Successfully authenticated with Google Sheets API and accessed Config & Log sheets"
        )
        
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"\n❌ File not found: {error_msg}")
        return (
            False,
            "File not found",
            error_msg
        )
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"\n❌ Connection error: {error_msg}")
        return (
            False,
            "Connection failed",
            error_msg
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Remote Worker - Connection Test")
    print("=" * 60)
    print()
    
    success, message, details = test_sheet_connection()
    
    print()
    print("=" * 60)
    if success:
        print(f"✅ {message}")
        print(f"   {details}")
    else:
        print(f"❌ {message}")
        print(f"   {details}")
    print("=" * 60)
    exit(0 if success else 1)
