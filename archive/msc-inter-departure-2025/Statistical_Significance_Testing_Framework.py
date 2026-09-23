#!/usr/bin/env python3
"""
统计显著性检验框架
Statistical Significance Testing Framework for Weight Optimization Research

This module provides comprehensive statistical testing methods to validate
the algorithmic improvements achieved through weight optimization.

Statistical Tests Implemented:
1. Paired t-test for mean performance comparison
2. Wilcoxon signed-rank test for non-parametric validation  
3. Effect size analysis (Cohen's d)
4. McNemar's test for classification algorithm comparison
5. Bootstrap confidence intervals
6. Cross-validation statistical validation

Author: Graduate Thesis Research Project
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, wilcoxon, norm
import json
from datetime import datetime
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

class StatisticalSignificanceValidator:
    """
    统计显著性验证器
    
    This class provides comprehensive statistical validation methods
    to prove that weight optimization improvements are statistically significant
    and not due to random chance.
    """
    
    def __init__(self, baseline_results, optimized_results, alpha=0.05):
        """
        Initialize statistical validator
        
        Args:
            baseline_results: Dictionary with baseline performance metrics
            optimized_results: Dictionary with optimized performance metrics  
            alpha: Significance level (default 0.05 for 95% confidence)
        """
        self.baseline_results = baseline_results
        self.optimized_results = optimized_results
        self.alpha = alpha
        self.test_results = {}
        
        print(f"🔬 Statistical Significance Testing Framework")
        print(f"   Significance level (α): {alpha}")
        print(f"   Confidence level: {(1-alpha)*100}%")
    
    def paired_t_test(self, metric='accuracy'):
        """
        配对t检验：检验权重优化前后性能差异的统计显著性
        
        H0: μ_optimized - μ_baseline = 0 (no difference)
        H1: μ_optimized - μ_baseline > 0 (improvement exists)
        """
        print(f"\n📊 Paired t-test for {metric}")
        print("-" * 40)
        
        # Extract baseline and optimized scores
        baseline_scores = []
        optimized_scores = []
        
        for method_name in self.baseline_results:
            if metric in self.baseline_results[method_name]:
                baseline_scores.append(self.baseline_results[method_name][metric])
        
        for method_name in self.optimized_results:
            if metric in self.optimized_results[method_name]:
                optimized_scores.append(self.optimized_results[method_name][metric])
        
        if len(baseline_scores) == 0 or len(optimized_scores) == 0:
            print(f"❌ Insufficient data for {metric} comparison")
            return None
        
        # Ensure equal length by taking minimum
        min_length = min(len(baseline_scores), len(optimized_scores))
        baseline_scores = baseline_scores[:min_length]
        optimized_scores = optimized_scores[:min_length]
        
        # Calculate differences
        differences = [opt - base for opt, base in zip(optimized_scores, baseline_scores)]
        
        # Perform paired t-test
        if len(differences) < 2:
            print(f"⚠️  Insufficient pairs for t-test ({len(differences)} pairs)")
            return None
        
        t_statistic, p_value = ttest_rel(optimized_scores, baseline_scores, alternative='greater')
        
        # Calculate descriptive statistics
        mean_baseline = np.mean(baseline_scores)
        mean_optimized = np.mean(optimized_scores)
        mean_improvement = np.mean(differences)
        std_improvement = np.std(differences)
        
        # Degrees of freedom
        df = len(differences) - 1
        
        # Critical value
        t_critical = stats.t.ppf(1 - self.alpha, df)
        
        # Effect size (Cohen's d for paired samples)
        cohens_d = mean_improvement / std_improvement if std_improvement > 0 else 0
        
        # Interpretation
        if p_value < self.alpha:
            significance = "✅ STATISTICALLY SIGNIFICANT"
            conclusion = "Reject H0: Weight optimization provides significant improvement"
        else:
            significance = "❌ NOT SIGNIFICANT"  
            conclusion = "Fail to reject H0: No significant improvement detected"
        
        # Effect size interpretation
        if abs(cohens_d) >= 0.8:
            effect_interpretation = "Large effect size"
        elif abs(cohens_d) >= 0.5:
            effect_interpretation = "Medium effect size"
        elif abs(cohens_d) >= 0.2:
            effect_interpretation = "Small effect size"
        else:
            effect_interpretation = "Negligible effect size"
        
        print(f"   Sample size: {len(differences)} pairs")
        print(f"   Baseline mean: {mean_baseline:.4f}")
        print(f"   Optimized mean: {mean_optimized:.4f}")
        print(f"   Mean improvement: {mean_improvement:.4f}")
        print(f"   t-statistic: {t_statistic:.4f}")
        print(f"   Critical value: {t_critical:.4f}")
        print(f"   p-value: {p_value:.6f}")
        print(f"   Cohen's d: {cohens_d:.4f} ({effect_interpretation})")
        print(f"   Result: {significance}")
        print(f"   Conclusion: {conclusion}")
        
        # Store results
        self.test_results[f'paired_t_test_{metric}'] = {
            'test_type': 'Paired t-test',
            'metric': metric,
            'sample_size': len(differences),
            'baseline_mean': mean_baseline,
            'optimized_mean': mean_optimized,
            'mean_improvement': mean_improvement,
            't_statistic': t_statistic,
            't_critical': t_critical,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'effect_interpretation': effect_interpretation,
            'significant': p_value < self.alpha,
            'conclusion': conclusion
        }
        
        return self.test_results[f'paired_t_test_{metric}']
    
    def wilcoxon_signed_rank_test(self, metric='accuracy'):
        """
        威尔科克森符号秩检验：非参数版本的配对检验
        
        More robust to outliers and non-normal distributions
        """
        print(f"\n📊 Wilcoxon Signed-Rank Test for {metric}")
        print("-" * 45)
        
        # Extract scores (same as t-test)
        baseline_scores = []
        optimized_scores = []
        
        for method_name in self.baseline_results:
            if metric in self.baseline_results[method_name]:
                baseline_scores.append(self.baseline_results[method_name][metric])
        
        for method_name in self.optimized_results:
            if metric in self.optimized_results[method_name]:
                optimized_scores.append(self.optimized_results[method_name][metric])
        
        if len(baseline_scores) == 0 or len(optimized_scores) == 0:
            print(f"❌ Insufficient data for {metric} comparison")
            return None
        
        min_length = min(len(baseline_scores), len(optimized_scores))
        baseline_scores = baseline_scores[:min_length]
        optimized_scores = optimized_scores[:min_length]
        
        if len(baseline_scores) < 3:
            print(f"⚠️  Insufficient pairs for Wilcoxon test ({len(baseline_scores)} pairs)")
            return None
        
        # Perform Wilcoxon signed-rank test
        statistic, p_value = wilcoxon(
            optimized_scores, baseline_scores, 
            alternative='greater',
            zero_method='wilcox'
        )
        
        # Calculate median improvement
        differences = [opt - base for opt, base in zip(optimized_scores, baseline_scores)]
        median_improvement = np.median(differences)
        
        # Interpretation
        if p_value < self.alpha:
            significance = "✅ STATISTICALLY SIGNIFICANT"
            conclusion = "Reject H0: Optimization provides significant improvement (non-parametric)"
        else:
            significance = "❌ NOT SIGNIFICANT"
            conclusion = "Fail to reject H0: No significant improvement (non-parametric)"
        
        print(f"   Sample size: {len(baseline_scores)} pairs")
        print(f"   Median baseline: {np.median(baseline_scores):.4f}")
        print(f"   Median optimized: {np.median(optimized_scores):.4f}")
        print(f"   Median improvement: {median_improvement:.4f}")
        print(f"   W-statistic: {statistic:.4f}")
        print(f"   p-value: {p_value:.6f}")
        print(f"   Result: {significance}")
        print(f"   Conclusion: {conclusion}")
        
        # Store results
        self.test_results[f'wilcoxon_{metric}'] = {
            'test_type': 'Wilcoxon Signed-Rank Test',
            'metric': metric,
            'sample_size': len(baseline_scores),
            'median_baseline': np.median(baseline_scores),
            'median_optimized': np.median(optimized_scores),
            'median_improvement': median_improvement,
            'w_statistic': statistic,
            'p_value': p_value,
            'significant': p_value < self.alpha,
            'conclusion': conclusion
        }
        
        return self.test_results[f'wilcoxon_{metric}']
    
    def bootstrap_confidence_interval(self, metric='accuracy', n_bootstrap=1000):
        """
        自助法置信区间：估计改进效果的置信区间
        
        Uses bootstrap resampling to estimate confidence intervals
        for the improvement without distributional assumptions
        """
        print(f"\n📊 Bootstrap Confidence Interval for {metric}")
        print("-" * 50)
        
        # Extract scores
        baseline_scores = []
        optimized_scores = []
        
        for method_name in self.baseline_results:
            if metric in self.baseline_results[method_name]:
                baseline_scores.append(self.baseline_results[method_name][metric])
        
        for method_name in self.optimized_results:
            if metric in self.optimized_results[method_name]:
                optimized_scores.append(self.optimized_results[method_name][metric])
        
        if len(baseline_scores) == 0 or len(optimized_scores) == 0:
            print(f"❌ Insufficient data for {metric} comparison")
            return None
        
        min_length = min(len(baseline_scores), len(optimized_scores))
        baseline_scores = np.array(baseline_scores[:min_length])
        optimized_scores = np.array(optimized_scores[:min_length])
        
        # Original improvement
        original_improvement = np.mean(optimized_scores - baseline_scores)
        
        # Bootstrap resampling
        bootstrap_improvements = []
        np.random.seed(42)  # For reproducibility
        
        for _ in range(n_bootstrap):
            # Resample with replacement
            indices = np.random.choice(len(baseline_scores), size=len(baseline_scores), replace=True)
            boot_baseline = baseline_scores[indices]
            boot_optimized = optimized_scores[indices]
            
            # Calculate improvement for this bootstrap sample
            boot_improvement = np.mean(boot_optimized - boot_baseline)
            bootstrap_improvements.append(boot_improvement)
        
        bootstrap_improvements = np.array(bootstrap_improvements)
        
        # Calculate confidence intervals
        confidence_level = (1 - self.alpha) * 100
        lower_percentile = (self.alpha / 2) * 100
        upper_percentile = (1 - self.alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_improvements, lower_percentile)
        ci_upper = np.percentile(bootstrap_improvements, upper_percentile)
        
        # Check if confidence interval excludes zero
        excludes_zero = ci_lower > 0
        
        print(f"   Original improvement: {original_improvement:.4f}")
        print(f"   Bootstrap samples: {n_bootstrap}")
        print(f"   {confidence_level}% Confidence Interval: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"   Excludes zero: {'✅ Yes' if excludes_zero else '❌ No'}")
        
        if excludes_zero:
            print(f"   Interpretation: ✅ Significant improvement with {confidence_level}% confidence")
        else:
            print(f"   Interpretation: ❌ Improvement not significant at {confidence_level}% confidence")
        
        # Store results
        self.test_results[f'bootstrap_ci_{metric}'] = {
            'test_type': 'Bootstrap Confidence Interval',
            'metric': metric,
            'original_improvement': original_improvement,
            'n_bootstrap': n_bootstrap,
            'confidence_level': confidence_level,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'excludes_zero': excludes_zero,
            'significant': excludes_zero
        }
        
        return self.test_results[f'bootstrap_ci_{metric}']
    
    def mcnemar_test(self, baseline_predictions, optimized_predictions, actual_labels):
        """
        McNemar检验：专门用于比较两个分类算法的配对检验
        
        Tests whether the disagreements between two classifiers are significantly different
        """
        print(f"\n📊 McNemar's Test for Classification Comparison")
        print("-" * 50)
        
        if len(baseline_predictions) != len(optimized_predictions) or len(baseline_predictions) != len(actual_labels):
            print("❌ Prediction arrays must have equal length")
            return None
        
        # Create contingency table for McNemar's test
        # Table format:
        #                Optimized Correct
        #                Yes       No
        # Baseline Yes   a         b
        # Correct  No    c         d
        
        baseline_correct = np.array(baseline_predictions) == np.array(actual_labels)
        optimized_correct = np.array(optimized_predictions) == np.array(actual_labels)
        
        # McNemar table
        a = np.sum(baseline_correct & optimized_correct)    # Both correct
        b = np.sum(baseline_correct & ~optimized_correct)   # Baseline correct, optimized wrong
        c = np.sum(~baseline_correct & optimized_correct)   # Baseline wrong, optimized correct  
        d = np.sum(~baseline_correct & ~optimized_correct)  # Both wrong
        
        # McNemar's test statistic
        # Focus on disagreements: b (baseline better) vs c (optimized better)
        if b + c == 0:
            print("⚠️  No disagreements between classifiers - cannot perform McNemar test")
            return None
        
        # McNemar test statistic with continuity correction
        chi_squared = ((abs(b - c) - 1) ** 2) / (b + c)
        p_value = 1 - stats.chi2.cdf(chi_squared, df=1)
        
        # One-tailed p-value for testing if optimized is better
        if c > b:
            p_value_one_tailed = p_value / 2
            direction = "Optimized > Baseline"
        elif b > c:
            p_value_one_tailed = 1 - (p_value / 2)
            direction = "Baseline > Optimized"
        else:
            p_value_one_tailed = 0.5
            direction = "Equal performance"
        
        # Interpretation
        if p_value_one_tailed < self.alpha:
            significance = "✅ STATISTICALLY SIGNIFICANT"
            conclusion = f"Reject H0: {direction} is statistically significant"
        else:
            significance = "❌ NOT SIGNIFICANT"
            conclusion = "Fail to reject H0: No significant difference between classifiers"
        
        print(f"   Contingency Table:")
        print(f"   Both correct (a): {a}")
        print(f"   Baseline better (b): {b}")  
        print(f"   Optimized better (c): {c}")
        print(f"   Both wrong (d): {d}")
        print(f"   χ² statistic: {chi_squared:.4f}")
        print(f"   p-value (two-tailed): {p_value:.6f}")
        print(f"   p-value (one-tailed): {p_value_one_tailed:.6f}")
        print(f"   Direction: {direction}")
        print(f"   Result: {significance}")
        print(f"   Conclusion: {conclusion}")
        
        # Store results
        self.test_results['mcnemar_test'] = {
            'test_type': 'McNemar Test',
            'contingency_table': {'a': a, 'b': b, 'c': c, 'd': d},
            'chi_squared': chi_squared,
            'p_value_two_tailed': p_value,
            'p_value_one_tailed': p_value_one_tailed,
            'direction': direction,
            'significant': p_value_one_tailed < self.alpha,
            'conclusion': conclusion
        }
        
        return self.test_results['mcnemar_test']
    
    def comprehensive_statistical_report(self):
        """
        生成综合统计报告：汇总所有统计检验结果
        """
        print(f"\n" + "="*70)
        print(f"📈 COMPREHENSIVE STATISTICAL SIGNIFICANCE REPORT")
        print(f"="*70)
        
        if not self.test_results:
            print("❌ No statistical tests have been performed yet")
            return
        
        # Count significant results
        total_tests = len(self.test_results)
        significant_tests = sum(1 for test in self.test_results.values() 
                              if test.get('significant', False))
        
        print(f"📊 STATISTICAL TESTING SUMMARY:")
        print(f"   Total tests performed: {total_tests}")
        print(f"   Significant results: {significant_tests}/{total_tests}")
        print(f"   Significance rate: {significant_tests/total_tests*100:.1f}%")
        
        print(f"\n🔍 DETAILED TEST RESULTS:")
        for test_name, results in self.test_results.items():
            status = "✅ SIGNIFICANT" if results.get('significant', False) else "❌ NOT SIGNIFICANT"
            p_value = results.get('p_value', results.get('p_value_one_tailed', 'N/A'))
            
            print(f"   {results['test_type']}: {status}")
            if isinstance(p_value, (int, float)):
                print(f"     p-value: {p_value:.6f}")
            print(f"     Conclusion: {results.get('conclusion', 'N/A')}")
        
        # Overall conclusion
        if significant_tests >= total_tests * 0.5:  # Majority of tests significant
            overall_conclusion = (
                "✅ STRONG STATISTICAL EVIDENCE: "
                "Weight optimization provides statistically significant improvements"
            )
        elif significant_tests > 0:
            overall_conclusion = (
                "⚠️ MODERATE EVIDENCE: "
                "Some statistical evidence for weight optimization improvements"
            )
        else:
            overall_conclusion = (
                "❌ INSUFFICIENT EVIDENCE: "
                "No statistically significant improvements detected"
            )
        
        print(f"\n🎯 OVERALL CONCLUSION:")
        print(f"   {overall_conclusion}")
        
        # Research implications
        print(f"\n📜 RESEARCH IMPLICATIONS:")
        if significant_tests >= total_tests * 0.5:
            print(f"   ✅ The weight optimization algorithm demonstrates statistically")
            print(f"      significant improvements in transfer prediction accuracy")
            print(f"   ✅ Results support the core research hypothesis")
            print(f"   ✅ Algorithmic contribution is validated by rigorous statistical testing")
        else:
            print(f"   ⚠️  Statistical evidence for algorithmic improvement is limited")
            print(f"   ⚠️  Consider larger sample sizes or refined optimization methods")
            print(f"   ⚠️  Further validation may be needed")
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"Statistical_Significance_Report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'significant_tests': significant_tests,
                'significance_rate': significant_tests/total_tests if total_tests > 0 else 0,
                'overall_conclusion': overall_conclusion
            },
            'detailed_results': self.test_results
        }
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed statistical report saved to: {report_filename}")
        
        return report_data

def example_statistical_validation():
    """
    示例：如何使用统计显著性检验框架
    """
    print("🧪 EXAMPLE: Statistical Significance Testing")
    print("="*60)
    
    # Simulate baseline results (multiple methods)
    baseline_results = {
        'uniform_weights': {'accuracy': 0.750, 'f1_score': 0.741},
        'expert_weights': {'accuracy': 0.825, 'f1_score': 0.816}, 
        'random_weights_1': {'accuracy': 0.700, 'f1_score': 0.692},
        'random_weights_2': {'accuracy': 0.775, 'f1_score': 0.768}
    }
    
    # Simulate optimized results  
    optimized_results = {
        'bayesian_optimization': {'accuracy': 0.950, 'f1_score': 0.944},
        'genetic_algorithm': {'accuracy': 0.925, 'f1_score': 0.918},
        'grid_search': {'accuracy': 0.900, 'f1_score': 0.894},
        'random_search': {'accuracy': 0.875, 'f1_score': 0.866}
    }
    
    # Initialize validator
    validator = StatisticalSignificanceValidator(baseline_results, optimized_results)
    
    # Run statistical tests
    validator.paired_t_test('accuracy')
    validator.wilcoxon_signed_rank_test('accuracy')
    validator.bootstrap_confidence_interval('accuracy')
    
    # Simulate classification predictions for McNemar test
    n_samples = 20
    np.random.seed(42)
    actual_labels = np.random.choice([0, 1], n_samples, p=[0.6, 0.4])
    baseline_pred = actual_labels.copy()
    baseline_pred[np.random.choice(n_samples, size=3, replace=False)] = 1 - baseline_pred[np.random.choice(n_samples, size=3, replace=False)]
    
    optimized_pred = actual_labels.copy()
    optimized_pred[np.random.choice(n_samples, size=1, replace=False)] = 1 - optimized_pred[np.random.choice(n_samples, size=1, replace=False)]
    
    validator.mcnemar_test(baseline_pred, optimized_pred, actual_labels)
    
    # Generate comprehensive report
    validator.comprehensive_statistical_report()

if __name__ == "__main__":
    example_statistical_validation()