# Phase 1: Environment Setup

## Google Cloud Console Setup

1. **Enable APIs:**
   - Enable the **Google Sheets API**
   - Enable the **Google Drive API**

2. **Create Service Account:**
   - Create a Service Account in Google Cloud Console
   - Download the `credentials.json` file
   - **Important:** Store this securely and add to `.gitignore`

**Status:** ✅ Service account set up (credentials.json obtained)

**Next Steps:** Determine how to use credentials.json in the environment setup

## GitHub Repository Structure

Initialize a repository with the following structure:

```
/scripts/
  └── (Where your actual logic lives)

runner.py              (The main loop that talks to Google Sheets)
requirements.txt       (Include `gspread` and `oauth2client`)
.gitignore            (Crucial: ignore your `credentials.json`)
```

### Key Files:

- **`runner.py`** - Main service that:
  - Authenticates with Google
  - Polls the Google Sheet periodically
  - Checks for "START" flags
  - Executes corresponding scripts

- **`requirements.txt`** - Python dependencies:
  ```
  gspread
  oauth2client
  ```

- **`.gitignore`** - Must exclude:
  ```
  credentials.json
  .env
  __pycache__/
  *.pyc
  ```

