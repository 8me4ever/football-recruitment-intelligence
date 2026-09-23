#!/usr/bin/env python3
import numpy as np
import pandas as pd
import json
import time
import math
from datetime import datetime
from sklearn.metrics import (precision_score, recall_score, f1_score, 
                             average_precision_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)

# 从Enhanced_Weight_Optimization_Experiment导入核心函数
from Enhanced_Weight_Optimization_Experiment import (
    load_experimental_data_enhanced, get_universal_metrics, get_position_specific_metrics,
    calculate_enhanced_percentile_scores, calculate_departure_probability_with_weights,
    calculate_contract_risk_adjustment
)

class SAOptimizer:
    """模拟退火优化器 - 支持5个通用+10个位置特色指标"""
    
    def __init__(self, inter_data, league_data, position_datasets, position):
        self.inter_data = inter_data
        self.league_data = league_data
        self.position_datasets = position_datasets
        self.position = position
        self.iteration_count = 0
        self.best_result = None
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.temperature_history = []
        self.fitness_history = []
    
    def get_bounds(self):
        """获取权重边界 - 基于5通用+10位置特色指标"""
        universal_metrics = get_universal_metrics()
        position_metrics = get_position_specific_metrics()
        
        if self.position not in position_metrics:
            return {}
        
        bounds = {}
        
        # 通用指标权重边界
        for metric_name in universal_metrics.keys():
            if metric_name == 'Contract_expires':
                bounds[f'{metric_name}_weight'] = (0.05, 0.12)  # 合同指标权重较低
            else:
                bounds[f'{metric_name}_weight'] = (0.08, 0.15)  # 其他通用指标
        
        # 位置特色指标权重边界
        position_specific = list(position_metrics[self.position].keys())
        
        if self.position == 'Forward':
            # 前锋：强调进球和创造
            important_metrics = ['Gls', 'xG', 'SoT', 'SCA', 'GCA']
        elif self.position == 'Midfielder':
            # 中场：强调传球和创造
            important_metrics = ['Ast', 'xAG', 'KP', 'Cmp_pct', 'PrgP']
        elif self.position == 'Defender':
            # 后卫：强调防守和传球
            important_metrics = ['Tkl', 'Int', 'Blocks', 'Clr', 'Cmp_pct']
        else:  # Goalkeeper
            # 守门员：强调扑救和表现
            important_metrics = ['Saves', 'Save_pct', 'CS', 'CS_pct']
        
        for metric in position_specific:
            if metric in important_metrics:
                bounds[f'{metric}_weight'] = (0.08, 0.15)  # 重要指标
            else:
                bounds[f'{metric}_weight'] = (0.05, 0.12)  # 一般指标
        
        # 风险参数
        bounds.update({
            'base_risk': (0.2, 0.4),
            'risk_multiplier': (0.3, 0.7)
        })
        
        return bounds
    
    def fitness_function(self, weights_array):
        """适应度函数 - 基于综合ML指标评估"""
        self.iteration_count += 1
        weight_bounds = self.get_bounds()
        weight_names = list(weight_bounds.keys())
        weights_dict = dict(zip(weight_names, weights_array))
        
        # 评估权重性能
        predictions = []
        actuals = []
        probabilities = []
        
        position_data = self.inter_data[self.inter_data['position_group'] == self.position].copy()
        
        for _, player in position_data.iterrows():
            # 计算百分位得分
            percentile_scores = calculate_enhanced_percentile_scores(
                player, self.league_data, self.position_datasets)
            
            # 计算离队概率
            departure_prob = calculate_departure_probability_with_weights(
                player, percentile_scores, weights_dict)
            
            # 预测
            prediction = 1 if departure_prob > 0.5 else 0
            actual = int(player.get('departed_label', 0))
            
            predictions.append(prediction)
            actuals.append(actual)
            probabilities.append(departure_prob)
        
        if not predictions:
            return -1.0
        
        # 计算综合评分
        try:
            accuracy = sum(p == a for p, a in zip(predictions, actuals)) / len(predictions)
            
            if len(set(actuals)) > 1:
                pr_auc = average_precision_score(actuals, probabilities)
                f1 = f1_score(actuals, predictions, zero_division=0)
                balanced_acc = balanced_accuracy_score(actuals, predictions)
                brier = brier_score_loss(actuals, probabilities)
                
                # 综合评分 (权重分配与Enhanced版本一致)
                composite_score = (
                    0.40 * pr_auc +           # 40%: 排序能力
                    0.30 * f1 +               # 30%: F1得分
                    0.20 * balanced_acc +     # 20%: 平衡准确率
                    0.10 * (1 - brier)        # 10%: 概率质量
                )
            else:
                composite_score = accuracy
                
        except Exception as e:
            composite_score = accuracy if 'accuracy' in locals() else 0.0
        
        # 记录最佳结果
        if composite_score > (self.best_result or -1):
            self.best_result = composite_score
        
        # 记录适应度历史
        self.fitness_history.append(composite_score)
        
        return composite_score
    
    def generate_neighbor(self, solution, bounds, temperature):
        """生成邻域解 - 基于温度的动态扰动"""
        new_solution = solution.copy()
        
        # 根据温度确定变化的维度数量
        n_dims_to_change = max(1, int(len(solution) * min(0.3, temperature / 100)))
        dims_to_change = np.random.choice(len(solution), n_dims_to_change, replace=False)
        
        # 对选定的维度进行扰动
        for dim in dims_to_change:
            low, high = bounds[dim]
            noise_scale = (high - low) * min(0.1, temperature / 1000)
            noise = np.random.normal(0, noise_scale)
            new_solution[dim] = np.clip(solution[dim] + noise, low, high)
        
        return new_solution
    
    def cooling_schedule(self, initial_temp, iteration, max_iterations, method='exponential'):
        """冷却策略"""
        if method == 'exponential':
            alpha = 0.95
            return initial_temp * (alpha ** iteration)
        elif method == 'linear':
            return initial_temp * (1 - iteration / max_iterations)
        elif method == 'logarithmic':
            return initial_temp / (1 + np.log(1 + iteration))
        elif method == 'adaptive':
            # 自适应冷却：基于接受率调整
            if hasattr(self, 'recent_acceptance_rate'):
                if self.recent_acceptance_rate > 0.8:
                    # 接受率太高，降温更快
                    return initial_temp * (0.90 ** iteration)
                elif self.recent_acceptance_rate < 0.2:
                    # 接受率太低，降温更慢
                    return initial_temp * (0.98 ** iteration)
            return initial_temp * (0.95 ** iteration)
        else:
            return initial_temp * (0.95 ** iteration)
    
    def optimize(self, initial_temp=100, max_iterations=1000, cooling_method='exponential'):
        """模拟退火优化主函数"""
        print(f"🔥 开始模拟退火优化 {self.position} 位置...")
        print(f"  初始温度: {initial_temp}, 最大迭代: {max_iterations}, 冷却策略: {cooling_method}")
        
        weight_bounds = self.get_bounds()
        bounds = [(low, high) for low, high in weight_bounds.values()]
        
        # 初始化
        current_solution = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        current_fitness = self.fitness_function(current_solution)
        
        best_solution = current_solution.copy()
        best_fitness = current_fitness
        
        start_time = time.time()
        self.iteration_count = 0
        self.best_result = None
        self.accepted_moves = 0
        self.rejected_moves = 0
        self.temperature_history = []
        self.fitness_history = []
        
        improvement_iterations = []
        
        # 模拟退火主循环
        for iteration in range(max_iterations):
            # 计算当前温度
            temperature = self.cooling_schedule(initial_temp, iteration, max_iterations, cooling_method)
            self.temperature_history.append(temperature)
            
            # 生成邻域解
            neighbor_solution = self.generate_neighbor(current_solution, bounds, temperature)
            neighbor_fitness = self.fitness_function(neighbor_solution)
            
            # 计算适应度差
            delta_fitness = neighbor_fitness - current_fitness
            
            # 接受准则
            if delta_fitness > 0:
                # 更好的解，直接接受
                current_solution = neighbor_solution
                current_fitness = neighbor_fitness
                self.accepted_moves += 1
                
                # 更新全局最优
                if neighbor_fitness > best_fitness:
                    best_solution = neighbor_solution.copy()
                    best_fitness = neighbor_fitness
                    improvement_iterations.append(iteration)
            else:
                # 较差的解，按概率接受
                if temperature > 0:
                    acceptance_probability = math.exp(delta_fitness / temperature)
                    if np.random.random() < acceptance_probability:
                        current_solution = neighbor_solution
                        current_fitness = neighbor_fitness
                        self.accepted_moves += 1
                    else:
                        self.rejected_moves += 1
                else:
                    self.rejected_moves += 1
            
            # 计算最近的接受率（用于自适应冷却）
            if iteration > 0 and iteration % 100 == 0:
                recent_window = min(100, iteration + 1)
                self.recent_acceptance_rate = self.accepted_moves / (self.accepted_moves + self.rejected_moves)
            
            # 每200次迭代显示进度
            if (iteration + 1) % 200 == 0:
                acceptance_rate = self.accepted_moves / (self.accepted_moves + self.rejected_moves) * 100
                print(f"  迭代 {iteration + 1}/{max_iterations}, 温度: {temperature:.4f}, "
                      f"最佳适应度: {best_fitness:.4f}, 接受率: {acceptance_rate:.1f}%")
        
        optimization_time = time.time() - start_time
        best_weights = dict(zip(weight_bounds.keys(), best_solution))
        
        # 计算统计信息
        total_moves = self.accepted_moves + self.rejected_moves
        acceptance_rate = self.accepted_moves / total_moves if total_moves > 0 else 0
        improvement_rate = len(improvement_iterations) / max_iterations
        final_temperature = self.temperature_history[-1] if self.temperature_history else 0
        
        print(f"✅ {self.position} 位置模拟退火完成!")
        print(f"   最佳适应度: {best_fitness:.4f}")
        print(f"   接受率: {acceptance_rate:.1%}")
        print(f"   改进率: {improvement_rate:.1%}")
        print(f"   最终温度: {final_temperature:.4f}")
        
        return {
            'method': f'Simulated Annealing ({cooling_method})',
            'weights': best_weights,
            'score': best_fitness,
            'time': optimization_time,
            'iterations': self.iteration_count,
            'accepted_moves': self.accepted_moves,
            'rejected_moves': self.rejected_moves,
            'acceptance_rate': acceptance_rate,
            'improvement_rate': improvement_rate,
            'final_temperature': final_temperature,
            'improvement_iterations': improvement_iterations,
            'temperature_history': self.temperature_history,
            'fitness_history': self.fitness_history
        }

