"""
Skeleton for future compatibility model between adopters and pets.
This is a placeholder showing where dataset loading, training and saving will go.
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_example():
    # TODO: replace with real dataset and feature engineering
    df = pd.DataFrame({
        'age': [1, 5, 3, 2],
        'size': [0,1,0,1],
        'match': [1, 0, 1, 0]
    })
    X = df[['age','size']]
    y = df['match']
    clf = RandomForestClassifier(n_estimators=10)
    clf.fit(X, y)
    joblib.dump(clf, '../models/compatibility_v0.joblib')

if __name__ == '__main__':
    train_example()
