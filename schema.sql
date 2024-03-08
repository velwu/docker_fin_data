CREATE TABLE IF NOT EXISTS financial_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price NUMERIC(10, 2) NOT NULL,
    close_price NUMERIC(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE(symbol, date)
);