def run_sa_weight_optimization():
    """运行模拟退火权重优化实验"""
    print("Simulated Annealing Weight Optimization - 5通用+10位置特色指标")
    print("=" * 65)
    
    start_time = time.time()
    
    # 加载增强数据
    inter_data, league_data, position_datasets = load_experimental_data_enhanced()
    if inter_data is None:
        print("❌ 数据加载失败")
        return None
    
    print(f"✅ 数据加载成功: {len(inter_data)}名Inter球员")
    
    # 实验结果
    results = {
        'timestamp': datetime.now().isoformat(),
        'algorithm': 'Simulated Annealing (SA)',
        'metric_system': '5通用指标 + 10位置特色指标',
        'data_summary': {
            'total_inter_players': len(inter_data),
            'positions_analyzed': []
        },
        'positions': {}
    }
    
    positions = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
    optimized_weights = {}
    
    # 对每个位置进行优化
    for position in positions:
        pos_data = inter_data[inter_data['position_group'] == position]
        if len(pos_data) == 0:
            print(f"⚠️ {position} 位置无球员数据，跳过")
            continue
        
        print(f"\n📍 开始优化 {position} 位置 ({len(pos_data)}名球员)")
        results['data_summary']['positions_analyzed'].append(position)
        
        # 创建优化器
        optimizer = SAOptimizer(inter_data, league_data, position_datasets, position)
        
        # 运行模拟退火优化
        opt_result = optimizer.optimize(
            initial_temp=150,     # 较高初始温度
            max_iterations=800,   # 适中迭代次数
            cooling_method='exponential'
        )
        optimized_weights[position] = opt_result['weights']
        
        # 保存位置结果
        results['positions'][position] = {
            'player_count': len(pos_data),
            'optimization_result': opt_result
        }
    
    # 使用优化权重生成最终预测
    print("\n🎯 生成最终预测结果...")
    predictions = []
    
    for _, player in inter_data.iterrows():
        position = player['position_group']
        if position not in optimized_weights:
            continue
        
        # 计算百分位得分
        percentile_scores = calculate_enhanced_percentile_scores(
            player, league_data, position_datasets)
        
        # 计算离队概率
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
    
    # 按离队概率排序
    predictions.sort(key=lambda x: x['departure_probability'], reverse=True)
    
    # 计算整体性能指标
    correct = sum(1 for p in predictions if p['predicted_departed'] == p['actual_departed'])
    accuracy = correct / len(predictions) if predictions else 0
    
    actuals = [p['actual_departed'] for p in predictions]
    predicted = [p['predicted_departed'] for p in predictions]
    probs = [p['departure_probability'] for p in predictions]
    
    try:
        # 计算增强ML指标
        pr_auc = average_precision_score(actuals, probs) if len(set(actuals)) > 1 else 0.0
        kappa = cohen_kappa_score(actuals, predicted)
        brier = brier_score_loss(actuals, probs)
        balanced_acc = balanced_accuracy_score(actuals, predicted)
        mcc = matthews_corrcoef(actuals, predicted)
        
        # 输出结果
        print("\n" + "=" * 55)
        print("🔥 模拟退火算法 - 最终结果")
        print("=" * 55)
        
        print("\n📊 指标体系:")
        print("  🔷 5个通用指标: minutes, age, CrdY, CrdR, Contract_expires")
        print("  🔶 10个位置特色指标 (因位置而异)")
        
        print("\n🏆 优化后的权重配置:")
        for position, weights in optimized_weights.items():
            print(f"\n📍 {position} 位置:")
            for name, value in sorted(weights.items()):
                print(f"  {name:<25}: {value:.6f}")
        
        print(f"\n📈 ML性能指标:")
        print(f"  🎯 基础指标:")
        print(f"    准确率 (Accuracy): {accuracy:.4f}")
        print(f"    精确率 (Precision): {precision_score(actuals, predicted, zero_division=0):.4f}")
        print(f"    召回率 (Recall): {recall_score(actuals, predicted, zero_division=0):.4f}")
        print(f"    F1得分 (F1-Score): {f1_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  📊 增强ML指标:")
        print(f"    PR-AUC: {pr_auc:.4f} (不平衡数据排序能力)")
        print(f"    Cohen's Kappa: {kappa:.4f} (消除偶然性准确度)")
        print(f"    Brier Score: {brier:.4f} (概率质量, 越小越好)")
        print(f"    Balanced Accuracy: {balanced_acc:.4f} (平衡分类准确率)")
        print(f"    MCC: {mcc:.4f} (最稳健相关系数)")
        
        print(f"\n👥 球员预测结果:")
        for pred in predictions:
            status = "✈️ 离队" if pred['actual_departed'] == 1 else "🏠 留队"
            correct_mark = "✅" if pred['predicted_departed'] == pred['actual_departed'] else "❌"
            print(f"  {correct_mark} {pred['player']:<18} ({pred['position']:<10}): "
                  f"离队={pred['departure_probability']:.1%}, "
                  f"留队={pred['stay_probability']:.1%} - 实际: {status}")
        
        # 保存ML指标
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
        print(f"❌ ML指标计算错误: {e}")
        results['ml_metrics'] = {'accuracy': accuracy}
    
    # 保存完整结果
    results['predictions'] = predictions
    results['optimized_weights'] = optimized_weights
    results['execution_time'] = time.time() - start_time
    
    # 保存到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SA_Weight_Optimization_Results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存到: {filename}")
    print(f"⏱️ 总执行时间: {results['execution_time']:.1f}秒")
    
    return results

if __name__ == "__main__":
    run_sa_weight_optimization()