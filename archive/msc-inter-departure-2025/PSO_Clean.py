#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from scipy import stats
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             average_precision_score, roc_auc_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)
import warnings
warnings.filterwarnings('ignore')

def load_data():
    df_labels = pd.read_csv('Inter_Players_Departure_Labels.csv', encoding='utf-8')
    
    std_path = 'data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv'
    df_std = pd.read_csv(std_path, skiprows=3, names=[
        'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', 
        'MP', 'Starts', 'Min', '90s', 'Gls', 'Ast', 'GA', 'G_minus_PK', 'PK', 'PKatt', 
        'CrdY', 'CrdR', 'xG', 'npxG', 'xAG', 'npxG_plus_xAG', 'PrgC', 'PrgP', 'PrgR',
        'Gls_per90', 'Ast_per90', 'GA_per90', 'G_minus_PK_per90', 'GA_minus_PK_per90',
        'xG_per90', 'xAG_per90', 'xG_plus_xAG_per90', 'npxG_per90', 'npxG_plus_xAG_per90'
    ])
    
    df_std = df_std[df_std['Min'] > 90].copy()
    df_league = df_std.copy()
    df_inter = df_std[df_std['team'] == 'Inter'].copy()
    
    matched_data = []
    for _, label_row in df_labels.iterrows():
        player_name = label_row['Player_Name']
        departed = label_row['Departed_Label']
        
        match_found = False
        for _, inter_row in df_inter.iterrows():
            inter_name = str(inter_row['player']).strip()
            if player_name == inter_name:
                matched_data.append({
                    'player_name': player_name,
                    'departed': departed,
                    'data': inter_row.to_dict()
                })
                match_found = True
                break
        
        if not match_found:
            matched_data.append({
                'player_name': player_name,
                'departed': departed,
                'data': None
            })
    
    return matched_data, df_league

def get_position_group(position_str):
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

def calculate_percentile_score(value, reference_data, ascending=True):
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

def get_position_specific_metrics():
    return {
        'Forward': {
            'goals': {'source': 'standard', 'column': 'Gls', 'ascending': True},
            'assists': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'shots_on_target': {'source': 'standard', 'column': 'GA', 'ascending': True},
            'conversion_rate': {'source': 'standard', 'column': 'Gls_per90', 'ascending': True},
            'expected_goals': {'source': 'standard', 'column': 'xG', 'ascending': True},
            'shot_creating_actions': {'source': 'standard', 'column': 'PrgC', 'ascending': True},
            'goal_creating_actions': {'source': 'standard', 'column': 'PrgP', 'ascending': True},
            'shots_per_90': {'source': 'standard', 'column': 'xG_per90', 'ascending': True}
        },
        'Midfielder': {
            'assists': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'pass_completion': {'source': 'standard', 'column': 'PrgP', 'ascending': True},
            'progressive_passes': {'source': 'standard', 'column': 'PrgC', 'ascending': True},
            'key_passes': {'source': 'standard', 'column': 'xAG', 'ascending': True},
            'expected_assists': {'source': 'standard', 'column': 'xAG', 'ascending': True},
            'touches': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'progressive_carries': {'source': 'standard', 'column': 'PrgR', 'ascending': True},
            'successful_take_ons': {'source': 'standard', 'column': 'GA', 'ascending': True}
        },
        'Defender': {
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'progressive_passes': {'source': 'standard', 'column': 'PrgP', 'ascending': True},
            'pass_completion': {'source': 'standard', 'column': 'PrgC', 'ascending': True},
            'long_pass_completion': {'source': 'standard', 'column': 'GA', 'ascending': True},
            'passes_to_final_third': {'source': 'standard', 'column': 'xAG', 'ascending': True},
            'tackles': {'source': 'standard', 'column': 'CrdY', 'ascending': True},
            'interceptions': {'source': 'standard', 'column': 'PrgR', 'ascending': True},
            'blocks': {'source': 'standard', 'column': 'CrdR', 'ascending': True},
            'clearances': {'source': 'standard', 'column': 'PK', 'ascending': True}
        },
        'Goalkeeper': {
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'saves': {'source': 'standard', 'column': 'GA', 'ascending': True},
            'save_percentage': {'source': 'standard', 'column': 'Gls_per90', 'ascending': False},
            'clean_sheets': {'source': 'standard', 'column': 'PK', 'ascending': True},
            'clean_sheet_percentage': {'source': 'standard', 'column': 'Starts', 'ascending': True},
            'goals_against_per_90': {'source': 'standard', 'column': 'GA_per90', 'ascending': False},
            'penalty_save_rate': {'source': 'standard', 'column': 'PKatt', 'ascending': True},
            'shots_faced': {'source': 'standard', 'column': 'xG', 'ascending': True},
            'wins': {'source': 'standard', 'column': 'MP', 'ascending': True}
        }
    }

