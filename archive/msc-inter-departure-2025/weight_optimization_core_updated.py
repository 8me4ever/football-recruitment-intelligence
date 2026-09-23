#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             average_precision_score, roc_auc_score, cohen_kappa_score,
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

def calculate_base_risk_sigmoid(age, years_left, alpha, tau, contract_length=3):
    year_score = max(0, min(1, (contract_length - years_left) / contract_length))
    optimal_age = 30.0
    age_width = 6.0
    age_score = max(0, min(1, 1 - abs(age - optimal_age) / age_width))
    combined_score = 0.6 * year_score + 0.4 * age_score
    base_risk = 1 / (1 + np.exp(-alpha * (combined_score - tau)))
    return np.clip(base_risk, 0.1, 0.3)

def calculate_departure_probability_with_weights(player_row, percentile_scores, weights):
    position = player_row['position_group']
    if not percentile_scores:
        return 0.5
    universal_metrics = get_universal_metrics()
    position_metrics = get_position_specific_metrics()
    if position not in position_metrics:
        return 0.5
    universal_score = 0.0
    universal_weight = 0.0
    for metric_name in universal_metrics.keys():
        if metric_name in ['age', 'Contract_expires']:
            continue
        weight_key = f'{metric_name}_weight'
        weight = weights.get(weight_key, 0.1)
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
    contract_years = max(0, (1 - contract_percentile) * 4)
    age = player_row.get('age', 25)
    alpha = weights.get('alpha', 2.0)
    tau = weights.get('tau', 0.5)
    base_risk = calculate_base_risk_sigmoid(age, contract_years, alpha, tau)
    risk_multiplier = weights.get('risk_multiplier', 0.6)
    departure_prob = base_risk + (1 - performance_score) * risk_multiplier
    return max(0.05, min(0.95, departure_prob))

def evaluate_weights_enhanced(weights_dict, inter_data, league_data, position_datasets, position):
    predictions = []
    actuals = []
    probabilities = []
    position_data = inter_data[inter_data['position_group'] == position].copy()
    for _, player in position_data.iterrows():
        percentile_scores = calculate_enhanced_percentile_scores(
            player, league_data, position_datasets)
        departure_prob = calculate_departure_probability_with_weights(
            player, percentile_scores, weights_dict)
        prediction = 1 if departure_prob > 0.5 else 0
        actual = int(player.get('departed_label', 0))
        predictions.append(prediction)
        actuals.append(actual)
        probabilities.append(departure_prob)
    if not predictions:
        return 0.0, {}
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
        metrics = {
            'accuracy': accuracy,
            'pr_auc': pr_auc if len(set(actuals)) > 1 else 0.0,
            'f1_score': f1_score(actuals, predictions, zero_division=0),
            'cohen_kappa': cohen_kappa_score(actuals, predictions),
            'brier_score': brier_score_loss(actuals, probabilities),
            'balanced_accuracy': balanced_accuracy_score(actuals, predictions),
            'mcc': matthews_corrcoef(actuals, predictions)
        }
    except Exception as e:
        composite_score = accuracy if 'accuracy' in locals() else 0.0
        metrics = {'accuracy': composite_score}
    return composite_score, metrics