#!/usr/bin/env python3
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             average_precision_score, roc_auc_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)
import warnings
warnings.filterwarnings('ignore')
from GA_Weight_Optimization_Experiment_Final import run_ga_weight_optimization
from PSO_Weight_Optimization_Experiment_Final import run_pso_weight_optimization
from SA_Weight_Optimization_Experiment_Final import run_sa_weight_optimization
from RS_Weight_Optimization_Experiment_Final import run_rs_weight_optimization
from Algorithm_Comparison_Visualization import AlgorithmComparisonVisualization

class SingleRunTestFramework:
    def __init__(self):
        self.algorithms = {
            'GA': run_ga_weight_optimization,
            'PSO': run_pso_weight_optimization,
            'SA': run_sa_weight_optimization,
            'RS': run_rs_weight_optimization
        }
        self.results = {}
    
    def test_single_algorithm(self, alg_name, alg_function):
        try:
            start_time = time.time()
            result = alg_function()
            execution_time = time.time() - start_time
            if result:
                if 'ml_metrics' in result:
                    ml_metrics = result['ml_metrics']
                    accuracy = ml_metrics.get('accuracy', 0)
                    pr_auc = ml_metrics.get('pr_auc', 0)
                    f1_score_val = ml_metrics.get('f1_score', 0)
                elif 'overall_ml_metrics' in result:
                    overall_metrics = result['overall_ml_metrics']
                    accuracy = overall_metrics.get('accuracy', 0)
                    pr_auc = overall_metrics.get('pr_auc', 0)
                    f1_score_val = overall_metrics.get('f1_score', 0)
                else:
                    pass
                if 'optimized_weights' in result:
                    weights = result['optimized_weights']
                elif 'weights' in result:
                    weights = result['weights']
                else:
                    pass
                if 'predictions' in result:
                    predictions = result['predictions']
                else:
                    pass
                return {
                    'success': True,
                    'execution_time': execution_time,
                    'result': result
                }
            else:
                pass
                return {
                    'success': False,
                    'error': 'Algorithm returned None'
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_ml_metrics_to_txt(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Single Run Machine Learning Metrics Comparison\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Core ML Metrics Table
            f.write("MACHINE LEARNING PERFORMANCE METRICS\n")
            f.write("-" * 50 + "\n")
            f.write(f"{'Algorithm':<12} {'Accuracy':<10} {'PR-AUC':<10} {'Bal-Acc':<10} {'Cohen-K':<10} {'MCC':<10} {'Brier':<10} {'Exec-Time':<12}\n")
            f.write("-" * 94 + "\n")
            
            # Calculate composite scores to find best algorithm
            best_algorithm = None
            best_composite_score = -1
            best_weights = None
            
            for alg_name, test_result in self.results.items():
                if test_result['success']:
                    result = test_result['result']
                    execution_time = test_result['execution_time']
                    
                    # Extract ML metrics
                    if 'ml_metrics' in result:
                        ml_metrics = result['ml_metrics']
                    elif 'overall_ml_metrics' in result:
                        ml_metrics = result['overall_ml_metrics']
                    else:
                        ml_metrics = {}
                    
                    accuracy = ml_metrics.get('accuracy', 0)
                    pr_auc = ml_metrics.get('pr_auc', 0)
                    balanced_acc = ml_metrics.get('balanced_accuracy', 0)
                    cohen_kappa = ml_metrics.get('cohen_kappa', 0)
                    mcc = ml_metrics.get('mcc', 0)
                    brier_score = ml_metrics.get('brier_score', 1)
                    
                    # Calculate composite score (same formula as multi-run)
                    f1_score_val = ml_metrics.get('f1_score', accuracy)  # fallback to accuracy
                    composite_score = (
                        0.40 * pr_auc +
                        0.30 * f1_score_val + 
                        0.20 * balanced_acc +
                        0.10 * (1 - brier_score)
                    )
                    
                    # Check if this is the best algorithm
                    if composite_score > best_composite_score:
                        best_composite_score = composite_score
                        best_algorithm = alg_name
                        best_weights = result.get('optimized_weights') or result.get('weights')
                    
                    # Write metrics row
                    f.write(f"{alg_name:<12} {accuracy:<10.4f} {pr_auc:<10.4f} {balanced_acc:<10.4f} {cohen_kappa:<10.4f} {mcc:<10.4f} {brier_score:<10.4f} {execution_time:<12.2f}\n")
                else:
                    f.write(f"{alg_name:<12} {'FAILED':<10} {'FAILED':<10} {'FAILED':<10} {'FAILED':<10} {'FAILED':<10} {'FAILED':<10} {'ERROR':<12}\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
            
            # Best Algorithm Section
            if best_algorithm:
                f.write("BEST PERFORMING ALGORITHM\n")
                f.write("-" * 30 + "\n")
                f.write(f"Best Algorithm: {best_algorithm}\n")
                f.write(f"Composite Score: {best_composite_score:.6f}\n")
                f.write(f"Composite Formula: 0.4×PR-AUC + 0.3×F1 + 0.2×Balanced_Acc + 0.1×(1-Brier)\n\n")
                
                # Best Algorithm's Optimized Weights
                if best_weights:
                    f.write(f"OPTIMAL WEIGHTS CONFIGURATION ({best_algorithm})\n")
                    f.write("-" * 40 + "\n")
                    
                    for position, position_weights in best_weights.items():
                        f.write(f"{position}:\n")
                        if isinstance(position_weights, dict):
                            # Group weights by type for better readability
                            special_weights = {}
                            universal_weights = {}
                            position_specific_weights = {}
                            
                            for weight_name, weight_value in position_weights.items():
                                if weight_name in ['alpha', 'tau', 'risk_multiplier']:
                                    special_weights[weight_name] = weight_value
                                elif weight_name.endswith('_weight') and any(x in weight_name for x in ['minutes', 'CrdY', 'CrdR']):
                                    universal_weights[weight_name] = weight_value
                                else:
                                    position_specific_weights[weight_name] = weight_value
                            
                            # Special parameters (alpha, tau, risk_multiplier)
                            if special_weights:
                                f.write("  Special Parameters:\n")
                                for name, value in special_weights.items():
                                    f.write(f"    {name}: {value:.6f}\n")
                            
                            # Universal weights
                            if universal_weights:
                                f.write("  Universal Weights:\n")
                                for name, value in universal_weights.items():
                                    f.write(f"    {name}: {value:.6f}\n")
                            
                            # Position-specific weights
                            if position_specific_weights:
                                f.write("  Position-Specific Weights:\n")
                                for name, value in position_specific_weights.items():
                                    f.write(f"    {name}: {value:.6f}\n")
                        f.write("\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def run_all_tests(self):
        overall_start_time = time.time()
        for alg_name, alg_function in self.algorithms.items():
            test_result = self.test_single_algorithm(alg_name, alg_function)
            self.results[alg_name] = test_result
        overall_execution_time = time.time() - overall_start_time
        successful_algorithms = []
        failed_algorithms = []
        for alg_name, test_result in self.results.items():
            if test_result['success']:
                successful_algorithms.append(alg_name)
            else:
                failed_algorithms.append(alg_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"Single_Run_Test_Results_{timestamp}.json"
        metrics_file = f"Single_Run_ML_Metrics_{timestamp}.txt"
        self.save_ml_metrics_to_txt(metrics_file)
        
        print(f"\nSingle Run Test Framework Results")
        print("=" * 50)
        print(f"Successful algorithms: {len(successful_algorithms)}/{len(self.algorithms)}")
        if successful_algorithms:
            print(f"Success: {', '.join(successful_algorithms)}")
        if failed_algorithms:
            print(f"Failed: {', '.join(failed_algorithms)}")
        print(f"ML Metrics saved to: {metrics_file}")
        print(f"Total execution time: {overall_execution_time:.2f} seconds")
        
        if successful_algorithms:
            try:
                visualizer = AlgorithmComparisonVisualization()
                chart_paths = visualizer.create_all_charts(self.results, "Single_Run_Test")
                if chart_paths:
                    print(f"Visualization charts created")
            except Exception as e:
                pass
        return self.results

def main():
    framework = SingleRunTestFramework()
    results = framework.run_all_tests()

if __name__ == "__main__":
    main()