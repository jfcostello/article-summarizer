# utils/logging_utils.py
# This module provides utility functions for logging the status and duration of script executions
# to a Supabase database. These functions help in tracking the performance and identifying issues
# in the execution of various scripts in the system.

import json
from datetime import datetime, timezone
from utils.db_utils import get_supabase_client

def log_status(script_name, log_entries, status):
    """
    Logs the execution status and related messages for a given script to the Supabase database.
    
    Args:
        script_name (str): The name of the script whose status is being logged.
        log_entries (list): A list of log messages to be recorded.
        status (str): The overall status of the script execution (e.g., "Success", "Error").
    
    Returns:
        None
    """
    supabase = get_supabase_client()
    supabase.table("log_script_status").insert({
        "script_name": script_name,
        "log_entry": json.dumps(log_entries),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status
    }).execute()

def log_duration(script_name, start_time, end_time):
    """
    Logs the duration of the script execution to the Supabase database.
    
    Args:
        script_name (str): The name of the script whose execution duration is being logged.
        start_time (datetime): The start time of the script execution.
        end_time (datetime): The end time of the script execution.
    
    Returns:
        None
    """
    supabase = get_supabase_client()
    duration_seconds = (end_time - start_time).total_seconds()
    supabase.table("log_script_duration").insert({
        "script_name": script_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds
    }).execute()
