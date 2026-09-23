#!/usr/bin/env python3
"""
核心算法创新：基于相对百分位排名的多层次概率融合算法权重优化框架
Weight Optimization Framework for Percentile-Based Transfer Prediction

This module implements the core algorithmic contribution of the research:
systematic weight optimization algorithms applied to percentile-based features.

Algorithm Innovation Highlights:
1. Bayesian Optimization for intelligent weight space exploration
2. Genetic Algorithm for evolutionary weight optimization  
3. Grid Search for exhaustive weight space coverage
4. Multi-objective optimization balancing accuracy and generalization

Author: Graduate Thesis Research Project
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import differential_evolution
import json
import time
from datetime import datetime
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# Advanced optimization libraries
try:
    from skopt import gp_minimize
    from skopt.space import Real
    from skopt.utils import use_named_args
    BAYESIAN_AVAILABLE = True
except ImportError:
    print("⚠️  scikit-optimize not available. Install with: pip install scikit-optimize")
    BAYESIAN_AVAILABLE = False

class PercentileWeightOptimizer:
    """
    核心创新类：百分位特征权重优化算法
    
    This class implements the core algorithmic innovation:
    systematic optimization of weights applied to percentile-based features
    for football transfer prediction.
    """
    
    def __init__(self, training_data, validation_data, position_type='Forward'):
        """
        Initialize the weight optimization framework
        
        Args:
            training_data: DataFrame with player stats and departure labels
            validation_data: DataFrame for validation during optimization
            position_type: Position to optimize for ('Forward', 'Midfielder', 'Defender')
        """
        self.training_data = training_data
        self.validation_data = validation_data
        self.position_type = position_type
        self.league_reference_data = None  # Will be loaded for percentile calculation
        
        # Define position-specific weight spaces for optimization
        self.weight_bounds = self._define_weight_bounds()
        self.optimization_history = []
        
        print(f"🚀 Initializing Weight Optimization for {position_type}")
        print(f"   Training samples: {len(training_data)}")
        print(f"   Validation samples: {len(validation_data)}")
    
    def _define_weight_bounds(self):
        """
        定义位置特化的权重优化边界
        Core Innovation: Position-specific weight space definition
        """
        if self.position_type == 'Forward':
            return {
                'goals_weight': (0.2, 0.5),          # 进球权重优化范围
                'assists_weight': (0.1, 0.3),       # 助攻权重优化范围
                'xG_weight': (0.05, 0.25),          # 预期进球权重优化范围
                'minutes_weight': (0.15, 0.4),      # 出场时间权重优化范围
                'age_weight': (0.0, 0.15),          # 年龄权重优化范围
                'base_risk': (0.2, 0.4),            # 基础风险优化范围
                'risk_multiplier': (0.4, 0.8)       # 风险乘数优化范围
            }
        elif self.position_type == 'Midfielder':
            return {
                'assists_weight': (0.2, 0.35),      # 中场助攻权重
                'goals_weight': (0.1, 0.25),        # 中场进球权重
                'xAG_weight': (0.15, 0.3),          # 预期助攻权重
                'progressive_passes_weight': (0.1, 0.25),  # 向前传球权重
                'minutes_weight': (0.1, 0.25),      # 出场时间权重
                'age_weight': (0.0, 0.1),           # 年龄权重
                'base_risk': (0.25, 0.45),
                'risk_multiplier': (0.3, 0.7)
            }
        elif self.position_type == 'Defender':
            return {
                'minutes_weight': (0.25, 0.45),     # 后卫稳定性权重
                'progressive_passes_weight': (0.15, 0.35),  # 组织能力权重
                'assists_weight': (0.1, 0.25),      # 助攻贡献权重
                'goals_weight': (0.05, 0.2),        # 进球贡献权重
                'age_weight': (0.05, 0.2),          # 经验价值权重
                'base_risk': (0.2, 0.4),
                'risk_multiplier': (0.4, 0.8)
            }
        else:  # Default/Unknown
            return {
                'performance_weight': (0.3, 0.7),
                'minutes_weight': (0.2, 0.5),
                'base_risk': (0.2, 0.5),
                'risk_multiplier': (0.3, 0.8)
            }
    
    def calculate_percentile_features(self, player_data, league_data):
        """
        核心特征工程：百分位排名计算
        
        This is the foundational algorithm that converts absolute values
        to relative percentile rankings for fair comparison.
        """
        percentile_features = {}
        position_players = league_data[league_data['position_group'] == self.position_type]
        
        if self.position_type == 'Forward':
            percentile_features['goals_percentile'] = self._calculate_single_percentile(
                player_data.get('Gls', 0), position_players['Gls'].dropna(), True)
            percentile_features['assists_percentile'] = self._calculate_single_percentile(
                player_data.get('Ast', 0), position_players['Ast'].dropna(), True)
            percentile_features['xG_percentile'] = self._calculate_single_percentile(
                player_data.get('xG', 0), position_players['xG'].dropna(), True)
            percentile_features['minutes_percentile'] = self._calculate_single_percentile(
                player_data.get('Min', 0), position_players['Min'].dropna(), True)
            percentile_features['age_percentile'] = self._calculate_single_percentile(
                player_data.get('age', 25), position_players['age'].dropna(), False)
                
        elif self.position_type == 'Midfielder':
            percentile_features['assists_percentile'] = self._calculate_single_percentile(
                player_data.get('Ast', 0), position_players['Ast'].dropna(), True)
            percentile_features['goals_percentile'] = self._calculate_single_percentile(
                player_data.get('Gls', 0), position_players['Gls'].dropna(), True)
            percentile_features['xAG_percentile'] = self._calculate_single_percentile(
                player_data.get('xAG', 0), position_players['xAG'].dropna(), True)
            percentile_features['progressive_passes_percentile'] = self._calculate_single_percentile(
                player_data.get('PrgP', 0), position_players['PrgP'].dropna(), True)
            percentile_features['minutes_percentile'] = self._calculate_single_percentile(
                player_data.get('Min', 0), position_players['Min'].dropna(), True)
            percentile_features['age_percentile'] = self._calculate_single_percentile(
                player_data.get('age', 25), position_players['age'].dropna(), False)
                
        elif self.position_type == 'Defender':
            percentile_features['minutes_percentile'] = self._calculate_single_percentile(
                player_data.get('Min', 0), position_players['Min'].dropna(), True)
            percentile_features['progressive_passes_percentile'] = self._calculate_single_percentile(
                player_data.get('PrgP', 0), position_players['PrgP'].dropna(), True)
            percentile_features['assists_percentile'] = self._calculate_single_percentile(
                player_data.get('Ast', 0), position_players['Ast'].dropna(), True)
            percentile_features['goals_percentile'] = self._calculate_single_percentile(
                player_data.get('Gls', 0), position_players['Gls'].dropna(), True)
            percentile_features['age_percentile'] = self._calculate_single_percentile(
                player_data.get('age', 25), position_players['age'].dropna(), False)
        
        return percentile_features
    
    def _calculate_single_percentile(self, value, reference_data, ascending=True):
        """计算单个指标的百分位排名"""
        if len(reference_data) == 0:
            return 0.5
        
        if ascending:
            percentile = stats.percentileofscore(reference_data, value, kind='rank') / 100
        else:
            percentile = 1 - (stats.percentileofscore(reference_data, value, kind='rank') / 100)
        
        return max(0, min(1, percentile))
    
    def calculate_departure_probability(self, percentile_features, weights):
        """
        核心预测算法：基于百分位特征和优化权重计算离队概率
        
        This is where the optimized weights are applied to percentile features
        to generate transfer probability predictions.
        """
        # Normalize weights to ensure they sum to 1 (excluding base_risk and risk_multiplier)
        weight_keys = [k for k in weights.keys() if k not in ['base_risk', 'risk_multiplier']]
        weight_sum = sum(weights[k] for k in weight_keys)
        
        if weight_sum > 0:
            normalized_weights = {k: weights[k]/weight_sum for k in weight_keys}
        else:
            normalized_weights = {k: 1.0/len(weight_keys) for k in weight_keys}
        
        # Calculate weighted performance score
        performance_score = 0
        for feature, percentile in percentile_features.items():
            weight_key = feature.replace('_percentile', '_weight')
            if weight_key in normalized_weights:
                performance_score += percentile * normalized_weights[weight_key]
        
        # Apply risk calculation with optimized parameters
        base_risk = weights.get('base_risk', 0.3)
        risk_multiplier = weights.get('risk_multiplier', 0.6)
        
        departure_probability = base_risk + (1 - performance_score) * risk_multiplier
        
        # Ensure probability bounds
        return max(0.05, min(0.95, departure_probability))
    
    def objective_function(self, weights_array, weight_keys):
        """
        核心优化目标函数
        
        This function evaluates the performance of a given weight configuration
        and returns a score that the optimization algorithms will try to minimize.
        """
        # Convert array to dictionary
        weights = dict(zip(weight_keys, weights_array))
        
        predictions = []
        actuals = []
        
        # Make predictions on validation data
        for _, player in self.validation_data.iterrows():
            percentile_features = self.calculate_percentile_features(
                player, self.league_reference_data)
            
            departure_prob = self.calculate_departure_probability(
                percentile_features, weights)
            
            prediction = 1 if departure_prob > 0.5 else 0
            actual = player.get('departed_label', 0)
            
            predictions.append(prediction)
            actuals.append(actual)
        
        # Calculate accuracy (minimize negative accuracy to maximize accuracy)
        accuracy = accuracy_score(actuals, predictions)
        f1 = f1_score(actuals, predictions, average='weighted', zero_division=0)
        
        # Multi-objective: balance accuracy and F1-score
        objective_score = -(0.7 * accuracy + 0.3 * f1)
        
        # Store history
        self.optimization_history.append({
            'weights': weights.copy(),
            'accuracy': accuracy,
            'f1_score': f1,
            'objective_score': -objective_score
        })
        
        return objective_score
    
    def bayesian_optimization(self, n_calls=50, random_state=42):
        """
        核心创新算法1: 贝叶斯权重优化
        
        Uses Gaussian Process-based Bayesian optimization to intelligently
        explore the weight space for optimal configurations.
        """
        if not BAYESIAN_AVAILABLE:
            print("❌ Bayesian optimization not available. Using random search instead.")
            return self.random_search_optimization(n_iterations=n_calls)
        
        print(f"🔬 Starting Bayesian Weight Optimization ({n_calls} iterations)")
        start_time = time.time()
        
        # Define optimization space
        weight_keys = list(self.weight_bounds.keys())
        dimensions = [Real(bounds[0], bounds[1], name=key) 
                     for key, bounds in self.weight_bounds.items()]
        
        # Define objective function for skopt
        @use_named_args(dimensions)
        def objective(**params):
            weights_array = [params[key] for key in weight_keys]
            return self.objective_function(weights_array, weight_keys)
        
        # Run Bayesian optimization
        result = gp_minimize(
            func=objective,
            dimensions=dimensions,
            n_calls=n_calls,
            n_initial_points=10,
            random_state=random_state,
            acq_func='EI'  # Expected Improvement
        )
        
        # Extract best weights
        best_weights = dict(zip(weight_keys, result.x))
        best_score = -result.fun
        
        optimization_time = time.time() - start_time
        
        print(f"✅ Bayesian Optimization Complete!")
        print(f"   Time taken: {optimization_time:.2f} seconds")
        print(f"   Best score: {best_score:.4f}")
        print(f"   Function evaluations: {len(result.func_vals)}")
        
        return {
            'method': 'Bayesian Optimization',
            'best_weights': best_weights,
            'best_score': best_score,
            'optimization_time': optimization_time,
            'iterations': n_calls,
            'convergence_history': [-score for score in result.func_vals]
        }
    
    def genetic_algorithm_optimization(self, population_size=20, generations=50, random_state=42):
        """
        核心创新算法2: 遗传算法权重优化
        
        Uses evolutionary computation to optimize weights through
        natural selection, crossover, and mutation operations.
        """
        print(f"🧬 Starting Genetic Algorithm Optimization ({generations} generations)")
        start_time = time.time()
        
        # Define bounds for differential evolution
        weight_keys = list(self.weight_bounds.keys())
        bounds = [self.weight_bounds[key] for key in weight_keys]
        
        # Run differential evolution (a variant of genetic algorithms)
        result = differential_evolution(
            func=lambda x: self.objective_function(x, weight_keys),
            bounds=bounds,
            maxiter=generations,
            popsize=population_size,
            random_state=random_state,
            updating='deferred',  # Evaluate entire population before updating
            workers=1  # Single worker for consistency
        )
        
        best_weights = dict(zip(weight_keys, result.x))
        best_score = -result.fun
        
        optimization_time = time.time() - start_time
        
        print(f"✅ Genetic Algorithm Optimization Complete!")
        print(f"   Time taken: {optimization_time:.2f} seconds")
        print(f"   Best score: {best_score:.4f}")
        print(f"   Function evaluations: {result.nfev}")
        print(f"   Generations completed: {result.nit}")
        
        return {
            'method': 'Genetic Algorithm',
            'best_weights': best_weights,
            'best_score': best_score,
            'optimization_time': optimization_time,
            'iterations': result.nit,
            'function_evaluations': result.nfev
        }
    
    def grid_search_optimization(self, grid_resolution=5):
        """
        核心创新算法3: 网格搜索权重优化
        
        Exhaustively searches the weight space using a systematic grid
        to ensure comprehensive coverage of all weight combinations.
        """
        print(f"🔍 Starting Grid Search Optimization (resolution={grid_resolution})")
        start_time = time.time()
        
        weight_keys = list(self.weight_bounds.keys())
        
        # Create grid points for each weight
        grid_points = {}
        for key, (min_val, max_val) in self.weight_bounds.items():
            grid_points[key] = np.linspace(min_val, max_val, grid_resolution)
        
        # Calculate total combinations
        total_combinations = grid_resolution ** len(weight_keys)
        print(f"   Total combinations to evaluate: {total_combinations}")
        
        best_score = float('-inf')
        best_weights = None
        combinations_evaluated = 0
        
        # Generate all combinations (recursive approach for dynamic keys)
        def generate_combinations(keys, current_combination, index):
            nonlocal best_score, best_weights, combinations_evaluated
            
            if index == len(keys):
                # Evaluate this combination
                weights_array = [current_combination[key] for key in weight_keys]
                score = -self.objective_function(weights_array, weight_keys)
                
                if score > best_score:
                    best_score = score
                    best_weights = current_combination.copy()
                
                combinations_evaluated += 1
                
                if combinations_evaluated % 100 == 0:
                    print(f"   Evaluated {combinations_evaluated}/{total_combinations} combinations...")
                
                return
            
            # Recursive case
            current_key = keys[index]
            for value in grid_points[current_key]:
                current_combination[current_key] = value
                generate_combinations(keys, current_combination, index + 1)
        
        # Start grid search
        generate_combinations(weight_keys, {}, 0)
        
        optimization_time = time.time() - start_time
        
        print(f"✅ Grid Search Optimization Complete!")
        print(f"   Time taken: {optimization_time:.2f} seconds")
        print(f"   Best score: {best_score:.4f}")
        print(f"   Combinations evaluated: {combinations_evaluated}")
        
        return {
            'method': 'Grid Search',
            'best_weights': best_weights,
            'best_score': best_score,
            'optimization_time': optimization_time,
            'combinations_evaluated': combinations_evaluated,
            'grid_resolution': grid_resolution
        }
    
    def random_search_optimization(self, n_iterations=100, random_state=42):
        """
        基准算法: 随机搜索权重优化
        
        Random baseline for comparison with intelligent optimization methods.
        """
        print(f"🎲 Starting Random Search Optimization ({n_iterations} iterations)")
        start_time = time.time()
        
        np.random.seed(random_state)
        weight_keys = list(self.weight_bounds.keys())
        
        best_score = float('-inf')
        best_weights = None
        
        for i in range(n_iterations):
            # Generate random weights within bounds
            random_weights = {}
            for key, (min_val, max_val) in self.weight_bounds.items():
                random_weights[key] = np.random.uniform(min_val, max_val)
            
            # Evaluate
            weights_array = [random_weights[key] for key in weight_keys]
            score = -self.objective_function(weights_array, weight_keys)
            
            if score > best_score:
                best_score = score
                best_weights = random_weights.copy()
            
            if (i + 1) % 20 == 0:
                print(f"   Iteration {i + 1}/{n_iterations}, Current best: {best_score:.4f}")
        
        optimization_time = time.time() - start_time
        
        print(f"✅ Random Search Optimization Complete!")
        print(f"   Time taken: {optimization_time:.2f} seconds")
        print(f"   Best score: {best_score:.4f}")
        
        return {
            'method': 'Random Search',
            'best_weights': best_weights,
            'best_score': best_score,
            'optimization_time': optimization_time,
            'iterations': n_iterations
        }
    
    def compare_optimization_methods(self, league_data):
        """
        核心实验: 权重优化算法对比
        
        This method implements the core experimental framework that compares
        different optimization algorithms to prove the algorithmic contribution.
        """
        self.league_reference_data = league_data
        
        print("🏁 Starting Comprehensive Weight Optimization Comparison")
        print("=" * 70)
        
        # Store all results
        all_results = {}
        
        # 1. Baseline: Random Search
        all_results['Random_Search'] = self.random_search_optimization(n_iterations=50)
        
        # 2. Grid Search (Exhaustive)
        all_results['Grid_Search'] = self.grid_search_optimization(grid_resolution=4)
        
        # 3. Genetic Algorithm (Evolutionary)
        all_results['Genetic_Algorithm'] = self.genetic_algorithm_optimization(
            population_size=15, generations=30)
        
        # 4. Bayesian Optimization (Intelligent)
        all_results['Bayesian_Optimization'] = self.bayesian_optimization(n_calls=50)
        
        # Generate comparison report
        self.generate_optimization_report(all_results)
        
        return all_results
    
    def generate_optimization_report(self, results):
        """生成权重优化对比报告"""
        print("\n" + "="*70)
        print("📊 WEIGHT OPTIMIZATION ALGORITHM COMPARISON REPORT")
        print("="*70)
        
        # Sort by performance
        sorted_results = sorted(results.items(), 
                              key=lambda x: x[1]['best_score'], 
                              reverse=True)
        
        print(f"\n🏆 PERFORMANCE RANKING:")
        for rank, (method, result) in enumerate(sorted_results, 1):
            print(f"   {rank}. {method}: {result['best_score']:.4f}")
        
        print(f"\n⏱️  COMPUTATIONAL EFFICIENCY:")
        for method, result in results.items():
            print(f"   {method}: {result['optimization_time']:.2f} seconds")
        
        print(f"\n🎯 BEST WEIGHTS FOUND:")
        best_method, best_result = sorted_results[0]
        print(f"   Method: {best_method}")
        for weight, value in best_result['best_weights'].items():
            print(f"   {weight}: {value:.4f}")
        
        # Calculate improvement over random baseline
        if 'Random_Search' in results:
            baseline_score = results['Random_Search']['best_score']
            print(f"\n📈 IMPROVEMENT OVER RANDOM BASELINE:")
            for method, result in results.items():
                if method != 'Random_Search':
                    improvement = ((result['best_score'] - baseline_score) / baseline_score) * 100
                    print(f"   {method}: +{improvement:.2f}%")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"Weight_Optimization_Results_{self.position_type}_{timestamp}.json"
        
        # Convert numpy types to native Python types for JSON serialization
        json_results = {}
        for method, result in results.items():
            json_result = {}
            for key, value in result.items():
                if isinstance(value, (np.float64, np.float32)):
                    json_result[key] = float(value)
                elif isinstance(value, (np.int64, np.int32)):
                    json_result[key] = int(value)
                elif isinstance(value, dict):
                    json_result[key] = {k: float(v) if isinstance(v, (np.float64, np.float32)) else v 
                                      for k, v in value.items()}
                else:
                    json_result[key] = value
            json_results[method] = json_result
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    print("🚀 Weight Optimization Framework - Core Algorithmic Innovation")
    print("This module implements systematic weight optimization algorithms")
    print("applied to percentile-based features for transfer prediction.")
    print("\nTo use this framework:")
    print("1. Load training and validation data")
    print("2. Initialize PercentileWeightOptimizer")
    print("3. Run compare_optimization_methods()")
    print("4. Analyze results for algorithmic contribution evidence")