def calculate_player_score(player_data, position, league_data, weights, base_risk, risk_multiplier):
    if player_data is None:
        return 0.5
    
    position_metrics = get_position_specific_metrics().get(position, {})
    if not position_metrics:
        return 0.5
    
    position_players = league_data[league_data['pos'].str.contains(
        'GK' if position == 'Goalkeeper' else 
        'FW|CF|LW|RW|ST' if position == 'Forward' else
        'MF|CM|DM|AM|LM|RM' if position == 'Midfielder' else
        'DF|CB|LB|RB|WB', na=False
    )]
    
    total_score = 0
    total_weight = 0
    
    for metric_name, metric_info in position_metrics.items():
        weight_key = f"{metric_name}_weight"
        if weight_key in weights:
            weight = weights[weight_key]
            column = metric_info['column']
            ascending = metric_info['ascending']
            
            player_value = player_data.get(column, 0)
            reference_values = position_players[column].dropna()
            
            percentile_score = calculate_percentile_score(player_value, reference_values, ascending)
            total_score += percentile_score * weight
            total_weight += weight
    
    if total_weight > 0:
        normalized_score = total_score / total_weight
    else:
        normalized_score = 0.5
    
    departure_probability = base_risk + (1 - normalized_score) * risk_multiplier
    departure_probability = max(0.0, min(1.0, departure_probability))
    
    return departure_probability

class PSO:
    def __init__(self, n_particles=20, n_iterations=30, bounds=None):
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.bounds = bounds
        self.dim = len(bounds)
        
        self.positions = np.random.uniform(
            low=[b[0] for b in bounds],
            high=[b[1] for b in bounds],
            size=(n_particles, self.dim)
        )
        
        self.velocities = np.random.uniform(-1, 1, (n_particles, self.dim))
        self.personal_best_positions = self.positions.copy()
        self.personal_best_scores = np.full(n_particles, float('inf'))
        self.global_best_position = None
        self.global_best_score = float('inf')
        
    def evaluate_particle(self, position):
        weights = {}
        param_idx = 0
        
        for pos in ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']:
            position_weights = {}
            metrics = get_position_specific_metrics()[pos]
            
            for metric_name in metrics.keys():
                position_weights[f"{metric_name}_weight"] = position[param_idx]
                param_idx += 1
            
            position_weights['base_risk'] = position[param_idx]
            param_idx += 1
            position_weights['risk_multiplier'] = position[param_idx]
            param_idx += 1
            
            weights[pos] = position_weights
        
        matched_data, league_data = load_data()
        
        y_true = []
        y_pred = []
        y_prob = []
        
        for player in matched_data:
            if player['data'] is None:
                continue
            
            position = get_position_group(player['data']['pos'])
            if position == 'Unknown' or position not in weights:
                continue
            
            departure_prob = calculate_player_score(
                player['data'], position, league_data, 
                weights[position], 
                weights[position]['base_risk'],
                weights[position]['risk_multiplier']
            )
            
            y_true.append(player['departed'])
            y_pred.append(1 if departure_prob > 0.5 else 0)
            y_prob.append(departure_prob)
        
        if len(y_true) < 2:
            return float('inf')
        
        try:
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
            if len(set(y_true)) > 1:
                pr_auc = average_precision_score(y_true, y_prob)
                cohen_kappa = cohen_kappa_score(y_true, y_pred)
                balanced_acc = balanced_accuracy_score(y_true, y_pred)
                mcc = matthews_corrcoef(y_true, y_pred)
                brier_score = brier_score_loss(y_true, y_prob)
            else:
                pr_auc = 0.5
                cohen_kappa = 0.0
                balanced_acc = accuracy
                mcc = 0.0
                brier_score = 0.5
            
            composite_score = (
                0.40 * pr_auc +
                0.30 * f1 + 
                0.20 * balanced_acc +
                0.10 * (1 - brier_score)
            )
            
            return -composite_score
        except:
            return float('inf')
    
    def optimize(self):
        w = 0.7
        c1 = 1.4
        c2 = 1.4
        
        for iteration in range(self.n_iterations):
            for i in range(self.n_particles):
                score = self.evaluate_particle(self.positions[i])
                
                if score < self.personal_best_scores[i]:
                    self.personal_best_scores[i] = score
                    self.personal_best_positions[i] = self.positions[i].copy()
                
                if score < self.global_best_score:
                    self.global_best_score = score
                    self.global_best_position = self.positions[i].copy()
            
            for i in range(self.n_particles):
                r1, r2 = np.random.rand(2)
                self.velocities[i] = (w * self.velocities[i] +
                                    c1 * r1 * (self.personal_best_positions[i] - self.positions[i]) +
                                    c2 * r2 * (self.global_best_position - self.positions[i]))
                
                self.positions[i] += self.velocities[i]
                
                for j in range(self.dim):
                    self.positions[i][j] = np.clip(self.positions[i][j], 
                                                 self.bounds[j][0], self.bounds[j][1])
        
        return self.global_best_position

