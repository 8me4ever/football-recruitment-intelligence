#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             average_precision_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)
import warnings
warnings.filterwarnings('ignore')

sys.path.append(r"F:\Samuel\学习\final project")
from weight_optimization_core_updated import (
    load_experimental_data_enhanced,
    get_universal_metrics, 
    get_position_specific_metrics,
    calculate_enhanced_percentile_scores,
    calculate_departure_probability_with_weights
)

def load_2023_2024_data():
    try:
        departure_df = pd.read_csv(r"data excel\2023-2024\Inter_departured_2023_2024.csv", encoding='utf-8-sig')
        departure_labels = dict(zip(departure_df['Name'], departure_df['Departed_Label']))
        
        column_names = [
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born',
            'MP', 'Starts', 'Min', '90s', 'Gls', 'Ast', 'GA', 'G_minus_PK', 'PK', 'PKatt',
            'CrdY', 'CrdR', 'xG', 'npxG', 'xAG', 'npxG_plus_xAG', 'PrgC', 'PrgP', 'PrgR',
            'Gls_per90', 'Ast_per90', 'GA_per90', 'G_minus_PK_per90', 'GA_minus_PK_per90',
            'xG_per90', 'xAG_per90', 'xG_plus_xAG_per90', 'npxG_per90', 'npxG_plus_xAG_per90'
        ]
        
        df_league_2023_2024 = pd.read_csv(
            r"data excel\2023-2024\ITA_SerieA_player_standard_stats_2023_2024.csv",
            skiprows=2, names=column_names, encoding='utf-8-sig'
        )
        
        def get_position_group(pos_str):
            if pd.isna(pos_str):
                return 'Unknown'
            pos_str = str(pos_str)
            if 'GK' in pos_str:
                return 'Goalkeeper'
            elif 'FW' in pos_str:
                return 'Forward'
            elif 'MF' in pos_str:
                return 'Midfielder'
            elif 'DF' in pos_str:
                return 'Defender'
            else:
                return 'Unknown'
        
        df_league_2023_2024['position_group'] = df_league_2023_2024['pos'].apply(get_position_group)
        
        df_inter_raw = df_league_2023_2024[df_league_2023_2024['team'] == 'Inter'].copy()
        
        matched_players = []
        for _, inter_player in df_inter_raw.iterrows():
            player_name = inter_player['player']
            if player_name in departure_labels:
                inter_player_dict = inter_player.to_dict()
                inter_player_dict['departed_label'] = departure_labels[player_name]
                matched_players.append(inter_player_dict)
                
        if not matched_players:
            print("ERROR: No matched player data found")
            return None, None
            
        inter_data_2023_2024 = pd.DataFrame(matched_players)
        
        print(f"Data loaded successfully: {len(inter_data_2023_2024)} Inter players, {len(df_league_2023_2024)} league players")
        
        return inter_data_2023_2024, df_league_2023_2024
        
    except Exception as e:
        print(f"Data loading failed: {e}")
        return None, None

def load_pso_optimal_weights():
    return {
        'Forward': {
            'alpha': 4.000000,
            'tau': 0.611825,
            'risk_multiplier': 0.700000,
            'minutes_weight': 0.150000,
            'CrdY_weight': 0.080000,
            'CrdR_weight': 0.080000,
            'Gls_weight': 0.080000,
            'Ast_weight': 0.050000,
            'xG_weight': 0.080000,
            'SoT_weight': 0.150000,
            'G_per_Sh_weight': 0.050000,
            'Sh_per90_weight': 0.120000,
            'SCA_weight': 0.080000,
            'GCA_weight': 0.150000,
            'Att_Pen_weight': 0.050000,
            'TakeOn_Succ_weight': 0.050000,
        },
        'Midfielder': {
            'alpha': 4.000000,
            'tau': 0.700000,
            'risk_multiplier': 0.700000,
            'minutes_weight': 0.150000,
            'CrdY_weight': 0.080000,
            'CrdR_weight': 0.139911,
            'Ast_weight': 0.080000,
            'xAG_weight': 0.150000,
            'KP_weight': 0.080000,
            'Cmp_pct_weight': 0.104396,
            'PrgP_weight': 0.150000,
            'Touches_weight': 0.050000,
            'PrgC_weight': 0.050000,
            'TakeOn_Succ_weight': 0.050000,
            'Tkl_weight': 0.050000,
            'SCA_weight': 0.050000,
        },
        'Defender': {
            'alpha': 1.969604,
            'tau': 0.700000,
            'risk_multiplier': 0.433024,
            'minutes_weight': 0.080673,
            'CrdY_weight': 0.097681,
            'CrdR_weight': 0.150000,
            'Tkl_weight': 0.149751,
            'Int_weight': 0.150000,
            'Blocks_weight': 0.080343,
            'Clr_weight': 0.080000,
            'Tkl_pct_weight': 0.120000,
            'Cmp_pct_weight': 0.080000,
            'Cmp_pct_Long_weight': 0.050000,
            'PrgP_weight': 0.055806,
            'Final_Third_weight': 0.050000,
            'Def_3rd_weight': 0.050000,
        },
        'Goalkeeper': {
            'alpha': 1.541406,
            'tau': 0.519183,
            'risk_multiplier': 0.492299,
            'minutes_weight': 0.121718,
            'CrdY_weight': 0.133025,
            'CrdR_weight': 0.099819,
            'Saves_weight': 0.130262,
            'Save_pct_weight': 0.112501,
            'CS_weight': 0.116150,
            'CS_pct_weight': 0.117921,
            'GA90_weight': 0.062131,
            'SoTA_weight': 0.069787,
            'PK_Save_weight': 0.105331,
            'PK_Save_pct_weight': 0.080525,
            'W_weight': 0.075160,
            'Cmp_40_plus_weight': 0.056702,
        }
    }

