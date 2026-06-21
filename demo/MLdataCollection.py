# Stock data collection module for machine learning model training
# Goal: Fetch stock data from Yahoo Finance 
# This module handles all stock data retrieval and processing

# import requests
import yfinance as yf
import pandas as pd
import numpy as np
import requests

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
    # basic stuff to validate ticker
    if not ticker or len(ticker.strip()) < 1:
        return None 
    ticker = ticker.upper().strip()
    if not ticker.isalnum() or len(ticker) > 5:
        print(f"Invalid ticker symbol: {ticker}")
        return None
    try:
        ticker = yf.Ticker(ticker) 
        # 5 yrs of historical data 
        hist = ticker.history(period="5y")
        hist_returns = hist['Close'].pct_change(window) # calculate return over 5 day window from same history frame
        return hist_returns
    except Exception as e:
        print(f"An error occurred while fetching stock data for {ticker}: {e}")
        return None


def highLowDifference(ticker):
    # Accept either a ticker symbol string or a yf.Ticker object
    try:
        # if the input is a string, create a yf.Ticker object.
        # if it's already a yf.Ticker object use it directly
        if isinstance(ticker, str):
            ticker_obj = yf.Ticker(ticker)
        else:
            ticker_obj = ticker
        hist = ticker_obj.history(period="6y", interval="1d") # sets period to 6 years since we need a year more of data to compare earlier dates
        # finds highest and lowest price in the past year
        hist["high"] = hist["High"].rolling(window=252, min_periods=1).max()
        hist["low"] = hist["Low"].rolling(window=252, min_periods=1).min()

        # calculates the position of the stock price within the 52 week range.
        # finds the difference between current stock price and lowest stock price.
        # divides that by difference between highest and lowest stock price to get value btwn 0 and 1
        hist["range"] = ( # creates a value finding the current stock price's position 52 weeks 
            (hist["Close"] - hist["low"]) /
            (hist["high"] - hist["low"])
        )
        years_five = hist.index.max() - pd.DateOffset(years=5) # limits the data to 5 years
        hist_5 = hist.loc[hist.index >= years_five].copy() # creates a new dataframe with only the last 5 years of data

        # fill any missing values with 0 as it indicates a low end
        if "range" in hist_5.columns:
            price_range = (hist_5["high"] - hist_5["low"]).replace(0, np.nan)
            hist_5["range"] = ((hist_5["Close"] - hist_5["low"]) / price_range).fillna(0)
        return hist_5
    except Exception as e:
        print(f"An error occurred while calculating high-low difference for {ticker}: {e}")
        return None

def get_stock_data(ticker):
    """
    fetch stock data for a given ticker symbol and date range.
    
    args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL') 
        hist: 
        

    returns: 
        dict_history = {{
            close: float, data format: NNN.NN (the )
            volume: int, data format: NNNNNN (the vol)
            volume change ratio: float, data format: N.NNNN (the percentage change in volume compared to previous day)
            return over 5 days: float, data format: N.NNNN (return window )
            position in 52 week range: float, data format: N.NNNN (, calculated as (current price - lowest price) / (highest price - lowest price))
        }}
    """
    period = "5y"

    try:
        tickerStock = yf.Ticker(ticker) # ticker initialisation
        hist = tickerStock.history(period=period) # fetch historical data for the specified period
        volume_ratios = hist["Volume"].pct_change().replace([np.inf, -np.inf], np.nan) # calculate volume change ratio from the same history frame
        return_window = hist['Close'].pct_change(periods=5).replace([np.inf, -np.inf], np.nan)
        # first five days have to be dropped since return over 5 days cannot be calculated for those days
        # not enough historical data to compare to
        high_low_diff = highLowDifference(ticker) 
        # sentiment_data = sentiment_analysis(ticker) 

        dict_history = pd.DataFrame({
            'Close': hist['Close'],
            'Volume': hist['Volume'],
            'Volume Change Ratio': volume_ratios,
            'Return Over 5 Days': return_window,
            'Position in 52 Week Range': high_low_diff['range'],
            # 'Sentiment Score': sentiment_data['sentiment_score']
        })
        dict_history = dict_history.replace([np.inf, -np.inf], np.nan)
        return dict_history
    except Exception as e:
        print(f"an error occured when fetching stock data for {ticker}: {e}")
        return None 

# print(get_stock_data('AAPL'))
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
