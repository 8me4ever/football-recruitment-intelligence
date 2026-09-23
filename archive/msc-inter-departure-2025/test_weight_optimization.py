#!/usr/bin/env python3

# Simple test of the weight optimization framework
import pandas as pd
import numpy as np
import sys
import os

print("🧪 Testing Weight Optimization Framework")
print("=" * 50)

# Test basic imports
try:
    from Weight_Optimization_Framework import PercentileWeightOptimizer
    print("✅ Weight Optimization Framework imported successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test data loading
try:
    df_labels = pd.read_csv('Inter_Players_Departure_Labels.csv')
    print(f"✅ Loaded {len(df_labels)} departure labels")
except Exception as e:
    print(f"❌ Failed to load departure labels: {e}")
    sys.exit(1)

try:
    std_path = 'data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv'
    df_all = pd.read_csv(std_path, skiprows=3)
    df_all.columns = [
        'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', 
        'MP', 'Starts', 'Min', '90s', 'Gls', 'Ast', 'GA', 'G_minus_PK', 'PK', 'PKatt', 
        'CrdY', 'CrdR', 'xG', 'npxG', 'xAG', 'npxG_plus_xAG', 'PrgC', 'PrgP', 'PrgR',
        'Gls_per90', 'Ast_per90', 'GA_per90', 'G_minus_PK_per90', 'GA_minus_PK_per90',
        'xG_per90', 'xAG_per90', 'xG_plus_xAG_per90', 'npxG_per90', 'npxG_plus_xAG_per90'
    ]
    df_all = df_all[df_all['Min'] > 90].copy()
    inter_df = df_all[df_all['team'] == 'Inter'].copy()
    print(f"✅ Loaded {len(inter_df)} Inter players from {len(df_all)} Serie A players")
except Exception as e:
    print(f"❌ Failed to load Serie A data: {e}")
    sys.exit(1)

# Test position grouping
def get_position_group(pos_str):
    if pd.isna(pos_str):
        return 'Unknown'
    if 'GK' in str(pos_str):
        return 'Goalkeeper'
    elif 'FW' in str(pos_str):
        return 'Forward'
    elif 'MF' in str(pos_str):
        return 'Midfielder'  
    elif 'DF' in str(pos_str):
        return 'Defender'
    else:
        return 'Unknown'

df_all['position_group'] = df_all['pos'].apply(get_position_group)
inter_df['position_group'] = inter_df['pos'].apply(get_position_group)

# Add departure labels
departure_labels = dict(zip(df_labels['Player_Name'], df_labels['Departed_Label']))
inter_df['departed_label'] = inter_df['player'].map(departure_labels).fillna(0)

# Test forward position data
forwards = inter_df[inter_df['position_group'] == 'Forward'].copy()
print(f"✅ Found {len(forwards)} forwards")

if len(forwards) >= 2:
    # Test simple weight optimization
    print("\n🔬 Testing simple weight optimization...")
    
    # Split data
    train_data = forwards.iloc[:max(1, len(forwards)//2)].copy()
    val_data = forwards.iloc[max(1, len(forwards)//2):].copy()
    
    print(f"   Training: {len(train_data)} players")
    print(f"   Validation: {len(val_data)} players") 
    
    # Initialize optimizer
    optimizer = PercentileWeightOptimizer(train_data, val_data, 'Forward')
    optimizer.league_reference_data = df_all
    
    print("✅ Optimizer initialized successfully")
    
    # Test percentile calculation
    if len(train_data) > 0:
        player = train_data.iloc[0]
        percentiles = optimizer.calculate_percentile_features(player, df_all)
        print(f"✅ Percentile calculation test: {len(percentiles)} features calculated")
        for feature, value in percentiles.items():
            print(f"   {feature}: {value:.3f}")
    
    # Test simple optimization (reduced scale)
    print("\n🧬 Testing random search optimization (quick test)...")
    result = optimizer.random_search_optimization(n_iterations=10)
    print(f"✅ Random search complete: Best score = {result['best_score']:.4f}")
    
    print("\n✅ Weight Optimization Framework test successful!")
    
else:
    print("⚠️  Insufficient forward data for optimization test")

print("\n🎯 Framework is ready for full experimental run!")