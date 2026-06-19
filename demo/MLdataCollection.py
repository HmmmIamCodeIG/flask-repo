# Stock data collection module for machine learning model training
# Goal: Fetch stock data from Yahoo Finance 
# This module handles all stock data retrieval and processing

import yfinance as yf
import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)  # Display all columns in DataFrame

# volume change ratio is how much the volume of stock traded has changed compared to previous day
def volume_change_ratio(ticker):
    """
    Calculate the daily volume change ratio for a ticker.
    args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')

    returns:
        panda series containing the volume change ratio for each day.
    """
    if not ticker or len(ticker.strip()) < 1:
        return None # Return None if the ticker symbol is empty or invalid
    # Validate ticker symbol format 
    ticker = ticker.upper().strip()
    if not ticker.isalnum() or len(ticker) > 5:
        print(f"Invalid ticker symbol: {ticker}")
        return None
    try:
        stock = yf.Ticker(ticker) # ticker initialisation
        hist = stock.history(period="5yr") 
        return hist["Volume"].pct_change().fillna(0)
        # fillna(0) is used to replace the first value which will be NaN since there is no previous day to compare to, with 0 indicating no change in volume.
        # pandas has a inbuilt function to calculate percentage change apparently so that's simplified instead of:
        # volume_change_ratio = (current-volume - previous_volume) / previous_volume 

    except Exception as e:
        print(f"An error occurred while calculating volume change ratio for {ticker}: {e}")
        return None

def returnWindow(ticker, window=5):
    """
    returns over window 5 days
    note: this is backwards looking return, so it calculates the return from 5 days ago to today, not the future return over the next 5 days.
    
    args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        window: Number of days to calculate returns over (default is 5 days)
    returns:
        pandas DataFrame containing the stock data for the specified date range.
    """
    if not ticker or len(ticker.strip()) < 1:
        return None 
    ticker = ticker.upper().strip()
    if not ticker.isalnum() or len(ticker) > 5:
        print(f"Invalid ticker symbol: {ticker}")
        return None
    try:
        stock = yf.Ticker(ticker) 
        # 5 yrs of historical data 
        hist = stock.history(period="5y")
        hist_returns = hist['Close'].pct_change(window) # calculate return over 5 day window from same history frame
        return hist_returns
    except Exception as e:
        print(f"An error occurred while fetching stock data for {ticker}: {e}")
        return None

def get_stock_data(ticker):
    """
    fetch stock data for a given ticker symbol and date range.
    
    args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')

    returns: 
        dict_history = {{
            'Close': DataFrame
            'Volume': DataFrame
            'Volume Change Ratio': DataFrame
        }}
    """
    period = "5y"

    try:
        tickerStock = yf.Ticker(ticker) # ticker initialisation
        hist = tickerStock.history(period=period) # fetch historical data for the specified period
        volume_ratios = hist["Volume"].pct_change().fillna(0).replace([np.inf, -np.inf], np.nan) # calculate volume change ratio from the same history frame
        returnWindow = hist['Close'].pct_change(periods=5).dropna() # calculate return over 5 day window from same history frame
        # dropna used to remove the first 5 rows which will be NaN since there is no previous data to compare to for the first 5 days.

        dict_history = pd.DataFrame({
            'Close': hist['Close'],
            'Volume': hist['Volume'],
            'Volume Change Ratio': volume_ratios,
            'Return Over 5 Days': returnWindow
        })
        print(dict_history)
    except Exception as e:
        print(f"an error occured when fetching stock data for {ticker}: {e}")
        return None 

print(get_stock_data('AAPL'))
### NOTES:
# industry search on top industries in each sector, then search for stocks in those industries.

### FIVE FEATURES REQUIRED FOR REGRESSION LINE TO TRAIN ML MODEL
# - closing value
# - volume of stocks traded
# - top industry stock value
# - market cap

### Unique feature that is none of the above
# - note: not news sentiment analysis as it is broken
# - stock price volatility 