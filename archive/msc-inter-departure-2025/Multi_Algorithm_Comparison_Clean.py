#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime

from GA_Clean import run_ga_optimization
from PSO_Clean import run_pso_optimization
from SA_Clean import run_sa_optimization
from RS_Clean import run_rs_optimization

def run_all_algorithms():
    print("Multi-Algorithm Weight Optimization Comparison")
    print("=" * 60)
    print("Algorithms: GA, PSO, SA, RS")
    print("Dataset: Inter Milan 2022-2023 -> 2023-2024 Transfer Prediction")
    print("=" * 60)
    
    algorithms = {
        'GA': run_ga_optimization,
        'PSO': run_pso_optimization,
        'SA': run_sa_optimization,
        'RS': run_rs_optimization
    }
    
    results = {}
    overall_start_time = time.time()
    
    for alg_name, alg_function in algorithms.items():
        print(f"\nRunning {alg_name} Algorithm...")
        print("-" * 30)
        
        start_time = time.time()
        try:
            result = alg_function()
            execution_time = time.time() - start_time
            
            if result:
                results[alg_name] = result
                results[alg_name]['execution_time'] = execution_time
                print(f"{alg_name} completed successfully in {execution_time:.2f}s")
            else:
                print(f"{alg_name} failed - no valid result returned")
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"{alg_name} failed after {execution_time:.2f}s: {str(e)}")
    
    total_time = time.time() - overall_start_time
    
    print(f"\n" + "=" * 60)
    print("ALGORITHM COMPARISON SUMMARY")
    print("=" * 60)
    
    if not results:
        print("No algorithms completed successfully.")
        return
    
    print(f"\nPerformance Comparison:")
    print("-" * 50)
    print(f"{'Algorithm':<8} {'Accuracy':<10} {'PR-AUC':<10} {'F1-Score':<10} {'Cohen-K':<10} {'Time(s)':<8}")
    print("-" * 50)
    
    best_algorithm = None
    best_composite_score = -1
    
    for alg_name, result in results.items():
        metrics = result['overall_ml_metrics']
        accuracy = metrics['accuracy']
        pr_auc = metrics['pr_auc']
        f1_score = metrics['f1_score']
        cohen_kappa = metrics['cohen_kappa']
        exec_time = result['execution_time']
        
        composite_score = (
            0.40 * pr_auc +
            0.30 * f1_score + 
            0.20 * metrics['balanced_accuracy'] +
            0.10 * (1 - metrics['brier_score'])
        )
        
        if composite_score > best_composite_score:
            best_composite_score = composite_score
            best_algorithm = alg_name
        
        print(f"{alg_name:<8} {accuracy:<10.3f} {pr_auc:<10.3f} {f1_score:<10.3f} {cohen_kappa:<10.3f} {exec_time:<8.1f}")
    
    print("-" * 50)
    print(f"Best Algorithm: {best_algorithm} (Composite Score: {best_composite_score:.4f})")
    
    print(f"\nDetailed ML Metrics:")
    print("-" * 50)
    for alg_name, result in results.items():
        print(f"\n{alg_name} Algorithm:")
        metrics = result['overall_ml_metrics']
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
    
    print(f"\nOptimal Weights (Best Algorithm: {best_algorithm}):")
    print("-" * 50)
    best_result = results[best_algorithm]
    for position, weights in best_result['optimized_weights'].items():
        print(f"\n{position} Position:")
        for weight_name, weight_value in weights.items():
            print(f"  {weight_name}: {weight_value:.6f}")
    
    print(f"\nPlayer Departure Predictions (Best Algorithm: {best_algorithm}):")
    print("-" * 50)
    predictions = best_result['predictions']
    predictions_sorted = sorted(predictions, key=lambda x: x['departure_probability'], reverse=True)
    
    for pred in predictions_sorted:
        status = "DEPARTED" if pred['actual_departed'] == 1 else "STAYED"
        accuracy_indicator = "✓" if (pred['departure_probability'] > 0.5) == pred['actual_departed'] else "✗"
        print(f"  {accuracy_indicator} {pred['player']} ({pred['position']}): "
              f"Departure={pred['departure_probability']:.1%}, "
              f"Stay={pred['stay_probability']:.1%} - Actual: {status}")
    
    correct_predictions = sum(1 for pred in predictions if (pred['departure_probability'] > 0.5) == pred['actual_departed'])
    total_predictions = len(predictions)
    prediction_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    print(f"\nPrediction Summary:")
    print(f"  Total Players: {total_predictions}")
    print(f"  Correct Predictions: {correct_predictions}")
    print(f"  Prediction Accuracy: {prediction_accuracy:.1%}")
    print(f"  Total Execution Time: {total_time:.1f}s")
    
    print(f"\nExperiment completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return results

if __name__ == "__main__":
    results = run_all_algorithms()