def run_pso_optimization():
    start_time = time.time()
    
    bounds = []
    for position in ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']:
        metrics = get_position_specific_metrics()[position]
        for _ in metrics:
            bounds.append((0.05, 0.15))
        bounds.append((0.2, 0.4))
        bounds.append((0.3, 0.7))
    
    pso = PSO(n_particles=20, n_iterations=30, bounds=bounds)
    best_params = pso.optimize()
    
    execution_time = time.time() - start_time
    
    weights = {}
    param_idx = 0
    
    for position in ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']:
        position_weights = {}
        metrics = get_position_specific_metrics()[position]
        
        for metric_name in metrics.keys():
            position_weights[f"{metric_name}_weight"] = best_params[param_idx]
            param_idx += 1
        
        position_weights['base_risk'] = best_params[param_idx]
        param_idx += 1
        position_weights['risk_multiplier'] = best_params[param_idx]
        param_idx += 1
        
        weights[position] = position_weights
    
    matched_data, league_data = load_data()
    
    y_true = []
    y_pred = []
    y_prob = []
    predictions = []
    
    for player in matched_data:
        if player['data'] is None:
            continue
        
        position = get_position_group(player['data']['pos'])
        if position == 'Unknown' or position not in weights:
            continue
        
        departure_prob = calculate_player_score(
            player['data'], position, league_data, 
            weights[position], 
            weights[position]['base_risk'],
            weights[position]['risk_multiplier']
        )
        
        stay_prob = 1.0 - departure_prob
        
        y_true.append(player['departed'])
        y_pred.append(1 if departure_prob > 0.5 else 0)
        y_prob.append(departure_prob)
        
        predictions.append({
            'player': player['player_name'],
            'position': position,
            'departure_probability': departure_prob,
            'stay_probability': stay_prob,
            'actual_departed': player['departed']
        })
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    pr_auc = average_precision_score(y_true, y_prob)
    cohen_kappa = cohen_kappa_score(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)
    mcc = matthews_corrcoef(y_true, y_pred)
    brier_score = brier_score_loss(y_true, y_prob)
    
    ml_metrics = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'pr_auc': pr_auc,
        'cohen_kappa': cohen_kappa,
        'balanced_accuracy': balanced_acc,
        'mcc': mcc,
        'brier_score': brier_score
    }
    
    print("PSO Algorithm - Final Results")
    print("="*40)
    print("Optimized Weights:")
    for position, pos_weights in weights.items():
        print(f"\n{position}:")
        for weight_name, weight_value in pos_weights.items():
            print(f"  {weight_name}: {weight_value:.6f}")
    
    print(f"\nML Performance Metrics:")
    for metric, value in ml_metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print(f"\nPlayer Predictions:")
    for pred in predictions:
        status = "DEPARTED" if pred['actual_departed'] == 1 else "STAYED"
        print(f"  {pred['player']} ({pred['position']}): Departure={pred['departure_probability']:.1%}, Stay={pred['stay_probability']:.1%} - Actual: {status}")
    
    return {
        'algorithm': 'PSO',
        'optimized_weights': weights,
        'overall_ml_metrics': ml_metrics,
        'predictions': predictions,
        'execution_time': execution_time
    }

if __name__ == "__main__":
    result = run_pso_optimization()