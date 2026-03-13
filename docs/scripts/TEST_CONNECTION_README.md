# Test Connection Script

## Purpose
This script tests your connection to the Google Sheet and validates that:
- ✅ Credentials are valid
- ✅ Google Sheets API is accessible
- ✅ You can read/write to the sheet
- ✅ The logging system works

## Setup

### Before Running
1. Ensure `credentials.json` is in your project root
2. Update the sheet name in the script:
   ```python
   sheet_name = "Your_Sheet_Name"  # Change this to your actual sheet name
   ```
3. (Optional) Create a "Log" sheet in your spreadsheet, or let the script create it

### Run the Test

**From project root:**
```bash
python scripts/test_connection.py
```

**Or directly:**
```bash
cd scripts
python test_connection.py
```

## Expected Output
```
============================================================
🧪 Remote Worker - Connection Test
============================================================

📝 Loading credentials...
🔗 Authorizing with Google Sheets API...
📊 Opening spreadsheet...
📋 Accessing Log sheet...
✍️  Appending log entry...

✅ Connection test SUCCESSFUL!
   Logged entry: 2025-03-12 14:30:45 | test_connection.py | SUCCESS
   Sheet: Your_Sheet_Name → Log sheet

============================================================
```

## What Gets Logged
Each successful test creates a row in your "Log" sheet with:
- **Timestamp**: When the script ran
- **Script**: Script name (test_connection.py)
- **Status**: SUCCESS or FAILED
- **Message**: Description of what happened
- **Details**: Additional debugging info

## Troubleshooting

### "credentials.json not found"
- Ensure credentials.json is in the project root
- Check file name spelling (case-sensitive on Unix systems)

### "Could not find spreadsheet"
- Verify you updated the sheet name in the script
- Confirm the service account has access to the sheet
- Try sharing the sheet with the service account email

### "Connection timeout"
- Check your internet connection
- Verify Google APIs aren't rate-limiting
- Wait a minute and retry

## Next Steps
Once this test passes, you can integrate logging into other scripts using the same pattern.
