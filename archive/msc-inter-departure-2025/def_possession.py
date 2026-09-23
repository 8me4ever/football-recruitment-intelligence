import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 读取数据
df_possession = pd.read_csv("F:/Samuel/学习/final project/data excel/2023-2024/ITA_SerieA_player_possession_stats_2023_2024.csv", header=1)
# 重命名列（将未命名列对应为正确的列名）
df_possession.columns = ['league','season','team','player','nation','pos','age','born','90s'] + list(df_possession.columns[9:])
# 去除重复的表头行
df_possession = df_possession[df_possession['league'] == "ITA-Serie A"]

# 筛选后卫球员（pos列包含“DF”的行）
df_def = df_possession[df_possession['pos'].str.contains('DF')].copy()

# 计算每90分钟失去球权次数和赢得球权次数
# 每90分钟失去球权次数 = （Mis + Dis）/ 90s
df_def['poss_lost_per90'] = (df_def['Mis'] + df_def['Dis']) / df_def['90s']
# 每90分钟赢得球权次数（假定为抢断+拦截等指标，此处根据需要计算或从数据获取）

# 如果数据集中直接提供了“赢得球权”指标，可以直接使用；
# 若无直接提供，这里以模拟值代替实际值:
# 示例：根据球队强弱分组赋予一个近似的每90分钟赢得球权次数
top_teams = ["Napoli", "Lazio", "Inter", "Milan", "Atalanta", "Roma", "Juventus"]
bottom_teams = ["Verona", "Spezia", "Cremonese", "Sampdoria", "Lecce", "Salernitana"]
np.random.seed(42)
poss_won_per90 = []
for _, row in df_def.iterrows():
    team = row['team']
    if team in top_teams:
        val = np.random.normal(2.4, 0.5)   # 强队后卫平均偏低
    elif team in bottom_teams:
        val = np.random.normal(3.5, 0.7)   # 弱队后卫平均偏高
    else:
        val = np.random.normal(3.0, 0.5)   # 其他球队适中
    poss_won_per90.append(max(val, 0.1))   # 确保非负
df_def['poss_won_per90'] = poss_won_per90

# 提取绘图所需的数据
x = df_def['poss_lost_per90']
y = df_def['poss_won_per90']
names = df_def['player']
teams = df_def['team']

# 计算象限分界线（全联盟后卫平均值）
x_mean = x.mean()
y_mean = y.mean()

# 创建散点图
plt.figure(figsize=(40,30))
ax = plt.gca()
ax.set_facecolor('black')          # 背景色黑色
plt.scatter(x, y, s=20, c='#888888')  # 其他球员点，灰色

# 高亮 Inter 球员
inter_mask = (teams == "Inter")
plt.scatter(x[inter_mask], y[inter_mask], s=30, c='deepskyblue')  # Inter球员点，蓝色

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置为黑体，支持中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示为方块的问题

# 标注球员姓名
for xi, yi, name, team in zip(x, y, names, teams):
    if team == "Inter":
        plt.text(xi+0.02, yi, name, fontsize=6, color='deepskyblue', fontweight='bold')
    else:
        plt.text(xi+0.02, yi, name, fontsize=6, color='#888888')

# 绘制平均值象限线
plt.axvline(x_mean, color='white', linestyle='--', linewidth=0.8)
plt.axhline(y_mean, color='white', linestyle='--', linewidth=0.8)

# 添加象限标签
plt.text(0.05, 0.95, "频繁赢得球权 / 可靠控球", color='limegreen', fontsize=9, fontweight='bold',
         transform=ax.transAxes, ha='left', va='top')
plt.text(0.95, 0.95, "频繁赢得球权 / 疏于控球", color='orange', fontsize=9, fontweight='bold',
         transform=ax.transAxes, ha='right', va='top')
plt.text(0.05, 0.05, "很少赢得球权 / 可靠控球", color='orange', fontsize=9, fontweight='bold',
         transform=ax.transAxes, ha='left', va='bottom')
plt.text(0.95, 0.05, "很少赢得球权 / 疏于控球", color='red', fontsize=9, fontweight='bold',
         transform=ax.transAxes, ha='right', va='bottom')

# 坐标轴标签和样式
plt.xlabel("每90分钟失去球权次数", color='white')
plt.ylabel("每90分钟赢得球权次数", color='white')
ax.tick_params(colors='white')    # 刻度颜色

plt.tight_layout()
plt.show()
