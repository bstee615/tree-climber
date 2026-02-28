# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.
import logging
import sys
import json
import numpy as np
import argparse
from sklearn.metrics import accuracy_score,f1_score,recall_score,precision_score


def read_answers(filename):
    answers={}
    with open(filename) as f:
        for line in f:
            line=line.strip()
            js=json.loads(line)
            answers[js['idx']]=js['target']
    return answers

def read_predictions(filename):
    predictions={}
    with open(filename) as f:
        for line in f:
            line=line.strip()
            idx,label=line.split()
            predictions[int(idx)]=int(label)
    return predictions

def calculate_scores(answers,predictions):
    Acc=[]
    for key in answers:
        if key not in predictions:
            logging.error("Missing prediction for index {}.".format(key))
            sys.exit()
        Acc.append(answers[key]==predictions[key])

    scores={}
    scores['Acc'] = np.mean(Acc)

    true_labels = [answers[key] for key in answers]
    predicted_labels = [predictions[key] for key in answers]

    acc = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels, predicted_labels, average='macro')
    recall = recall_score(true_labels, predicted_labels, average='macro')
    f1 = f1_score(true_labels, predicted_labels, average='macro')

    scores = {
        'ortiginal_acc':acc,
        'Acc': acc,
        'Precision': precision,
        'Recall': recall,
        'F1': f1
    }

    return scores

def main():
    han_self_sn380_wn60_bz32 = '../saved_models/Han_selfat_sn380_wn60_bz32_ep100_lr5e4/predictions.txt'
    han_self_sn400_wn60_bz32 = '../saved_models/Han_selfatt_sn400_wn60_bz32_ep100_lr5e4/predictions.txt'
    han_self_sn400_wn60_bz64 = '../saved_models/Han_selfatt_sn400_wn60_bz64_ep100_lr5e4/predictions.txt'

    parser = argparse.ArgumentParser(description='Evaluate leaderboard predictions for Defect Detection dataset.')
    parser.add_argument('--answers', default='test.jsonl',type=str,help="filename of the labels, in txt format.")
    parser.add_argument('--predictions', '-p',help="filename of the leaderboard predictions, in txt format.")
    args = parser.parse_args()
    answers=read_answers(args.answers)

    predictions1=read_predictions(han_self_sn380_wn60_bz32)
    scores1=calculate_scores(answers,predictions1)
    print('han_self_sn380_wn60_bz32',scores1)

    predictions3 = read_predictions(han_self_sn400_wn60_bz64)
    scores3 = calculate_scores(answers, predictions3)
    print('han_self_sn400_wn60_bz64', scores3)

    predictions2=read_predictions(han_self_sn400_wn60_bz32)
    scores2 = calculate_scores(answers, predictions2)
    print("hi")

    print('han_self_sn400_wn60_bz32', scores2)

if __name__ == '__main__':
    main()
