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

def load_position_specific_data():
    position_datasets = {}
    
    try:
        goal_path = 'data excel/2022-2023/ITA_SerieA_player_goal_stats_2022_2023.csv'
        df_goal = pd.read_csv(goal_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', '90s',
            'SCA', 'SCA90', 'PassLive', 'PassDead', 'TO', 'Sh', 'Fld', 'Def',
            'GCA', 'GCA90', 'GCA_PassLive', 'GCA_PassDead', 'GCA_TO', 'GCA_Sh', 'GCA_Fld', 'GCA_Def'
        ])
        
        shoot_path = 'data excel/2022-2023/ITA_SerieA_player_shooting_stats_2022_2023.csv'
        df_shoot = pd.read_csv(shoot_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', '90s',
            'Gls', 'Sh', 'SoT', 'SoT_pct', 'Sh_per90', 'SoT_per90', 'G_per_Sh', 'G_per_SoT',
            'Dist', 'FK', 'PK', 'PKatt', 'xG', 'npxG', 'npxG_per_Sh', 'G_minus_xG', 'np_G_minus_xG'
        ])
        
        position_datasets['Forward'] = {'goal': df_goal, 'shooting': df_shoot}
        
    except Exception as e:
        pass
    
    try:
        pass_path = 'data excel/2022-2023/ITA_SerieA_player_passing_stats_2022_2023.csv'  
        df_pass = pd.read_csv(pass_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', '90s',
            'Cmp', 'Att', 'Cmp_pct', 'TotDist', 'PrgDist', 'Cmp_Short', 'Att_Short', 'Cmp_pct_Short',
            'Cmp_Medium', 'Att_Medium', 'Cmp_pct_Medium', 'Cmp_Long', 'Att_Long', 'Cmp_pct_Long',
            'Ast', 'xAG', 'xA', 'A_minus_xAG', 'KP', 'Final_Third', 'PPA', 'CrsPA', 'PrgP'
        ])
        
        poss_path = 'data excel/2022-2023/ITA_SerieA_player_possession_stats_2022_2023.csv'
        df_poss = pd.read_csv(poss_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', '90s',
            'Touches', 'Def_Pen', 'Def_3rd', 'Mid_3rd', 'Att_3rd', 'Att_Pen', 'Live',
            'TakeOn_Att', 'TakeOn_Succ', 'TakeOn_Succ_pct', 'TakeOn_Tkld', 'TakeOn_Tkld_pct',
            'Carries', 'TotDist_Carries', 'PrgDist_Carries', 'PrgC', 'Carries_Final_Third', 'CPA',
            'Mis', 'Dis', 'Rec', 'PrgR'
        ])
        
        position_datasets['Midfielder'] = {'passing': df_pass, 'possession': df_poss}
        
    except Exception as e:
        pass
    
    try:
        def_path = 'data excel/2022-2023/ITA_SerieA_player_defensive_stats_2022_2023.csv'
        df_def = pd.read_csv(def_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', '90s',
            'Tkl', 'TklW', 'Def_3rd_Tkl', 'Mid_3rd_Tkl', 'Att_3rd_Tkl', 'Tkl_Challenges', 'Att_Challenges',
            'Tkl_pct', 'Lost', 'Blocks', 'Sh_Blocks', 'Pass_Blocks', 'Int', 'Tkl_plus_Int', 'Clr', 'Err'
        ])
        
        position_datasets['Defender'] = {'passing': df_pass, 'defensive': df_def}
        
    except Exception as e:
        pass
    
    try:
        gk_path = 'data excel/2022-2023/ITA_SerieA_player_goalkeeper_stats_2022_2023.csv'
        df_gk = pd.read_csv(gk_path, skiprows=2, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born',
            'MP', 'Starts', 'Min', '90s', 'GA', 'GA90', 'SoTA', 'Saves', 'Save_pct',
            'W', 'D', 'L', 'CS', 'CS_pct', 'PKatt', 'PKA', 'PKsv', 'PKm', 'PK_Save_pct'
        ])
        
        try:
            gk_adv_path = 'data excel/2022-2023/ITA_SerieA_player_goalkeeper_advance_stats_2022_2023.csv'
            df_gk_adv = pd.read_csv(gk_adv_path, skiprows=2)
            position_datasets['Goalkeeper'] = {'goalkeeper': df_gk, 'goalkeeper_advance': df_gk_adv}
        except:
            position_datasets['Goalkeeper'] = {'goalkeeper': df_gk}
            
    except Exception as e:
        pass
    
    return position_datasets

