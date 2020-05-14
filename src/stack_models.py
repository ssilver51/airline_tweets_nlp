from joblib import dump, load
from naive_bayes import wordnet_lemmetize_tokenize
from data_cleaning import data_cleaning
from identify_users_of_interest import remove_users_of_interest
import pandas as pd
from helpers import print_model_metrics
from vader_analysis import vader_predict, vader_predict_proba
from statistics import mode, StatisticsError
import numpy as np

def stack_models_voting(rf_preds, nb_preds, vader_preds):
    final_preds = []
    for preds in zip(rf_preds, nb_preds, vader_preds):
        try:
            final_pred = mode(preds)
        except StatisticsError:
            # tie goes to random forest
            final_pred = preds[0]
        final_preds.append(final_pred)
    return final_preds

def stack_models_probas(rf_probas, nb_probas, vader_probas, weights=[1, 1, 1]):
    rf_weight = weights[0]
    nb_weight = weights[1]
    vader_weight = weights[2]
    final_preds = []
    for preds in zip(rf_probas, nb_probas, vader_probas):
        pred_dict = {"negative": 0, "positive": 0, "neutral": 0}
        for key in pred_dict:
            pred_dict[key] += preds[0][key] * rf_weight
            pred_dict[key] += preds[1][key] * nb_weight
            pred_dict[key] += preds[2][key] * vader_weight
        final_preds.append(max(pred_dict, key=pred_dict.get))
    return final_preds

def format_probas(labels, probas):
    probas_dicts = []
    for pred in probas:
        probas_dicts.append(dict(zip(labels, pred)))
    return probas_dicts

if __name__ == '__main__':
    rf_pipeline = load('models/randomforest.joblib')
    nb_pipeline = load('models/naivebayes.joblib')

    data_cleaning("data/Holdout_Tweets.csv", "data/Clean_Holdout_Tweets.csv")
    holdout_df = pd.read_csv("data/Clean_Holdout_Tweets.csv")
    holdout_df = remove_users_of_interest(holdout_df)
    holdout_df.to_csv("data/Clean_Holdout_Tweets_wo_Users.csv")

    X_holdout = holdout_df['text']
    y_holdout = holdout_df['airline_sentiment']

    y_preds_nb = nb_pipeline.predict(X_holdout)
    print("Naive Bayes Metrics:")
    print_model_metrics(y_holdout, y_preds_nb)

    print("\n\n")

    y_preds_rf = rf_pipeline.predict(X_holdout)
    print("Random Forest Metrics:")
    print_model_metrics(y_holdout, y_preds_rf)


    print("\n\n")   

    y_preds_vader = vader_predict(X_holdout)
    print("VADER Metrics:")
    print_model_metrics(y_holdout, y_preds_vader)

    print("\n\n")   

    print("Baseline Metrics:")
    print_model_metrics(y_holdout, ["negative"] * len(y_holdout))

    print("\n\n")   

    y_probas_rf = rf_pipeline.predict_proba(X_holdout)
    labels = rf_pipeline.classes_
    rf_fmt_probas = format_probas(labels, y_probas_rf)

    y_probas_nb = nb_pipeline.predict_proba(X_holdout)
    labels = nb_pipeline.classes_
    nb_fmt_probas = format_probas(labels, y_probas_nb)

    y_probas_vader = vader_predict_proba(X_holdout)

    y_preds_voting = stack_models_probas(rf_fmt_probas, nb_fmt_probas, y_probas_vader, weights=[1, 0.8, 0.5])
    print("Stacked Probas Metrics:")
    print_model_metrics(y_holdout, y_preds_voting)


    y_preds_voting = stack_models_voting(y_preds_rf, y_preds_nb, y_preds_vader)
    print("Stacked Voting Metrics:")
    print_model_metrics(y_holdout, y_preds_voting)