#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_main_metrics_chart(results_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    
    algorithms = []
    accuracy_vals = []
    pr_auc_vals = []
    cohen_kappa_vals = []
    balanced_acc_vals = []
    mcc_vals = []
    
    for alg_name, result_data in results_data.items():
        if result_data.get('success', False):
            algorithms.append(alg_name)
            ml_metrics = result_data['result'].get('ml_metrics', {})
            accuracy_vals.append(ml_metrics.get('accuracy', 0))
            pr_auc_vals.append(ml_metrics.get('pr_auc', 0))
            cohen_kappa_vals.append(ml_metrics.get('cohen_kappa', 0))
            balanced_acc_vals.append(ml_metrics.get('balanced_accuracy', 0))
            mcc_vals.append(ml_metrics.get('mcc', 0))
    
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = np.arange(len(algorithms))
    width = 0.15
    
    
    bars1 = ax.bar(x - 2*width, accuracy_vals, width, label='Accuracy', color='#5B9BD5', alpha=0.8)
    bars2 = ax.bar(x - width, pr_auc_vals, width, label='PR_AUC', color='#FF9900', alpha=0.8)
    bars3 = ax.bar(x, cohen_kappa_vals, width, label='Cohen_Kappa', color='#70AD47', alpha=0.8)
    bars4 = ax.bar(x + width, balanced_acc_vals, width, label='Balanced_Accuracy', color='#FF6B6B', alpha=0.8)
    bars5 = ax.bar(x + 2*width, mcc_vals, width, label='MCC', color='#9B59B6', alpha=0.8)
    
    
    for bars, values in [(bars1, accuracy_vals), (bars2, pr_auc_vals), (bars3, cohen_kappa_vals), 
                         (bars4, balanced_acc_vals), (bars5, mcc_vals)]:
        for bar, value in zip(bars, values):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Metric Value')
    ax.set_title('Main ML Metrics Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms)
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    filename = f"Main_Metrics_Comparison_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    pass
    return filename

def create_composite_score_chart(results_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    
    composite_scores = {}
    for alg_name, result_data in results_data.items():
        if result_data.get('success', False):
            ml_metrics = result_data['result'].get('ml_metrics', {})
            
            pr_auc = ml_metrics.get('pr_auc', 0)
            f1_score = ml_metrics.get('f1_score', ml_metrics.get('accuracy', 0))
            balanced_acc = ml_metrics.get('balanced_accuracy', 0)
            brier_score = ml_metrics.get('brier_score', 1.0)
            
            composite_score = (
                0.40 * pr_auc +
                0.30 * f1_score + 
                0.20 * balanced_acc +
                0.10 * (1 - brier_score)
            )
            composite_scores[alg_name] = composite_score
    
    
    sorted_items = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
    algorithms = [item[0] for item in sorted_items]
    scores = [item[1] for item in sorted_items]
    
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#5B9BD5', '#70AD47', '#FFC000', '#C5504B']
    bars = ax.barh(algorithms, scores, color=colors[:len(algorithms)])
    
    
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
               f'{score:.3f}', ha='left', va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Composite Score')
    ax.set_title('Composite Score Ranking')
    ax.set_xlim(0, max(scores) * 1.15 if scores else 1)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    filename = f"Composite_Score_Ranking_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    pass
    return filename

def create_brier_score_chart(results_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    algorithms = []
    brier_scores = []
    
    for alg_name, result_data in results_data.items():
        if result_data.get('success', False):
            ml_metrics = result_data['result'].get('ml_metrics', {})
            brier_score = ml_metrics.get('brier_score', 1.0)
            
            algorithms.append(alg_name)
            brier_scores.append(brier_score)
    
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#5B9BD5', '#70AD47', '#FFC000', '#C5504B']
    bars = ax.bar(algorithms, brier_scores, color=colors[:len(algorithms)], alpha=0.8)
    
    # Add value labels
    for bar, score in zip(bars, brier_scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
               f'{score:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Brier Score')
    ax.set_title('Brier Score Comparison (Lower is Better)')
    ax.set_ylim(0, max(brier_scores) * 1.15 if brier_scores else 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    filename = f"Brier_Score_Comparison_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    pass
    return filename

def create_all_charts(results_data, prefix="Algorithm_Comparison"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    
    
    try:
        chart1 = create_main_metrics_chart(results_data, timestamp)
        chart2 = create_composite_score_chart(results_data, timestamp)
        chart3 = create_brier_score_chart(results_data, timestamp)
        
        
        
        return {
            'main_metrics': chart1,
            'composite_score': chart2,
            'brier_score': chart3
        }
    except Exception as e:
        pass
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    pass