def load_experimental_data():
    try:
        encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252', 'iso-8859-1']
        df_labels = None
        
        for encoding in encodings_to_try:
            try:
                df_labels = pd.read_csv('Inter_Players_Departure_Labels.csv', encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df_labels is None:
            raise Exception("Cannot read CSV file with common encodings")
        
        df_labels['Player_Name'] = df_labels['Player_Name'].astype(str).str.strip()
        departure_labels = dict(zip(df_labels['Player_Name'], df_labels['Departed_Label']))
        
        std_path = 'data excel/2022-2023/ITA_SerieA_player_standard_stats_2022_2023.csv'
        df_league = pd.read_csv(std_path, skiprows=3, names=[
            'league', 'season', 'team', 'player', 'nation', 'pos', 'age', 'born', 
            'MP', 'Starts', 'Min', '90s', 'Gls', 'Ast', 'GA', 'G_minus_PK', 'PK', 'PKatt', 
            'CrdY', 'CrdR', 'xG', 'npxG', 'xAG', 'npxG_plus_xAG', 'PrgC', 'PrgP', 'PrgR',
            'Gls_per90', 'Ast_per90', 'GA_per90', 'G_minus_PK_per90', 'GA_minus_PK_per90',
            'xG_per90', 'xAG_per90', 'xG_plus_xAG_per90', 'npxG_per90', 'npxG_plus_xAG_per90'
        ])
        
        position_datasets = load_position_specific_data()
        
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
        
        df_league['position_group'] = df_league['pos'].apply(get_position_group)
        df_inter_raw = df_league[df_league['team'] == 'Inter'].copy()
        
        matched_players = []
        label_names = list(departure_labels.keys())
        
        for _, inter_player in df_inter_raw.iterrows():
            serie_a_name = inter_player['player']
            if serie_a_name in label_names:
                inter_player = inter_player.copy()
                inter_player['departed_label'] = departure_labels[serie_a_name]
                matched_players.append(inter_player)
        
        if matched_players:
            df_inter_final = pd.DataFrame(matched_players)
        else:
            return None, None, None
        
        return df_inter_final, df_league, position_datasets
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None, None

def calculate_percentile_score(value, reference_data, ascending=True):
    if pd.isna(value) or len(reference_data) == 0:
        return 0.5
    
    reference_data = reference_data.dropna()
    if len(reference_data) == 0:
        return 0.5
    
    if ascending:
        percentile = stats.percentileofscore(reference_data, value, kind='rank') / 100
    else:
        percentile = 1 - (stats.percentileofscore(reference_data, value, kind='rank') / 100)
    
    return max(0, min(1, percentile))

def get_position_metrics():
    return {
        'Forward': {
            'goals': {'source': 'standard', 'column': 'Gls', 'ascending': True},
            'assists': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'shots_on_target': {'source': 'shooting', 'column': 'SoT', 'ascending': True},
            'conversion_rate': {'source': 'shooting', 'column': 'G_per_Sh', 'ascending': True}, 
            'expected_goals': {'source': 'shooting', 'column': 'xG', 'ascending': True},
            'shot_creating_actions': {'source': 'goal', 'column': 'SCA', 'ascending': True},
            'goal_creating_actions': {'source': 'goal', 'column': 'GCA', 'ascending': True},
            'shots_per_90': {'source': 'shooting', 'column': 'Sh_per90', 'ascending': True}
        },
        'Midfielder': {
            'assists': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'pass_completion': {'source': 'passing', 'column': 'Cmp_pct', 'ascending': True},
            'progressive_passes': {'source': 'passing', 'column': 'PrgP', 'ascending': True},
            'key_passes': {'source': 'passing', 'column': 'KP', 'ascending': True},
            'expected_assists': {'source': 'passing', 'column': 'xAG', 'ascending': True},
            'touches': {'source': 'possession', 'column': 'Touches', 'ascending': True},
            'progressive_carries': {'source': 'possession', 'column': 'PrgC', 'ascending': True},
            'successful_take_ons': {'source': 'possession', 'column': 'TakeOn_Succ', 'ascending': True}
        },
        'Defender': {
            'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
            'age': {'source': 'standard', 'column': 'age', 'ascending': False},
            'progressive_passes': {'source': 'standard', 'column': 'PrgP', 'ascending': True},
            'pass_completion': {'source': 'passing', 'column': 'Cmp_pct', 'ascending': True},
            'long_pass_completion': {'source': 'passing', 'column': 'Cmp_pct_Long', 'ascending': True},
            'passes_to_final_third': {'source': 'passing', 'column': 'Final_Third', 'ascending': True},
            'tackles': {'source': 'defensive', 'column': 'Tkl', 'ascending': True},
            'interceptions': {'source': 'defensive', 'column': 'Int', 'ascending': True},
            'blocks': {'source': 'defensive', 'column': 'Blocks', 'ascending': True},
            'clearances': {'source': 'defensive', 'column': 'Clr', 'ascending': True}
        },
        'Goalkeeper': {
            'minutes': {'source': 'goalkeeper', 'column': 'Min', 'ascending': True},
            'age': {'source': 'goalkeeper', 'column': 'age', 'ascending': False},
            'saves': {'source': 'goalkeeper', 'column': 'Saves', 'ascending': True},
            'save_percentage': {'source': 'goalkeeper', 'column': 'Save_pct', 'ascending': True},
            'clean_sheets': {'source': 'goalkeeper', 'column': 'CS', 'ascending': True},
            'clean_sheet_percentage': {'source': 'goalkeeper', 'column': 'CS_pct', 'ascending': True},
            'goals_against_per_90': {'source': 'goalkeeper', 'column': 'GA90', 'ascending': False},
            'penalty_save_rate': {'source': 'goalkeeper', 'column': 'PK_Save_pct', 'ascending': True},
            'shots_faced': {'source': 'goalkeeper', 'column': 'SoTA', 'ascending': True},
            'wins': {'source': 'goalkeeper', 'column': 'W', 'ascending': True}
        }
    }

def calculate_percentile_scores(player_row, df_all, position_datasets):
    position = player_row['position_group']
    metrics_config = get_position_metrics()
    
    if position not in metrics_config:
        return {}
    
    scores = {}
    player_name = player_row['player']
    
    if position == 'Forward':
        position_filter = df_all['pos'].str.contains('FW', na=False)
    elif position == 'Midfielder':
        position_filter = df_all['pos'].str.contains('MF', na=False)
    elif position == 'Defender':
        position_filter = df_all['pos'].str.contains('DF', na=False)
    else:  
        position_filter = df_all['pos'].str.contains('GK', na=False)
    
    position_players = df_all[position_filter]
    
    for metric_name, metric_config in metrics_config[position].items():
        source_dataset = metric_config['source']
        column_name = metric_config['column']
        ascending = metric_config['ascending']
        
        try:
            player_value = None
            
            if source_dataset == 'standard':
                player_value = player_row.get(column_name, None)
            else:
                if source_dataset in position_datasets and position_datasets[source_dataset] is not None:
                    dataset = position_datasets[source_dataset]
                    player_data = dataset[dataset['player'] == player_name]
                    if not player_data.empty and column_name in player_data.columns:
                        player_value = player_data[column_name].iloc[0]
            
            if source_dataset == 'standard':
                reference_data = position_players[column_name]
            else:
                if source_dataset in position_datasets and position_datasets[source_dataset] is not None:
                    dataset = position_datasets[source_dataset]
                    if position == 'Forward':
                        ref_players = dataset[dataset['pos'].str.contains('FW', na=False)]
                    elif position == 'Midfielder':
                        ref_players = dataset[dataset['pos'].str.contains('MF', na=False)]
                    elif position == 'Defender':
                        ref_players = dataset[dataset['pos'].str.contains('DF', na=False)]
                    else:  
                        ref_players = dataset[dataset['pos'].str.contains('GK', na=False)]
                    
                    reference_data = ref_players[column_name] if column_name in ref_players.columns else pd.Series([])
                else:
                    reference_data = pd.Series([])
            
            if player_value is not None and not pd.isna(player_value):
                score = calculate_percentile_score(player_value, reference_data, ascending)
                scores[metric_name] = score
            else:
                scores[metric_name] = 0.5  
                
        except Exception as e:
            scores[metric_name] = 0.5
    
    return scores

def calculate_departure_probability(player_row, percentile_scores, weights):
    position = player_row['position_group']
    base_risk = weights.get('base_risk', 0.3)
    
    if not percentile_scores:
        return 0.5
    
    metrics_config = get_position_metrics()
    
    if position not in metrics_config:
        return 0.5
    
    performance_score = 0.0
    total_weight = 0.0
    
    for metric_name in metrics_config[position].keys():
        weight_key = f'{metric_name}_weight'
        weight = weights.get(weight_key, 1.0 / len(metrics_config[position]))  
        percentile_score = percentile_scores.get(metric_name, 0.5)
        
        performance_score += percentile_score * weight
        total_weight += weight
    
    if total_weight > 0:
        performance_score = performance_score / total_weight
    else:
        performance_score = 0.5
    
    if position == 'Goalkeeper':
        age = player_row.get('age', 25)
        if age > 35:
            age_penalty = 0.3
        elif age > 30:
            age_penalty = 0.1
        else:
            age_penalty = 0.0
        
        risk_multiplier = weights.get('risk_multiplier', 0.5)
        departure_prob = base_risk + (1 - performance_score) * risk_multiplier + age_penalty
    
    else:
        age = player_row.get('age', 25)
        minutes = player_row.get('Min', 0)
        if age >= 30 and minutes > 1000:
            performance_score += 0.1  
        
        risk_multiplier = weights.get('risk_multiplier', 0.6)
        departure_prob = base_risk + (1 - performance_score) * risk_multiplier
    
    return max(0.05, min(0.95, departure_prob))

def evaluate_weights(weights_dict, inter_data, league_data, position_datasets, position):
    predictions = []
    actuals = []
    probabilities = []
    
    position_data = inter_data[inter_data['position_group'] == position].copy()
    
    for _, player in position_data.iterrows():
        percentile_scores = calculate_percentile_scores(player, league_data, position_datasets)
        departure_prob = calculate_departure_probability(player, percentile_scores, weights_dict)
        
        prediction = 1 if departure_prob > 0.5 else 0
        actual = int(player.get('departed_label', 0))
        
        predictions.append(prediction)
        actuals.append(actual)
        probabilities.append(departure_prob)
    
    accuracy = accuracy_score(actuals, predictions)
    
    try:
        pr_auc = average_precision_score(actuals, probabilities) if len(set(actuals)) > 1 else 0.0
        kappa = cohen_kappa_score(actuals, predictions) if len(predictions) > 0 else 0.0
        brier = brier_score_loss(actuals, probabilities) if len(actuals) > 0 else 1.0
        balanced_acc = balanced_accuracy_score(actuals, predictions) if len(predictions) > 0 else 0.0
        mcc = matthews_corrcoef(actuals, predictions) if len(predictions) > 0 else 0.0
        
    except Exception as e:
        pr_auc = kappa = balanced_acc = mcc = 0.0
        brier = 1.0
    
    composite_score = (
        0.40 * pr_auc +           
        0.30 * f1_score(actuals, predictions, average='weighted', zero_division=0) +         
        0.20 * balanced_acc +     
        0.10 * (1 - brier)
    )
    
    return composite_score, {
        'accuracy': accuracy,
        'pr_auc': pr_auc,
        'cohen_kappa': kappa,
        'brier_score': brier,
        'balanced_accuracy': balanced_acc,
        'mcc': mcc,
        'composite_score': composite_score
    }