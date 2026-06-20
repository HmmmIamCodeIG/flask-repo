import numpy as np 
import pandas as pd
import MLdataCollection

from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_blobs
from sklearn.cluster import KMeans 

ticker = 'AAPL' 
df = MLdataCollection.get_stock_data(ticker) 

# features for clustering
features = df[
    ['Close',
     'Volume',
     'Volume Change Ratio',
     'Position in 52 Week Range',
     'Return Over 5 Days']
]
clean_df = df.dropna(subset=features.columns) # drop rows with missing feature values
print(f"--- Initialised dataset for clustering ---")
print(f"--- Number of samples: {clean_df.shape[0]} ---")
print(f"--- Number of features: {clean_df.shape[1]} ---")
print(clean_df.head())

# scale the features for better performance of the KMeans algorithm
scaler = StandardScaler()
scaled_features = scaler.fit_transform(clean_df[features.columns])

# Train the AI model - KMeans clustering 
kmeans_model = KMeans(n_clusters=3, init="k-means++", random_state=42)
cluster_assignments = kmeans_model.fit_predict(scaled_features)

# append cluser assignments to original datframe
clean_df["Assigned_Cluster"] = cluster_assignments
print("--- Data with AI Cluster Assignments ---")
print(clean_df.head())

