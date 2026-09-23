#!/usr/bin/env python3
"""
Working 2023-2024赛季球员离队概率预测模型演示
基于PSO算法最优权重的可运行版本
"""

import json
from datetime import datetime

class WorkingPlayerPredictor:
    """简化但功能完整的球员预测器"""
    
    def __init__(self):
        # 使用PSO最优权重 (来自Optimal_Weights_20250813_003733.txt)
        self.weights = {
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
    
    def get_position(self, pos_str):
        """位置分组"""
        pos_str = str(pos_str).upper()
        if 'GK' in pos_str:
            return 'Goalkeeper'
        elif any(x in pos_str for x in ['FW', 'CF', 'LW', 'RW', 'ST']):
            return 'Forward'
        elif any(x in pos_str for x in ['MF', 'CM', 'DM', 'AM', 'LM', 'RM']):
            return 'Midfielder'
        elif any(x in pos_str for x in ['DF', 'CB', 'LB', 'RB', 'WB']):
            return 'Defender'
        return 'Unknown'
    
    def normalize_score(self, value, max_val):
        """归一化得分"""
        if max_val == 0:
            return 0
        return min(1.0, max(0.0, value / max_val))
    
    def predict_departure(self, player_data):
        """预测球员离队概率"""
        position = self.get_position(player_data.get('position', ''))
        if position not in self.weights:
            return 0.5, 0.5, 'Unknown Position'
        
        weights = self.weights[position]
        scores = {}
        
        # 根据位置计算不同指标得分
        if position == 'Forward':
            scores = {
                'goals': self.normalize_score(player_data.get('goals', 0), 25),
                'assists': self.normalize_score(player_data.get('assists', 0), 15),
                'minutes': self.normalize_score(player_data.get('minutes', 0), 3000),
                'age': 1.0 - self.normalize_score(player_data.get('age', 25) - 18, 20),
                'shots_on_target': self.normalize_score(player_data.get('shots_on_target', 0), 80),
                'conversion_rate': self.normalize_score(player_data.get('conversion_rate', 0.1), 0.3),
                'expected_goals': self.normalize_score(player_data.get('expected_goals', 0), 20),
                'shot_creating_actions': self.normalize_score(player_data.get('shot_creating_actions', 0), 120),
                'goal_creating_actions': self.normalize_score(player_data.get('goal_creating_actions', 0), 25),
                'shots_per_90': self.normalize_score(player_data.get('shots_per_90', 0), 6)
            }
        
        elif position == 'Midfielder':
            scores = {
                'assists': self.normalize_score(player_data.get('assists', 0), 15),
                'minutes': self.normalize_score(player_data.get('minutes', 0), 3000),
                'age': 1.0 - self.normalize_score(player_data.get('age', 25) - 18, 20),
                'pass_completion': self.normalize_score(player_data.get('pass_completion', 80), 100),
                'progressive_passes': self.normalize_score(player_data.get('progressive_passes', 0), 200),
                'key_passes': self.normalize_score(player_data.get('key_passes', 0), 100),
                'expected_assists': self.normalize_score(player_data.get('expected_assists', 0), 12),
                'touches': self.normalize_score(player_data.get('touches', 0), 3500),
                'progressive_carries': self.normalize_score(player_data.get('progressive_carries', 0), 120),
                'successful_take_ons': self.normalize_score(player_data.get('successful_take_ons', 0), 60)
            }
        
        elif position == 'Defender':
            scores = {
                'minutes': self.normalize_score(player_data.get('minutes', 0), 3000),
                'age': 1.0 - self.normalize_score(player_data.get('age', 25) - 18, 20),
                'progressive_passes': self.normalize_score(player_data.get('progressive_passes', 0), 180),
                'pass_completion': self.normalize_score(player_data.get('pass_completion', 80), 100),
                'long_pass_completion': self.normalize_score(player_data.get('long_pass_completion', 60), 100),
                'passes_to_final_third': self.normalize_score(player_data.get('passes_to_final_third', 0), 120),
                'tackles': self.normalize_score(player_data.get('tackles', 0), 90),
                'interceptions': self.normalize_score(player_data.get('interceptions', 0), 80),
                'blocks': self.normalize_score(player_data.get('blocks', 0), 40),
                'clearances': self.normalize_score(player_data.get('clearances', 0), 120)
            }
        
        elif position == 'Goalkeeper':
            scores = {
                'minutes': self.normalize_score(player_data.get('minutes', 0), 3000),
                'age': 1.0 - self.normalize_score(player_data.get('age', 25) - 18, 20),
                'saves': self.normalize_score(player_data.get('saves', 0), 120),
                'save_percentage': self.normalize_score(player_data.get('save_percentage', 0.7), 1.0),
                'clean_sheets': self.normalize_score(player_data.get('clean_sheets', 0), 20),
                'clean_sheet_percentage': self.normalize_score(player_data.get('clean_sheet_percentage', 0.4), 1.0),
                'goals_against_per_90': 1.0 - self.normalize_score(player_data.get('goals_against_per_90', 1.2), 2.5),
                'penalty_save_rate': self.normalize_score(player_data.get('penalty_save_rate', 0.2), 1.0),
                'shots_faced': self.normalize_score(player_data.get('shots_faced', 0), 150),
                'wins': self.normalize_score(player_data.get('wins', 0), 25)
            }
        
        # 计算加权得分
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, score in scores.items():
            weight_key = f"{metric}_weight"
            if weight_key in weights:
                weight = weights[weight_key]
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight > 0:
            performance_score = weighted_sum / total_weight
        else:
            performance_score = 0.5
        
        # 计算离队概率
        base_risk = weights['base_risk']
        risk_multiplier = weights['risk_multiplier']
        departure_prob = base_risk + (1 - performance_score) * risk_multiplier
        departure_prob = max(0.0, min(1.0, departure_prob))
        stay_prob = 1.0 - departure_prob
        
        # 风险等级
        if departure_prob >= 0.7:
            risk_level = '高风险离队'
        elif departure_prob >= 0.5:
            risk_level = '中等风险'
        elif departure_prob >= 0.3:
            risk_level = '低风险离队'
        else:
            risk_level = '极低风险'
        
        return departure_prob, stay_prob, risk_level

def run_prediction_demo():
    """运行预测演示"""
    # 创建预测器
    predictor = WorkingPlayerPredictor()
    
    # 示例球员数据 (基于2023-2024赛季Inter Milan球员)
    demo_players = [
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
        }
    ]
    
    # 进行预测
    results = []
    for player in demo_players:
        departure_prob, stay_prob, risk_level = predictor.predict_departure(player)
        results.append({
            'player_name': player['name'],
            'position': predictor.get_position(player['position']),
            'departure_probability': departure_prob,
            'stay_probability': stay_prob,
            'departure_percentage': f"{departure_prob:.1%}",
            'stay_percentage': f"{stay_prob:.1%}",
            'risk_level': risk_level
        })
    
    # 按离队概率排序
    results.sort(key=lambda x: x['departure_probability'], reverse=True)
    
    # 生成预测报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"Working_Prediction_Demo_Results_{timestamp}.txt"
    
    report_lines = []
    report_lines.append("🏟️ Inter Milan 2023-2024赛季球员离队概率预测报告")
    report_lines.append("=" * 70)
    report_lines.append(f"预测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("使用模型: PSO优化权重模型 (综合评分: 0.9275)")
    report_lines.append("=" * 70)
    
    # 统计分析
    total_players = len(results)
    high_risk = len([p for p in results if p['departure_probability'] >= 0.7])
    medium_risk = len([p for p in results if 0.5 <= p['departure_probability'] < 0.7])
    low_risk = len([p for p in results if p['departure_probability'] < 0.5])
    
    report_lines.append(f"")
    report_lines.append(f"📊 风险统计:")
    report_lines.append(f"  总球员数: {total_players}")
    report_lines.append(f"  高风险离队 (≥70%): {high_risk} 人")
    report_lines.append(f"  中等风险 (50-70%): {medium_risk} 人")
    report_lines.append(f"  低风险离队 (<50%): {low_risk} 人")
    
    # 详细预测结果
    report_lines.append(f"")
    report_lines.append(f"🎯 详细预测结果:")
    report_lines.append("-" * 70)
    report_lines.append(f"{'球员姓名':<20} {'位置':<12} {'离队概率':<10} {'留队概率':<10} {'风险等级':<12}")
    report_lines.append("-" * 70)
    
    for pred in results:
        line = f"{pred['player_name']:<20} "
        line += f"{pred['position']:<12} "
        line += f"{pred['departure_percentage']:<10} "
        line += f"{pred['stay_percentage']:<10} "
        line += f"{pred['risk_level']:<12}"
        report_lines.append(line)
    
    # 重点关注球员
    report_lines.append(f"")
    report_lines.append(f"⚠️ 重点关注球员 (离队概率 ≥ 60%):")
    high_risk_players = [p for p in results if p['departure_probability'] >= 0.6]
    
    if high_risk_players:
        for i, player in enumerate(high_risk_players, 1):
            line = f"  {i}. {player['player_name']} ({player['position']}) - "
            line += f"离队概率: {player['departure_percentage']}"
            report_lines.append(line)
    else:
        report_lines.append("  ✅ 无高风险离队球员")
    
    report_lines.append("")
    report_lines.append("✨ 预测演示完成！")
    
    # 保存到文件
    with open(report_file, 'w', encoding='utf-8') as f:
        for line in report_lines:
            f.write(line + '\n')
    
    # 同时保存JSON格式结果
    json_file = f"Working_Prediction_Demo_Results_{timestamp}.json"
    json_data = {
        'timestamp': datetime.now().isoformat(),
        'model': 'PSO优化权重模型',
        'composite_score': 0.9275,
        'total_players': total_players,
        'risk_statistics': {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk
        },
        'predictions': results
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return report_file, json_file, results

if __name__ == "__main__":
    print("🚀 Working Prediction Demo Starting...")
    try:
        report_file, json_file, results = run_prediction_demo()
        print(f"✅ Demo completed successfully!")
        print(f"📄 Text report: {report_file}")
        print(f"📊 JSON results: {json_file}")
        print(f"🏆 Analyzed {len(results)} players")
        
        # 显示前3个结果
        print("\n🎯 Top 3 Departure Risks:")
        for i, pred in enumerate(results[:3], 1):
            print(f"  {i}. {pred['player_name']} - {pred['departure_percentage']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()