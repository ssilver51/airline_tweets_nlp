from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from joblib import dump, load
from src.helpers import sw, define_axis_style, plot_feature_importances, print_model_metrics, wordnet_lemmetize_tokenize
import os

if __name__ == '__main__':

    # Read and split data into training and test
    data = pd.read_csv("data/Clean_T_Tweets_wo_Users.csv", index_col=0)

    X = data['text']
    y = data['airline_sentiment']
    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=10)

    # Initialize Count Vectorizer and Random Forest pipeline
    count_vect = CountVectorizer(stop_words=sw, analyzer='word', tokenizer=wordnet_lemmetize_tokenize)

    rf = RandomForestClassifier(
                            random_state=42,
                            n_jobs=-1,
                            n_estimators=250,
                            max_features='auto',
                            oob_score=True,
                            class_weight='balanced',
                            min_samples_split=10
                        )

    rf_pipeline = Pipeline([
                        ('vect', count_vect),
                        ('model', rf)
                    ])

    rf_pipeline.fit(X_train, y_train)

    # generate predictions
    y_preds = rf_pipeline.predict(X_test)

    plt.style.use('seaborn')
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Make it pretty/consistent
    define_axis_style(
                    ax=ax,
                    title="Random Forest Estimators vs. Macro F1 Score",
                    x_label="Number of Estimators",
                    y_label="Macro F1 Score on Unseen Data",
                    legend=False
                )

    # Evaluate model
    print_model_metrics(y_test, y_preds)

    # Fit on total training data and dump to /models
    rf_pipeline.fit(X, y)
    if not os.path.exists("models/"):
        os.mkdir('models/')
    dump(rf_pipeline, 'models/randomforest.joblib')

    # Plot feature importances
    plt.style.use("seaborn")

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    std = np.std([tree.feature_importances_ for tree in rf.estimators_], axis=0)

    n_features = 15
    define_axis_style(
                    ax=ax,
                    title=f"Top {n_features} Feature Importances for Random Forest (Bag of Words)",
                    x_label=None,
                    y_label='Feature Importance'
                )
    plot_feature_importances(
                    ax=ax,
                    feat_importances=rf.feature_importances_,
                    feat_std_deviations=std,
                    feat_names=count_vect.get_feature_names(),
                    n_features=n_features,
                    outfilename="images/rf_feat_importances.png"
                )
