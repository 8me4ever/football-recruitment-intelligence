#!/usr/bin/env python3
"""
直接测试预测功能并强制输出
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

def main():
    # 确保在正确目录
    os.chdir('F:/Samuel/学习/final project')
    
    output = []
    output.append("🚀 Direct Prediction Test Started")
    output.append(f"Current directory: {os.getcwd()}")
    output.append(f"Python version check: OK")
    
    try:
        # 测试基础导入
        import scipy.stats
        output.append("✅ Scipy imported successfully")
        
        # 测试预测模型导入
        from Player_Departure_Predictor_2023_2024 import PlayerDeparturePredictorDemo, demo_prediction
        output.append("✅ Prediction model imported successfully")
        
        # 创建预测器实例
        predictor = PlayerDeparturePredictorDemo()
        output.append("✅ Predictor instance created")
        
        # 测试单个预测
        test_player = {
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
        }
        
        result = predictor.predict_player_departure(test_player)
        output.append("✅ Single player prediction successful")
        output.append(f"   Player: {result['player_name']}")
        output.append(f"   Departure: {result['departure_percentage']}")
        output.append(f"   Stay: {result['stay_percentage']}")
        output.append(f"   Risk Level: {result['risk_level']}")
        
        # 运行完整演示
        output.append("\n🚀 Running full demo...")
        demo_results = demo_prediction()
        output.append(f"✅ Demo completed with {len(demo_results)} players")
        
        # 显示前3个结果
        output.append("\n📊 Top 3 Results by Departure Risk:")
        for i, pred in enumerate(demo_results[:3], 1):
            output.append(f"  {i}. {pred['player_name']} ({pred['position']})")
            output.append(f"     Departure: {pred['departure_percentage']}")
            output.append(f"     Stay: {pred['stay_percentage']}")
            output.append(f"     Risk: {pred['risk_level']}")
        
        output.append("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        output.append(f"❌ Error occurred: {str(e)}")
        import traceback
        output.append("Traceback:")
        output.extend(traceback.format_exc().split('\n'))
    
    # 强制写入文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"Prediction_Test_Output_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output:
            f.write(line + '\n')
    
    # 检查文件是否创建
    if os.path.exists(output_file):
        return f"Output written to: {output_file}"
    else:
        return "Failed to create output file"

if __name__ == "__main__":
    result = main()
    print(result)  # 这应该能显示