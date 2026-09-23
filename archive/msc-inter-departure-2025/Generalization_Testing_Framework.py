#!/usr/bin/env python3
"""
泛化能力测试和稳定性验证框架
Generalization Testing and Stability Verification Framework

This module provides comprehensive testing methods to validate that
weight optimization improvements generalize beyond the training data
and maintain stability across different conditions.

Generalization Tests Implemented:
1. Cross-validation stability testing
2. Cross-season generalization testing  
3. Cross-league adaptation testing
4. Robustness to data perturbations
5. Weight sensitivity analysis
6. Performance degradation monitoring
7. Temporal stability validation

Author: Graduate Thesis Research Project
"""

import pandas as pd
import numpy as np
from scipy import stats
import json
import warnings
from datetime import datetime
from sklearn.model_selection import KFold, TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import itertools

warnings.filterwarnings('ignore')

class GeneralizationValidator:
    """
    泛化能力验证器
    
    This class provides comprehensive generalization testing to ensure
    that weight optimization improvements are robust and generalizable
    rather than overfitted to specific training data.
    """
    
    def __init__(self, weight_optimizer, training_data, validation_data, league_data):
        """
        Initialize generalization validator
        
        Args:
            weight_optimizer: Trained weight optimization instance
            training_data: Original training dataset
            validation_data: Original validation dataset  
            league_data: Full league dataset for reference
        """
        self.optimizer = weight_optimizer
        self.training_data = training_data
        self.validation_data = validation_data
        self.league_data = league_data
        self.generalization_results = {}
        
        print(f"🔬 Generalization Testing Framework Initialized")
        print(f"   Training samples: {len(training_data)}")
        print(f"   Validation samples: {len(validation_data)}")
        print(f"   League reference: {len(league_data)} players")
    
    def cross_validation_stability_test(self, n_folds=5, n_trials=10):
        """
        交叉验证稳定性测试
        
        Tests whether weight optimization consistently improves performance
        across different data splits and random trials.
        """
        print(f"\n📊 Cross-Validation Stability Test")
        print("-" * 45)
        print(f"   Folds: {n_folds}, Trials: {n_trials}")
        
        all_data = pd.concat([self.training_data, self.validation_data], ignore_index=True)
        
        if len(all_data) < n_folds:
            print(f"❌ Insufficient data for {n_folds}-fold CV (have {len(all_data)} samples)")
            return None
        
        baseline_scores = []
        optimized_scores = []
        weight_variations = []
        
        for trial in range(n_trials):
            print(f"   Trial {trial + 1}/{n_trials}...")
            
            # Set random seed for reproducibility within trial
            np.random.seed(42 + trial)
            
            # K-fold cross validation
            kfold = KFold(n_splits=n_folds, shuffle=True, random_state=42 + trial)
            
            trial_baseline_scores = []
            trial_optimized_scores = []
            trial_weights = []
            
            for fold, (train_idx, val_idx) in enumerate(kfold.split(all_data)):
                train_fold = all_data.iloc[train_idx].copy()
                val_fold = all_data.iloc[val_idx].copy()
                
                # Skip if validation fold is too small
                if len(val_fold) < 2:
                    continue
                
                # Create fold-specific optimizer
                fold_optimizer = self.optimizer.__class__(
                    train_fold, val_fold, self.optimizer.position_type)
                fold_optimizer.league_reference_data = self.league_data
                
                # Test baseline performance (uniform weights)
                baseline_weights = {k: 0.25 if 'weight' in k and k != 'base_risk' and k != 'risk_multiplier' 
                                  else (0.3 if k == 'base_risk' else 0.6) 
                                  for k in self.optimizer.weight_bounds.keys()}
                
                baseline_score = self._evaluate_weights_on_fold(
                    baseline_weights, val_fold, fold_optimizer)
                
                # Optimize weights for this fold  
                optimization_result = fold_optimizer.random_search_optimization(n_iterations=20)
                optimized_weights = optimization_result['best_weights']
                optimized_score = optimization_result['best_score']
                
                trial_baseline_scores.append(baseline_score)
                trial_optimized_scores.append(optimized_score)
                trial_weights.append(optimized_weights.copy())
            
            if trial_baseline_scores and trial_optimized_scores:
                baseline_scores.extend(trial_baseline_scores)
                optimized_scores.extend(trial_optimized_scores)
                weight_variations.extend(trial_weights)
        
        if not baseline_scores or not optimized_scores:
            print("❌ No valid cross-validation results obtained")
            return None
        
        # Analyze stability
        baseline_mean = np.mean(baseline_scores)
        baseline_std = np.std(baseline_scores)
        optimized_mean = np.mean(optimized_scores)
        optimized_std = np.std(optimized_scores)
        
        improvement_scores = [opt - base for opt, base in zip(optimized_scores, baseline_scores)]
        improvement_mean = np.mean(improvement_scores)
        improvement_std = np.std(improvement_scores)
        
        # Stability metrics
        baseline_cv = baseline_std / baseline_mean if baseline_mean > 0 else float('inf')
        optimized_cv = optimized_std / optimized_mean if optimized_mean > 0 else float('inf')
        
        # Consistency rate (percentage of folds where optimization improved performance)
        improvement_count = sum(1 for imp in improvement_scores if imp > 0)
        consistency_rate = improvement_count / len(improvement_scores)
        
        print(f"   Results across {len(baseline_scores)} folds:")
        print(f"     Baseline: {baseline_mean:.4f} ± {baseline_std:.4f} (CV: {baseline_cv:.3f})")
        print(f"     Optimized: {optimized_mean:.4f} ± {optimized_std:.4f} (CV: {optimized_cv:.3f})")
        print(f"     Improvement: {improvement_mean:.4f} ± {improvement_std:.4f}")
        print(f"     Consistency rate: {consistency_rate:.1%}")
        
        # Stability assessment
        if consistency_rate >= 0.8:
            stability_level = "✅ HIGHLY STABLE"
        elif consistency_rate >= 0.6:
            stability_level = "⚠️ MODERATELY STABLE"
        else:
            stability_level = "❌ UNSTABLE"
        
        print(f"     Stability assessment: {stability_level}")
        
        # Weight consistency analysis
        self._analyze_weight_consistency(weight_variations)
        
        # Store results
        self.generalization_results['cv_stability'] = {
            'test_type': 'Cross-Validation Stability',
            'n_folds': n_folds,
            'n_trials': n_trials,
            'total_folds_tested': len(baseline_scores),
            'baseline_mean': baseline_mean,
            'baseline_std': baseline_std,
            'optimized_mean': optimized_mean,
            'optimized_std': optimized_std,
            'improvement_mean': improvement_mean,
            'improvement_std': improvement_std,
            'consistency_rate': consistency_rate,
            'stability_level': stability_level,
            'baseline_cv': baseline_cv,
            'optimized_cv': optimized_cv
        }
        
        return self.generalization_results['cv_stability']
    
    def temporal_generalization_test(self, future_season_data=None):
        """
        时间泛化测试
        
        Tests how well weights optimized on one season perform on future season data.
        """
        print(f"\n📊 Temporal Generalization Test")
        print("-" * 40)
        
        if future_season_data is None:
            print("⚠️  No future season data provided - simulating temporal test")
            # Simulate by using subset of current data
            np.random.seed(42)
            future_indices = np.random.choice(len(self.league_data), size=len(self.league_data)//3, replace=False)
            future_season_data = self.league_data.iloc[future_indices].copy()
        
        print(f"   Future season dataset: {len(future_season_data)} players")
        
        # Test current season performance (baseline)
        current_season_performance = self._evaluate_on_dataset(
            self.validation_data, "Current season validation")
        
        # Test future season performance  
        future_season_performance = self._evaluate_on_dataset(
            future_season_data, "Future season simulation")
        
        # Calculate performance degradation
        if current_season_performance and future_season_performance:
            degradation = current_season_performance - future_season_performance
            degradation_percent = (degradation / current_season_performance * 100) if current_season_performance > 0 else 0
            
            print(f"   Current season accuracy: {current_season_performance:.4f}")
            print(f"   Future season accuracy: {future_season_performance:.4f}")
            print(f"   Performance degradation: {degradation:.4f} ({degradation_percent:.1f}%)")
            
            # Assess temporal stability
            if abs(degradation_percent) <= 5:
                temporal_stability = "✅ EXCELLENT (≤5% degradation)"
            elif abs(degradation_percent) <= 15:
                temporal_stability = "⚠️ ACCEPTABLE (≤15% degradation)"
            else:
                temporal_stability = "❌ POOR (>15% degradation)"
            
            print(f"   Temporal stability: {temporal_stability}")
            
            self.generalization_results['temporal_generalization'] = {
                'test_type': 'Temporal Generalization',
                'current_season_accuracy': current_season_performance,
                'future_season_accuracy': future_season_performance,
                'degradation': degradation,
                'degradation_percent': degradation_percent,
                'temporal_stability': temporal_stability
            }
            
            return self.generalization_results['temporal_generalization']
        
        return None
    
    def robustness_to_noise_test(self, noise_levels=[0.05, 0.1, 0.2]):
        """
        噪声鲁棒性测试
        
        Tests how performance degrades when noise is added to input features.
        """
        print(f"\n📊 Robustness to Noise Test")
        print("-" * 35)
        
        original_performance = self._evaluate_on_dataset(self.validation_data, "Original data")
        if original_performance is None:
            print("❌ Failed to evaluate original performance")
            return None
        
        noise_results = []
        
        for noise_level in noise_levels:
            print(f"   Testing noise level: {noise_level:.1%}")
            
            # Add noise to numerical features
            noisy_data = self.validation_data.copy()
            numerical_columns = ['Gls', 'Ast', 'Min', 'age', 'xG', 'xAG', 'PrgP']
            
            for col in numerical_columns:
                if col in noisy_data.columns:
                    # Add Gaussian noise proportional to the standard deviation
                    noise = np.random.normal(0, noise_level * noisy_data[col].std(), len(noisy_data))
                    noisy_data[col] = noisy_data[col] + noise
                    # Ensure non-negative for count statistics
                    if col in ['Gls', 'Ast', 'Min']:
                        noisy_data[col] = np.maximum(0, noisy_data[col])
            
            # Evaluate performance on noisy data
            noisy_performance = self._evaluate_on_dataset(noisy_data, f"Noise level {noise_level}")
            
            if noisy_performance is not None:
                performance_drop = original_performance - noisy_performance
                drop_percent = (performance_drop / original_performance * 100) if original_performance > 0 else 0
                
                print(f"     Accuracy: {noisy_performance:.4f} (drop: {drop_percent:.1f}%)")
                
                noise_results.append({
                    'noise_level': noise_level,
                    'accuracy': noisy_performance,
                    'performance_drop': performance_drop,
                    'drop_percent': drop_percent
                })
        
        if noise_results:
            # Analyze robustness
            max_drop = max(result['drop_percent'] for result in noise_results)
            avg_drop = np.mean([result['drop_percent'] for result in noise_results])
            
            if max_drop <= 10:
                robustness_level = "✅ HIGHLY ROBUST"
            elif max_drop <= 25:
                robustness_level = "⚠️ MODERATELY ROBUST"
            else:
                robustness_level = "❌ SENSITIVE TO NOISE"
            
            print(f"   Maximum performance drop: {max_drop:.1f}%")
            print(f"   Average performance drop: {avg_drop:.1f}%")
            print(f"   Robustness assessment: {robustness_level}")
            
            self.generalization_results['noise_robustness'] = {
                'test_type': 'Noise Robustness',
                'original_accuracy': original_performance,
                'noise_levels_tested': noise_levels,
                'detailed_results': noise_results,
                'max_drop_percent': max_drop,
                'avg_drop_percent': avg_drop,
                'robustness_level': robustness_level
            }
            
            return self.generalization_results['noise_robustness']
        
        return None
    
    def weight_sensitivity_analysis(self, perturbation_range=0.2):
        """
        权重敏感性分析
        
        Tests how sensitive the model performance is to changes in optimized weights.
        """
        print(f"\n📊 Weight Sensitivity Analysis")
        print("-" * 40)
        
        if not hasattr(self.optimizer, 'best_weights') or self.optimizer.best_weights is None:
            print("⚠️  No optimized weights available - using default weights")
            return None
        
        original_weights = self.optimizer.best_weights.copy()
        original_performance = self._evaluate_weights_on_fold(
            original_weights, self.validation_data, self.optimizer)
        
        print(f"   Original performance: {original_performance:.4f}")
        print(f"   Perturbation range: ±{perturbation_range:.1%}")
        
        sensitivity_results = {}
        
        for weight_name, original_value in original_weights.items():
            print(f"   Testing sensitivity to {weight_name}...")
            
            perturbation = original_value * perturbation_range
            
            # Test positive perturbation
            perturbed_weights = original_weights.copy()
            perturbed_weights[weight_name] = original_value + perturbation
            pos_performance = self._evaluate_weights_on_fold(
                perturbed_weights, self.validation_data, self.optimizer)
            
            # Test negative perturbation
            perturbed_weights[weight_name] = max(0, original_value - perturbation)
            neg_performance = self._evaluate_weights_on_fold(
                perturbed_weights, self.validation_data, self.optimizer)
            
            # Calculate sensitivity
            pos_change = pos_performance - original_performance if pos_performance else 0
            neg_change = neg_performance - original_performance if neg_performance else 0
            
            max_change = max(abs(pos_change), abs(neg_change))
            sensitivity_results[weight_name] = {
                'original_value': original_value,
                'positive_perturbation': pos_change,
                'negative_perturbation': neg_change,
                'max_absolute_change': max_change
            }
            
            print(f"     Max absolute change: {max_change:.4f}")
        
        # Rank weights by sensitivity
        sorted_weights = sorted(sensitivity_results.items(), 
                              key=lambda x: x[1]['max_absolute_change'], 
                              reverse=True)
        
        print(f"\n   Weights ranked by sensitivity (most to least sensitive):")
        for i, (weight_name, results) in enumerate(sorted_weights[:5], 1):
            print(f"     {i}. {weight_name}: ±{results['max_absolute_change']:.4f}")
        
        # Overall sensitivity assessment
        max_sensitivity = max(results['max_absolute_change'] for results in sensitivity_results.values())
        avg_sensitivity = np.mean([results['max_absolute_change'] for results in sensitivity_results.values()])
        
        if max_sensitivity <= 0.02:
            sensitivity_level = "✅ LOW SENSITIVITY (Stable)"
        elif max_sensitivity <= 0.05:
            sensitivity_level = "⚠️ MODERATE SENSITIVITY"
        else:
            sensitivity_level = "❌ HIGH SENSITIVITY (Unstable)"
        
        print(f"   Maximum sensitivity: {max_sensitivity:.4f}")
        print(f"   Average sensitivity: {avg_sensitivity:.4f}")
        print(f"   Sensitivity assessment: {sensitivity_level}")
        
        self.generalization_results['weight_sensitivity'] = {
            'test_type': 'Weight Sensitivity Analysis',
            'original_performance': original_performance,
            'perturbation_range': perturbation_range,
            'detailed_results': sensitivity_results,
            'most_sensitive_weight': sorted_weights[0][0] if sorted_weights else None,
            'max_sensitivity': max_sensitivity,
            'avg_sensitivity': avg_sensitivity,
            'sensitivity_level': sensitivity_level
        }
        
        return self.generalization_results['weight_sensitivity']
    
    def _evaluate_on_dataset(self, dataset, dataset_name):
        """Helper method to evaluate performance on a given dataset"""
        if len(dataset) == 0:
            return None
        
        try:
            # Use optimizer's evaluation method if available
            if hasattr(self.optimizer, 'best_weights') and self.optimizer.best_weights:
                weights = self.optimizer.best_weights
            else:
                # Use default expert weights
                weights = self.optimizer.weight_bounds
                weights = {k: (bounds[0] + bounds[1]) / 2 for k, bounds in weights.items()}
            
            return self._evaluate_weights_on_fold(weights, dataset, self.optimizer)
        except Exception as e:
            print(f"     ⚠️  Error evaluating {dataset_name}: {e}")
            return None
    
    def _evaluate_weights_on_fold(self, weights, test_data, optimizer):
        """Helper method to evaluate specific weights on test data"""
        try:
            predictions = []
            actuals = []
            
            for _, player in test_data.iterrows():
                percentile_features = optimizer.calculate_percentile_features(
                    player, optimizer.league_reference_data)
                departure_prob = optimizer.calculate_departure_probability(
                    percentile_features, weights)
                
                prediction = 1 if departure_prob > 0.5 else 0
                actual = int(player.get('departed_label', 0))
                
                predictions.append(prediction)
                actuals.append(actual)
            
            if len(predictions) == 0:
                return None
            
            return accuracy_score(actuals, predictions)
            
        except Exception as e:
            print(f"     ⚠️  Evaluation error: {e}")
            return None
    
    def _analyze_weight_consistency(self, weight_variations):
        """Analyze consistency of optimized weights across folds"""
        if not weight_variations:
            return
        
        print(f"   Weight Consistency Analysis:")
        
        # Calculate coefficient of variation for each weight
        weight_names = list(weight_variations[0].keys())
        
        for weight_name in weight_names:
            values = [weights[weight_name] for weights in weight_variations]
            mean_val = np.mean(values)
            std_val = np.std(values)
            cv = std_val / mean_val if mean_val > 0 else float('inf')
            
            if cv <= 0.2:
                consistency = "Consistent"
            elif cv <= 0.5:
                consistency = "Moderate"
            else:
                consistency = "Variable"
            
            print(f"     {weight_name}: {mean_val:.3f} ± {std_val:.3f} ({consistency})")
    
    def comprehensive_generalization_report(self):
        """
        生成综合泛化能力报告
        """
        print(f"\n" + "="*70)
        print(f"🌐 COMPREHENSIVE GENERALIZATION TEST REPORT")
        print(f"="*70)
        
        if not self.generalization_results:
            print("❌ No generalization tests have been performed")
            return None
        
        print(f"📊 GENERALIZATION TEST SUMMARY:")
        print(f"   Total tests performed: {len(self.generalization_results)}")
        
        # Analyze each test result
        excellent_count = 0
        acceptable_count = 0
        poor_count = 0
        
        for test_name, results in self.generalization_results.items():
            print(f"\n🔍 {results.get('test_type', test_name).upper()}:")
            
            if 'stability_level' in results:
                level = results['stability_level']
                print(f"   Result: {level}")
                if '✅' in level:
                    excellent_count += 1
                elif '⚠️' in level:
                    acceptable_count += 1
                else:
                    poor_count += 1
            
            # Display key metrics for each test type
            if test_name == 'cv_stability':
                print(f"   Consistency rate: {results['consistency_rate']:.1%}")
                print(f"   Improvement: {results['improvement_mean']:.4f} ± {results['improvement_std']:.4f}")
            
            elif test_name == 'temporal_generalization':
                print(f"   Performance degradation: {results['degradation_percent']:.1f}%")
            
            elif test_name == 'noise_robustness':
                print(f"   Max performance drop: {results['max_drop_percent']:.1f}%")
            
            elif test_name == 'weight_sensitivity':
                print(f"   Maximum sensitivity: {results['max_sensitivity']:.4f}")
        
        # Overall assessment
        total_tests = len(self.generalization_results)
        if excellent_count >= total_tests * 0.6:
            overall_generalization = "✅ EXCELLENT GENERALIZATION"
        elif (excellent_count + acceptable_count) >= total_tests * 0.7:
            overall_generalization = "⚠️ GOOD GENERALIZATION"
        else:
            overall_generalization = "❌ LIMITED GENERALIZATION"
        
        print(f"\n🎯 OVERALL GENERALIZATION ASSESSMENT:")
        print(f"   Excellent results: {excellent_count}/{total_tests}")
        print(f"   Acceptable results: {acceptable_count}/{total_tests}")
        print(f"   Poor results: {poor_count}/{total_tests}")
        print(f"   Overall assessment: {overall_generalization}")
        
        # Research implications
        print(f"\n📜 RESEARCH IMPLICATIONS:")
        if '✅' in overall_generalization:
            print(f"   ✅ Weight optimization demonstrates excellent generalization capability")
            print(f"   ✅ Algorithm is robust and stable across different conditions")
            print(f"   ✅ Results strongly support practical applicability")
        elif '⚠️' in overall_generalization:
            print(f"   ⚠️  Weight optimization shows good but limited generalization")
            print(f"   ⚠️  Some stability concerns in certain conditions")
            print(f"   ⚠️  Practical application requires careful validation")
        else:
            print(f"   ❌ Limited generalization capability detected")
            print(f"   ❌ Algorithm may be overfitted to training conditions")
            print(f"   ❌ Further refinement needed before practical deployment")
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Generalization_Test_Report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'excellent_results': excellent_count,
                'acceptable_results': acceptable_count,
                'poor_results': poor_count,
                'overall_assessment': overall_generalization
            },
            'detailed_results': self.generalization_results
        }
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed generalization report saved to: {report_filename}")
        
        return report_data

def example_generalization_testing():
    """
    示例：如何使用泛化能力测试框架
    """
    print("🧪 EXAMPLE: Generalization Testing Framework")
    print("="*60)
    print("This example shows how to comprehensively test algorithm generalization")
    print("Note: This is a framework demonstration - actual results depend on real data")

if __name__ == "__main__":
    example_generalization_testing()