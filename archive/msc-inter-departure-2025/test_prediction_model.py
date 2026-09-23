#!/usr/bin/env python3
"""
测试2023-2024赛季球员离队预测模型
"""

import os
import sys
import traceback

# 确保工作目录正确
os.chdir('F:/Samuel/学习/final project')
sys.path.append('F:/Samuel/学习/final project')

def test_basic_imports():
    """测试基础导入"""
    print("🧪 测试基础导入...")
    try:
        import pandas as pd
        import numpy as np
        from datetime import datetime
        from scipy import stats
        print("✅ 基础库导入成功")
        return True
    except Exception as e:
        print(f"❌ 基础库导入失败: {e}")
        return False

def test_prediction_model_import():
    """测试预测模型导入"""
    print("\n🧪 测试预测模型导入...")
    try:
        from Player_Departure_Predictor_2023_2024 import PlayerDeparturePredictorDemo
        print("✅ 预测模型类导入成功")
        
        # 测试实例化
        predictor = PlayerDeparturePredictorDemo()
        print("✅ 预测器实例化成功")
        return True, predictor
    except Exception as e:
        print(f"❌ 预测模型导入失败: {e}")
        traceback.print_exc()
        return False, None

def test_single_prediction():
    """测试单个球员预测"""
    print("\n🧪 测试单个球员预测...")
    try:
        from Player_Departure_Predictor_2023_2024 import PlayerDeparturePredictorDemo
        predictor = PlayerDeparturePredictorDemo()
        
        # 测试球员数据
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
        
        print("✅ 单个球员预测成功")
        print(f"   球员: {result['player_name']}")
        print(f"   离队概率: {result['departure_percentage']}")
        print(f"   留队概率: {result['stay_percentage']}")
        print(f"   风险等级: {result['risk_level']}")
        
        return True, result
    except Exception as e:
        print(f"❌ 单个球员预测失败: {e}")
        traceback.print_exc()
        return False, None

def test_demo_function():
    """测试演示函数"""
    print("\n🧪 测试演示函数...")
    try:
        from Player_Departure_Predictor_2023_2024 import demo_prediction
        print("✅ 演示函数导入成功")
        
        print("🚀 开始运行演示...")
        results = demo_prediction()
        
        print(f"✅ 演示函数运行成功，返回{len(results)}个结果")
        
        # 显示前3个结果
        print("\n📊 前3个预测结果:")
        for i, pred in enumerate(results[:3], 1):
            print(f"  {i}. {pred['player_name']} - 离队: {pred['departure_percentage']}, 留队: {pred['stay_percentage']}")
        
        return True, results
    except Exception as e:
        print(f"❌ 演示函数运行失败: {e}")
        traceback.print_exc()
        return False, None

def main():
    """主测试函数"""
    print("🔬 2023-2024赛季球员离队预测模型测试")
    print("=" * 60)
    
    tests = [
        ("基础导入测试", test_basic_imports),
        ("预测模型导入测试", test_prediction_model_import),
        ("单个球员预测测试", test_single_prediction),
        ("演示函数测试", test_demo_function)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n▶️ {test_name}")
        try:
            if test_name == "基础导入测试":
                success = test_func()
                results.append((test_name, success))
            else:
                success, data = test_func()
                results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！预测模型工作正常。")
    else:
        print("\n⚠️ 部分测试失败，需要检查问题。")
    
    return all_passed

if __name__ == "__main__":
    main()