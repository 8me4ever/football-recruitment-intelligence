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
                pass
            else:
                failed_algorithms.append(alg_name)
                pass
        if successful_algorithms:
            pass
        if failed_algorithms:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"Single_Run_Test_Results_{timestamp}.json"
        pass
        if successful_algorithms:
            try:
                visualizer = AlgorithmComparisonVisualization()
                chart_paths = visualizer.create_all_charts(self.results, "Single_Run_Test")
            except Exception as e:
                pass
        return self.results

def main():
    framework = SingleRunTestFramework()
    results = framework.run_all_tests()

if __name__ == "__main__":
    main()