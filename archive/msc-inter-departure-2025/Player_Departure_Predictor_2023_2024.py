#!/usr/bin/env python3
"""
2023-2024赛季球员离队/留队概率预测模型 (Demo版)
基于最优权重报告生成的预测系统

Author: Graduate Thesis Research Project
"""

import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class PlayerDeparturePredictorDemo:
    """
    球员离队概率预测器 - Demo版本
    使用从最优权重报告中提取的权重配置
    """
    
    def __init__(self):
        # 基于最优权重报告的PSO算法权重配置
        self.optimal_weights = {
            'Forward': {
                'goals_weight': 0.150000,
                'assists_weight': 0.120000,
                'minutes_weight': 0.120000,
                'age_weight': 0.050000,
                'shots_on_target_weight': 0.080000,
                'conversion_rate_weight': 0.050000,
                'expected_goals_weight': 0.080000,
                'shot_creating_actions_weight': 0.080000,
                'goal_creating_actions_weight': 0.050000,
                'shots_per_90_weight': 0.050000,
                'base_risk': 0.257264,
                'risk_multiplier': 0.700000
            },
            'Midfielder': {
                'assists_weight': 0.150000,
                'minutes_weight': 0.120000,
                'age_weight': 0.083103,
                'pass_completion_weight': 0.050000,
                'progressive_passes_weight': 0.080000,
                'key_passes_weight': 0.150000,
                'expected_assists_weight': 0.080000,
                'touches_weight': 0.050000,
                'progressive_carries_weight': 0.050000,
                'successful_take_ons_weight': 0.050000,
                'base_risk': 0.200000,
                'risk_multiplier': 0.700000
            },
            'Defender': {
                'minutes_weight': 0.150000,
                'age_weight': 0.050000,
                'progressive_passes_weight': 0.120000,
                'pass_completion_weight': 0.080000,
                'long_pass_completion_weight': 0.050000,
                'passes_to_final_third_weight': 0.050000,
                'tackles_weight': 0.080000,
                'interceptions_weight': 0.080000,
                'blocks_weight': 0.050000,
                'clearances_weight': 0.050000,
                'base_risk': 0.200000,
                'risk_multiplier': 0.685508
            },
            'Goalkeeper': {
                'minutes_weight': 0.120000,
                'age_weight': 0.071191,
                'saves_weight': 0.150000,
                'save_percentage_weight': 0.098458,
                'clean_sheets_weight': 0.080000,
                'clean_sheet_percentage_weight': 0.067658,
                'goals_against_per_90_weight': 0.082167,
                'penalty_save_rate_weight': 0.059067,
                'shots_faced_weight': 0.120000,
                'wins_weight': 0.084329,
                'base_risk': 0.400000,
                'risk_multiplier': 0.700000
            }
        }
        
        print("🏆 球员离队概率预测模型 (Demo版) 已初始化")
        print("✅ 使用PSO算法优化的最优权重配置")
    
    def get_position_group(self, position_str):
        """位置分组"""
        if pd.isna(position_str):
            return 'Unknown'
        pos_str = str(position_str).upper()
        
        if 'GK' in pos_str:
            return 'Goalkeeper'
        elif any(fwd in pos_str for fwd in ['FW', 'CF', 'LW', 'RW', 'ST']):
            return 'Forward'
        elif any(mid in pos_str for mid in ['MF', 'CM', 'DM', 'AM', 'LM', 'RM']):
            return 'Midfielder'
        elif any(def_pos in pos_str for def_pos in ['DF', 'CB', 'LB', 'RB', 'WB']):
            return 'Defender'
        else:
            return 'Unknown'
    
    def calculate_percentile_score(self, value, reference_data, ascending=True):
        """计算百分位得分"""
        if pd.isna(value) or len(reference_data) == 0:
            return 0.5
        
        reference_data = pd.Series(reference_data).dropna()
        if len(reference_data) == 0:
            return 0.5
        
        try:
            if ascending:
                percentile = stats.percentileofscore(reference_data, value, kind='rank') / 100
            else:
                percentile = 1 - (stats.percentileofscore(reference_data, value, kind='rank') / 100)
            return max(0, min(1, percentile))
        except:
            return 0.5
    
    def calculate_departure_probability(self, player_data, position, league_reference=None):
        """
        计算球员离队概率
        """
        if position not in self.optimal_weights:
            return 0.5, "位置未知"
        
        weights = self.optimal_weights[position]
        base_risk = weights['base_risk']
        risk_multiplier = weights['risk_multiplier']
        
        # 模拟计算百分位得分 (在实际应用中需要完整的联赛数据)
        performance_scores = {}
        
        if position == 'Forward':
            # 前锋关键指标
            performance_scores = {
                'goals': min(1.0, player_data.get('goals', 0) / 20),  # 假设20球为满分
                'assists': min(1.0, player_data.get('assists', 0) / 15),
                'minutes': min(1.0, player_data.get('minutes', 0) / 3000),
                'age': 1.0 - max(0, min(1, (player_data.get('age', 25) - 18) / 20)),  # 年龄越小越好
                'shots_on_target': min(1.0, player_data.get('shots_on_target', 0) / 50),
                'conversion_rate': min(1.0, player_data.get('conversion_rate', 0.1)),
                'expected_goals': min(1.0, player_data.get('expected_goals', 0) / 15),
                'shot_creating_actions': min(1.0, player_data.get('shot_creating_actions', 0) / 100),
                'goal_creating_actions': min(1.0, player_data.get('goal_creating_actions', 0) / 30),
                'shots_per_90': min(1.0, player_data.get('shots_per_90', 0) / 5)
            }
        
        elif position == 'Midfielder':
            # 中场关键指标
            performance_scores = {
                'assists': min(1.0, player_data.get('assists', 0) / 12),
                'minutes': min(1.0, player_data.get('minutes', 0) / 3000),
                'age': 1.0 - max(0, min(1, (player_data.get('age', 25) - 18) / 20)),
                'pass_completion': min(1.0, player_data.get('pass_completion', 80) / 100),
                'progressive_passes': min(1.0, player_data.get('progressive_passes', 0) / 200),
                'key_passes': min(1.0, player_data.get('key_passes', 0) / 80),
                'expected_assists': min(1.0, player_data.get('expected_assists', 0) / 10),
                'touches': min(1.0, player_data.get('touches', 0) / 3000),
                'progressive_carries': min(1.0, player_data.get('progressive_carries', 0) / 100),
                'successful_take_ons': min(1.0, player_data.get('successful_take_ons', 0) / 50)
            }
        
        elif position == 'Defender':
            # 后卫关键指标
            performance_scores = {
                'minutes': min(1.0, player_data.get('minutes', 0) / 3000),
                'age': 1.0 - max(0, min(1, (player_data.get('age', 25) - 18) / 20)),
                'progressive_passes': min(1.0, player_data.get('progressive_passes', 0) / 150),
                'pass_completion': min(1.0, player_data.get('pass_completion', 80) / 100),
                'long_pass_completion': min(1.0, player_data.get('long_pass_completion', 60) / 100),
                'passes_to_final_third': min(1.0, player_data.get('passes_to_final_third', 0) / 100),
                'tackles': min(1.0, player_data.get('tackles', 0) / 80),
                'interceptions': min(1.0, player_data.get('interceptions', 0) / 60),
                'blocks': min(1.0, player_data.get('blocks', 0) / 30),
                'clearances': min(1.0, player_data.get('clearances', 0) / 100)
            }
        
        elif position == 'Goalkeeper':
            # 门将关键指标
            performance_scores = {
                'minutes': min(1.0, player_data.get('minutes', 0) / 3000),
                'age': 1.0 - max(0, min(1, (player_data.get('age', 25) - 18) / 20)),
                'saves': min(1.0, player_data.get('saves', 0) / 100),
                'save_percentage': min(1.0, player_data.get('save_percentage', 0.7)),
                'clean_sheets': min(1.0, player_data.get('clean_sheets', 0) / 20),
                'clean_sheet_percentage': min(1.0, player_data.get('clean_sheet_percentage', 0.4)),
                'goals_against_per_90': 1.0 - min(1.0, player_data.get('goals_against_per_90', 1.5) / 3),  # 越少越好
                'penalty_save_rate': min(1.0, player_data.get('penalty_save_rate', 0.2)),
                'shots_faced': min(1.0, player_data.get('shots_faced', 0) / 150),
                'wins': min(1.0, player_data.get('wins', 0) / 25)
            }
        
        # 计算加权得分
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric, score in performance_scores.items():
            weight_key = f"{metric}_weight"
            if weight_key in weights:
                weight = weights[weight_key]
                weighted_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0.5
        
        # 计算离队概率
        # 高表现 -> 低离队概率，低表现 -> 高离队概率
        departure_probability = base_risk + (1 - normalized_score) * risk_multiplier
        departure_probability = max(0.0, min(1.0, departure_probability))
        
        return departure_probability, f"基于{position}位置优化权重计算"
    
    def predict_player_departure(self, player_data):
        """
        预测单个球员的离队概率
        """
        player_name = player_data.get('name', 'Unknown Player')
        position_str = player_data.get('position', 'Unknown')
        position_group = self.get_position_group(position_str)
        
        if position_group == 'Unknown':
            return {
                'player_name': player_name,
                'position': position_str,
                'position_group': position_group,
                'departure_probability': 0.5,
                'stay_probability': 0.5,
                'risk_level': 'Unknown',
                'explanation': '位置信息不完整，无法预测'
            }
        
        departure_prob, explanation = self.calculate_departure_probability(
            player_data, position_group)
        stay_prob = 1.0 - departure_prob
        
        # 风险等级分类
        if departure_prob >= 0.7:
            risk_level = '高风险离队'
        elif departure_prob >= 0.5:
            risk_level = '中等风险'
        elif departure_prob >= 0.3:
            risk_level = '低风险离队'
        else:
            risk_level = '极低风险'
        
        return {
            'player_name': player_name,
            'position': position_str,
            'position_group': position_group,
            'departure_probability': round(departure_prob, 4),
            'stay_probability': round(stay_prob, 4),
            'departure_percentage': f"{departure_prob:.1%}",
            'stay_percentage': f"{stay_prob:.1%}",
            'risk_level': risk_level,
            'explanation': explanation
        }
    
    def predict_team_departures(self, team_data):
        """
        预测整支球队的离队情况
        """
        predictions = []
        
        for player_data in team_data:
            prediction = self.predict_player_departure(player_data)
            predictions.append(prediction)
        
        # 按离队概率排序
        predictions.sort(key=lambda x: x['departure_probability'], reverse=True)
        
        return predictions
    
    def generate_prediction_report(self, predictions, team_name="Inter Milan"):
        """
        生成预测报告
        """
        print(f"\n🏟️  {team_name} 2023-2024赛季球员离队概率预测报告")
        print("=" * 80)
        print(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"使用模型: PSO优化权重模型 (综合评分: 0.9275)")
        print("=" * 80)
        
        # 统计分析
        total_players = len(predictions)
        high_risk = len([p for p in predictions if p['departure_probability'] >= 0.7])
        medium_risk = len([p for p in predictions if 0.5 <= p['departure_probability'] < 0.7])
        low_risk = len([p for p in predictions if p['departure_probability'] < 0.5])
        
        print(f"\n📊 风险统计:")
        print(f"  总球员数: {total_players}")
        print(f"  高风险离队 (≥70%): {high_risk} 人")
        print(f"  中等风险 (50-70%): {medium_risk} 人")
        print(f"  低风险离队 (<50%): {low_risk} 人")
        
        # 按位置分组显示预测结果
        print(f"\n🎯 按位置分组的详细预测结果:")
        print("=" * 80)
        
        # 分组
        position_groups = {}
        for pred in predictions:
            pos_group = pred['position_group']
            if pos_group not in position_groups:
                position_groups[pos_group] = []
            position_groups[pos_group].append(pred)
        
        # 按位置显示
        for position, players in position_groups.items():
            if not players:
                continue
                
            print(f"\n📍 {position.upper()} ({len(players)}名球员):")
            print("-" * 80)
            print(f"{'球员姓名':<20} {'原位置':<8} {'离队概率':<10} {'留队概率':<10} {'风险等级':<12}")
            print("-" * 80)
            
            # 按离队概率排序
            players_sorted = sorted(players, key=lambda x: x['departure_probability'], reverse=True)
            for pred in players_sorted:
                print(f"{pred['player_name']:<20} "
                      f"{pred['position']:<8} "
                      f"{pred['departure_percentage']:<10} "
                      f"{pred['stay_percentage']:<10} "
                      f"{pred['risk_level']:<12}")
        
        # 总体排名（所有球员）
        print(f"\n🏆 全队离队风险总排名:")
        print("-" * 80)
        print(f"{'排名':<4} {'球员姓名':<20} {'位置组':<12} {'离队概率':<10} {'留队概率':<10} {'风险等级':<12}")
        print("-" * 80)
        
        for i, pred in enumerate(predictions, 1):
            risk_indicator = "🔴" if pred['departure_probability'] >= 0.7 else "🟡" if pred['departure_probability'] >= 0.5 else "🟢"
            print(f"{i:<4} {pred['player_name']:<20} "
                  f"{pred['position_group']:<12} "
                  f"{pred['departure_percentage']:<10} "
                  f"{pred['stay_percentage']:<10} "
                  f"{risk_indicator}{pred['risk_level']:<11}")
        
        # 重点关注球员
        print(f"\n⚠️  重点关注球员 (离队概率 ≥ 60%):")
        high_risk_players = [p for p in predictions if p['departure_probability'] >= 0.6]
        
        if high_risk_players:
            for i, player in enumerate(high_risk_players, 1):
                print(f"  {i}. {player['player_name']} ({player['position']}) - "
                      f"离队概率: {player['departure_percentage']}")
        else:
            print("  ✅ 无高风险离队球员")
        
        return predictions

