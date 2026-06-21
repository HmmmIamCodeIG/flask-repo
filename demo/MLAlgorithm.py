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
import sqlite3
import yfinance as yf

def predicted_price(ticker):
    try:
        # fetch the predicted price from the polynomial regression model
        ml_results = polynomial_regression(ticker)
        if not ml_results:
            return None
        return ml_results.get('predicted_close')
    except Exception as e:
        print(f"[predicted_price] Error for {ticker}: {e}")
        return None

def in_portfolio(ticker, user_id):
    if user_id is None:
        return None
    # fetch the average_buy_price for the ticker from the Portfolio table for the given user_id
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # fetch the average_buy_price for the ticker from the Portfolio table for the given user_id
        cursor.execute("""SELECT ticker, average_buy_price FROM Portfolio WHERE user_id = ? AND ticker = ?""", (user_id, ticker))
        portfolio = cursor.fetchone()
        conn.close()
        
        if portfolio is None:
            return None  # Not in portfolio
        # Check if average_buy_price is valid
        ticker_symbol, avg_buy_price = portfolio
        if avg_buy_price is None or avg_buy_price <= 0:
            print(f"[in_portfolio] Invalid average_buy_price for {ticker_symbol}")
            return None
        return (ticker_symbol, avg_buy_price)
    except Exception as e:
        print(f"[in_portfolio] Error for {ticker}: {e}")
        return None

def not_in_portfolio(ticker):
    try:
        ml_results = polynomial_regression(ticker)
        if not ml_results:
            print(f"[not_in_portfolio] ML failed for {ticker}")
            return None
        # Fetch current price using yfinance
        history = yf.Ticker(ticker).history(period="1d")
        if history.empty:
            print(f"[not_in_portfolio] No price data for {ticker}")
            return None
        return history['Close'].iloc[-1]
    except Exception as e:
        print(f"[not_in_portfolio] Error for {ticker}: {e}")
        return None

# the analyse ticker function is the main function called by the PWA to get the predicted price and monentum rate for a given ticker
def analyse_ticker(ticker, user_id=None):
    portfolio = in_portfolio(ticker, user_id)
    predicted = predicted_price(ticker)
    # check if predicted price is valid
    if predicted is None:
        print(f"[analyse_ticker] No predicted price for {ticker}")
        return None
    if portfolio:
        # Use average_buy_price
        purchase_price = portfolio[1]
    else:
        # Use current market price
        purchase_price = not_in_portfolio(ticker)
    # check if purchase price is valid
    if purchase_price is None:
        print(f"[analyse_ticker] Could not determine purchase/current price for {ticker}")
        return None
    return algorithm(ticker, purchase_price, predicted)


def algorithm(ticker, purchase_price, predicted_price):
    try:
        # calculate the momentum rate by dividing the price difference by the current price and multiplying by 100 to get a percentage
        momentum_rate = ((predicted_price - purchase_price) / purchase_price) * 100
        result = {
            'ticker': ticker,
            'purchased_price': purchase_price,
            'predicted_price': predicted_price,
            'momentum_rate': momentum_rate
        }
        print(f"Ticker: {ticker}")
        print(f"Purchase price: {purchase_price:.2f}")
        print(f"Predicted price: {predicted_price:.2f}")
        print(f"Momentum rate: {momentum_rate:.2f}%")
        return result
    except Exception as e:
        print(f"[algorithm] Error for {ticker}: {e}")
        return None

# using sentiment score as a feature
def sentiment_analysis(ticker):
    try:
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey=DMZ57B8EW0H0LZJ&limit=1'
        response = requests.get(url)
        data = response.json()

        # Check for API errors or rate limits
        if 'Information' in data:
            print(f"[sentiment_analysis] API limit/info message for {ticker}: {data['Information']}")
            return None
        if 'Note' in data:
            print(f"[sentiment_analysis] Rate limited for {ticker}: {data['Note']}")
            return None
        if 'Error Message' in data:
            print(f"[sentiment_analysis] API error for {ticker}: {data['Error Message']}")
            return None
        
        # Check if feed data is available
        feed = data.get('feed')
        if not feed:
            print(f"[sentiment_analysis] No news feed available for {ticker} (likely unsupported ticker/exchange)")
            return None
        sentiment_score = feed[0]['overall_sentiment_score']
        print(f"Sentiment score for {ticker}: {sentiment_score}")
        return sentiment_score
    except Exception as e:
        print(f"[sentiment_analysis] An error occurred while fetching sentiment score for {ticker}: {e}")
        return None

# using market cap as a feature in the decision tree model
def market_cap_to_revenue(ticker):
    try:
        tickerStock = yf.Ticker(ticker)
        market_cap = tickerStock.info['marketCap']
        # annual revenue of the company 
        annual_revenue = tickerStock.info['totalRevenue']
        if annual_revenue > 0:
            # calculating the market cap
            market_cap_to_revenue = (market_cap / annual_revenue) * 100
            print(f"Market Cap to Revenue Ratio for {ticker}: {market_cap_to_revenue:.2f}")
            return market_cap_to_revenue
        else:
            print(f"Annual revenue is zero or negative for {ticker}, cannot calculate market cap to revenue ratio.")
            return None
    except Exception as e:
        print(f"An error occurred while calculating market cap to revenue ratio for {ticker}: {e}")
        return None

def decision_tree_algorithm(ticker, desired_change, momentum_rate):
    # variable to keep track of the points for each feature
    points = 0
    ratio = market_cap_to_revenue(ticker)
    sentiment = sentiment_analysis(ticker)

    # points for momentum rate
    if momentum_rate >= desired_change:
        points += 1
    elif momentum_rate < 0: 
        points -= 1

    # points for sentiment score 
    if sentiment is not None:
        if sentiment <= -0.35:
            points -= 5
        elif sentiment <= 0.15:
            points -= 2
        elif sentiment > 0.35:
            points += 5
        elif sentiment > 0.15:
            points += 2

    # for market cap ratio
    if ratio is not None:
        if ratio < 50:
            points += 2
        elif ratio < 200:
            points += 1
        elif ratio < 500:
            points += 0
        elif ratio < 1000:
            points -= 2
        else:
            points -= 5

### TESTING THE ALGORITHM ###
ticker_test = 'NAB.AX'
user_id = 1
portfolio = in_portfolio(ticker_test, user_id)
pred_price = predicted_price(ticker_test)
# Determine purchase price
if portfolio:
    purchase_price = portfolio[1] # average_buy_price from portfolio
else:
    purchase_price = not_in_portfolio(ticker_test) # current market price
algorithm(ticker_test, purchase_price, pred_price)
sentiment_analysis(ticker_test)
market_cap_to_revenue(ticker_test)