# -*- coding: utf-8 -*-
"""审计探针 11：核对论文 composite 分数与自身表格是否自洽。"""
import json
import numpy as np

P = r"F:\Samuel\football recruitment\final project\Multi_Run_Experiment_Results_20250826_171631.json"
d = json.load(open(P, encoding="utf-8"))

print("用公式 0.4*pr_auc + 0.3*f1 + 0.2*bal_acc + 0.1*(1-brier) 代入【真实 JSON 的 5 轮均值】：")
print()
for alg, res in d["results"].items():
    A = []
    for r in res["all_run_data"]:
        m = r.get("all_metrics", {}) or {}
        A.append((m.get("pr_auc"), m.get("f1_score"),
                  m.get("balanced_accuracy"), m.get("brier_score")))
    A = np.array(A, dtype=float)
    mean = A.mean(axis=0)
    comp = 0.4*mean[0] + 0.3*mean[1] + 0.2*mean[2] + 0.1*(1-mean[3])
    print(f"  {alg:5s} pr_auc={mean[0]:.4f}  f1={mean[1]:.4f}  bal_acc={mean[2]:.4f}  "
          f"brier={mean[3]:.4f}  ->  composite={comp:.5f}")

print()
print("论文 results.tex:400 结果小结宣称 PSO composite = 0.9315")
print("论文 tab:algorithm_performance 只给了 accuracy/pr_auc/bal_acc/kappa/mcc，未给 f1 与 brier")
print()
print("补充：磁盘 Single_Run_ML_Metrics_20250826_134951.txt 中 GA/PSO/RS 的指标：")
for line in open(r"F:\Samuel\football recruitment\final project\Single_Run_ML_Metrics_20250826_134951.txt",
                 encoding="utf-8", errors="replace"):
    if line[:3] in ("GA ", "PSO", "SA ", "RS "):
        print("   ", line.rstrip())
