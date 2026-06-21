# the structure of calculating the algorithm 
# 1. import the predicted price from the polynomial regression model
# 2. fetch the price of the stock when user purchased in the Portfolio table from database.db
# Portfolio (user_id, ticker, shares, average_buy_price) VALUES (?, ?, ?, ?)
# 3. subtract the current price of each ticker from the predicted price in the portfolio table 
# 4. calculate the momentum rate by dividing the price difference by the current price and multiplying by 100 to get a percentage
# 5. return the predicted price and momentum rate to the PWA for display in the in the quote_stock.html template when the user clicks on a stock in their portfolio.

# note to self to make it so it grabs all ticker's in the user's portfolio and runs the ML algorithm for each ticker.
# returning a dictionary of the predicted price and momentum rate for each ticker.

import sqlite3
from PolynomialRegression import polynomial_regression

def ml_algorithm(ticker, user_id):
    try:
        # get the ticker symbol from the user's portfolio in the database
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ticker, average_buy_price FROM Portfolio WHERE user_id = ? AND ticker = ?",
            (user_id, ticker) # parametrised for security to prevent SQL injection
        )
        portfolio = cursor.fetchone()

        # check if a ticker is in the user's portfolio before running the ML algorithm.
        if not portfolio:
            print(f"{ticker} is not in the user's portfolio.")
            return None
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

ml_algorithm('CBA.AX', 1)