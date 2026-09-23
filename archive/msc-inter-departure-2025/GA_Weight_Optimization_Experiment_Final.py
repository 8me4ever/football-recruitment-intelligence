#!/usr/bin/env python3
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from scipy.optimize import differential_evolution
from sklearn.metrics import (precision_score, recall_score, f1_score, 
                             average_precision_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)
from weight_optimization_core_updated import (
    load_experimental_data_enhanced, get_universal_metrics, get_position_specific_metrics,
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
    evaluate_weights_enhanced
)

class GAOptimizer:
    def __init__(self, inter_data, league_data, position_datasets, position):
        self.inter_data = inter_data
        self.league_data = league_data
        self.position_datasets = position_datasets
        self.position = position
        self.iteration_count = 0
        self.best_result = None
    
    def get_bounds(self):
        universal_metrics = get_universal_metrics()
        position_metrics = get_position_specific_metrics()
        if self.position not in position_metrics:
            return {}
        bounds = {}
        for metric_name in universal_metrics.keys():
            if metric_name in ['age', 'Contract_expires']:
                continue
            bounds[f'{metric_name}_weight'] = (0.08, 0.15)
        position_specific = list(position_metrics[self.position].keys())
        if self.position == 'Forward':
            important = ['Gls', 'xG', 'SoT', 'SCA', 'GCA']
        elif self.position == 'Midfielder':
            important = ['Ast', 'xAG', 'KP', 'Cmp_pct', 'PrgP']
        elif self.position == 'Defender':
            important = ['Tkl', 'Int', 'Blocks', 'Clr', 'Cmp_pct']
        else:
            important = ['Saves', 'Save_pct', 'CS', 'CS_pct']
        for metric in position_specific:
            if metric in important:
                bounds[f'{metric}_weight'] = (0.08, 0.15)
            else:
                bounds[f'{metric}_weight'] = (0.05, 0.12)
        bounds.update({
            'alpha': (1.0, 4.0),
            'tau': (0.3, 0.7),
            'risk_multiplier': (0.3, 0.7)
        })
        return bounds
    
    def fitness_function(self, weights_array):
        self.iteration_count += 1
        weight_bounds = self.get_bounds()
        weight_names = list(weight_bounds.keys())
        weights_dict = dict(zip(weight_names, weights_array))
        score, metrics = evaluate_weights_enhanced(
            weights_dict, self.inter_data, self.league_data, 
            self.position_datasets, self.position
        )
        if score > (self.best_result or -1):
            self.best_result = score
        return -score
    
    def optimize(self):
        weight_bounds = self.get_bounds()
        bounds = [(low, high) for low, high in weight_bounds.values()]
        start_time = time.time()
        self.iteration_count = 0
        self.best_result = None
        result = differential_evolution(
            func=self.fitness_function,
            bounds=bounds,
            maxiter=20,
            popsize=10,
            seed=42,
            disp=False
        )
        optimization_time = time.time() - start_time
        best_weights = dict(zip(weight_bounds.keys(), result.x))
        return {
            'method': 'Genetic Algorithm',
            'weights': best_weights,
            'score': -result.fun,
            'time': optimization_time,
            'iterations': self.iteration_count
        }

def run_ga_weight_optimization():
    start_time = time.time()
    inter_data, league_data, position_datasets = load_experimental_data_enhanced()
    if inter_data is None:
        return None
    results = {
        'timestamp': datetime.now().isoformat(),
        'algorithm': 'GA',
        'positions': {}
    }
    positions = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
    optimized_weights = {}
    for position in positions:
        pos_data = inter_data[inter_data['position_group'] == position]
        if len(pos_data) == 0:
            continue
        optimizer = GAOptimizer(inter_data, league_data, position_datasets, position)
        opt_result = optimizer.optimize()
        optimized_weights[position] = opt_result['weights']
        results['positions'][position] = {
            'player_count': len(pos_data),
            'result': opt_result
        }
    predictions = []
    for _, player in inter_data.iterrows():
        position = player['position_group']
        if position not in optimized_weights:
            continue
        percentile_scores = calculate_enhanced_percentile_scores(
            player, league_data, position_datasets)
        departure_prob = calculate_departure_probability_with_weights(
            player, percentile_scores, optimized_weights[position])
        predictions.append({
            'player': player['player'],
            'position': position,
            'age': int(player['age']),
            'minutes': int(player['Min']),
            'departure_probability': round(departure_prob, 4),
            'stay_probability': round(1.0 - departure_prob, 4),
            'actual_departed': int(player['departed_label']),
            'predicted_departed': 1 if departure_prob > 0.5 else 0
        })
    predictions.sort(key=lambda x: x['departure_probability'], reverse=True)
    correct = sum(1 for p in predictions if p['predicted_departed'] == p['actual_departed'])
    accuracy = correct / len(predictions) if predictions else 0
    actuals = [p['actual_departed'] for p in predictions]
    predicted = [p['predicted_departed'] for p in predictions]
    probs = [p['departure_probability'] for p in predictions]
    try:
        pr_auc = average_precision_score(actuals, probs) if len(set(actuals)) > 1 else 0.0
        kappa = cohen_kappa_score(actuals, predicted)
        brier = brier_score_loss(actuals, probs)
        balanced_acc = balanced_accuracy_score(actuals, predicted)
        mcc = matthews_corrcoef(actuals, predicted)
        print("GA Algorithm - Final Results")
        print("=" * 40)
        print("Optimized Weights:")
        for position, weights in optimized_weights.items():
            print(f"\n{position}:")
            for name, value in weights.items():
                print(f"  {name}: {value:.6f}")
        print(f"\nML Performance Metrics:")
        print(f"  accuracy: {accuracy:.4f}")
        print(f"  precision: {precision_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  recall: {recall_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  f1_score: {f1_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  pr_auc: {pr_auc:.4f}")
        print(f"  cohen_kappa: {kappa:.4f}")
        print(f"  balanced_accuracy: {balanced_acc:.4f}")
        print(f"  mcc: {mcc:.4f}")
        print(f"  brier_score: {brier:.4f}")
        print(f"\nPlayer Predictions:")
        for pred in predictions:
            status = "DEPARTED" if pred['actual_departed'] == 1 else "STAYED"
            print(f"  {pred['player']} ({pred['position']}): "
                  f"Departure={pred['departure_probability']:.1%}, "
                  f"Stay={pred['stay_probability']:.1%} - Actual: {status}")
        results['ml_metrics'] = {
            'accuracy': accuracy,
            'precision': precision_score(actuals, predicted, zero_division=0),
            'recall': recall_score(actuals, predicted, zero_division=0),
            'f1_score': f1_score(actuals, predicted, zero_division=0),
            'pr_auc': pr_auc,
            'cohen_kappa': kappa,
            'brier_score': brier,
            'balanced_accuracy': balanced_acc,
            'mcc': mcc
        }
    except Exception as e:
        pass
    results['predictions'] = predictions
    results['optimized_weights'] = optimized_weights
    results['execution_time'] = time.time() - start_time
    return results

if __name__ == "__main__":
    run_ga_weight_optimization()