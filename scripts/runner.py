import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import subprocess

# 1. Setup the client
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# 2. Open the sheet
sheet = client.open("Your_Sheet_Name").sheet1

def run_task(script_name):
    print(f"Executing {script_name}...")
    # This runs your script as a subprocess
    result = subprocess.run(["python3", f"scripts/{script_name}"], capture_output=True, text=True)
    return result.stdout

while True:
    try:
        # Example: Column A is Script Name, Column B is "Run?" (TRUE/FALSE)
        records = sheet.get_all_records()
        
        for i, row in enumerate(records):
            if row['Run?'] == "TRUE":
                # Update status in Sheet so we don't loop infinitely
                sheet.update_cell(i + 2, 2, "RUNNING") 
                
                output = run_task(row['Script_Name'])
                
                # Reset to FALSE and log output/timestamp
                sheet.update_cell(i + 2, 2, "FALSE")
                sheet.update_cell(i + 2, 3, f"Last run: {time.ctime()}")
        
        time.sleep(10) # Poll every 10 seconds
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(30)