def run_prediction():
    print("Inter Milan 2023-2024 Season Departure Prediction")
    print("=" * 60)
    
    os.chdir(r"F:\Samuel\学习\final project")
    start_time = time.time()
    
    inter_data_2023_2024, league_data_2023_2024 = load_2023_2024_data()
    if inter_data_2023_2024 is None:
        return None
    
    try:
        from weight_optimization_core_updated import load_position_specific_data
        position_datasets = load_position_specific_data()
    except:
        position_datasets = {}
    
    optimized_weights = load_pso_optimal_weights()
    
    predictions = []
    
    for _, player in inter_data_2023_2024.iterrows():
        position = player['position_group']
        if position not in optimized_weights:
            continue
            
        try:
            percentile_scores = calculate_enhanced_percentile_scores(
                player, league_data_2023_2024, position_datasets)
            
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
            
        except Exception as e:
            print(f"Prediction failed for {player['player']}: {e}")
            continue
    
    if not predictions:
        print("No successful predictions")
        return None
    
    predictions.sort(key=lambda x: x['departure_probability'], reverse=True)
    correct = sum(1 for p in predictions if p['predicted_departed'] == p['actual_departed'])
    accuracy = correct / len(predictions) if predictions else 0
    
    actuals = [p['actual_departed'] for p in predictions]
    predicted = [p['predicted_departed'] for p in predictions]
    probs = [p['departure_probability'] for p in predictions]
    
    try:
        pr_auc = average_precision_score(actuals, probs) if len(set(actuals)) > 1 else 0.0
        kappa = cohen_kappa_score(actuals, predicted)
        brier = brier_score_loss(actuals, probs)
        balanced_acc = balanced_accuracy_score(actuals, predicted)
        mcc = matthews_corrcoef(actuals, predicted)
        precision = precision_score(actuals, predicted, zero_division=0)
        recall = recall_score(actuals, predicted, zero_division=0)
        f1 = f1_score(actuals, predicted, zero_division=0)
        
        composite_score = (0.4 * pr_auc + 0.3 * f1 + 0.2 * balanced_acc + 0.1 * (1 - brier))
        
        execution_time = time.time() - start_time
        
        print(f"\n2023-2024 Season Prediction Performance Metrics")
        print("=" * 55)
        print(f"{'Metric':<35} {'Value':<10}")
        print("-" * 55)
        print(f"{'Accuracy':<35} {accuracy:.4f}")
        print(f"{'Precision':<35} {precision:.4f}")
        print(f"{'Recall':<35} {recall:.4f}")
        print(f"{'F1-Score':<35} {f1:.4f}")
        print(f"{'PR-AUC':<35} {pr_auc:.4f}")
        cohens_kappa_label = "Cohen's Kappa"
        print(f"{cohens_kappa_label:<35} {kappa:.4f}")
        print(f"{'Balanced Accuracy':<35} {balanced_acc:.4f}")
        print(f"{'Matthews Correlation Coefficient':<35} {mcc:.4f}")
        print(f"{'Brier Score':<35} {brier:.4f}")
        print()
        print(f"{'Composite Score':<35} {composite_score:.4f}")
        print(f"{'Execution Time (seconds)':<35} {execution_time:.2f}")
        
        print(f"\nIndividual Predictions")
        print("=" * 75)
        print(f"{'Player':<20} {'Position':<12} {'Age':<4} {'Min':<6} {'Prob':<8} {'Pred':<5} {'Actual':<6} {'Status':<6}")
        print("-" * 75)
        
        for pred in predictions:
            status = "CORRECT" if pred['predicted_departed'] == pred['actual_departed'] else "WRONG"
            pred_label = "OUT" if pred['predicted_departed'] == 1 else "STAY"
            actual_label = "OUT" if pred['actual_departed'] == 1 else "STAY"
            
            print(f"{pred['player']:<20} {pred['position']:<12} {pred['age']:<4} {pred['minutes']:<6} {pred['departure_probability']:<8.3f} {pred_label:<5} {actual_label:<6} {status:<6}")
        
        print(f"\nSummary: {correct}/{len(predictions)} correct ({accuracy:.1%})")
        
        return {
            'predictions': predictions,
            'metrics': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'pr_auc': pr_auc,
                'cohen_kappa': kappa,
                'brier_score': brier,
                'balanced_accuracy': balanced_acc,
                'mcc': mcc,
                'composite_score': composite_score
            },
            'execution_time': execution_time
        }
        
    except Exception as e:
        print(f"Metrics calculation failed: {e}")
        return None

if __name__ == "__main__":
    try:
        results = run_prediction()
        if results:
            print(f"\nPrediction completed successfully")
        else:
            print(f"\nPrediction failed")
    except Exception as e:
        print(f"Script execution failed: {e}")