# Financial Data API Service

## Project Description
This project provides a RESTful API service for retrieving financial data of specific stocks and calculating statistics over a given time range. It enables users to fetch historical financial data for IBM and Apple Inc. for the most recently two weeks and supports queries for financial data within specified date ranges, including pagination for result sets. Additionally, it offers an endpoint to calculate average daily open price, close price, and volume for a specified stock symbol and date range. For verification purposes, the original prompt from the fork source is preserved in the file `employer_reqs.md`.

## Tech Stack
- **Programming Language**: Python 3
- **Web Framework**: Flask
- **Database**: PostgreSQL
- **API**: AlphaVantage for financial data retrieval

## Libraries and API Choices

- **Requests**: Chosen for its simplicity and reliability for making HTTP requests in Python.
- **Flask**: As originally demanded. A lightweight web framework that is easy to use for creating RESTful APIs.
- **PostgreSQL**: Selected for its robustness, reliability, and support for complex queries.
- **Psycopg2**: A PostgreSQL adapter for Python, known for its performance and compatibility with PostgreSQL features.
- **AlphaVantage API**: As originally demanded. Provides reliable and up-to-date financial data, with a generous free tier for development purposes.

## Running the Code in a Local Environment
To run this project locally, follow these steps:

1. **Clone the Repository**: Clone this repository to your local machine.

2. **Install Dependencies**: Navigate to the project directory and install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Variables**: Set the `ALPHAVANTAGE_API_KEY` environment variable with your Alpha Vantage API key. For Linux and macOS:
    ```bash
    export ALPHAVANTAGE_API_KEY='your_api_key_here'
    ```
    For Windows:
    ```cmd
    set ALPHAVANTAGE_API_KEY=your_api_key_here
    ```
(Optional!) You may also create a `.env` file in the project root directory and add your Alpha Vantage API key:
    ```
    ALPHAVANTAGE_API_KEY=your_api_key_here
    ```
    This `.env` file will be used by Docker to set the environment variable in your containers.

4. **Docker Setup**: Ensure Docker and Docker Compose are installed on your local machine.

5. **Start Services**: From the project directory, start the PostgreSQL database and Flask application by running:
```bash
docker-compose up --build
```

This command builds the Docker images and starts the containers as defined in your `docker-compose.yml` and `Dockerfile`. The Flask application will be accessible at `http://localhost:5000/api/`.

6. **Initialize Data**: After the Docker containers are up and running, execute the `get_raw_data.py` script to fetch and insert the financial data into your database. This can be done in a separate terminal window. The example here inserts the data of IBM and Apple's financial data of the latest 500 days to the PostgresSQL inside its designated Docker container:
```bash
python get_raw_data.py 500
```
or, to default to 14 days if no parameter is given,
```bash
python get_raw_data.py
```

At the time of writing this README, I recommend using `python get_raw_data.py 500` as that ensures your database contains data that cover the sample requests/API uses in Step 7.

7. **Retrieve Data(Flask API)**: After the data is inserted to PostgresSQL, you may use respective CURL commands to look at the data.

For instance, to use the `financial_data` API:
```bash
curl -X GET 'http://localhost:5000/api/financial_data?start_date=2023-01-01&end_date=2023-01-14&symbol=IBM&limit=3&page=2'
```

Result should look something like this:
```json
{"data":[{"close_price":"143.70","date":"2023-01-06","id":432,"open_price":"142.38","symbol":"IBM","volume":3574042},{"close_price":"143.55","date":"2023-01-09","id":431,"open_price":"144.08","symbol":"IBM","volume":3987782},{"close_price":"144.80","date":"2023-01-10","id":430,"open_price":"143.61","symbol":"IBM","volume":2152172}],"info":{"error":null},"pagination":{"count":9,"limit":3,"page":2,"pages":3}}
```

Or, to use the `statistics` API:
```bash
curl -X GET 'http://localhost:5000/api/statistics?start_date=2023-01-01&end_date=2023-01-31&symbol=IBM'
```

Result should look something like this:
```json
{"data":{"average_daily_close_price":141.22,"average_daily_open_price":141.35,"average_daily_volume":5278800,"end_date":"2023-01-31","start_date":"2023-01-01","symbol":"IBM"},"info":{"error":null}}
```

## Maintaining the API Key
- **Local Development**: Store the AlphaVantage API key in your environment variables as described above in Step 3. This method keeps the key out of the source code in this project and can be easily changed without code modifications.
- **Production Environment**: For production deployments, use a more secure method of managing secrets, such as a secrets manager or environment variable management tools provided by your hosting service (e.g., AWS Secrets Manager, Azure Key Vault). Ensure the API key is never hardcoded in part of this project's source code or checked into version control.

Remember to replace the `your_api_key_here` in Step 3 with your actual AlphaVantage API key. For production environments, it's crucial to manage your API key securely to prevent unauthorized access to your AlphaVantage account.
