import numpy as np 
import pandas as pd
import MLdataCollection
from sklearn.preprocessing import StandardScaler 
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans 

def predictStockPerformance(ticker):
    # how the AI model works:
    # 1. collect original stock data from MLdataCollection module
    # 2. implement a clustering algorithm (KMeans) to identify patterns in the stock data
    # 3. assigning cluster labels to original stock data to identify which cluster each data point belongs to
    # 4. use the cluster assignments to make predictions about future stock performance based on the patterns identified in the clusters
    try: 
        df = MLdataCollection.get_stock_data(ticker) 
        features = df[
            ['Close',
            'Volume',
            'Volume Change Ratio',
            'Position in 52 Week Range',
            'Return Over 5 Days']
        ]

        clean_df = df.dropna(subset=features.columns) # drop rows with missing feature values
        print(f"Initialised dataset for clustering")
        print(f" - Number of samples: {clean_df.shape[0]}")
        print(f" - Number of features: {clean_df.shape[1]}")

        # scale the features for better performance of the KMeans algorithm
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(clean_df[features.columns])

        # Train the AI model - KMeans clustering 
        kmeans_model = KMeans(n_clusters=3, init="k-means++", random_state=42)
        # sklearn.cluster.KMeans(n_clusters=8, *, init='k-means++', n_init='auto', max_iter=300, tol=0.0001, verbose=0, random_state=None, copy_x=True, algorithm='lloyd'
        # n_clusters: the number of clusters to form
        # there are these things called centriods which are the center point of each cluster
        # means that the algorithm will try to find 3 centriods in the data and assign each data point to the nearest centriod to form clusters
        # init: method for initialising the centriods using k-means++
        # random_state is used to ensure the reproducibility of results (basically ensures same random numbers are generated each time the code is executed)
        cluster_assignments = kmeans_model.fit_predict(scaled_features) # returns the cluster labels for each datapoint 

        # append cluser assignments to original dataframe
        # adds new column to the original dataframe with cluster labels assigned to each point 
        clean_df["Assigned_Cluster"] = cluster_assignments
        print("Data with AI Cluster Assignments")
        print(clean_df.head())
        # 0 assigned clusters indicate one pattern in stock data
        # 1 assigned means 2nd pattern 
        # 2 assigned means 3rd pattern

        # predict future stock price based on the average closing price of each cluster
        cluster_performance = clean_df.groupby("Assigned_Cluster")["Close"].mean()
        print("📈 Average Closing Price for Each Cluster:")
        print(cluster_performance)

        future_price_in_5_days = cluster_performance.mean() 
        print(f"📈 Predicted future stock price for {ticker} in 5 days: ${future_price_in_5_days:.2f}")

    except Exception as e:
        print(f"an error occurred while predicting stock performance for {ticker}: {e}")
        return None
    
predictStockPerformance('NVDA')

