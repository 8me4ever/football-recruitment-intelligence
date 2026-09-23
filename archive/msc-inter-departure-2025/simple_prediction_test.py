#!/usr/bin/env python3
"""
简化版预测模型测试
"""

import pandas as pd
import numpy as np
from datetime import datetime

def test_simple_prediction():
    """简单预测测试"""
    print("🚀 Simple Prediction Test Started")
    
    # 使用PSO最优权重 (从 Optimal_Weights_20250813_003733.txt)
    forward_weights = {
        'goals_weight': 0.150000,
        'assists_weight': 0.120000,
        'minutes_weight': 0.120000,
        'age_weight': 0.050000,
        'base_risk': 0.257264,
        'risk_multiplier': 0.700000
    }
    
    # 测试球员数据
    player_data = {
        'name': 'Lautaro Martinez',
        'position': 'FW',
        'age': 26,
        'goals': 24,
        'assists': 5,
        'minutes': 2800
    }
    
    # 简化计算
    scores = {
        'goals': min(1.0, player_data['goals'] / 20),  # 24/20 = 1.0
        'assists': min(1.0, player_data['assists'] / 15),  # 5/15 = 0.33
        'minutes': min(1.0, player_data['minutes'] / 3000),  # 2800/3000 = 0.93
        'age': 1.0 - max(0, min(1, (player_data['age'] - 18) / 20))  # 1-(26-18)/20 = 0.6
    }
    
    # 加权得分
    weighted_score = (
        scores['goals'] * forward_weights['goals_weight'] +
        scores['assists'] * forward_weights['assists_weight'] +
        scores['minutes'] * forward_weights['minutes_weight'] +
        scores['age'] * forward_weights['age_weight']
    )
    
    total_weight = (forward_weights['goals_weight'] + 
                   forward_weights['assists_weight'] + 
                   forward_weights['minutes_weight'] + 
                   forward_weights['age_weight'])
    
    normalized_score = weighted_score / total_weight
    
    # 计算离队概率
    base_risk = forward_weights['base_risk']
    risk_multiplier = forward_weights['risk_multiplier']
    departure_probability = base_risk + (1 - normalized_score) * risk_multiplier
    departure_probability = max(0.0, min(1.0, departure_probability))
    
    stay_probability = 1.0 - departure_probability
    
    print(f"Player: {player_data['name']}")
    print(f"Position: {player_data['position']}")
    print(f"Scores: {scores}")
    print(f"Weighted Score: {weighted_score:.4f}")
    print(f"Normalized Score: {normalized_score:.4f}")
    print(f"Departure Probability: {departure_probability:.1%}")
    print(f"Stay Probability: {stay_probability:.1%}")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"Simple_Prediction_Test_{timestamp}.txt"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        f.write("Simple Prediction Test Results\n")
        f.write("=" * 40 + "\n")
        f.write(f"Player: {player_data['name']}\n")
        f.write(f"Position: {player_data['position']}\n")
        f.write(f"Departure Probability: {departure_probability:.1%}\n")
        f.write(f"Stay Probability: {stay_probability:.1%}\n")
        f.write(f"Test completed at: {datetime.now()}\n")
    
    print(f"Results saved to: {results_file}")
    print("✅ Simple Prediction Test Completed")
    
    return departure_probability, stay_probability

if __name__ == "__main__":
    test_simple_prediction()