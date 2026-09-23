#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class AlgorithmComparisonVisualization:
    
    def __init__(self):
        self.colors = {
            'GA': '#5B9BD5',    # Blue
            'PSO': '#70AD47',   # Green  
            'SA': '#FFC000',    # Orange
            'RS': '#C5504B'     # Red
        }
        
    def create_main_metrics_comparison(self, results_data, save_path=None):
        
        
        algorithms = list(results_data.keys())
        metrics = ['accuracy', 'pr_auc', 'cohen_kappa', 'balanced_accuracy', 'mcc']
        metric_labels = ['Accuracy', 'PR_AUC', 'Cohen_Kappa', 'Balanced_Accuracy', 'MCC']
        
        
        data = []
        for alg in algorithms:
            if results_data[alg]['success']:
                result = results_data[alg]['result']
                ml_metrics = result.get('ml_metrics', {})
                data.append([
                    ml_metrics.get('accuracy', 0),
                    ml_metrics.get('pr_auc', 0),
                    ml_metrics.get('cohen_kappa', 0),
                    ml_metrics.get('balanced_accuracy', 0),
                    ml_metrics.get('mcc', 0)
                ])
            else:
                data.append([0, 0, 0, 0, 0])
        
        data = np.array(data)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(algorithms))
        width = 0.15
        
        colors = ['#5B9BD5', '#FF9900', '#70AD47', '#FF6B6B', '#9B59B6']
        
        for i, (metric, label, color) in enumerate(zip(metrics, metric_labels, colors)):
            values = data[:, i]
            bars = ax.bar(x + i * width, values, width, label=label, color=color, alpha=0.8)
            
            
            for bar, value in zip(bars, values):
                if value > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                           f'{value:.3f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Algorithm', fontsize=12)
        ax.set_ylabel('Metric Value', fontsize=12)
        ax.set_title('Main ML Metrics Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(algorithms)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_ylim(0, 1.0)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            pass
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Main_Metrics_Comparison_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            pass
        
        plt.show()
        plt.close()
    
    def create_composite_score_ranking(self, results_data, save_path=None):
        
        
        composite_scores = {}
        for alg_name, result_data in results_data.items():
            if result_data['success']:
                result = result_data['result']
                ml_metrics = result.get('ml_metrics', {})
                
                pr_auc = ml_metrics.get('pr_auc', 0)
                f1_score = ml_metrics.get('f1_score', 0)
                balanced_acc = ml_metrics.get('balanced_accuracy', 0)
                brier_score = ml_metrics.get('brier_score', 1.0)
                
                
                composite_score = (
                    0.40 * pr_auc +
                    0.30 * f1_score + 
                    0.20 * balanced_acc +
                    0.10 * (1 - brier_score)
                )
                composite_scores[alg_name] = composite_score
            else:
                composite_scores[alg_name] = 0
        
        
        sorted_scores = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        
        algorithms = [item[0] for item in sorted_scores]
        scores = [item[1] for item in sorted_scores]
        
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.barh(algorithms, scores, color=[self.colors.get(alg, '#888888') for alg in algorithms])
        
        
        for bar, score in zip(bars, scores):
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                   f'{score:.3f}', ha='left', va='center', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('Composite Score', fontsize=12)
        ax.set_title('Composite Score Ranking', fontsize=14, fontweight='bold')
        ax.set_xlim(0, max(scores) * 1.15 if scores else 1)
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            pass
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Composite_Score_Ranking_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            pass
        
        plt.show()
        plt.close()
    
    def create_brier_score_comparison(self, results_data, save_path=None):
        
        
        algorithms = []
        brier_scores = []
        
        for alg_name, result_data in results_data.items():
            if result_data['success']:
                result = result_data['result']
                ml_metrics = result.get('ml_metrics', {})
                brier_score = ml_metrics.get('brier_score', 1.0)
                
                algorithms.append(alg_name)
                brier_scores.append(brier_score)
        
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(algorithms, brier_scores, 
                     color=[self.colors.get(alg, '#888888') for alg in algorithms],
                     alpha=0.8)
        
        
        for bar, score in zip(bars, brier_scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                   f'{score:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('Algorithm', fontsize=12)
        ax.set_ylabel('Brier Score', fontsize=12)
        ax.set_title('Brier Score Comparison (Lower is Better)', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(brier_scores) * 1.15 if brier_scores else 1)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            pass
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Brier_Score_Comparison_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            pass
        
        plt.show()
        plt.close()
    
    def create_all_charts(self, results_data, prefix="Algorithm_Comparison"):
        """创建所有对比图表"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("🎨 Generating algorithm comparison charts...")
        
        # 1. Main metrics comparison
        main_metrics_path = f"{prefix}_Main_Metrics_{timestamp}.png"
        self.create_main_metrics_comparison(results_data, main_metrics_path)
        
        # 2. Composite score ranking
        composite_score_path = f"{prefix}_Composite_Score_{timestamp}.png"
        self.create_composite_score_ranking(results_data, composite_score_path)
        
        # 3. Brier score comparison
        brier_score_path = f"{prefix}_Brier_Score_{timestamp}.png"
        self.create_brier_score_comparison(results_data, brier_score_path)
        
        print(f"✅ All charts generated with timestamp: {timestamp}")
        
        return {
            'main_metrics': main_metrics_path,
            'composite_score': composite_score_path,
            'brier_score': brier_score_path
        }

def create_charts_from_multi_run_data(comparison_df, prefix="Multi_Run_Comparison"):
    """从多次运行数据创建图表"""
    
    visualizer = AlgorithmComparisonVisualization()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    
    results_data = {}
    for _, row in comparison_df.iterrows():
        alg_name = row['Algorithm']
        results_data[alg_name] = {
            'success': True,
            'result': {
                'ml_metrics': {
                    'accuracy': row['Accuracy'],
                    'pr_auc': row['PR_AUC'],
                    'cohen_kappa': row['Cohen_Kappa'],
                    'balanced_accuracy': row['Balanced_Accuracy'],
                    'mcc': row['MCC'],
                    'brier_score': row['Brier_Score'],
                    'f1_score': row.get('F1_Score', row['Accuracy'])
                }
            }
        }
    
    return visualizer.create_all_charts(results_data, prefix)

if __name__ == "__main__":
    pass