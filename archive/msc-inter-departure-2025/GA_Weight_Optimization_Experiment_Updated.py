#!/usr/bin/env python3
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
from scipy import stats
from scipy.optimize import differential_evolution
from sklearn.metrics import (precision_score, recall_score, f1_score, 
                             average_precision_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)

def load_experimental_data_enhanced():
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
            return None, None, None
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
        return None, None, None

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
        position_datasets['Goalkeeper'] = {'goalkeeper': df_gk}
    except Exception as e:
        pass
    return position_datasets

def get_universal_metrics():
    return {
        'minutes': {'source': 'standard', 'column': 'Min', 'ascending': True},
        'age': {'source': 'standard', 'column': 'age', 'ascending': False},
        'CrdY': {'source': 'standard', 'column': 'CrdY', 'ascending': False},
        'CrdR': {'source': 'standard', 'column': 'CrdR', 'ascending': False},
        'Contract_expires': {'source': 'contract', 'column': 'Contract_expires', 'ascending': False}
    }

def get_position_specific_metrics():
    return {
        'Forward': {
            'Gls': {'source': 'standard', 'column': 'Gls', 'ascending': True},
            'Ast': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'xG': {'source': 'shooting', 'column': 'xG', 'ascending': True},
            'SoT': {'source': 'shooting', 'column': 'SoT', 'ascending': True},
            'G_per_Sh': {'source': 'shooting', 'column': 'G_per_Sh', 'ascending': True},
            'Sh_per90': {'source': 'shooting', 'column': 'Sh_per90', 'ascending': True},
            'SCA': {'source': 'goal', 'column': 'SCA', 'ascending': True},
            'GCA': {'source': 'goal', 'column': 'GCA', 'ascending': True},
            'Att_Pen': {'source': 'possession', 'column': 'Att_Pen', 'ascending': True},
            'TakeOn_Succ': {'source': 'possession', 'column': 'TakeOn_Succ', 'ascending': True}
        },
        'Midfielder': {
            'Ast': {'source': 'standard', 'column': 'Ast', 'ascending': True},
            'xAG': {'source': 'passing', 'column': 'xAG', 'ascending': True},
            'KP': {'source': 'passing', 'column': 'KP', 'ascending': True},
            'Cmp_pct': {'source': 'passing', 'column': 'Cmp_pct', 'ascending': True},
            'PrgP': {'source': 'passing', 'column': 'PrgP', 'ascending': True},
            'Touches': {'source': 'possession', 'column': 'Touches', 'ascending': True},
            'PrgC': {'source': 'possession', 'column': 'PrgC', 'ascending': True},
            'TakeOn_Succ': {'source': 'possession', 'column': 'TakeOn_Succ', 'ascending': True},
            'Tkl': {'source': 'defensive', 'column': 'Tkl', 'ascending': True},
            'SCA': {'source': 'goal', 'column': 'SCA', 'ascending': True}
        },
        'Defender': {
            'Tkl': {'source': 'defensive', 'column': 'Tkl', 'ascending': True},
            'Int': {'source': 'defensive', 'column': 'Int', 'ascending': True},
            'Blocks': {'source': 'defensive', 'column': 'Blocks', 'ascending': True},
            'Clr': {'source': 'defensive', 'column': 'Clr', 'ascending': True},
            'Tkl_pct': {'source': 'defensive', 'column': 'Tkl_pct', 'ascending': True},
            'Cmp_pct': {'source': 'passing', 'column': 'Cmp_pct', 'ascending': True},
            'Cmp_pct_Long': {'source': 'passing', 'column': 'Cmp_pct_Long', 'ascending': True},
            'PrgP': {'source': 'passing', 'column': 'PrgP', 'ascending': True},
            'Final_Third': {'source': 'passing', 'column': 'Final_Third', 'ascending': True},
            'Def_3rd': {'source': 'possession', 'column': 'Def_3rd', 'ascending': True}
        },
        'Goalkeeper': {
            'Saves': {'source': 'goalkeeper', 'column': 'Saves', 'ascending': True},
            'Save_pct': {'source': 'goalkeeper', 'column': 'Save_pct', 'ascending': True},
            'CS': {'source': 'goalkeeper', 'column': 'CS', 'ascending': True},
            'CS_pct': {'source': 'goalkeeper', 'column': 'CS_pct', 'ascending': True},
            'GA90': {'source': 'goalkeeper', 'column': 'GA90', 'ascending': False},
            'SoTA': {'source': 'goalkeeper', 'column': 'SoTA', 'ascending': True},
            'PK_Save': {'source': 'goalkeeper', 'column': 'PK_Save', 'ascending': True},
            'PK_Save_pct': {'source': 'goalkeeper', 'column': 'PK_Save_pct', 'ascending': True},
            'W': {'source': 'goalkeeper', 'column': 'W', 'ascending': True},
            'Cmp_40_plus': {'source': 'goalkeeper', 'column': 'Cmp_40_plus', 'ascending': True}
        }
    }

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

