"""
This module is designed to fetch financial data for specified stock symbols from the AlphaVantage API,
process this data, and insert it into a PostgreSQL database. It demonstrates the use of environment variables
for configuration, making HTTP requests to an external API, handling JSON data, and interacting with a PostgreSQL
database using psycopg2.

The script fetches daily stock data for a predefined list of symbols over a specified number of days.
It processes the raw JSON data from the API to extract relevant financial information and inserts this
information into the database, avoiding duplicates through the use of PostgreSQL's ON CONFLICT clause.

Requirements:
- An AlphaVantage API key set as an environment variable (ALPHAVANTAGE_API_KEY).
- PostgreSQL database credentials set as environment variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD).

Usage:
The script can be run from the command line with an optional integer argument specifying the number of days
to fetch data for. If no argument is provided, it defaults to 14 days.

Example:
    python get_raw_data.py 30

This will fetch and process the last 30 days of financial data for the specified stock symbols.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values

# Load the API key from an environment variable
API_KEY = os.getenv('ALPHAVANTAGE_API_KEY')
if not API_KEY:
    message = """
    Please set the 'ALPHAVANTAGE_API_KEY' environment variable with your Alpha Vantage API key.
    If you do not have an API key, you can obtain one for free by signing up at https://www.alphavantage.co/support/#api-key.
    Once you have your API key, you can set it as an environment variable using the command:

    For Windows: set ALPHAVANTAGE_API_KEY=your_api_key_here
    For Unix/Linux/MacOS: export ALPHAVANTAGE_API_KEY=your_api_key_here
    """
    raise ValueError(message)

# PostgreSQL database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'fin_data')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# Define the base URL for the AlphaVantage API
BASE_URL = 'https://www.alphavantage.co/query'

# Function to fetch and process stock data
def fetch_stock_data(symbol: str, days: int) -> list:
    """
    Fetches and processes daily stock data for a given symbol from the AlphaVantage API over a specified number of days.

    This function sends a request to the AlphaVantage API to retrieve daily time series data for the specified stock symbol.
    It then processes this data to include only the relevant days as specified by the 'days' parameter, filtering out older data.
    The data is returned as a list of dictionaries, each representing one day's data including the open price, close price, and volume.

    Parameters:
    - symbol (str): The stock symbol for which to fetch data (e.g., 'IBM', 'AAPL').
    - days (int): The number of days from the current date for which to fetch and process stock data.

    Returns:
    - list: A list of dictionaries, where each dictionary contains the stock symbol, date, open price, close price, and volume
      for one day. The list includes data for the number of days specified, up to the current date.

    Raises:
    - HTTPError: If the request to the AlphaVantage API fails or returns an error response.
    """

    # Define the parameters for the API request to fetch daily time series data for the given stock symbol.
    # The 'outputsize' parameter is set to 'full' to retrieve as much historical data as possible.
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': API_KEY,
        'outputsize': 'full'
    }
    # Make the API request to AlphaVantage to retrieve the stock data.
    response = requests.get(BASE_URL, params=params)
    # Check the response status and raise an exception for any HTTP errors encountered.
    response.raise_for_status()
    # Convert the response data to JSON format for processing.
    data = response.json()
    # Extract the time series data from the JSON response. Default to an empty dict if not found.
    time_series = data.get('Time Series (Daily)', {})
    
    # Initialize a list to hold the processed stock data for the specified number of days.
    processed_data = []
    # Calculate today's date and the target start date based on the 'days' parameter.
    today = datetime.today()
    target_date = today - timedelta(days=days)
    
    # Iterate through the time series data, filtering for entries within the specified date range.
    for date_str, daily_data in time_series.items():
        # Convert the date string to a datetime object for comparison.
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Check if the date is within the desired range (from 'target_date' to 'today').
        if date_obj >= target_date and date_obj <= today:
            # Add the processed data to the list, including the stock symbol, date, and relevant financial metrics.
            processed_data.append({
                'symbol': symbol,                # The stock symbol for the data entry.
                'date': date_str,                # The date of the data entry.
                'open_price': daily_data['1. open'],  # The opening price for the stock on this date.
                'close_price': daily_data['4. close'], # The closing price for the stock on this date.
                'volume': daily_data['5. volume'],     # The trading volume for the stock on this date.
            })
    
    # Return the list of processed stock data entries for the specified date range.
    return processed_data

def insert_data_into_db(data: list):
    """
    Inserts financial data into the PostgreSQL database.

    This function takes a list of dictionaries, each representing financial data for a stock on a given date,
    and inserts each entry into the 'financial_data' table of the database. It uses the 'execute_values'
    method from psycopg2 to efficiently insert multiple rows at once. If a record with the same symbol
    and date already exists in the database, the ON CONFLICT clause ensures that the new data does not
    overwrite the existing data, thus avoiding duplicate entries.

    Parameters:
    - data (list): A list of dictionaries, where each dictionary contains the financial data for a stock symbol
      on a specific date. Each dictionary must have the keys 'symbol', 'date', 'open_price', 'close_price',
      and 'volume'.

    Example of a data entry:
    {
        'symbol': 'AAPL',
        'date': '2023-01-01',
        'open_price': '150.00',
        'close_price': '155.00',
        'volume': '100000'
    }

    Note: The database connection parameters (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) are assumed to be
    set in the environment or defined elsewhere in the code.

    The function does not return a value but will raise exceptions related to database operations,
    such as connection errors or issues with executing the insert operation.
    """
    
    # Define the SQL query for inserting stock data into the financial_data table.
    # The ON CONFLICT clause is utilized to prevent the insertion of duplicate records,
    # specifically for entries with the same symbol and date.
    insert_query = """
    INSERT INTO financial_data (symbol, date, open_price, close_price, volume)
    VALUES %s ON CONFLICT (symbol, date) DO NOTHING;
    """
    # This approach ensures data integrity and avoids errors related to primary key violations.

    # Convert the list of dictionaries (data) into a list of tuples.
    # Each tuple corresponds to a row of data to be inserted into the database.
    # This conversion is necessary because execute_values expects data in tuple format.
    data_tuples = [(d['symbol'], d['date'], d['open_price'], d['close_price'], d['volume']) for d in data]

    # Establish a connection to the PostgreSQL database using the connection parameters.
    # The 'with' statement ensures that the database connection is properly closed after execution,
    # which helps in managing database resources efficiently.
    with psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
    ) as conn:
        # Create a new database cursor for executing SQL commands.
        with conn.cursor() as cur:
            # Insert the data into the financial_data table using the execute_values function.
            # execute_values efficiently handles the bulk insertion of multiple records at once,
            # making it more performant than inserting each record individually.
            execute_values(cur, insert_query, data_tuples)

def main(days: int):
    """
    The main function to fetch and insert financial data for specified stock symbols.

    Iterates over a predefined list of stock symbols, fetching financial data for each symbol for the past 'days' days,
    then inserts this data into a PostgreSQL database.

    Parameters:
    - days (int): Number of days from today to fetch data for.

    Each step of the process is logged to the console.
    """
    for symbol in ['IBM', 'AAPL']:  # List of stock symbols to process.
        print(f"Fetching data for {symbol}")
        data = fetch_stock_data(symbol, days)  # Fetch stock data for the given symbol and date range.
        print(f"Inserting data for {symbol} of {days} days into the database")
        insert_data_into_db(data)  # Insert the fetched data into the database.
        print(f"Data insertion COMPLETE: {symbol}")

if __name__ == "__main__":
    # Set a default number of days if not provided as a command-line argument.
    days = 14  
    # Check for command-line arguments to override the default number of days.
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])  # Attempt to convert the first argument to an integer.
        except ValueError:  # Handle the case where the conversion fails.
            print("The provided argument must be an integer representing the number of days.")
            sys.exit(1)  # Exit the script with an error code.

    main(days)  # Execute the main function with the specified or default number of days.
