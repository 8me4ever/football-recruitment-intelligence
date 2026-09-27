# GITHUB_SYNC_NOTES — 同步到 GitHub 与换机接续

> 本文档说明如何把这个工作区同步到 GitHub，并在另一台电脑上继续开发。
> 本文于 2026-09-27 更新，记录现有仓库接续方式；项目进度见 Recruitment & Squad Intelligence 交接文档。

---

## 0. 当前状态

本地 Git 仓库位于工作区根目录，当前分支为 `main`，`origin` 已指向 `https://github.com/8me4ever/football-recruitment-intelligence.git`。仓库包含旧 Inter 项目归档、M1 交付物，以及当前 Recruitment & Squad Planning 项目的代码、文档和数据。

```
4c66476  chore: 报告中改用相对路径，避免写入本机绝对路径
d17d839  fix: 纳入 M1 交付产物（此前被 .gitignore 误排除）
fce9b2b  docs: GitHub 同步与换机接续指南
c3181ea  docs(audit): 旧项目取证审计与迁移路线图
a686437  chore(archive): 归档原 MSc 项目（移动而非删除）
44d6fc1  feat: M1 clean data layer for Recruitment & Squad Intelligence System
```

原先记录的 233 个文件、约 14.4 MB 是 2026-09-27 本轮 CSL 交付加入前的仓库基线，不能代表当前仓库大小。当前中超规范数据与原始可见页面记录也纳入版本控制，以便离线复核和重建审计导出；虚拟环境、浏览器配置目录和临时运行状态仍排除在外。

本轮新增的项目状态与接续建议见 [`recruitment-squad-intelligence/docs/HANDOFF_2026-09-27.md`](recruitment-squad-intelligence/docs/HANDOFF_2026-09-27.md)。

以下是旧版仓库的历史推送前检查记录，不代表 2026 CSL 文件加入后的新扫描结果。每次同步较大的新增文件集时，都应重新核对敏感信息与单文件体积：

| 检查 | 结果 |
|---|---|
| `git fsck` 完整性 | ✅ 无损坏 |
| 硬编码凭据 / token / 私钥 | ✅ 无 |
| 邮箱地址 | ✅ 无 |
| 真实学号 | ✅ 无（仅 PPT 大纲里一行清单文字「姓名、学号、导师」） |
| 本机绝对路径（泄露用户名） | ✅ 已改为相对路径 |
| 大文件（>5 MB） | ✅ 无，最大 1.99 MB |
| venv 排除（457 MB） | ✅ 已排除 |
| 工作区状态 | ✅ 干净 |

公开可见性仍为 Public。更新仓库内容时，先检查 `git status` 和待提交文件，再提交并推送到现有 `origin`；不要重复创建仓库或把本机认证信息写入文件。

---

## 1. 仓库可见性：Public（已确认）

你已确认**公开仓库**（理由：早已毕业，数据伪造不构成在读期间的学术风险）。据此：

- `_audit/DOC_CLAIMS_RAW.md` 与 `EXISTING_PROJECT_AUDIT.md` 中的取证内容**保留完整**；
- 学生姓名（Ziming Chen）、院校（University of Birmingham）作为作品署名保留。

> 如果以后改变主意，`gh repo edit --visibility private` 可随时改回私有。

---

## 2. 同步到现有 GitHub 仓库

```powershell
# 在本地仓库根目录执行以下命令

# 检查现有远端
git remote -v

# 检查待提交内容，然后提交并推送；本项目变更可按需明确添加以下路径
git status --short
git add .gitignore GITHUB_SYNC_NOTES.md recruitment-squad-intelligence/
git commit -m "feat(data): add recruitment intelligence evidence"
git push -u origin main
```

仓库已存在时不要再次运行 `gh repo create`。推送后可用以下命令核对远端提交：

```powershell
git remote -v
git log --oneline -3
git ls-remote origin refs/heads/main
```

---

## 3. 在另一台电脑上接续

### 3.1 克隆

```powershell
git clone https://github.com/8me4ever/football-recruitment-intelligence.git
cd football-recruitment-intelligence
```

### 3.2 重建 Python 环境

仓库**不含 venv**（457 MB，已排除），需重建：

```powershell
python -m venv venv
# Windows
.\venv\Scripts\python.exe -m pip install -r recruitment-squad-intelligence\requirements.txt
# macOS / Linux
./venv/bin/python -m pip install -r recruitment-squad-intelligence/requirements.txt
```

> 若目标机器**无法联网**安装 pytest，测试仍可运行：
> `python recruitment-squad-intelligence/scripts/run_tests.py`
> （零依赖运行器，实现同样 77 项断言）

### 3.3 验证环境（必须做，用来确认数据层在新机器上可复现）

```powershell
cd recruitment-squad-intelligence

# 重建数据层
python scripts/run_m1_build_data.py

# 跑回归测试，应输出「通过 77 / 失败 0」
python scripts/run_tests.py
```

**期望输出**（用于判断环境是否正确）：

```
赛季 2022-2023（完整 8 类统计，来自 CSV）
  原始: 行数=603  唯一球员=577  球队=20
  清洗后: 唯一球员=577  赛季中转会=26 人  低样本(Min<450)=147 人
  国米阵容: 25 人（离队 12 / 留队 13）
  候选池 (Min>=450): 430 人
... 2023-2024: 590 / 27 人 / 422 人
... 2024-2025: 599 / 26 人 / 429 人（仅 standard 类，来自原始 HTML）
完成，用时 ~1.4s
```

