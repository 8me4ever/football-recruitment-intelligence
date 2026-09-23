#!/usr/bin/env python3
"""
快速测试多次运行框架 - 每个算法只运行3次
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def simulate_algorithm_results(algorithm_name, n_runs=3):
    """模拟算法运行结果"""
    np.random.seed(42)
    
    # 为不同算法设置不同的基础性能
    base_performance = {
        'GA': {'acc': 0.92, 'pr_auc': 0.94, 'kappa': 0.84},
        'PSO': {'acc': 0.91, 'pr_auc': 0.93, 'kappa': 0.83},
        'SA': {'acc': 0.72, 'pr_auc': 0.85, 'kappa': 0.45},
        'RS': {'acc': 0.93, 'pr_auc': 0.95, 'kappa': 0.85}
    }
    
    base = base_performance.get(algorithm_name, {'acc': 0.8, 'pr_auc': 0.8, 'kappa': 0.6})
    
    results = []
    for i in range(n_runs):
        # 添加随机噪声
        noise = np.random.normal(0, 0.02)
        result = {
            'Accuracy': max(0, min(1, base['acc'] + noise)),
            'PR_AUC': max(0, min(1, base['pr_auc'] + noise)),
            'Cohen_Kappa': max(0, min(1, base['kappa'] + noise)),
            'Brier_Score': max(0, min(1, 0.19 + np.random.normal(0, 0.01))),
            'Balanced_Accuracy': max(0, min(1, base['acc'] - 0.01 + noise)),
            'MCC': max(0, min(1, base['kappa'] + noise)),
            'Execution_Time': 60 + np.random.normal(0, 10)
        }
        results.append(result)
    
    return results

def create_averaged_comparison_data():
    """创建平均对比数据"""
    algorithms = ['GA', 'PSO', 'SA', 'RS']
    comparison_data = []
    
    for alg in algorithms:
        runs = simulate_algorithm_results(alg, 3)
        df_runs = pd.DataFrame(runs)
        
        # 计算平均值和标准差
        avg_data = {
            'Algorithm': alg,
            'Accuracy': df_runs['Accuracy'].mean(),
            'PR_AUC': df_runs['PR_AUC'].mean(),
            'Cohen_Kappa': df_runs['Cohen_Kappa'].mean(),
            'Brier_Score': df_runs['Brier_Score'].mean(),
            'Balanced_Accuracy': df_runs['Balanced_Accuracy'].mean(),
            'MCC': df_runs['MCC'].mean(),
            'Execution_Time': df_runs['Execution_Time'].mean(),
            'Accuracy_Std': df_runs['Accuracy'].std(),
            'PR_AUC_Std': df_runs['PR_AUC'].std(),
            'Cohen_Kappa_Std': df_runs['Cohen_Kappa'].std(),
            'Brier_Score_Std': df_runs['Brier_Score'].std(),
            'Balanced_Accuracy_Std': df_runs['Balanced_Accuracy'].std(),
            'MCC_Std': df_runs['MCC'].std(),
            'Success_Rate': 1.0
        }
        
        comparison_data.append(avg_data)
    
    return pd.DataFrame(comparison_data)

def test_improved_visualization():
    """测试改进后的可视化效果"""
    print("🧪 测试改进后的多次运行可视化...")
    
    # 生成模拟的平均对比数据
    df_comparison = create_averaged_comparison_data()
    
    print("📊 生成的平均性能数据:")
    print(df_comparison[['Algorithm', 'Accuracy', 'PR_AUC', 'Cohen_Kappa', 'Accuracy_Std']].round(3))
    
    # 创建改进后的图表
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('多算法权重优化性能对比（多次运行平均值）', fontsize=18, fontweight='bold')
    
    # 1. 主要ML指标对比 - 带误差条
    ax1 = axes[0, 0]
    metrics_to_plot = ['Accuracy', 'PR_AUC', 'Cohen_Kappa', 'Balanced_Accuracy', 'MCC']
    
    x = np.arange(len(df_comparison))
    width = 0.15
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, metric in enumerate(metrics_to_plot):
        offset = (i - 2) * width
        std_col = f'{metric}_Std'
        yerr = df_comparison[std_col] if std_col in df_comparison.columns else None
        
        bars = ax1.bar(x + offset, df_comparison[metric], width, 
                      label=metric, color=colors[i], alpha=0.8, 
                      yerr=yerr, capsize=3, error_kw={'linewidth':1})
        
        # 添加数值标签 - 避免遮挡
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                if height > 0.85:
                    label_y = height - 0.05
                    va_align = 'top'
                    color = 'white'
                else:
                    label_y = height + 0.02
                    va_align = 'bottom'
                    color = 'black'
                
                ax1.text(bar.get_x() + bar.get_width()/2, label_y,
                        f'{height:.3f}', ha='center', va=va_align, 
                        fontsize=9, fontweight='bold', color=color)
    
    ax1.set_title('主要ML指标对比 (含标准差)', fontsize=14)
    ax1.set_ylabel('指标得分', fontsize=12)
    ax1.set_xlabel('算法', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_comparison['Algorithm'])
    ax1.legend(loc='upper left', bbox_to_anchor=(0, 1))
    ax1.set_ylim(0, 1.15)
    ax1.grid(axis='y', alpha=0.3)
    
    # 其他子图
    ax2 = axes[0, 1]
    composite_scores = [0.894, 0.891, 0.800, 0.896]  # 模拟综合评分
    bars2 = ax2.barh(df_comparison['Algorithm'], composite_scores, color='steelblue', alpha=0.7)
    ax2.set_title('综合评分排名', fontsize=14)
    ax2.set_xlabel('综合评分', fontsize=12)
    for i, bar in enumerate(bars2):
        width = bar.get_width()
        ax2.text(width + 0.005, bar.get_y() + bar.get_height()/2, f'{width:.3f}',
                ha='left', va='center', fontsize=11)
    
    ax3 = axes[1, 0]
    bars3 = ax3.bar(df_comparison['Algorithm'], df_comparison['Brier_Score'], 
                   color='coral', alpha=0.7, yerr=df_comparison['Brier_Score_Std'], 
                   capsize=3)
    ax3.set_title('Brier Score对比 (越小越好)', fontsize=14)
    ax3.set_ylabel('Brier Score', fontsize=12)
    ax3.grid(axis='y', alpha=0.3)
    
    ax4 = axes[1, 1]
    bars4 = ax4.bar(df_comparison['Algorithm'], df_comparison['Execution_Time'], 
                   color='lightgreen', alpha=0.7)
    ax4.set_title('算法执行时间对比', fontsize=14)
    ax4.set_ylabel('执行时间 (秒)', fontsize=12)
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout(pad=3.0)
    plt.savefig('test_improved_multi_run_chart.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print("✅ 改进后的可视化测试完成")
    print("📊 生成的图表应该包含:")
    print("  - 误差条显示标准差")
    print("  - 避免标签遮挡的智能定位")
    print("  - 更大的图表尺寸和清晰的布局")

if __name__ == "__main__":
    test_improved_visualization()