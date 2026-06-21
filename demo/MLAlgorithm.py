# the structure of calculating the algorithm 
# 1. import the predicted price from the polynomial regression model
# 2. fetch the price of the stock when user purchased in the Portfolio table from database.db
# Portfolio (user_id, ticker, shares, average_buy_price) VALUES (?, ?, ?, ?)
# 3. subtract the current price of each ticker from the predicted price in the portfolio table 
# 4. calculate the momentum rate by dividing the price difference by the current price and multiplying by 100 to get a percentage
# 5. return the predicted price and momentum rate to the PWA for display in the in the quote_stock.html template when the user clicks on a stock in their portfolio.

# the decision tree model:
# 1 means BUY, 0 means HOLD, -1 means SELL
# allow for other current value variables (news headlines using alphavantage)
# note to self to make it so it grabs all ticker's in the user's portfolio and runs the ML algorithm for each ticker.
# returning a dictionary of the predicted price and momentum rate for each ticker.

import sqlite3
import requests
from textblob import TextBlob
import yfinance as yf
from PolynomialRegression import polynomial_regression

def ml_algorithm(ticker, user_id):
    try:
        # get the ticker symbol from the user's portfolio in the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ticker, average_buy_price FROM Portfolio WHERE user_id = ? AND ticker = ?",
            (user_id, ticker) # parametrised for security to prevent SQL injection
        )
        portfolio = cursor.fetchone() 
        conn.close()
        portfolio_ticker, purchased_price = portfolio

        # run the polynomial regression model to get the predicted price for the ticker.
        ml_results = polynomial_regression(portfolio_ticker)
        if not ml_results:
            print(f"ML algorithm failed to produce results for {portfolio_ticker}.")
            return None

        # check if the purchased price is valid before calculating the momentum rate.
        if purchased_price is None or purchased_price <= 0:
            print(f"Missing or invalid average_buy_price for {portfolio_ticker} in Portfolio.")
            return None

        # fetch the predicted price from the ML results and calculate the momentum rate
        predicted_price = ml_results.get('predicted_close')
        if predicted_price is None:
            print(f"Predicted close price is missing for {portfolio_ticker}.")
            return None
        
        # calculate the momentum rate as a percentage change from the purchased price to the predicted price
        momentum_rate = ((predicted_price - purchased_price) / purchased_price) * 100
        prediction = {
            'ticker': portfolio_ticker,
            'purchased_price': purchased_price,
            'predicted_price': predicted_price,
            'momentum_rate': momentum_rate,
        }
        print(f"Ticker: {portfolio_ticker}")
        print(f"Purchased price: {purchased_price:.2f}")
        print(f"Predicted price: {predicted_price:.2f}")
        print(f"Momentum rate: {momentum_rate:.2f}%")
        return prediction
    except Exception as e:
        print(f"An error occurred while running the ML algorithm for {ticker}: {e}")
        return None
    
def sentiment_analysis(ticker):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&ticker={ticker}&apikey=DMZ57B8EW0H0LZJ&limit=1'
    try:
        # fetch the latest news sentiment score for ticker using alphavantage API
        news = requests.get(url)
        sentiment_score = news.json()['feed'][0]['overall_sentiment_score']
        print(f"Sentiment score for {ticker}: {sentiment_score}")
        return sentiment_score
    # why does it grey out when no comment here
    except KeyError as e:
        print(f"Alphavantage API ratelimit reached")
        return None

# using market cap as a feature in the decision tree algorithm to determine the weight of the sentiment score in the final decision.
def market_cap_to_revenue(ticker):
    try:
        tickerStock = yf.Ticker(ticker)
        market_cap = tickerStock.info['marketCap']
        # annual revenue of the company 
        annual_revenue = tickerStock.info['totalRevenue']
        if annual_revenue > 0:
            market_cap_to_revenue = (market_cap / annual_revenue) * 100
            print(f"Market Cap to Revenue Ratio for {ticker}: {market_cap_to_revenue:.2f}")
            return market_cap_to_revenue
        else:
            print(f"Annual revenue is zero or negative for {ticker}, cannot calculate market cap to revenue ratio.")
            return None
    except Exception as e:
        print(f"An error occurred while calculating market cap to revenue ratio for {ticker}: {e}")
        return None

def decision_tree_algorithm(ticker, desired_change, momentum_rate, predicted_price):
    points = 0
    if momentum_rate >= desired_change:
        points += 1
    elif momentum_rate < 0: 
        points -= 1

    if sentiment_analysis(ticker) is not None:
        if sentiment_analysis(ticker) <= -0.35: 
            points -= 5
        elif sentiment_analysis(ticker) <= 0.15: 
            points -= 2
        elif sentiment_analysis(ticker) > 0.35:
            points += 5
        elif sentiment_analysis(ticker) > 0.15:
            points += 2
    
ml_algorithm('AAPL', 1)
sentiment_analysis('AAPL')
market_cap_to_revenue('AAPL')