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
from GA_Weight_Optimization_Experiment_Updated import run_ga_weight_optimization
from PSO_Weight_Optimization_Experiment_Updated import run_pso_weight_optimization
from SA_Weight_Optimization_Experiment_Updated import run_sa_weight_optimization
from RS_Weight_Optimization_Experiment_Updated import run_rs_weight_optimization
from Algorithm_Comparison_Visualization import create_charts_from_multi_run_data

class MultiRunExperimentFramework:
    def __init__(self, n_runs=10):
        self.n_runs = n_runs
        self.algorithms = {
            'GA': run_ga_weight_optimization,
            'PSO': run_pso_weight_optimization,
            'SA': run_sa_weight_optimization,
            'RS': run_rs_weight_optimization
        }
        self.results = {}
        self.averaged_results = {}
    
    def run_single_algorithm_multiple_times(self, alg_name, alg_function):
        run_results = []
        all_run_data = []
        valid_runs = 0
        best_composite_score = -1
        best_weights = None
        for run_i in range(self.n_runs):
            try:
                np.random.seed(42 + run_i)
                result = alg_function()
                if result and (result.get('overall_ml_metrics') or result.get('ml_metrics')):
                    metrics = result.get('overall_ml_metrics') or result.get('ml_metrics')
                    execution_time = result.get('execution_time', 0)
                    optimized_weights = result.get('optimized_weights') or result.get('weights', {})
                    pr_auc = metrics.get('pr_auc', 0.0)
                    f1_score = metrics.get('f1_score', metrics.get('accuracy', 0.0))
                    balanced_acc = metrics.get('balanced_accuracy', 0.0)
                    brier_score = metrics.get('brier_score', 1.0)
                    composite_score = (
                        0.40 * pr_auc +
                        0.30 * f1_score + 
                        0.20 * balanced_acc +
                        0.10 * (1 - brier_score)
                    )
                    run_data = {
                        'run': run_i + 1,
                        'accuracy': metrics.get('accuracy', 0),
                        'pr_auc': pr_auc,
                        'cohen_kappa': metrics.get('cohen_kappa', 0),
                        'brier_score': brier_score,
                        'balanced_accuracy': balanced_acc,
                        'mcc': metrics.get('mcc', 0),
                        'execution_time': execution_time,
                        'composite_score': composite_score
                    }
                    full_run_data = run_data.copy()
                    full_run_data['weights'] = optimized_weights
                    full_run_data['all_metrics'] = metrics
                    all_run_data.append(full_run_data)
                    if composite_score > best_composite_score:
                        best_composite_score = composite_score
                        best_weights = optimized_weights
                    run_results.append(run_data)
                    valid_runs += 1
                else:
                    pass
            except Exception as e:
                pass
        if best_weights:
            pass
        return run_results, all_run_data, best_weights
    
    def calculate_statistics(self, run_results):
        if not run_results:
            return None
        df_runs = pd.DataFrame(run_results)
        stats = {}
        metrics = ['accuracy', 'pr_auc', 'cohen_kappa', 'brier_score', 'balanced_accuracy', 'mcc', 'execution_time']
        
        for metric in metrics:
            if metric in df_runs.columns:
                values = df_runs[metric].dropna()
                if len(values) > 0:
                    stats[f'{metric}_mean'] = values.mean()
                    stats[f'{metric}_std'] = values.std()
                    stats[f'{metric}_min'] = values.min()
                    stats[f'{metric}_max'] = values.max()
                    stats[f'{metric}_median'] = values.median()
                else:
                    stats[f'{metric}_mean'] = 0
                    stats[f'{metric}_std'] = 0
                    stats[f'{metric}_min'] = 0
                    stats[f'{metric}_max'] = 0
                    stats[f'{metric}_median'] = 0
        stats['valid_runs'] = len(df_runs)
        stats['success_rate'] = len(df_runs) / self.n_runs
        return stats
    
    def run_all_algorithms_multiple_times(self):
        overall_start_time = time.time()
        self.best_weights_per_algorithm = {}
        global_best_score = -1
        global_best_algorithm = None
        global_best_weights = None
        for alg_name, alg_function in self.algorithms.items():
            start_time = time.time()
            run_results, all_run_data, best_weights = self.run_single_algorithm_multiple_times(alg_name, alg_function)
            stats = self.calculate_statistics(run_results)
            self.results[alg_name] = {
                'individual_runs': run_results,
                'all_run_data': all_run_data,
                'statistics': stats,
                'best_weights': best_weights
            }
            if best_weights:
                self.best_weights_per_algorithm[alg_name] = best_weights
                if run_results:
                    best_composite = max(run_results, key=lambda x: x['composite_score'])['composite_score']
                    if best_composite > global_best_score:
                        global_best_score = best_composite
                        global_best_algorithm = alg_name
                        global_best_weights = best_weights
            execution_time = time.time() - start_time
            if stats:
                pass
            else:
                pass
        overall_execution_time = time.time() - overall_start_time
        self.global_best = {
            'algorithm': global_best_algorithm,
            'score': global_best_score,
            'weights': global_best_weights
        }
        if global_best_algorithm:
            pass
    
    def generate_averaged_comparison_data(self):
        comparison_data = []
        for alg_name, result in self.results.items():
            stats = result.get('statistics')
            if stats:
                comparison_data.append({
                    'algorithm': alg_name,
                    'accuracy': stats.get('accuracy_mean', 0),
                    'pr_auc': stats.get('pr_auc_mean', 0),
                    'f1_score': stats.get('f1_score_mean', stats.get('accuracy_mean', 0)),
                    'cohen_kappa': stats.get('cohen_kappa_mean', 0),
                    'brier_score': stats.get('brier_score_mean', 1),
                    'balanced_accuracy': stats.get('balanced_accuracy_mean', 0),
                    'mcc': stats.get('mcc_mean', 0),
                    'execution_time': stats.get('execution_time_mean', 0),
                    'success_rate': stats.get('success_rate', 0)
                })
        return comparison_data
    
    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Multi_Run_Experiment_Results_{timestamp}.json"
        full_results = {
            'timestamp': datetime.now().isoformat(),
            'n_runs': self.n_runs,
            'global_best': self.global_best,
            'results': self.results,
            'best_weights_per_algorithm': self.best_weights_per_algorithm
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        optimal_weights_filename = f"Optimal_Weights_{timestamp}.txt"
        with open(optimal_weights_filename, 'w', encoding='utf-8') as f:
            f.write("Multi-Run Weight Optimization Results\n")
            f.write("="*50 + "\n\n")
            if self.global_best['algorithm']:
                f.write(f"Global Best Algorithm: {self.global_best['algorithm']}\n")
                f.write(f"Global Best Score: {self.global_best['score']:.6f}\n\n")
            f.write("Best Weights per Algorithm:\n")
            f.write("-"*30 + "\n\n")
            for alg_name, weights in self.best_weights_per_algorithm.items():
                f.write(f"{alg_name} Algorithm:\n")
                if isinstance(weights, dict):
                    for position, position_weights in weights.items():
                        f.write(f"  {position}:\n")
                        if isinstance(position_weights, dict):
                            for weight_name, weight_value in position_weights.items():
                                f.write(f"    {weight_name}: {weight_value:.8f}\n")
                        f.write("\n")
                f.write("\n")
        return filename, optimal_weights_filename
    
    def run_experiment(self):
        self.run_all_algorithms_multiple_times()
        averaged_data = self.generate_averaged_comparison_data()
        results_file, weights_file = self.save_results()
        try:
            chart_paths = create_charts_from_multi_run_data(self.results, "Multi_Run_Experiment")
        except Exception as e:
            pass
        return self.results

def main():
    framework = MultiRunExperimentFramework(n_runs=5)
    results = framework.run_experiment()

if __name__ == "__main__":
    main()