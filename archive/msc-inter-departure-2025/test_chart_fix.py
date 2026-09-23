#!/usr/bin/env python3
"""
测试修复后的图表生成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 模拟对比数据
test_data = {
    'Algorithm': ['GA', 'PSO', 'SA', 'RS'],
    'Accuracy': [0.950, 0.920, 0.720, 0.960],
    'PR_AUC': [0.950, 0.945, 0.900, 0.965],
    'Cohen_Kappa': [0.840, 0.840, 0.450, 0.840],
    'Brier_Score': [0.193, 0.191, 0.216, 0.190],
    'Balanced_Accuracy': [0.915, 0.915, 0.725, 0.915],
    'MCC': [0.845, 0.845, 0.495, 0.845],
    'Execution_Time': [170.9, 83.6, 57.9, 86.1]
}

df_comparison = pd.DataFrame(test_data)

# 测试新的图表代码
print("🧪 测试修复后的图表生成...")

# 创建图表 - 增大尺寸以避免显示问题
fig, axes = plt.subplots(2, 2, figsize=(20, 16))
fig.suptitle('多算法权重优化性能对比（测试版本）', fontsize=18, fontweight='bold')

# 1. 主要ML指标对比 - 使用matplotlib而非seaborn避免显示问题
ax1 = axes[0, 0]
metrics_to_plot = ['Accuracy', 'PR_AUC', 'Cohen_Kappa', 'Balanced_Accuracy', 'MCC']

# 手动创建分组柱状图
x = np.arange(len(df_comparison))
width = 0.15
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for i, metric in enumerate(metrics_to_plot):
    offset = (i - 2) * width
    bars = ax1.bar(x + offset, df_comparison[metric], width, 
                  label=metric, color=colors[i], alpha=0.8)
    
    # 为每个柱子添加数值标签
    for bar in bars:
        height = bar.get_height()
        if height > 0:  # 只显示有值的柱子
            ax1.text(bar.get_x() + bar.get_width()/2, height + 0.01,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=9)

ax1.set_title('主要ML指标对比', fontsize=14)
ax1.set_ylabel('指标得分', fontsize=12)
ax1.set_xlabel('算法', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(df_comparison['Algorithm'])
ax1.legend(loc='upper left', bbox_to_anchor=(0, 1))
ax1.set_ylim(0, 1.1)
ax1.grid(axis='y', alpha=0.3)

# 其他子图保持简单
ax2 = axes[0, 1]
ax2.bar(df_comparison['Algorithm'], [0.894, 0.891, 0.800, 0.684], color='steelblue', alpha=0.7)
ax2.set_title('综合评分排名', fontsize=14)
ax2.set_ylabel('综合评分', fontsize=12)

ax3 = axes[1, 0]
ax3.bar(df_comparison['Algorithm'], df_comparison['Brier_Score'], color='coral', alpha=0.7)
ax3.set_title('Brier Score对比 (越小越好)', fontsize=14)
ax3.set_ylabel('Brier Score', fontsize=12)

ax4 = axes[1, 1]
ax4.bar(df_comparison['Algorithm'], df_comparison['Execution_Time'], color='lightgreen', alpha=0.7)
ax4.set_title('算法执行时间对比', fontsize=14)
ax4.set_ylabel('执行时间 (秒)', fontsize=12)

plt.tight_layout(pad=3.0)
plt.savefig('test_chart_fix.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.show()

print("✅ 测试图表已生成: test_chart_fix.png")
print("请检查GA算法的Accuracy柱状图是否正确显示")