#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版评估指标框架 - 球队数据科学家的完整评估体系
"""

import pandas as pd
import numpy as np
from sklearn.metrics import *
import matplotlib.pyplot as plt
import seaborn as sns

class FootballTransferEvaluationFramework:
    """
    足球转会预测的综合评估框架
    """
    
    def __init__(self, predictions, actuals, player_info):
        """
        初始化评估框架
        
        Args:
            predictions: 预测概率列表
            actuals: 实际结果列表 (0=留队, 1=离队)  
            player_info: 球员信息 (包含位置、年龄、市场价值等)
        """
        self.predictions = np.array(predictions)
        self.actuals = np.array(actuals)
        self.player_info = player_info
        self.binary_predictions = (self.predictions > 0.5).astype(int)
        
    def calculate_basic_metrics(self):
        """基础分类指标"""
        return {
            'accuracy': accuracy_score(self.actuals, self.binary_predictions),
            'precision': precision_score(self.actuals, self.binary_predictions),
            'recall': recall_score(self.actuals, self.binary_predictions),
            'f1_score': f1_score(self.actuals, self.binary_predictions),
            'roc_auc': roc_auc_score(self.actuals, self.predictions),
            'average_precision': average_precision_score(self.actuals, self.predictions)
        }
    
    def calculate_business_impact_metrics(self):
        """业务影响指标 - 球队管理层最关心的指标"""
        
        # 1. 核心球员预测准确性
        core_players = self.player_info['is_core_player'] == 1
        core_accuracy = accuracy_score(
            self.actuals[core_players], 
            self.binary_predictions[core_players]
        ) if np.any(core_players) else 0
        
        # 2. 高价值球员预测准确性  
        high_value = self.player_info['market_value'] > self.player_info['market_value'].median()
        high_value_accuracy = accuracy_score(
            self.actuals[high_value],
            self.binary_predictions[high_value]
        ) if np.any(high_value) else 0
        
        # 3. 转会窗口预警指标
        departure_precision = precision_score(self.actuals, self.binary_predictions)  # 预测离队的准确性
        departure_recall = recall_score(self.actuals, self.binary_predictions)       # 实际离队的捕获率
        
        # 4. 误报成本分析
        false_positives = np.sum((self.binary_predictions == 1) & (self.actuals == 0))
        false_negatives = np.sum((self.binary_predictions == 0) & (self.actuals == 1))
        
        return {
            'core_player_accuracy': core_accuracy,
            'high_value_accuracy': high_value_accuracy,
            'departure_precision': departure_precision,  # 关键：避免不必要的恐慌
            'departure_recall': departure_recall,        # 关键：不错过真正的离队
            'false_alarm_rate': false_positives / len(self.predictions),
            'missed_departure_rate': false_negatives / np.sum(self.actuals)
        }
    
    def calculate_position_specific_metrics(self):
        """位置特定评估指标"""
        position_metrics = {}
        
        for position in self.player_info['position'].unique():
            pos_mask = self.player_info['position'] == position
            if np.sum(pos_mask) == 0:
                continue
                
            pos_accuracy = accuracy_score(
                self.actuals[pos_mask], 
                self.binary_predictions[pos_mask]
            )
            
            pos_f1 = f1_score(
                self.actuals[pos_mask], 
                self.binary_predictions[pos_mask],
                zero_division=0
            )
            
            position_metrics[position] = {
                'accuracy': pos_accuracy,
                'f1_score': pos_f1,
                'sample_size': np.sum(pos_mask)
            }
        
        return position_metrics
    
    def calculate_probability_calibration_metrics(self):
        """概率校准指标 - 预测概率的可信度"""
        
        # Brier Score - 概率预测的整体质量
        brier_score = np.mean((self.predictions - self.actuals) ** 2)
        
        # 概率分箱校准分析
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        calibration_data = []
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (self.predictions > bin_lower) & (self.predictions <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = self.actuals[in_bin].mean()
                avg_confidence_in_bin = self.predictions[in_bin].mean()
                
                calibration_data.append({
                    'bin_range': f'{bin_lower:.1f}-{bin_upper:.1f}',
                    'predicted_prob': avg_confidence_in_bin,
                    'actual_rate': accuracy_in_bin,
                    'count': np.sum(in_bin)
                })
        
        return {
            'brier_score': brier_score,
            'calibration_data': calibration_data
        }
    
    def calculate_early_warning_metrics(self):
        """早期预警系统指标"""
        
        # 按概率阈值的性能分析
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        threshold_metrics = {}
        
        for threshold in thresholds:
            pred_at_threshold = (self.predictions >= threshold).astype(int)
            
            precision = precision_score(self.actuals, pred_at_threshold, zero_division=0)
            recall = recall_score(self.actuals, pred_at_threshold, zero_division=0)
            
            # 预警价值计算
            true_positives = np.sum((pred_at_threshold == 1) & (self.actuals == 1))
            false_positives = np.sum((pred_at_threshold == 1) & (self.actuals == 0))
            
            threshold_metrics[threshold] = {
                'precision': precision,
                'recall': recall,
                'true_alerts': true_positives,
                'false_alerts': false_positives,
                'alert_rate': np.mean(pred_at_threshold)
            }
        
        return threshold_metrics
    
    def calculate_financial_impact_metrics(self):
        """财务影响评估指标"""
        
        # 假设的财务参数 (可根据实际情况调整)
        avg_replacement_cost = 25_000_000  # 平均替换成本 2500万欧元
        contract_negotiation_cost = 2_000_000  # 合同谈判成本 200万欧元
        opportunity_cost_rate = 0.15  # 机会成本率 15%
        
        # 计算各类预测的财务影响
        true_positives = np.sum((self.binary_predictions == 1) & (self.actuals == 1))
        false_positives = np.sum((self.binary_predictions == 1) & (self.actuals == 0))
        false_negatives = np.sum((self.binary_predictions == 0) & (self.actuals == 1))
        true_negatives = np.sum((self.binary_predictions == 0) & (self.actuals == 0))
        
        # 财务收益计算
        saved_replacement_costs = true_positives * avg_replacement_cost
        wasted_negotiation_costs = false_positives * contract_negotiation_cost
        surprise_replacement_costs = false_negatives * avg_replacement_cost * (1 + opportunity_cost_rate)
        
        net_financial_benefit = saved_replacement_costs - wasted_negotiation_costs - surprise_replacement_costs
        
        return {
            'saved_replacement_costs': saved_replacement_costs,
            'wasted_negotiation_costs': wasted_negotiation_costs,
            'surprise_replacement_costs': surprise_replacement_costs,
            'net_financial_benefit': net_financial_benefit,
            'roi_per_prediction': net_financial_benefit / len(self.predictions)
        }
    
    def generate_comprehensive_report(self):
        """生成综合评估报告"""
        
        print("🏆 足球转会预测模型 - 综合评估报告")
        print("=" * 70)
        
        # 1. 基础指标
        basic_metrics = self.calculate_basic_metrics()
        print(f"\n📊 基础分类指标:")
        print(f"  准确率 (Accuracy): {basic_metrics['accuracy']:.3f}")
        print(f"  精确率 (Precision): {basic_metrics['precision']:.3f}")
        print(f"  召回率 (Recall): {basic_metrics['recall']:.3f}")
        print(f"  F1分数: {basic_metrics['f1_score']:.3f}")
        print(f"  ROC-AUC: {basic_metrics['roc_auc']:.3f}")
        print(f"  平均精度 (AP): {basic_metrics['average_precision']:.3f}")
        
        # 2. 业务影响指标
        business_metrics = self.calculate_business_impact_metrics()
        print(f"\n💼 业务影响指标:")
        print(f"  核心球员预测准确率: {business_metrics['core_player_accuracy']:.3f}")
        print(f"  高价值球员预测准确率: {business_metrics['high_value_accuracy']:.3f}")
        print(f"  离队预测精确率: {business_metrics['departure_precision']:.3f}")
        print(f"  离队捕获率: {business_metrics['departure_recall']:.3f}")
        print(f"  误报率: {business_metrics['false_alarm_rate']:.3f}")
        print(f"  漏报率: {business_metrics['missed_departure_rate']:.3f}")
        
        # 3. 位置特定指标
        position_metrics = self.calculate_position_specific_metrics()
        print(f"\n📍 位置特定指标:")
        for position, metrics in position_metrics.items():
            print(f"  {position}: 准确率={metrics['accuracy']:.3f}, F1={metrics['f1_score']:.3f} (n={metrics['sample_size']})")
        
        # 4. 概率校准指标
        calibration_metrics = self.calculate_probability_calibration_metrics()
        print(f"\n🎯 概率校准指标:")
        print(f"  Brier Score: {calibration_metrics['brier_score']:.3f} (越低越好)")
        
        # 5. 早期预警指标
        warning_metrics = self.calculate_early_warning_metrics()
        print(f"\n⚠️ 早期预警系统:")
        print(f"  最优阈值分析:")
        for threshold, metrics in warning_metrics.items():
            if metrics['precision'] > 0 or metrics['recall'] > 0:
                print(f"    阈值{threshold}: 精确率={metrics['precision']:.3f}, "
                      f"召回率={metrics['recall']:.3f}, 预警率={metrics['alert_rate']:.3f}")
        
        # 6. 财务影响指标
        financial_metrics = self.calculate_financial_impact_metrics()
        print(f"\n💰 财务影响评估:")
        print(f"  节省替换成本: {financial_metrics['saved_replacement_costs']:,.0f} 欧元")
        print(f"  浪费谈判成本: {financial_metrics['wasted_negotiation_costs']:,.0f} 欧元")
        print(f"  意外替换成本: {financial_metrics['surprise_replacement_costs']:,.0f} 欧元")
        print(f"  净财务收益: {financial_metrics['net_financial_benefit']:,.0f} 欧元")
        print(f"  单预测ROI: {financial_metrics['roi_per_prediction']:,.0f} 欧元")
        
        return {
            'basic_metrics': basic_metrics,
            'business_metrics': business_metrics,
            'position_metrics': position_metrics,
            'calibration_metrics': calibration_metrics,
            'warning_metrics': warning_metrics,
            'financial_metrics': financial_metrics
        }

def create_sample_evaluation():
    """创建示例评估"""
    
    # 模拟Inter球员数据
    np.random.seed(42)
    n_players = 26
    
    # 模拟预测概率和实际结果
    predictions = np.random.beta(2, 5, n_players)  # 偏向低概率
    actuals = np.random.binomial(1, 0.35, n_players)  # 35%离队率
    
    # 模拟球员信息
    positions = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
    player_info = pd.DataFrame({
        'player': [f'Player_{i+1}' for i in range(n_players)],
        'position': np.random.choice(positions, n_players),
        'age': np.random.normal(26, 4, n_players),
        'market_value': np.random.lognormal(16, 0.5, n_players),  # 百万欧元
        'is_core_player': np.random.binomial(1, 0.3, n_players)
    })
    
    # 创建评估框架
    evaluator = FootballTransferEvaluationFramework(predictions, actuals, player_info)
    
    # 生成报告
    comprehensive_results = evaluator.generate_comprehensive_report()
    
    return comprehensive_results

if __name__ == "__main__":
    # 运行示例评估
    results = create_sample_evaluation()
    
    print("\n" + "="*70)
    print("✅ 综合评估框架已构建完成!")
    print("📋 该框架提供了传统准确率之外的全方位评估指标")
    print("💡 可用于实际的Inter转会预测模型评估")