def calculate_enhanced_percentile_scores(player_row, df_all, position_datasets, contract_data=None):
    position = player_row['position_group']
    universal_metrics = get_universal_metrics()
    position_metrics = get_position_specific_metrics()
    if position not in position_metrics:
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
    for metric_name, metric_config in universal_metrics.items():
        source_dataset = metric_config['source']
        column_name = metric_config['column']
        ascending = metric_config['ascending']
        try:
            if source_dataset == 'standard':
                player_value = player_row.get(column_name, None)
                reference_data = position_players[column_name]
            elif source_dataset == 'contract' and contract_data is not None:
                contract_info = contract_data[contract_data['player'] == player_name]
                if not contract_info.empty:
                    player_value = contract_info[column_name].iloc[0]
                else:
                    player_value = None
                position_player_names = position_players['player'].tolist()
                position_contracts = contract_data[contract_data['player'].isin(position_player_names)]
                reference_data = position_contracts[column_name]
            else:
                player_value = None
                reference_data = pd.Series([])
            if player_value is not None and not pd.isna(player_value):
                score = calculate_percentile_score(player_value, reference_data, ascending)
                scores[metric_name] = score
            else:
                scores[metric_name] = 0.5
        except Exception as e:
            scores[metric_name] = 0.5
    for metric_name, metric_config in position_metrics[position].items():
        source_dataset = metric_config['source']
        column_name = metric_config['column']
        ascending = metric_config['ascending']
        try:
            player_value = None
            if source_dataset == 'standard':
                player_value = player_row.get(column_name, None)
            else:
                player_value = None
                if position in position_datasets and source_dataset in position_datasets[position]:
                    dataset = position_datasets[position][source_dataset]
                    player_data = dataset[dataset['player'] == player_name]
                    if not player_data.empty and column_name in player_data.columns:
                        player_value = player_data[column_name].iloc[0]
            if source_dataset == 'standard':
                reference_data = position_players[column_name]
            else:
                reference_data = pd.Series([])
                if position in position_datasets and source_dataset in position_datasets[position]:
                    dataset = position_datasets[position][source_dataset]
                    if position == 'Forward':
                        ref_players = dataset[dataset['pos'].str.contains('FW', na=False)]
                    elif position == 'Midfielder':
                        ref_players = dataset[dataset['pos'].str.contains('MF', na=False)]
                    elif position == 'Defender':
                        ref_players = dataset[dataset['pos'].str.contains('DF', na=False)]
                    else:
                        ref_players = dataset[dataset['pos'].str.contains('GK', na=False)]
                    if not ref_players.empty and column_name in ref_players.columns:
                        reference_data = ref_players[column_name]
            if player_value is not None and not pd.isna(player_value):
                score = calculate_percentile_score(player_value, reference_data, ascending)
                scores[metric_name] = score
            else:
                scores[metric_name] = 0.5
        except Exception as e:
            scores[metric_name] = 0.5
    return scores

def calculate_contract_risk_adjustment(contract_years, age, performance_score, position):
    if contract_years == -1:
        if performance_score > 0.7 and age < 30:
            return 0.3
        elif performance_score > 0.6:
            return 0.5
        else:
            return 0.8
    base_contract_risk = 0.0
    if contract_years <= 0.5:
        base_contract_risk = 0.6
    elif contract_years <= 1:
        base_contract_risk = 0.4
    elif contract_years <= 2:
        base_contract_risk = 0.2
    else:
        base_contract_risk = 0.1
    if performance_score > 0.8:
        if contract_years <= 1:
            performance_modifier = 0.6
        else:
            performance_modifier = 0.3
    elif performance_score > 0.6:
        performance_modifier = 1.0
    elif performance_score > 0.4:
        performance_modifier = 1.3
    else:
        performance_modifier = 1.6
    if age < 23:
        if performance_score > 0.7:
            age_modifier = 0.7
        else:
            age_modifier = 1.2
    elif age < 28:
        age_modifier = 1.1
    elif age < 32:
        age_modifier = 0.9
    else:
        if performance_score > 0.6:
            age_modifier = 0.8
        else:
            age_modifier = 1.4
    if position == 'Goalkeeper':
        if age > 35:
            position_modifier = 1.3
        elif age > 32:
            position_modifier = 0.8
        else:
            position_modifier = 1.0
    elif position == 'Defender':
        if age > 30 and performance_score > 0.6:
            position_modifier = 0.9
        else:
            position_modifier = 1.0
    else:
        position_modifier = 1.0
    contract_risk = base_contract_risk * performance_modifier * age_modifier * position_modifier
    return max(0.0, min(1.0, contract_risk))

