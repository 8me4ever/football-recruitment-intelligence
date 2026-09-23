#!/usr/bin/env python3
"""
多算法对比实验 - Multi-Algorithm Comparison Experiment
运行并对比四种不同的权重优化算法

算法列表:
1. Genetic Algorithm (GA) - 遗传算法
2. Particle Swarm Optimization (PSO) - 粒子群优化  
3. Simulated Annealing (SA) - 模拟退火
4. Random Search (RS) - 随机搜索

Author: Graduate Thesis Research Project
"""

import pandas as pd
import numpy as np
import json
import time
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             average_precision_score, roc_auc_score, cohen_kappa_score,
                             matthews_corrcoef, balanced_accuracy_score, brier_score_loss)
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class MultiAlgorithmComparison:
    """
    多算法对比分析类
    """
    
    def __init__(self):
        self.results = {}
        self.algorithms = {
            'GA': 'Enhanced_Weight_Optimization_Experiment',
            'PSO': 'PSO_Weight_Optimization_Experiment', 
            'SA': 'SA_Weight_Optimization_Experiment',
            'RS': 'RS_Weight_Optimization_Experiment'
        }
    
    def run_all_algorithms(self):
        """运行所有算法"""
        print("🚀 多算法权重优化对比实验")
        print("=" * 70)
        print("将依次运行以下算法:")
        print("  1. 🧬 遗传算法 (Genetic Algorithm)")
        print("  2. 🐝 粒子群优化 (Particle Swarm Optimization)")
        print("  3. 🔥 模拟退火 (Simulated Annealing)")
        print("  4. 🎲 随机搜索 (Random Search)")
        print("=" * 70)
        
        # 依次运行各个算法
        for alg_name, module_name in self.algorithms.items():
            print(f"\n🔄 正在运行 {alg_name} 算法...")
            start_time = time.time()
            
            try:
                # 动态导入并运行对应的算法
                if alg_name == 'GA':
                    from Enhanced_Weight_Optimization_Experiment import run_enhanced_weight_optimization
                    result = run_enhanced_weight_optimization()
                elif alg_name == 'PSO':
                    from PSO_Weight_Optimization_Experiment import run_pso_weight_optimization
                    result = run_pso_weight_optimization()
                elif alg_name == 'SA':
                    from SA_Weight_Optimization_Experiment import run_sa_weight_optimization
                    result = run_sa_weight_optimization()
                elif alg_name == 'RS':
                    from RS_Weight_Optimization_Experiment import run_rs_weight_optimization
                    result = run_rs_weight_optimization()
                
                execution_time = time.time() - start_time
                result['execution_time'] = execution_time
                self.results[alg_name] = result
                
                print(f"✅ {alg_name} 完成，耗时: {execution_time:.2f}秒")
                
            except Exception as e:
                print(f"❌ {alg_name} 执行失败: {e}")
                self.results[alg_name] = None
        
        print(f"\n🎉 所有算法执行完毕！")
    
    def generate_comparison_report(self):
        """生成对比分析报告"""
        print(f"\n📊 === 多算法性能对比分析 ===")
        
        # 收集所有算法的性能指标
        comparison_data = []
        
        for alg_name, result in self.results.items():
            if result is None:
                continue
                
            ml_metrics = result.get('overall_ml_metrics', {})
            execution_time = result.get('execution_time', 0)
            
            comparison_data.append({
                'Algorithm': alg_name,
                'Accuracy': ml_metrics.get('accuracy', 0),
                'PR_AUC': ml_metrics.get('pr_auc', 0),
                'Cohen_Kappa': ml_metrics.get('cohen_kappa', 0),
                'Brier_Score': ml_metrics.get('brier_score', 1),
                'Balanced_Accuracy': ml_metrics.get('balanced_accuracy', 0),
                'MCC': ml_metrics.get('mcc', 0),
                'ROC_AUC': ml_metrics.get('roc_auc', 0.5),
                'Execution_Time': execution_time
            })
        
        if not comparison_data:
            print("❌ 没有可用的结果数据进行对比")
            return
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # 打印对比表格
        print(f"\n🏆 算法性能对比表:")
        print("=" * 120)
        print(f"{'算法':<12} {'准确率':<8} {'PR-AUC':<8} {'Kappa':<8} {'Brier':<8} {'平衡准确率':<10} {'MCC':<8} {'ROC-AUC':<8} {'耗时(秒)':<8}")
        print("-" * 120)
        
        for _, row in df_comparison.iterrows():
            print(f"{row['Algorithm']:<12} {row['Accuracy']:<8.3f} {row['PR_AUC']:<8.3f} "
                  f"{row['Cohen_Kappa']:<8.3f} {row['Brier_Score']:<8.3f} {row['Balanced_Accuracy']:<10.3f} "
                  f"{row['MCC']:<8.3f} {row['ROC_AUC']:<8.3f} {row['Execution_Time']:<8.1f}")
        
        # 算法排名分析
        print(f"\n🥇 算法排名分析:")
        
        # 综合评分 (Brier Score越小越好，其他越大越好)
        df_comparison['Composite_Score'] = (
            0.25 * df_comparison['PR_AUC'] +
            0.20 * df_comparison['Balanced_Accuracy'] +
            0.20 * df_comparison['Cohen_Kappa'] +
            0.15 * df_comparison['MCC'] +
            0.10 * df_comparison['Accuracy'] +
            0.10 * (1 - df_comparison['Brier_Score'])
        )
        
        df_ranked = df_comparison.sort_values('Composite_Score', ascending=False)
        
        print("基于综合评分的排名:")
        for i, (_, row) in enumerate(df_ranked.iterrows(), 1):
            print(f"  {i}. {row['Algorithm']}: 综合评分 {row['Composite_Score']:.3f}")
        
        # 特定指标的最佳算法
        print(f"\n🎯 各指标最佳算法:")
        best_accuracy = df_comparison.loc[df_comparison['Accuracy'].idxmax(), 'Algorithm']
        best_pr_auc = df_comparison.loc[df_comparison['PR_AUC'].idxmax(), 'Algorithm']
        best_kappa = df_comparison.loc[df_comparison['Cohen_Kappa'].idxmax(), 'Algorithm']
        best_brier = df_comparison.loc[df_comparison['Brier_Score'].idxmin(), 'Algorithm']  # 越小越好
        best_balanced = df_comparison.loc[df_comparison['Balanced_Accuracy'].idxmax(), 'Algorithm']
        best_mcc = df_comparison.loc[df_comparison['MCC'].idxmax(), 'Algorithm']
        fastest = df_comparison.loc[df_comparison['Execution_Time'].idxmin(), 'Algorithm']
        
        print(f"  最高准确率: {best_accuracy}")
        print(f"  最佳PR-AUC: {best_pr_auc}")
        print(f"  最佳Cohen's Kappa: {best_kappa}")
        print(f"  最佳Brier Score: {best_brier}")
        print(f"  最佳平衡准确率: {best_balanced}")
        print(f"  最佳MCC: {best_mcc}")
        print(f"  最快执行: {fastest}")
        
        return df_comparison
    
    def create_visualization(self, df_comparison):
        """创建可视化图表"""
        if df_comparison is None or len(df_comparison) == 0:
            return
            
        print(f"\n📈 正在生成可视化图表...")
        
        # 创建图表 - 增大尺寸以避免显示问题
        fig, axes = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle('多算法权重优化性能对比', fontsize=18, fontweight='bold')
        
        # 1. 主要ML指标对比 - 使用matplotlib而非seaborn避免显示问题
        ax1 = axes[0, 0]
        metrics_to_plot = ['Accuracy', 'PR_AUC', 'Cohen_Kappa', 'Balanced_Accuracy', 'MCC']
        
        # 手动创建分组柱状图 - 支持误差条
        x = np.arange(len(df_comparison))
        width = 0.15
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, metric in enumerate(metrics_to_plot):
            offset = (i - 2) * width
            
            # 检查是否有标准差数据
            std_col = f'{metric}_Std'
            if std_col in df_comparison.columns:
                yerr = df_comparison[std_col]
            else:
                yerr = None
            
            bars = ax1.bar(x + offset, df_comparison[metric], width, 
                          label=metric, color=colors[i], alpha=0.8, 
                          yerr=yerr, capsize=3, error_kw={'linewidth':1})
            
            # 为每个柱子添加数值标签 - 调整位置避免被遮挡
            for bar in bars:
                height = bar.get_height()
                if height > 0:  # 只显示有值的柱子
                    # 如果柱子太高，将标签放在柱子内部
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
        
        ax1.set_title('主要ML指标对比', fontsize=14)
        ax1.set_ylabel('指标得分', fontsize=12)
        ax1.set_xlabel('算法', fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(df_comparison['Algorithm'])
        ax1.legend(loc='upper left', bbox_to_anchor=(0, 1))
        ax1.set_ylim(0, 1.15)  # 增加上限为标签留出更多空间
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. 综合评分排名
        ax2 = axes[0, 1]
        df_sorted = df_comparison.sort_values('Composite_Score', ascending=True)
        bars = ax2.barh(df_sorted['Algorithm'], df_sorted['Composite_Score'], 
                       color='steelblue', alpha=0.7)
        ax2.set_title('综合评分排名', fontsize=14)
        ax2.set_xlabel('综合评分', fontsize=12)
        
        # 为每个柱子添加数值标签
        for bar in bars:
            width = bar.get_width()
            ax2.text(width + 0.005, bar.get_y() + bar.get_height()/2, f'{width:.3f}',
                    ha='left', va='center', fontsize=11)
        ax2.grid(axis='x', alpha=0.3)
        
        # 3. Brier Score对比 (越小越好)
        ax3 = axes[1, 0]
        bars3 = ax3.bar(df_comparison['Algorithm'], df_comparison['Brier_Score'], 
                       color='coral', alpha=0.7)
        ax3.set_title('Brier Score对比 (越小越好)', fontsize=14)
        ax3.set_ylabel('Brier Score', fontsize=12)
        ax3.set_xlabel('算法', fontsize=12)
        ax3.set_ylim(0, max(df_comparison['Brier_Score']) * 1.15)
        
        # 为每个柱子添加数值标签
        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2, height + 0.002,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=11)
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. 执行时间对比
        ax4 = axes[1, 1]
        bars4 = ax4.bar(df_comparison['Algorithm'], df_comparison['Execution_Time'], 
                       color='lightgreen', alpha=0.7)
        ax4.set_title('算法执行时间对比', fontsize=14)
        ax4.set_ylabel('执行时间 (秒)', fontsize=12)
        ax4.set_xlabel('算法', fontsize=12)
        
        # 为每个柱子添加数值标签
        for bar in bars4:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2, height + max(df_comparison['Execution_Time']) * 0.02,
                    f'{height:.1f}s', ha='center', va='bottom', fontsize=11)
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout(pad=3.0)  # 增加子图间距
        
        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_file = f"Multi_Algorithm_Comparison_Chart_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight', facecolor='white', 
                   edgecolor='none', format='png')
        plt.show()
        
        print(f"📊 可视化图表已保存: {chart_file}")
        
    def save_comprehensive_results(self):
        """保存综合结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"Multi_Algorithm_Comparison_Results_{timestamp}.json"
        
        comprehensive_results = {
            'timestamp': datetime.now().isoformat(),
            'experiment_type': 'Multi-Algorithm Weight Optimization Comparison',
            'algorithms_tested': list(self.algorithms.keys()),
            'individual_results': self.results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 综合对比结果已保存: {results_file}")
        return results_file

def main():
    """主函数"""
    print("🚀 启动多算法权重优化对比实验")
    
    # 创建对比分析器
    comparator = MultiAlgorithmComparison()
    
    # 运行所有算法
    comparator.run_all_algorithms()
    
    # 生成对比报告
    df_comparison = comparator.generate_comparison_report()
    
    # 创建可视化
    if df_comparison is not None:
        comparator.create_visualization(df_comparison)
    
    # 保存结果
    results_file = comparator.save_comprehensive_results()
    
    print(f"\n🎉 多算法对比实验完成!")
    print(f"📈 查看图表了解各算法性能差异")
    print(f"📄 详细结果请查看: {results_file}")

if __name__ == "__main__":
    main()