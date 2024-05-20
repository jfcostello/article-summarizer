# utils/db_utils.py
# This module provides utility functions for interacting with the Supabase database.
# These functions handle common database operations such as fetching and updating data,
# ensuring a consistent and reusable approach across different scripts.

from supabase import create_client
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

def get_supabase_client():
    """
    Initialize and return a Supabase client using environment variables.
    This function ensures a single point of client creation, making it easier
    to manage and maintain the connection settings.
    
    Returns:
        Client: An instance of Supabase client.
    """
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    return create_client(url, key)

def fetch_table_data(table_name, filters=None, complex_filters=None, columns=None):
    """
    Fetch data from a specific table with optional filters and column selection.
    
    Args:
        table_name (str): The name of the table to fetch data from.
        filters (dict, optional): A dictionary of filters to apply to the query.
            Each key-value pair represents a column name and its desired value.
        complex_filters (str, optional): A complex filter string for more advanced queries.
        columns (list, optional): A list of columns to select from the table.
    
    Returns:
        list: A list of records matching the query filters, or an empty list if no records are found.
    """
    supabase = get_supabase_client()
    
    # Select specified columns or all columns if not provided
    if columns:
        query = supabase.table(table_name).select(", ".join(columns))
    else:
        query = supabase.table(table_name).select("*")
    
    # Apply filters to the query
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    # Apply complex filters to the query
    if complex_filters:
        query = query.or_(complex_filters)
    
    # Execute the query and return the results
    response = query.execute()
    return response.data if response.data else []

def fetch_feed_urls():
    """
    Fetch enabled RSS feed URLs from the 'rss_feed_list' table in Supabase.

    Returns:
        list: A list of enabled RSS feed URLs.
    """
    return fetch_table_data("rss_feed_list", {"isEnabled": 'TRUE'})

def update_table_data(table_name, data, condition):
    """
    Update data in a specific table based on a condition.
    
    Args:
        table_name (str): The name of the table to update.
        data (dict): A dictionary of column names and values to update.
        condition (tuple): A tuple representing the condition for the update.
            The first element is the column name, and the second element is the value to match.
    
    Returns:
        None
    """
    supabase = get_supabase_client()
    supabase.table(table_name).update(data).eq(condition[0], condition[1]).execute()
