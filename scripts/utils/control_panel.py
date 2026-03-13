#!/usr/bin/env python3
"""
Control Panel Class
Manages Google Sheet based configuration and status tracking for script execution.

This module provides a centralized way to:
- Read script execution commands from a Config sheet
- Update script status (IDLE, START, RUNNING, SUCCESS, FAILED)
- Log all status changes and execution details to a Log sheet
- Support multi-processing script execution
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging


class ScriptStatus(Enum):
    """Enum for valid script status values."""
    IDLE = "IDLE"
    START = "START"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ControlPanel:
    """
    Main control panel class for managing script execution via Google Sheets.
    
    This class handles:
    - Authentication with Google Sheets API
    - Reading script configurations from a Config sheet
    - Managing script status lifecycle
    - Logging execution details to a Log sheet
    
    Attributes:
        workbook: The gspread workbook object
        config_sheet: The Config worksheet with script definitions
        log_sheet: The Log worksheet for execution tracking
        logger: Python logger for local logging
    """
    
    def __init__(self, spreadsheet_name: str, credentials_path: str = "credentials.json", 
                 config_sheet_name: str = "Config", log_sheet_name: str = "Log"):
        """
        Initialize the Control Panel and authenticate with Google Sheets.
        
        Args:
            spreadsheet_name: Name of the Google Spreadsheet
            credentials_path: Path to the service account credentials JSON file
            config_sheet_name: Name of the Config worksheet
            log_sheet_name: Name of the Log worksheet
            
        Raises:
            FileNotFoundError: If credentials file is not found
            gspread.exceptions.SpreadsheetNotFound: If spreadsheet doesn't exist
        """
        self.spreadsheet_name = spreadsheet_name
        self.credentials_path = credentials_path
        self.config_sheet_name = config_sheet_name
        self.log_sheet_name = log_sheet_name
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Authenticate and initialize sheets
        self.client = self._authenticate()
        self.workbook = self._open_workbook()
        self.config_sheet = self._get_or_create_sheet(config_sheet_name, self._init_config_sheet)
        self.log_sheet = self._get_or_create_sheet(log_sheet_name, self._init_log_sheet)
        
        self.logger.info(f"✅ Control Panel initialized for spreadsheet: {spreadsheet_name}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup local Python logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _authenticate(self) -> gspread.Client:
        """
        Authenticate with Google Sheets API using service account credentials.
        
        Returns:
            Authenticated gspread client
            
        Raises:
            FileNotFoundError: If credentials file not found
        """
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}\n"
                "Please ensure credentials.json is in the project root."
            )
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.credentials_path, scope
        )
        client = gspread.authorize(creds)
        self.logger.info("🔗 Successfully authenticated with Google Sheets API")
        return client
    
    def _open_workbook(self) -> gspread.Spreadsheet:
        """
        Open the Google Spreadsheet.
        
        Returns:
            Spreadsheet object
            
        Raises:
            gspread.exceptions.SpreadsheetNotFound: If spreadsheet doesn't exist
        """
        try:
            workbook = self.client.open(self.spreadsheet_name)
            self.logger.info(f"📊 Opened spreadsheet: {self.spreadsheet_name}")
            return workbook
        except gspread.exceptions.SpreadsheetNotFound:
            raise gspread.exceptions.SpreadsheetNotFound(
                f"Could not find spreadsheet: {self.spreadsheet_name}\n"
                f"Make sure it exists and the service account has access."
            )
    
    def _get_or_create_sheet(self, sheet_name: str, init_func) -> gspread.Worksheet:
        """
        Get a worksheet or create it if it doesn't exist.
        
        Args:
            sheet_name: Name of the worksheet
            init_func: Function to call to initialize headers if creating new sheet
            
        Returns:
            Worksheet object
        """
        try:
            worksheet = self.workbook.worksheet(sheet_name)
            self.logger.info(f"📋 Accessed existing worksheet: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            self.logger.info(f"📋 Creating new worksheet: {sheet_name}")
            worksheet = self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=10)
            init_func(worksheet)
        
        return worksheet
    
    def _init_config_sheet(self, worksheet: gspread.Worksheet) -> None:
        """Initialize Config sheet with headers."""
        headers = ["Script Name", "Status", "Last Used", "Details", "Priority"]
        worksheet.append_row(headers)
        self.logger.info("   Config sheet initialized with headers")
    
    def _init_log_sheet(self, worksheet: gspread.Worksheet) -> None:
        """Initialize Log sheet with headers."""
        headers = ["Timestamp", "Script Name", "Status", "Message", "Details"]
        worksheet.append_row(headers)
        self.logger.info("   Log sheet initialized with headers")
    
    def get_script_status(self, script_name: str) -> Optional[ScriptStatus]:
        """
        Get the current status of a script from the Config sheet.
        
        Args:
            script_name: Name of the script
            
        Returns:
            ScriptStatus enum value or None if script not found
        """
        try:
            cell = self.config_sheet.find(script_name)
            status_cell = self.config_sheet.cell(cell.row, 2)  # Status is in column B
            
            try:
                return ScriptStatus(status_cell.value)
            except ValueError:
                self.logger.warning(
                    f"Invalid status '{status_cell.value}' for {script_name}. "
                    f"Valid values: {', '.join([s.value for s in ScriptStatus])}"
                )
                return None
        except gspread.exceptions.CellNotFound:
            return None
    
    def set_script_status(self, script_name: str, status: ScriptStatus, 
                          message: str = "", details: str = "") -> bool:
        """
        Update a script's status in the Config sheet and log the change.
        
        Args:
            script_name: Name of the script
            status: New ScriptStatus
            message: Optional message describing the status change
            details: Optional additional details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find script in config sheet
            cell = self.config_sheet.find(script_name)
            row = cell.row
            
            # Update status (column B)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.config_sheet.update_cell(row, 2, status.value)
            
            # Update "Last Used" (column C)
            self.config_sheet.update_cell(row, 3, timestamp)
            
            # Update "Details" (column D)
            if message:
                self.config_sheet.update_cell(row, 4, message)
            
            # Log the status change
            self._log_status_change(script_name, status, message, details)
            
            self.logger.info(
                f"✅ Updated {script_name} status to {status.value}"
                + (f" - {message}" if message else "")
            )
            return True
            
        except gspread.exceptions.CellNotFound:
            self.logger.error(f"❌ Script not found in Config sheet: {script_name}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error updating script status: {e}")
            return False
    
    def add_script_to_config(self, script_name: str, priority: int = 5) -> bool:
        """
        Add a new script entry to the Config sheet.
        
        Args:
            script_name: Name of the script
            priority: Priority level (1-10, default 5)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.config_sheet.append_row([
                script_name,
                ScriptStatus.IDLE.value,
                timestamp,
                "Newly added",
                priority
            ])
            self.logger.info(f"✅ Added script to Config sheet: {script_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error adding script: {e}")
            return False
    
    def get_scripts_to_run(self) -> List[str]:
        """
        Get all scripts with START status that need to run.
        
        Returns:
            List of script names with START status
        """
        try:
            records = self.config_sheet.get_all_records()
            scripts_to_run = [
                record["Script Name"] 
                for record in records 
                if record.get("Status") == ScriptStatus.START.value
            ]
            return scripts_to_run
        except Exception as e:
            self.logger.error(f"❌ Error retrieving scripts to run: {e}")
            return []
    
    def log_execution(self, script_name: str, status: ScriptStatus, 
                     message: str = "", details: str = "") -> bool:
        """
        Log an execution event to the Log sheet. Can be used independently or called 
        throughout script execution for detailed tracking.
        
        Args:
            script_name: Name of the script
            status: Execution status
            message: Human-readable message about execution
            details: Additional technical details
            
        Returns:
            True if successful, False otherwise
        """
        return self._log_status_change(script_name, status, message, details)
    
    def _log_status_change(self, script_name: str, status: ScriptStatus, 
                          message: str = "", details: str = "") -> bool:
        """
        Internal method to log status changes to the Log sheet.
        
        Args:
            script_name: Name of the script
            status: ScriptStatus
            message: Status message
            details: Additional details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_sheet.append_row([
                timestamp,
                script_name,
                status.value,
                message,
                details
            ])
            return True
        except Exception as e:
            self.logger.error(f"❌ Error logging to Log sheet: {e}")
            return False
    
    def execute_script_lifecycle(self, script_name: str, execution_func) -> bool:
        """
        Execute a complete script lifecycle: START → RUNNING → SUCCESS/FAILED.
        
        This method handles the full workflow for a script execution by:
        1. Setting status to RUNNING
        2. Executing the provided function
        3. Setting status to SUCCESS or FAILED based on result
        
        Args:
            script_name: Name of the script to execute
            execution_func: Callable that executes the actual script logic.
                          Should return (success: bool, message: str, details: str)
            
        Returns:
            True if script executed successfully, False otherwise
        """
        try:
            # Update to RUNNING
            self.set_script_status(script_name, ScriptStatus.RUNNING, 
                                  "Script execution started")
            
            # Execute the script
            success, message, details = execution_func()
            
            # Update final status
            if success:
                self.set_script_status(script_name, ScriptStatus.SUCCESS, 
                                      message or "Execution completed successfully", 
                                      details)
                self.logger.info(f"✅ {script_name} execution completed successfully")
            else:
                self.set_script_status(script_name, ScriptStatus.FAILED, 
                                      message or "Execution failed", 
                                      details)
                self.logger.error(f"❌ {script_name} execution failed")
            
            return success
            
        except Exception as e:
            self.set_script_status(script_name, ScriptStatus.FAILED, 
                                  "Unexpected error during execution", 
                                  str(e))
            self.logger.error(f"❌ Unexpected error in {script_name}: {e}")
            return False
    
    def get_all_scripts(self) -> List[Dict[str, str]]:
        """
        Get all scripts from the Config sheet.
        
        Returns:
            List of dictionaries with script information
        """
        try:
            records = self.config_sheet.get_all_records()
            return records
        except Exception as e:
            self.logger.error(f"❌ Error retrieving all scripts: {e}")
            return []
    
    def reset_all_to_idle(self) -> bool:
        """
        Reset all scripts in Config sheet to IDLE status.
        Useful for system recovery or batch operations.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            records = self.config_sheet.get_all_records()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for i, record in enumerate(records, start=2):  # Start at row 2 (skip header)
                if record.get("Script Name"):
                    self.config_sheet.update_cell(i, 2, ScriptStatus.IDLE.value)
                    self.config_sheet.update_cell(i, 3, timestamp)
            
            self.logger.info("✅ Reset all scripts to IDLE status")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error resetting scripts: {e}")
            return False
