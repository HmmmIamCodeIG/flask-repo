# Stock data collection module for machine learning model training
# Goal: Fetch stock data from Yahoo Finance using user-provided ticker symbols
# This module handles all stock data retrieval and processing

import yfinance as yf
import datetime
import numpy as np
import pandas as pd

def get_stock_data(ticker, start_date, end_date):
    """
    fetch stock data for a given ticker symbol and date range.
    
    args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        start_date: Start date in format 'YYYY-MM-DD' 
        end_date: End date in format 'YYYY-MM-DD' 
    
    returns:
        dictionary containing all the stock_data. 
              Structure: {
                  'ticker': str,
                  'name': str,
                  'current_price': float,
                  'previous_close': float,
                  'market_cap': int,
                  'currency': str,
                  'summary': str,
                  'last_updated': str,
                  'historical_data': DataFrame
              }
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        ticker_data = stock.history(start=start_date, end=end_date)

        # compile all the stock data into a dictionary for easy access and future use in ML model training
        stock_data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName') or f"{ticker} Stock",
            'current_price': info.get('currentPrice'),
            'previous_close': info.get('regularMarketPreviousClose'),
            'market_cap': info.get('marketCap'),
            'currency': info.get('currency', 'USD'),
            'summary': info.get('longBusinessSummary', 'No summary available.'),
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'historical_data': ticker_data
        }
        print("successful data retrieval")
        return stock_data
    
    except Exception as e:
        print(f"an error occured when fetching stock data for {ticker}: {e}")
        return None

# get latest stock price for a given ticker symbol
# for later use in ML model training and real-time predictions
def get_latest_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker) 
        # fetch 1 day back to get most recent page 
        ticker_data = stock.history(period='1d')
        if not ticker_data.empty:
            latest_price = ticker_data['Close'].iloc[-1]
            return latest_price
        return None
    except Exception as e:
        print(f"an error occured when fetching latest stock price for {ticker}: {e}")
        return None

# Example 

# buy MAGA stocks -> open page (AI SLOP PAGE) -> type MAGA -> you press search and goes to MLdataCollection.py -> future ML file later works and predicts a result. 