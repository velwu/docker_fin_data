"""
This module implements the Flask API for retrieving and calculating statistics on financial data.
It defines routes for fetching raw financial data, paginated financial data, and statistical calculations.

In the context of a Flask application, functions here serve as endpoint handlers and are invoked in response 
to web requests made to their associated routes. The Flask framework automatically handles the routing of 
HTTP requests to the correct function based on the URL and the request method (GET, POST, etc.).

The reason why functions here do not have input parameters in their declaration is because they are designed to 
interact with request data using Flask's global request object, rather than through direct function arguments. 
This design allows the function to access request data (such as query parameters, form data, and JSON payloads) 
in a standardized way, regardless of the specific details of each request.

The script is meant to be called via API requests (CURL being one of them) so direct python command is not applicable.
"""

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

app = Flask(__name__)

# Database connection parameters
DB_HOST = "db"
DB_NAME = "fin_data"
DB_USER = "user"
DB_PASSWORD = "password"

@app.route('/api/financial_data')
def get_financial_data():
    """
    Retrieves and returns paginated financial data for a specified stock symbol within a given date range.
    
    This endpoint accepts query parameters for start and end dates, stock symbol, pagination limit, and page number.
    It connects to a PostgreSQL database to fetch the relevant financial data, calculates pagination details,
    and formats the data for JSON response.
    
    Parameters:
    - start_date (str): The start date of the data range in 'YYYY-MM-DD' format.
    - end_date (str): The end date of the data range in 'YYYY-MM-DD' format.
    - symbol (str): The stock symbol to fetch data for.
    - limit (int): The number of records to return per page. Default is 5.
    - page (int): The page number to return. Default is 1.
    
    Returns:
    A JSON object containing:
    - data_list: A list holding all the queried data before pagination.
    - pagination: An object containing total number of records, current page number, number of records per page, and total pages available.
    - info: An object containing error information if any errors occurred during request processing.

    Sample request:
    curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-01-01&end_date=2023-01-14&symbol=IBM&limit=3&page=2'

    Sample response:
    {
        "data":[
            {"close_price":"143.70","date":"2023-01-06","id":432,"open_price":"142.38","symbol":"IBM","volume":3574042},
            {"close_price":"143.55","date":"2023-01-09","id":431,"open_price":"144.08","symbol":"IBM","volume":3987782},
            {"close_price":"144.80","date":"2023-01-10","id":430,"open_price":"143.61","symbol":"IBM","volume":2152172}
        ],
        "info":{"error":null},
        "pagination":{"count":9,"limit":3,"page":2,"pages":3}
    }
    """
    # Retrieve request parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    symbol = request.args.get('symbol')
    limit = request.args.get('limit', default=5, type=int)
    page = request.args.get('page', default=1, type=int)

    # Calculate offset for pagination. The offset determines where to start fetching the records from, 
    # based on the current page number and the number of records per page (limit). 
    # For example, if you're on page 2 and the limit is 5, the offset will be (2-1) * 5 = 5, 
    # meaning the query will skip the first 5 records and start fetching from the 6th record.
    offset = (page - 1) * limit

    # Initialize a list to hold conditions for the WHERE clause of the SQL query. 
    # This list will be dynamically populated based on the presence of query parameters.
    query_conditions = []

    # Initialize a list to hold the parameters for the SQL query that correspond to the conditions added to `query_conditions`.
    # This approach prevents SQL injection by ensuring that user inputs are parameterized.
    query_parameters = []

    # Check if a start date is provided and add it to the query conditions and parameters. 
    # This condition checks for records with a date greater than or equal to the specified start date.
    if start_date:
        query_conditions.append("date >= %s")
        query_parameters.append(start_date)

    # Similar to the start date, check if an end date is provided and add it to the query conditions and parameters. 
    # This condition checks for records with a date less than or equal to the specified end date.
    if end_date:
        query_conditions.append("date <= %s")
        query_parameters.append(end_date)

    # Check if a stock symbol is provided and add it to the query conditions and parameters. 
    # This condition filters the records for the specified stock symbol.
    if symbol:
        query_conditions.append("symbol = %s")
        query_parameters.append(symbol)

    # Combine the query conditions into a single WHERE clause. If no conditions are specified, a fallback of "1=1" is used, 
    # which is a tautology and effectively applies no filter, thus selecting all records.
    # The conditions are joined by " AND ", meaning all conditions must be met for a record to be included in the result.
    where_clause = " AND ".join(query_conditions) if query_conditions else "1=1"

    # Connect to the database
    with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Query to get the total count (without pagination)
            count_query = f"SELECT COUNT(*) FROM financial_data WHERE {where_clause};"
            cur.execute(count_query, query_parameters)
            total_count = cur.fetchone()[0]

            # Query to get the paginated data
            data_query = f"""
            SELECT * FROM financial_data
            WHERE {where_clause}
            ORDER BY date
            LIMIT %s OFFSET %s;
            """
            cur.execute(data_query, query_parameters + [limit, offset])
            data = cur.fetchall()

    # Calculate total pages
    total_pages = (total_count + limit - 1) // limit

    # Format data for JSON response
    data_list = []
    for row in data:
        formatted_row = dict(row)
        # Convert the 'date' field to the desired format 'YYYY-MM-DD'
        if 'date' in formatted_row and formatted_row['date']:
            formatted_date = formatted_row['date'].strftime('%Y-%m-%d')  # Directly format the date object
            formatted_row['date'] = formatted_date
        data_list.append(formatted_row)
    # Construct the response object to be returned to the client.
    # This object contains three main parts: data, pagination, and info.

    # 'data' holds the actual financial data fetched from the database,
    # formatted as a list of dictionaries where each dictionary represents a row of data.
    response = {
        "data": data_list,
        # 'pagination' provides details about the current state of pagination, helping clients navigate the paginated data.
        "pagination": {
            "count": total_count,  # The total number of records matching the query, before pagination.
            "page": page,          # The current page number.
            "limit": limit,        # The number of records per page.
            "pages": total_pages   # The total number of pages available, based on the count and limit.
        },
        # 'info' can include additional information about the request or the data.
        # Here, it's used to potentially convey error messages. In this case, it's set to None, indicating no errors.
        "info": {'error': None}
    }

    # Use jsonify to convert the response object into a Flask Response object with the JSON data,
    # setting the appropriate Content-Type header automatically.
    # This makes it suitable for returning from a Flask view function.
    return jsonify(response)

