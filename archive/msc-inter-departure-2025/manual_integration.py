#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

print("Python版本:", sys.version)
print("当前工作目录:", os.getcwd())

try:
    import pandas as pd
    print("✅ pandas导入成功，版本:", pd.__version__)
    
    try:
        import openpyxl
        print("✅ openpyxl导入成功")
    except ImportError:
        print("❌ 正在安装openpyxl...")
        os.system("pip install openpyxl")
        import openpyxl
        print("✅ openpyxl安装并导入成功")
        
    # 开始数据整合
    print("\n" + "="*50)
    print("开始Inter球员数据整合")
    print("="*50)
    
    # 定义文件列表
    files_info = {
        "2022-2023": [
            ("standard", "data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv"),
            ("defensive", "data excel/2022-2023/ITA_SerieA_player_defensive_stats_2022_2023.csv"),
            ("goal", "data excel/2022-2023/ITA_SerieA_player_goal_stats_2022_2023.csv"),
            ("passing", "data excel/2022-2023/ITA_SerieA_player_passing_stats_2022_2023.csv"),
            ("possession", "data excel/2022-2023/ITA_SerieA_player_possession_stats_2022_2023.csv"),
            ("shooting", "data excel/2022-2023/ITA_SerieA_player_shooting_stats_2022_2023.csv")
        ],
        "2023-2024": [
            ("standard", "data excel/2023-2024/ITA_SerieA_player_standard_stats_2023_2024.csv"),
            ("defensive", "data excel/2023-2024/ITA_SerieA_player_defensive_stats_2023_2024.csv"),
            ("goal", "data excel/2023-2024/ITA_SerieA_player_goal_stats_2023_2024.csv"),
            ("passing", "data excel/2023-2024/ITA_SerieA_player_passing_stats_2023_2024.csv"),
            ("possession", "data excel/2023-2024/ITA_SerieA_player_possession_stats_2023_2024.csv"),
            ("shooting", "data excel/2023-2024/ITA_SerieA_player_shooting_stats_2023_2024.csv")
        ]
    }
    
    # 创建Excel写入器
    excel_file = "Inter_Players_Complete_Analysis.xlsx"
    writer = pd.ExcelWriter(excel_file, engine='openpyxl')
    
    all_inter_data = {}
    
    # 处理每个赛季的数据
    for season, files in files_info.items():
        print(f"\n处理 {season} 赛季数据:")
        season_data = {}
        
        for data_type, file_path in files:
            print(f"  读取 {data_type} 数据...")
            
            try:
                # 读取CSV文件，跳过前两行
                df = pd.read_csv(file_path, skiprows=2, encoding='utf-8')
                print(f"    原始数据: {df.shape[0]} 行, {df.shape[1]} 列")
                
                # 筛选Inter球员（假设team列在第3列，索引为2）
                if df.shape[1] > 2:
                    inter_players = df[df.iloc[:, 2] == 'Inter'].copy()
                    
                    if len(inter_players) > 0:
                        print(f"    找到Inter球员: {len(inter_players)} 名")
                        
                        # 保存到Excel
                        sheet_name = f"{season.replace('-', '')}_{data_type}"
                        inter_players.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        # 保存到内存用于后续分析
                        season_data[data_type] = inter_players
                        
                    else:
                        print(f"    ⚠️ 未找到Inter球员数据")
                        
            except Exception as e:
                print(f"    ❌ 读取失败: {e}")
        
        all_inter_data[season] = season_data
    
    # 创建球员对比分析
    print(f"\n创建球员对比分析...")
    if '2022-2023' in all_inter_data and '2023-2024' in all_inter_data:
        if 'standard' in all_inter_data['2022-2023'] and 'standard' in all_inter_data['2023-2024']:
            
            # 获取球员名单
            players_2022 = set(all_inter_data['2022-2023']['standard'].iloc[:, 3].tolist())
            players_2023 = set(all_inter_data['2023-2024']['standard'].iloc[:, 3].tolist())
            
            # 创建对比数据
            comparison_data = []
            for player in sorted(players_2022.union(players_2023)):
                in_2022 = player in players_2022
                in_2023 = player in players_2023
                
                if in_2022 and in_2023:
                    status = "留队"
                elif in_2022 and not in_2023:
                    status = "离队"
                else:
                    status = "新援"
                
                comparison_data.append({
                    '球员姓名': player,
                    '2022-2023': '✓' if in_2022 else '✗',
                    '2023-2024': '✓' if in_2023 else '✗',
                    '状态': status
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df.to_excel(writer, sheet_name='球员变化对比', index=False)
            
            print(f"  球员变化统计:")
            print(f"    留队球员: {len([x for x in comparison_data if x['状态'] == '留队'])} 名")
            print(f"    离队球员: {len([x for x in comparison_data if x['状态'] == '离队'])} 名")
            print(f"    新援球员: {len([x for x in comparison_data if x['状态'] == '新援'])} 名")
    
    # 保存Excel文件
    writer.close()
    
    print(f"\n✅ 数据整合完成!")
    print(f"输出文件: {excel_file}")
    print(f"文件大小: {os.path.getsize(excel_file) / 1024:.1f} KB")
    
except ImportError as e:
    print(f"❌ 导入pandas失败: {e}")
    print("请安装pandas: pip install pandas")
except Exception as e:
    print(f"❌ 程序执行出错: {e}")
    import traceback
    traceback.print_exc()