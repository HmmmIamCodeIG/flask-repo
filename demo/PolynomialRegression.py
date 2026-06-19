import MLdataCollection
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from MLdataCollection import get_stock_data

plt.style.use('ggplot')

def polynomial_regression(ticker, degree=2):
    training_data = get_stock_data(ticker) # get the stock data from MLdataCollection module

    if training_data is None:
        print(f"No training data returned for {ticker}.")
        return None

    x = training_data[['Volume', 'Volume Change Ratio', 'Position in 52 Week Range', 'Return Over 5 Days']] # features on the x axis
    y = training_data['Close'] # target variable on the y axis

    # printing shape for validation
    # printing features used for validation
    print(f"yay! Dataset shape: {training_data.shape}") 
    print(f"Features used in model: {x.columns.tolist()}") 

    # setting test and training data split 
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    # setting the parameters for the polynomial regression model
    degree = 4
    use_ridge = True # for polynomial regression. ridge regression used to prevent overfitting. 
    ridge_alpha = 1.0 # regularisation strength for ridge regression. higher values -> more regularisation

    # weight parameters 
    weightVolume = 1.0
    weightVolumeChangeRatio = 1.0
    weightPositionIn52WeekRange = 1.0
    weightReturnOver5Days = 1.0

    # creating a copy so original data can be used for validation and testing without the weights applied
    # also allows for easy experimentation with different weights 
    x_train_w = x_train.copy() 
    x_test_w = x_test.copy()
    # setting the weights for each feature. these can be adjusted 
    x_train_w['Volume'] = x_train_w['Volume'] * weightVolume
    x_train_w['Volume Change Ratio'] = x_train_w['Volume Change Ratio'] * weightVolumeChangeRatio
    x_train_w['Position in 52 Week Range'] = x_train_w['Position in 52 Week Range'] * weightPositionIn52WeekRange
    x_train_w['Return Over 5 Days'] = x_train_w['Return Over 5 Days'] * weightReturnOver5Days

    # polynomial feature transformation
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    x_train_poly = poly.fit_transform(x_train_w)
    x_test_poly = poly.transform(x_test_w)

    model = Ridge(alpha=ridge_alpha) if use_ridge else LinearRegression()

    # training the model
    model.fit(x_train_poly, y_train)
    print("Model training complete.")

    # feature importance
    feature_names = poly.get_feature_names_out() # get the names of the polynomial features for better interpretability
    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Absolute Coefficient': np.abs(model.coef_) # get the absolute value of the coefficients to understand the importance of each feature regardless of direction (positive or negative)
    })

    # grouping features by original feature and summing their absolute coefficients to get a sense of relative importance
    volumeTerms = [f for f in feature_names if 'Volume' in f]
    volumeChangeRatioTerms = [f for f in feature_names if 'Volume Change Ratio' in f]
    positionIn52WeekRangeTerms = [f for f in feature_names if 'Position in 52 Week Range' in f]
    dailyReturnsTerms = [f for f in feature_names if 'Return Over 5 Days' in f]

    # calculating the total importance for each original feature by summing the absolute coefficients of all polynomial terms that include that feature
    volumeImportance = coef_df[coef_df['Feature'].isin(volumeTerms)]['Absolute Coefficient'].sum()
    volumeChangeRatioImportance = coef_df[coef_df['Feature'].isin(volumeChangeRatioTerms)]['Absolute Coefficient'].sum()
    positionIn52WeekRangeImportance = coef_df[coef_df['Feature'].isin(positionIn52WeekRangeTerms)]['Absolute Coefficient'].sum()
    returnOver5DaysImportance = coef_df[coef_df['Feature'].isin(dailyReturnsTerms)]['Absolute Coefficient'].sum()

    # calculating the total importance to get relative importance percentages
    total = volumeImportance + volumeChangeRatioImportance + positionIn52WeekRangeImportance + returnOver5DaysImportance
    print("\nRelative Feature Importance (%):")
    print(f"Volume: {(volumeImportance / total * 100):.1f}%")
    print(f"Volume Change Ratio:{(volumeChangeRatioImportance / total * 100):.1f}%")
    print(f"Position in 52 Week Range:{(positionIn52WeekRangeImportance / total * 100):.1f}%")
    print(f"Return Over 5 Days:{(returnOver5DaysImportance / total * 100):.1f}%")

    # evaluating the model on the test set using regression metrics
    # predicting the close price for the test set
    y_test_pred = model.predict(x_test_poly)
    print(f"\nTest R2:{r2_score(y_test, y_test_pred):.4f}")
    print(f"Test MAE:{mean_absolute_error(y_test, y_test_pred):.4f}")

    # saving the model and polynomial transformer for future use in the PWA
    # the model and transformer are saved with the ticker symbol in the filename for retrieval when making predictions in the PWA. 
    ticker_symbol = ticker
    cache_dir = Path(__file__).resolve().with_name('__pycache__')
    cache_dir.mkdir(exist_ok=True)
    joblib.dump(poly, cache_dir / f'{ticker_symbol}_poly_transformer_grades.pkl')
    joblib.dump(model, cache_dir / f'{ticker_symbol}_polynomial_regression_model_grades.pkl')

    # Plot actual vs predicted stock close price
    y_test_flat = y_test.values.ravel()
    y_test_pred_flat = y_test_pred.ravel()

    # setting the limits for the plot to be slightly beyond the min and max of the actual and predicted values for better visualization
    min_price = min(y_test_flat.min(), y_test_pred_flat.min())
    max_price = max(y_test_flat.max(), y_test_pred_flat.max())

    # creating a scatter plot of actual vs predicted close prices w/h reference line
    plt.figure(figsize=(10, 6))
    plt.scatter(
        y_test_flat,
        y_test_pred_flat,
        color='steelblue',
        alpha=0.7,
        s=50
    )
    plt.plot([min_price, max_price], [min_price, max_price], 'r--', lw=2)
    plt.xlabel("Actual Close Price")
    plt.ylabel("Predicted Close Price")
    plt.title(f"{ticker_symbol}: Actual vs Predicted Close Price (degree={degree})")
    plt.grid(True)
    plt.show()

polynomial_regression("NVDA")