def calculate_departure_probability_with_weights(player_row, percentile_scores, weights):
    position = player_row['position_group']
    base_risk = weights.get('base_risk', 0.3)
    if not percentile_scores:
        return 0.5
    universal_metrics = get_universal_metrics()
    position_metrics = get_position_specific_metrics()
    if position not in position_metrics:
        return 0.5
    universal_score = 0.0
    universal_weight = 0.0
    for metric_name in universal_metrics.keys():
        if metric_name == 'Contract_expires':
            continue
        weight_key = f'{metric_name}_weight'
        weight = weights.get(weight_key, 0.2)
        percentile_score = percentile_scores.get(metric_name, 0.5)
        universal_score += percentile_score * weight
        universal_weight += weight
    position_score = 0.0
    position_weight = 0.0
    for metric_name in position_metrics[position].keys():
        weight_key = f'{metric_name}_weight'
        weight = weights.get(weight_key, 0.1)
        percentile_score = percentile_scores.get(metric_name, 0.5)
        position_score += percentile_score * weight
        position_weight += weight
    if universal_weight + position_weight > 0:
        performance_score = (universal_score + position_score) / (universal_weight + position_weight)
    else:
        performance_score = 0.5
    contract_percentile = percentile_scores.get('Contract_expires', 0.5)
    contract_years = (1 - contract_percentile) * 4
    age = player_row.get('age', 25)
    contract_adjustment = calculate_contract_risk_adjustment(
        contract_years, age, performance_score, position)
    risk_multiplier = weights.get('risk_multiplier', 0.6)
    departure_prob = base_risk + (1 - performance_score) * risk_multiplier + contract_adjustment
    return max(0.05, min(0.95, departure_prob))

class GAOptimizer:
    def __init__(self, inter_data, league_data, position_datasets, position):
        self.inter_data = inter_data
        self.league_data = league_data
        self.position_datasets = position_datasets
        self.position = position
        self.iteration_count = 0
        self.best_result = None
    
    def get_bounds(self):
        universal_metrics = get_universal_metrics()
        position_metrics = get_position_specific_metrics()
        if self.position not in position_metrics:
            return {}
        bounds = {}
        for metric_name in universal_metrics.keys():
            if metric_name == 'Contract_expires':
                bounds[f'{metric_name}_weight'] = (0.05, 0.12)
            else:
                bounds[f'{metric_name}_weight'] = (0.08, 0.15)
        position_specific = list(position_metrics[self.position].keys())
        if self.position == 'Forward':
            important = ['Gls', 'xG', 'SoT', 'SCA', 'GCA']
        elif self.position == 'Midfielder':
            important = ['Ast', 'xAG', 'KP', 'Cmp_pct', 'PrgP']
        elif self.position == 'Defender':
            important = ['Tkl', 'Int', 'Blocks', 'Clr', 'Cmp_pct']
        else:
            important = ['Saves', 'Save_pct', 'CS', 'CS_pct']
        for metric in position_specific:
            if metric in important:
                bounds[f'{metric}_weight'] = (0.08, 0.15)
            else:
                bounds[f'{metric}_weight'] = (0.05, 0.12)
        bounds.update({
            'base_risk': (0.2, 0.4),
            'risk_multiplier': (0.3, 0.7)
        })
        return bounds
    
    def fitness_function(self, weights_array):
        self.iteration_count += 1
        weight_bounds = self.get_bounds()
        weight_names = list(weight_bounds.keys())
        weights_dict = dict(zip(weight_names, weights_array))
        predictions = []
        actuals = []
        probabilities = []
        position_data = self.inter_data[self.inter_data['position_group'] == self.position].copy()
        for _, player in position_data.iterrows():
            percentile_scores = calculate_enhanced_percentile_scores(
                player, self.league_data, self.position_datasets)
            departure_prob = calculate_departure_probability_with_weights(
                player, percentile_scores, weights_dict)
            prediction = 1 if departure_prob > 0.5 else 0
            actual = int(player.get('departed_label', 0))
            predictions.append(prediction)
            actuals.append(actual)
            probabilities.append(departure_prob)
        if not predictions:
            return 1.0
        try:
            accuracy = sum(p == a for p, a in zip(predictions, actuals)) / len(predictions)
            if len(set(actuals)) > 1:
                pr_auc = average_precision_score(actuals, probabilities)
                f1 = f1_score(actuals, predictions, zero_division=0)
                balanced_acc = balanced_accuracy_score(actuals, predictions)
                brier = brier_score_loss(actuals, probabilities)
                composite_score = (
                    0.40 * pr_auc +
                    0.30 * f1 +
                    0.20 * balanced_acc +
                    0.10 * (1 - brier)
                )
            else:
                composite_score = accuracy
        except Exception as e:
            composite_score = accuracy if 'accuracy' in locals() else 0.0
        if composite_score > (self.best_result or -1):
            self.best_result = composite_score
        return -composite_score
    
    def optimize(self):
        weight_bounds = self.get_bounds()
        bounds = [(low, high) for low, high in weight_bounds.values()]
        start_time = time.time()
        self.iteration_count = 0
        self.best_result = None
        result = differential_evolution(
            func=self.fitness_function,
            bounds=bounds,
            maxiter=20,
            popsize=10,
            seed=42,
            disp=False
        )
        optimization_time = time.time() - start_time
        best_weights = dict(zip(weight_bounds.keys(), result.x))
        return {
            'method': 'Genetic Algorithm',
            'weights': best_weights,
            'score': -result.fun,
            'time': optimization_time,
            'iterations': self.iteration_count
        }

