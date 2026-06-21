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
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # fetch the average_buy_price for the ticker from the Portfolio table for the given user_id
        cursor.execute("""SELECT ticker, average_buy_price FROM Portfolio WHERE user_id = ? AND ticker = ?""", (user_id, ticker))
        portfolio = cursor.fetchone()
        conn.close()
        return portfolio
    except Exception as e:
        print(f"[in_portfolio] Error for {ticker}: {e}")
        return None

def not_in_portfolio(ticker):
    try:
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
    purchase_price = portfolio[1] if portfolio else not_in_portfolio(ticker)
    if purchase_price is None:
        print(f"[analyse_ticker] Could not determine purchase/current price for {ticker}")
        return None
    return algorithm(ticker, purchase_price, predicted)

# algorithm function to calculate everything
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

def decision_tree_algorithm(ticker, desired_change, momentum_rate, user_id=None):
    BUY_THRESHOLD = 8.0
    STOP_LOSS = 5.0
    MARGIN = 3

    # details dictionary to store all the relevant information and reasoning for the decision
    # this will be returned to the PWA to display in the quote_stock.html template when the user clicks on a stock in thier portfolio. 
    details = {}
    buy_contribs = []
    sell_contribs = []

    # helper functions to add buy/sell contributions to the details dictionary 
    def b(points, reason):
        buy_contribs.append((points, reason))

    # helper function to add sell contributions to the details dictionary 
    def s(points, reason):
        sell_contribs.append((points, reason))

    # fetch the predicted price from the polynomial regression model
    predicted = predicted_price(ticker)
    details['predicted_price'] = predicted

    # fetch the price of the stock when user purchased in the Portfolio table from database.db
    portfolio_entry = in_portfolio(ticker, user_id)
    user_buy_price = portfolio_entry[1] if portfolio_entry else None # average_buy_price from portfolio if exiss
    details['user_buy_price'] = user_buy_price 
    owns = user_buy_price is not None # bool to indicate whether user has ticker in portfolio yet
    details['owns'] = owns

    # if unable to fetch a predicted price, return with HOLD
    if predicted is None:
        return "HOLD", {**details, "reason": "no_prediction"}

    # if unable to determine purchase price use current market price as a reference point for the predicted price and return HOLD
    current = None
    # try to fetch the current price using yfinance
    try:
        info = yf.Ticker(ticker).info or {}
        current = info.get('regularMarketPrice') or info.get('previousClose')
    except Exception:
        current = None

    # if the current price cannot be determined
    if current is None:
        current = not_in_portfolio(ticker)
    # if still unable to determine current price, return HOLD with reason
    details['current_price'] = current
    
    # if we cannot determine a reference price to compare the predicted price to, we cannot make an informed decision
    def pct(a, b):
        try:
            return ((a - b) / b) * 100 if (a is not None and b) else None
        except Exception:
            return None

    # calculate the percentage difference between the predicted price and the user's buy price if they own the stock, otherwise compare to current price
    predicted_pct_vs_buy = pct(predicted, user_buy_price) if owns else None
    predicted_pct_vs_now = pct(predicted, current)
    details['predicted_pct_vs_buy'] = predicted_pct_vs_buy
    details['predicted_pct_vs_now'] = predicted_pct_vs_now

    # gather additional data points for the decision tree model
    sentiment = sentiment_analysis(ticker)
    ratio = market_cap_to_revenue(ticker)
    volume = None
    # fetch the volume of the stock using yfinance, if unable to fetch volume data, it will be set to None and the decision tree algorithm will proceed without it as a feature
    try:
        history = yf.Ticker(ticker).history(period="5d")
        if not history.empty and 'Volume' in history:
            volume = float(history['Volume'].iloc[-1])
    except Exception:
        volume = None

    # update the details dictionary with all the features we have gathered for the decision tree model
    details.update({
        'sentiment': sentiment,
        'ratio': ratio,
        'momentum_rate': momentum_rate,
        'volume': volume
    })

    # decision tree logic:
    # if the predicted price is significantly higher than the user's buy price
    # indicates a strong upside and we should consider buying more if we already own, or buying if we don't own
    if owns and predicted_pct_vs_buy is not None and desired_change is not None and predicted_pct_vs_buy >= desired_change:
        s(6, "take_profit")
    if owns and predicted_pct_vs_buy is not None and predicted_pct_vs_buy <= -STOP_LOSS:
        s(5, "stop_loss")

    # if the predicted price is significantly higher than current price
    # indicates a strong upside and should consider buying more if we already own, or buying if we don't own
    if predicted_pct_vs_now is not None:
        if predicted_pct_vs_now >= BUY_THRESHOLD:
            b(5, "strong_upside")
        elif predicted_pct_vs_now >= BUY_THRESHOLD / 2:
            b(2, "moderate_upside")
    # if the predicted price is significantly lower than current price, then strong signal to sell
    try:
        if sentiment is not None:
            s_val = float(sentiment)
            if s_val >= 0.35:
                b(3, "sentiment_pos")
            elif s_val <= -0.35:
                s(3, "sentiment_neg")
            elif s_val >= 0.15:
                b(1, "sentiment_weak_pos")
            elif s_val <= -0.15:
                s(1, "sentiment_weak_neg")
    except Exception:
        pass

    # market to revenue ratio
    try:
        if ratio is not None:
            if ratio < 50:
                b(2, "market_cap_ratio_low")
            elif ratio < 200:
                b(1, "market_cap_ratio_mid")
            elif ratio < 500:
                b(0, "market_cap_ratio_neutral")
            elif ratio < 1000:
                s(2, "market_cap_ratio_high")
            else:
                s(5, "market_cap_ratio_very_high")
    except Exception:
        pass
    
    # momentum rate
    if momentum_rate is not None:
        if momentum_rate > 0.5:
            b(1, "momentum_pos")
        elif momentum_rate < -0.5:
            s(1, "momentum_neg")

    # volume
    try:
        if volume is not None and volume < 1000:
            b(-1, "low_volume_penalty")
    except Exception:
        pass

    # aggregate the buy and sell contributions 
    buy_score = sum(points for points, _ in buy_contribs)
    sell_score = sum(points for points, _ in sell_contribs)

    # add the contributions and scores to the details dictionary for display in the PWA
    details['buy_contribs'] = buy_contribs
    details['sell_contribs'] = sell_contribs
    details['buy_score'] = buy_score
    details['sell_score'] = sell_score

    # make the final decision based on the aggregated scores and a margin to avoid making decisions when buy and sell scores are close together
    if sell_score - buy_score >= MARGIN:
        action = "SELL" if owns else "AVOID"
    elif buy_score - sell_score >= MARGIN:
        action = "BUY"
    else:
        action = "HOLD"

    # determine the primary reason for the decision by finding the feature with the highest abs. contribution to the decision 
    # the three options:  buy, sell hold with reason "strong buy", "strong sell", "mixed signals" depending on the scores and the primary contributing feature
    all_contribs = buy_contribs + sell_contribs
    if all_contribs:
        primary = max(all_contribs, key=lambda x: abs(x[0]))
        details['primary_reason'] = {'points': primary[0], 'reason': primary[1]}
    else:
        details['primary_reason'] = None

    print(f"Decision for {ticker}: {action} (buy={buy_score}, sell={sell_score})")
    return action, details

### TESTING ###
ticker_test = 'NAB.AX'
user_id = 1
portfolio = in_portfolio(ticker_test, user_id)
pred_price = predicted_price(ticker_test)

# Determine purchase price
if portfolio:
    purchase_price = portfolio[1]  # average_buy_price from portfolio
else:
    purchase_price = not_in_portfolio(ticker_test)  # current market price

algorithm(ticker_test, purchase_price, pred_price)
sentiment_analysis(ticker_test)
market_cap_to_revenue(ticker_test)
decision_tree_algorithm(ticker_test, desired_change=10.0, momentum_rate=5.0, user_id=user_id)