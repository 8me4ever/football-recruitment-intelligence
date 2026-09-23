# -*- coding: utf-8 -*-
"""审计探针 7：核对 Multi_Run_Experiment_Results JSON 内部自洽性，以及论文表格数字的来源。"""
import json
import numpy as np

P = r"F:\Samuel\football recruitment\final project\Multi_Run_Experiment_Results_20250826_171631.json"
d = json.load(open(P, encoding="utf-8"))

print("=" * 92)
print("[1] 顶层信息")
print("=" * 92)
print("timestamp :", d.get("timestamp"))
print("n_runs    :", d.get("n_runs"))
print("global_best:", d.get("global_best", {}).get("algorithm"),
      "score=", d.get("global_best", {}).get("score"))
print()

print("=" * 92)
print("[2] 每个算法的逐次运行准确率（来自 all_run_data）与论文表格对照")
print("=" * 92)
PAPER = {"GA": 0.9200, "PSO": 0.9280, "SA": 0.7280, "RS": 0.9200}
for alg, res in d.get("results", {}).items():
    runs = res.get("all_run_data", [])
    accs, comps = [], []
    for r in runs:
        am = r.get("all_metrics", {}) or {}
        accs.append(am.get("accuracy", np.nan))
        comps.append(r.get("composite_score", np.nan))
    accs = np.array(accs, dtype=float)
    comps = np.array(comps, dtype=float)
    print(f"\n{alg}: runs={len(runs)}")
    print(f"   逐次 accuracy = {np.round(accs, 4).tolist()}")
    print(f"   mean accuracy = {np.nanmean(accs):.4f}   std = {np.nanstd(accs):.4f}")
    print(f"   逐次 composite = {np.round(comps, 4).tolist()}")
    print(f"   mean composite = {np.nanmean(comps):.4f}")
    print(f"   论文表格 value = {PAPER.get(alg)}   -> 与 mean accuracy "
          f"{'一致' if abs(np.nanmean(accs) - PAPER.get(alg, -1)) < 5e-4 else '不一致'}")
    print(f"   best_weights 位置 = {list((res.get('best_weights') or {}).keys())}")

print()
print("=" * 92)
print("[3] statistics 字段中关于 accuracy 的统计量")
print("=" * 92)
for alg, res in d.get("results", {}).items():
    st = res.get("statistics", {}) or {}
    keys = [k for k in st.keys() if "acc" in k.lower()][:8]
    print(f"{alg}: " + "  ".join(f"{k}={st[k]:.4f}" if isinstance(st[k], (int, float)) else f"{k}={st[k]}" for k in keys))

print()
print("=" * 92)
print("[4] global_best 的权重参数名（判断属于第几代算法实现）")
print("=" * 92)
gb = d.get("global_best", {})
w = gb.get("weights", {})
for pos, wd in w.items():
    print(f"{pos}: {sorted(wd.keys())}")
    break
print("总位置数:", list(w.keys()))