def run_ga_weight_optimization():
    start_time = time.time()
    inter_data, league_data, position_datasets = load_experimental_data_enhanced()
    if inter_data is None:
        return None
    results = {
        'timestamp': datetime.now().isoformat(),
        'algorithm': 'GA',
        'positions': {}
    }
    positions = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
    optimized_weights = {}
    for position in positions:
        pos_data = inter_data[inter_data['position_group'] == position]
        if len(pos_data) == 0:
            continue
        optimizer = GAOptimizer(inter_data, league_data, position_datasets, position)
        opt_result = optimizer.optimize()
        optimized_weights[position] = opt_result['weights']
        results['positions'][position] = {
            'player_count': len(pos_data),
            'result': opt_result
        }
    predictions = []
    for _, player in inter_data.iterrows():
        position = player['position_group']
        if position not in optimized_weights:
            continue
        percentile_scores = calculate_enhanced_percentile_scores(
            player, league_data, position_datasets)
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
        print("GA Algorithm - Final Results")
        print("=" * 40)
        print("Optimized Weights:")
        for position, weights in optimized_weights.items():
            print(f"\n{position}:")
            for name, value in weights.items():
                print(f"  {name}: {value:.6f}")
        print(f"\nML Performance Metrics:")
        print(f"  accuracy: {accuracy:.4f}")
        print(f"  precision: {precision_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  recall: {recall_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  f1_score: {f1_score(actuals, predicted, zero_division=0):.4f}")
        print(f"  pr_auc: {pr_auc:.4f}")
        print(f"  cohen_kappa: {kappa:.4f}")
        print(f"  balanced_accuracy: {balanced_acc:.4f}")
        print(f"  mcc: {mcc:.4f}")
        print(f"  brier_score: {brier:.4f}")
        print(f"\nPlayer Predictions:")
        for pred in predictions:
            status = "DEPARTED" if pred['actual_departed'] == 1 else "STAYED"
            print(f"  {pred['player']} ({pred['position']}): "
                  f"Departure={pred['departure_probability']:.1%}, "
                  f"Stay={pred['stay_probability']:.1%} - Actual: {status}")
        results['ml_metrics'] = {
            'accuracy': accuracy,
            'precision': precision_score(actuals, predicted, zero_division=0),
            'recall': recall_score(actuals, predicted, zero_division=0),
            'f1_score': f1_score(actuals, predicted, zero_division=0),
            'pr_auc': pr_auc,
            'cohen_kappa': kappa,
            'brier_score': brier,
            'balanced_accuracy': balanced_acc,
            'mcc': mcc
        }
    except Exception as e:
        pass
    results['predictions'] = predictions
    results['optimized_weights'] = optimized_weights
    results['execution_time'] = time.time() - start_time
    return results

if __name__ == "__main__":
    run_ga_weight_optimization()