def demo_prediction():
    """
    演示预测功能
    """
    print("🚀 启动2023-2024赛季球员离队概率预测演示")
    
    # 创建预测器
    predictor = PlayerDeparturePredictorDemo()
    
    # Inter Milan 2023-2024赛季完整球员数据
    demo_players = [
        # 前锋 (Forwards)
        {
            'name': 'Lautaro Martinez',
            'position': 'FW',
            'age': 26,
            'goals': 24,
            'assists': 5,
            'minutes': 2800,
            'shots_on_target': 60,
            'conversion_rate': 0.18,
            'expected_goals': 20.5,
            'shot_creating_actions': 85,
            'goal_creating_actions': 15,
            'shots_per_90': 3.2
        },
        {
            'name': 'Marcus Thuram',
            'position': 'FW',
            'age': 26,
            'goals': 15,
            'assists': 12,
            'minutes': 2500,
            'shots_on_target': 45,
            'conversion_rate': 0.15,
            'expected_goals': 13.8,
            'shot_creating_actions': 78,
            'goal_creating_actions': 18,
            'shots_per_90': 2.8
        },
        {
            'name': 'Marko Arnautovic',
            'position': 'FW',
            'age': 35,
            'goals': 7,
            'assists': 3,
            'minutes': 1200,
            'shots_on_target': 20,
            'conversion_rate': 0.20,
            'expected_goals': 6.5,
            'shot_creating_actions': 35,
            'goal_creating_actions': 8,
            'shots_per_90': 2.5
        },
        {
            'name': 'Alexis Sanchez',
            'position': 'FW',
            'age': 35,
            'goals': 4,
            'assists': 7,
            'minutes': 1100,
            'shots_on_target': 15,
            'conversion_rate': 0.13,
            'expected_goals': 4.2,
            'shot_creating_actions': 42,
            'goal_creating_actions': 12,
            'shots_per_90': 2.8
        },
        
        # 中场 (Midfielders)
        {
            'name': 'Nicolo Barella',
            'position': 'MF',
            'age': 27,
            'assists': 8,
            'minutes': 3100,
            'pass_completion': 88.5,
            'progressive_passes': 180,
            'key_passes': 65,
            'expected_assists': 7.2,
            'touches': 2800,
            'progressive_carries': 75,
            'successful_take_ons': 35
        },
        {
            'name': 'Hakan Calhanoglu',
            'position': 'MF',
            'age': 29,
            'assists': 6,
            'minutes': 2700,
            'pass_completion': 89.2,
            'progressive_passes': 160,
            'key_passes': 50,
            'expected_assists': 5.8,
            'touches': 2600,
            'progressive_carries': 60,
            'successful_take_ons': 25
        },
        {
            'name': 'Henrikh Mkhitaryan',
            'position': 'MF',
            'age': 35,
            'assists': 9,
            'minutes': 2400,
            'pass_completion': 85.8,
            'progressive_passes': 120,
            'key_passes': 55,
            'expected_assists': 6.5,
            'touches': 2200,
            'progressive_carries': 50,
            'successful_take_ons': 30
        },
        {
            'name': 'Davide Frattesi',
            'position': 'MF',
            'age': 25,
            'assists': 4,
            'minutes': 1800,
            'pass_completion': 87.2,
            'progressive_passes': 95,
            'key_passes': 35,
            'expected_assists': 3.8,
            'touches': 1650,
            'progressive_carries': 45,
            'successful_take_ons': 20
        },
        {
            'name': 'Kristjan Asllani',
            'position': 'MF',
            'age': 22,
            'assists': 2,
            'minutes': 900,
            'pass_completion': 89.5,
            'progressive_passes': 65,
            'key_passes': 20,
            'expected_assists': 2.1,
            'touches': 850,
            'progressive_carries': 25,
            'successful_take_ons': 12
        },
        {
            'name': 'Stefano Sensi',
            'position': 'MF',
            'age': 29,
            'assists': 1,
            'minutes': 500,
            'pass_completion': 86.3,
            'progressive_passes': 35,
            'key_passes': 12,
            'expected_assists': 1.2,
            'touches': 480,
            'progressive_carries': 15,
            'successful_take_ons': 8
        },
        
        # 后卫 (Defenders)
        {
            'name': 'Alessandro Bastoni',
            'position': 'DF',
            'age': 25,
            'minutes': 2900,
            'progressive_passes': 140,
            'pass_completion': 91.2,
            'long_pass_completion': 75.8,
            'passes_to_final_third': 85,
            'tackles': 45,
            'interceptions': 38,
            'blocks': 15,
            'clearances': 78
        },
        {
            'name': 'Francesco Acerbi',
            'position': 'DF',
            'age': 35,
            'minutes': 2400,
            'progressive_passes': 110,
            'pass_completion': 88.5,
            'long_pass_completion': 70.2,
            'passes_to_final_third': 70,
            'tackles': 55,
            'interceptions': 50,
            'blocks': 25,
            'clearances': 95
        },
        {
            'name': 'Stefan de Vrij',
            'position': 'DF',
            'age': 32,
            'minutes': 2100,
            'progressive_passes': 95,
            'pass_completion': 89.8,
            'long_pass_completion': 72.5,
            'passes_to_final_third': 65,
            'tackles': 40,
            'interceptions': 45,
            'blocks': 20,
            'clearances': 85
        },
        {
            'name': 'Benjamin Pavard',
            'position': 'DF',
            'age': 28,
            'minutes': 2600,
            'progressive_passes': 85,
            'pass_completion': 87.3,
            'long_pass_completion': 68.9,
            'passes_to_final_third': 55,
            'tackles': 50,
            'interceptions': 42,
            'blocks': 22,
            'clearances': 70
        },
        {
            'name': 'Denzel Dumfries',
            'position': 'DF',
            'age': 28,
            'minutes': 2500,
            'progressive_passes': 75,
            'pass_completion': 82.1,
            'long_pass_completion': 65.8,
            'passes_to_final_third': 60,
            'tackles': 55,
            'interceptions': 35,
            'blocks': 18,
            'clearances': 65
        },
        {
            'name': 'Federico Dimarco',
            'position': 'DF',
            'age': 26,
            'minutes': 2300,
            'progressive_passes': 95,
            'pass_completion': 84.7,
            'long_pass_completion': 71.2,
            'passes_to_final_third': 75,
            'tackles': 40,
            'interceptions': 30,
            'blocks': 12,
            'clearances': 55
        },
        {
            'name': 'Matteo Darmian',
            'position': 'DF',
            'age': 34,
            'minutes': 1800,
            'progressive_passes': 65,
            'pass_completion': 86.4,
            'long_pass_completion': 69.5,
            'passes_to_final_third': 50,
            'tackles': 35,
            'interceptions': 28,
            'blocks': 15,
            'clearances': 50
        },
        {
            'name': 'Carlos Augusto',
            'position': 'DF',
            'age': 25,
            'minutes': 1500,
            'progressive_passes': 55,
            'pass_completion': 83.8,
            'long_pass_completion': 66.7,
            'passes_to_final_third': 45,
            'tackles': 30,
            'interceptions': 25,
            'blocks': 10,
            'clearances': 40
        },
        
        # 门将 (Goalkeepers)
        {
            'name': 'Yann Sommer',
            'position': 'GK',
            'age': 35,
            'minutes': 2700,
            'saves': 85,
            'save_percentage': 0.78,
            'clean_sheets': 16,
            'clean_sheet_percentage': 0.52,
            'goals_against_per_90': 1.15,
            'penalty_save_rate': 0.33,
            'shots_faced': 120,
            'wins': 22
        },
        {
            'name': 'Emil Audero',
            'position': 'GK',
            'age': 27,
            'minutes': 630,
            'saves': 22,
            'save_percentage': 0.75,
            'clean_sheets': 3,
            'clean_sheet_percentage': 0.43,
            'goals_against_per_90': 1.29,
            'penalty_save_rate': 0.25,
            'shots_faced': 30,
            'wins': 4
        },
        {
            'name': 'Raffaele Di Gennaro',
            'position': 'GK',
            'age': 36,
            'minutes': 90,
            'saves': 3,
            'save_percentage': 0.60,
            'clean_sheets': 0,
            'clean_sheet_percentage': 0.00,
            'goals_against_per_90': 2.00,
            'penalty_save_rate': 0.00,
            'shots_faced': 5,
            'wins': 0
        }
    ]
    
    # 进行预测
    predictions = predictor.predict_team_departures(demo_players)
    
    # 生成报告
    predictor.generate_prediction_report(predictions, "Inter Milan")
    
    # 保存预测结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"Player_Departure_Predictions_2023_2024_{timestamp}.txt"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("Inter Milan 2023-2024赛季球员离队概率预测报告\n")
        f.write("=" * 70 + "\n")
        f.write(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("使用模型: PSO优化权重模型 (综合评分: 0.9275)\n")
        f.write(f"分析球员总数: {len(predictions)}名\n\n")
        
        # 统计信息
        total_players = len(predictions)
        high_risk = len([p for p in predictions if p['departure_probability'] >= 0.7])
        medium_risk = len([p for p in predictions if 0.5 <= p['departure_probability'] < 0.7])
        low_risk = len([p for p in predictions if p['departure_probability'] < 0.5])
        
        f.write("📊 风险统计汇总:\n")
        f.write(f"  总球员数: {total_players}名\n")
        f.write(f"  高风险离队 (≥70%): {high_risk}名\n")
        f.write(f"  中等风险 (50-70%): {medium_risk}名\n")
        f.write(f"  低风险离队 (<50%): {low_risk}名\n\n")
        
        # 按位置分组
        position_groups = {}
        for pred in predictions:
            pos_group = pred['position_group']
            if pos_group not in position_groups:
                position_groups[pos_group] = []
            position_groups[pos_group].append(pred)
        
        # 按位置写入详细信息
        for position, players in position_groups.items():
            if not players:
                continue
                
            f.write(f"📍 {position.upper()}位置 ({len(players)}名球员):\n")
            f.write("-" * 60 + "\n")
            
            # 按离队概率排序
            players_sorted = sorted(players, key=lambda x: x['departure_probability'], reverse=True)
            for i, pred in enumerate(players_sorted, 1):
                risk_indicator = "🔴" if pred['departure_probability'] >= 0.7 else "🟡" if pred['departure_probability'] >= 0.5 else "🟢"
                f.write(f"{i:2d}. {pred['player_name']} ({pred['position']})\n")
                f.write(f"    离队概率: {pred['departure_percentage']} | 留队概率: {pred['stay_percentage']}\n")
                f.write(f"    风险等级: {risk_indicator}{pred['risk_level']}\n")
                f.write(f"    预测说明: {pred['explanation']}\n\n")
        
        # 全队总排名
        f.write("🏆 全队离队风险总排名:\n")
        f.write("=" * 60 + "\n")
        for i, pred in enumerate(predictions, 1):
            risk_indicator = "🔴" if pred['departure_probability'] >= 0.7 else "🟡" if pred['departure_probability'] >= 0.5 else "🟢"
            f.write(f"{i:2d}. {pred['player_name']} ({pred['position_group']}) - ")
            f.write(f"离队: {pred['departure_percentage']}, 留队: {pred['stay_percentage']} ")
            f.write(f"{risk_indicator}{pred['risk_level']}\n")
        
        f.write(f"\n重点关注球员 (离队概率 ≥ 60%):\n")
        high_risk_players = [p for p in predictions if p['departure_probability'] >= 0.6]
        if high_risk_players:
            for i, player in enumerate(high_risk_players, 1):
                f.write(f"  {i}. {player['player_name']} ({player['position_group']}) - {player['departure_percentage']}\n")
        else:
            f.write("  ✅ 无高风险离队球员\n")
    
    print(f"\n💾 预测结果已保存: {results_file}")
    print("\n✨ 预测演示完成！")
    
    return predictions

if __name__ == "__main__":
    demo_prediction()