### 3.4 关键路径注意事项

`config/config.py` 通过**相对位置**推导路径，不写死绝对路径：

```
config/config.py  ->  PROJECT_ROOT = recruitment-squad-intelligence/
                  ->  WORKSPACE_ROOT = PROJECT_ROOT.parent
                  ->  LEGACY_RAW_DIR = WORKSPACE_ROOT/archive/msc-inter-departure-2025/data excel
```

因此**只要 `archive/` 与 `recruitment-squad-intelligence/` 保持同级**，换任何盘符/系统都能直接跑通。
若你把原始数据放在别处，用环境变量覆盖即可：

```powershell
$env:RSI_RAW_DATA_DIR = "D:\data\serie_a"
python scripts/run_m1_build_data.py
```

---

## 4. 跨平台注意事项

已在 `.gitattributes` 中处理：

| 项 | 处理 |
|---|---|
| 行尾 | 仓库内统一 LF；`*.ps1`/`*.bat` 保留 CRLF（Windows 专用） |
| 二进制 | `*.png`/`*.pptx`/`*.jpg` 标记为 binary，禁止行尾转换 |
| 大文件 diff | `*.html`/`*.csv` 关闭 diff 展示 |

**已知的跨平台风险**（克隆到 macOS/Linux 时留意）：

1. **文件名含全角括号**：`archive/.../Inter_Midfielders_Analysis(原）/`
   —— 在 Linux 上路径含全角字符一般可用，但某些工具链会出问题。本系统**不依赖**该目录。
2. **文件名含中文**：归档中的多份 `.md` 与 `.csv`（如 `权重优化算法实验原理详解.md`）
   —— 同上，仅归档用，`recruitment-squad-intelligence/` 内**全部为 ASCII 文件名**。
3. **文件名含空格**：`data/players_ITA-Serie A_2223_standard.html`
   —— `config.LEGACY_HTML_FILES` 中已按完整名登记，代码用 `Path` 拼接，无需转义。
4. `core.quotepath=false` 已设置，中文文件名在 `git status` 中正常显示。

---

## 5. 公开仓库的说明（本仓库已按此设置）

仓库为 **Public**，因此以下内容对所有人可见，请知悉：

| 内容 | 说明 |
|---|---|
| `_audit/DOC_CLAIMS_RAW.md` | 含对旧论文"统计显著性数据由 `np.random.normal()` 生成"的逐条取证与行号 |
| `_audit/EXISTING_PROJECT_AUDIT.md` | 含旧项目的 39 项技术债清单 |
| `archive/` | 旧 MSc 项目的全部代码、论文 LaTeX 源码、演示 PPT 与图表 |
| `recruitment-squad-intelligence/data/csl/` 与 `csl_2026_capture/` | 含中超及亚冠规范数据、原始可见网页记录和审计证据；用于复核采集结果 |
| 作者姓名 / 院校 | Ziming Chen / University of Birmingham（作为署名保留） |

**已确认无**：凭据、token、私钥、邮箱、真实学号、本机绝对路径。

如果将来希望改变可见性：

```powershell
gh repo edit --visibility private      # 改回私有
```

如果希望把"新系统"与"旧项目归档+取证"分开（例如想让招聘方只看到新系统）：

```powershell
# 方案：另建一个只含新系统的公开仓库
# 1) 复制出干净目录
git subtree split --prefix=recruitment-squad-intelligence -b portfolio-only
# 2) 推送到新仓库
gh repo create recruitment-squad-intelligence --public --source=. --push   # 需先切换到该分支
```

---

## 6. 同步状态清单

| 项 | 状态 |
|---|---|
| 本地 git 仓库初始化 | ✅ 完成 |
| 6 个结构化提交 | ✅ 完成 |
| venv 排除（457 MB） | ✅ 完成 |
| `.gitignore` / `.gitattributes`（跨平台） | ✅ 完成 |
| M1 交付产物纳入版本控制（约 1.5 MB） | ✅ 完成 |
| 归档完整性校验（SHA256 清单，171 个文件） | ✅ 无丢失 |
| 推送前隐私扫描（凭据/邮箱/学号/绝对路径） | ✅ 全部通过 |
| 新系统在新环境可复现（77 项测试） | ✅ 已验证 |
| GitHub 远端 | ✅ `origin` 已关联现有 Public 仓库；每批变更按第 2 节同步并复核 |
| 仓库可见性 | ✅ Public（已确认） |

---

## 7. 推送后建议立即做的事

1. **在另一台电脑上克隆并按第 3 节验证** —— 确认 `run_m1_build_data.py` 输出与本文档记录的期望值一致；
2. **在 `README.md` 顶部加上仓库链接**（可选，便于以后引用）；
3. **继续 C1/C2** —— 按 `recruitment-squad-intelligence/docs/正式项目章程.md` 与项目交接文档，先补齐逐人公开来源追溯和效力区间证据，再完成正式阵容需求诊断；不要把旧 Inter 原型的 M2/M3 阶段当作当前 CSL Gate。