@app.route('/api/statistics')
def get_statistics():
    """
    Retrieves and calculates average daily open price, close price, and volume for a specified stock symbol 
    over a given date range.

    This endpoint requires query parameters for start date, end date, and stock symbol to perform the calculations. 
    It validates the input parameters for their presence and correctness (e.g., date format and logical consistency) 
    and checks if the requested stock symbol exists in the database. If validation passes, it queries the database 
    for the average values and returns them in the response.

    Parameters:
    - start_date (str): The start date for the calculation range in 'YYYY-MM-DD' format.
    - end_date (str): The end date for the calculation range in 'YYYY-MM-DD' format.
    - symbol (str): The stock symbol to calculate statistics for.

    Returns:
    A JSON object containing:
    - data: An object with the calculated average daily open price, close price, and volume, 
            along with the specified start date, end date, and symbol.
    - info: An object containing error information if any errors occurred during request processing.

    Sample request:
    curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-01-01&end_date=2023-01-31&symbol=IBM'

    Sample response:
    {
        "data":{"average_daily_close_price":141.22,"average_daily_open_price":141.35,"average_daily_volume":5278800,"end_date":"2023-01-31","start_date":"2023-01-01","symbol":"IBM"},
        "info":{"error":null}
    }
    
    Raises:
    - Returns a 400 error if required query parameters are missing or if date parameters do not conform to the expected format.
    - Returns a 404 error if the specified symbol is not found in the database.
    """
    # Retrieve request parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    symbol = request.args.get('symbol')

    # Validate required parameters
    if not all([start_date, end_date, symbol]):
        return jsonify({"data": {}, "info": {"error": "Missing required parameters: start_date, end_date, and symbol are all required."}}), 400
    
    # Validate date formats
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        if start_date_obj > end_date_obj:
            raise ValueError("start_date cannot be after end_date.")
    except ValueError as e:
        return jsonify({"data": {}, "info": {"error": f"Invalid date format or logic: {str(e)}"}}), 400
    
    # Validate symbol exists in database (Assuming a function check_symbol_exists(symbol) that returns True if exists)
    if not check_symbol_exists(symbol):
        return jsonify({"data": {}, "info": {"error": f"Symbol '{symbol}' not found in the database."}}), 404

    # Connect to the database
    # With block ensures that the connection is automatically closed after the block is executed
    with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Query to calculate statistics
            stats_query = """
            SELECT AVG(open_price::numeric) AS average_daily_open_price,
                   AVG(close_price::numeric) AS average_daily_close_price,
                   AVG(volume::numeric) AS average_daily_volume
            FROM financial_data
            WHERE symbol = %s AND date BETWEEN %s AND %s;
            """
            cur.execute(stats_query, (symbol, start_date, end_date))
            result = cur.fetchone()

    # Prepare the response data based on the query result
    if result:
        # 'data' contains the statistics calculated from the financial data.
        # Each field is rounded or cast to the appropriate type for consistency in the response.
        data = {
            "start_date": start_date,  # The start date of the range for which statistics were calculated.
            "end_date": end_date,      # The end date of the range for which statistics were calculated.
            "symbol": symbol,          # The stock symbol for which statistics were calculated.
            "average_daily_open_price": round(float(result['average_daily_open_price']), 2),  # The average opening price in the specified date range.
            "average_daily_close_price": round(float(result['average_daily_close_price']), 2),  # The average closing price in the specified date range.
            "average_daily_volume": int(result['average_daily_volume'])  # The average trading volume in the specified date range.
        }
        # 'info' is used to convey additional information or error messages related to the request.
        # Here, it indicates that the request was processed successfully with no errors.
        response = {"data": data, "info": {'error': None}}
    else:
        # In cases where no data is found for the given parameters, the 'data' field is empty,
        # and 'info' contains an error message indicating no data was found.
        response = {"data": {}, "info": {'error': 'No data found for the given parameters.'}}

    # The response is formatted as JSON, making it easy for clients to parse and use the data.
    return jsonify(response)

def check_symbol_exists(symbol):
    """
    This is a sanity-check function to make sure that a symbol exists in the database to prevent bad inquiries from increasing server load.
    """
    # With block ensures that the connection is automatically closed after the block is executed
    with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM financial_data WHERE symbol = %s)", (symbol,))
            return cur.fetchone()[0]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
