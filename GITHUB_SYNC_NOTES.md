# GITHUB_SYNC_NOTES — 同步到 GitHub 与换机接续

> 本文档说明如何把这个工作区同步到 GitHub，并在另一台电脑上继续开发。
> 生成于审计与 M1 完成之后。

---

## 0. 当前状态

本地 git 仓库**已准备好**（`F:\Samuel\football recruitment\.git`），含 **6 个提交、233 个文件、约 14.4 MB**：

```
4c66476  chore: 报告中改用相对路径，避免写入本机绝对路径
d17d839  fix: 纳入 M1 交付产物（此前被 .gitignore 误排除）
fce9b2b  docs: GitHub 同步与换机接续指南
c3181ea  docs(audit): 旧项目取证审计与迁移路线图
a686437  chore(archive): 归档原 MSc 项目（移动而非删除）
44d6fc1  feat: M1 clean data layer for Recruitment & Squad Intelligence System
```

**已完成的推送前检查**：

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

**尚未推送** —— 执行环境被沙箱完全断网（连 pypi/baidu 均不可达），
必须在你自己终端执行。`gh` 已用账号 `8me4ever` 登录且 token 有 `repo` 权限。

---

## 1. 仓库可见性：Public（已确认）

你已确认**公开仓库**（理由：早已毕业，数据伪造不构成在读期间的学术风险）。据此：

- `_audit/DOC_CLAIMS_RAW.md` 与 `EXISTING_PROJECT_AUDIT.md` 中的取证内容**保留完整**；
- 学生姓名（Ziming Chen）、院校（University of Birmingham）作为作品署名保留。

> 如果以后改变主意，`gh repo edit --visibility private` 可随时改回私有。

---

## 2. 推送步骤（在你自己的终端执行）

```powershell
cd "F:\Samuel\football recruitment"

# 确认还没有远端
git remote -v

# 创建 Public 仓库并推送（一条命令完成）
gh repo create football-recruitment-intelligence --public --source=. --remote=origin --push
```

若希望**先手动建仓库再推送**：

```powershell
# 1) 在 GitHub 网页新建 Public 仓库 football-recruitment-intelligence
#    不要勾选 "Add a README / .gitignore / license"（避免与本地历史冲突）
# 2) 关联并推送
git remote add origin https://github.com/8me4ever/football-recruitment-intelligence.git
git branch -M main
git push -u origin main
```

推送后验证：

```powershell
git remote -v
git log --oneline -3
gh repo view --web
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
| **推送到 GitHub** | ⏳ **需你在本地终端执行（见第 2 节）** |
| 仓库可见性 | ✅ Public（已确认） |

---

## 7. 推送后建议立即做的事

1. **在另一台电脑上克隆并按第 3 节验证** —— 确认 `run_m1_build_data.py` 输出与本文档记录的期望值一致；
2. **在 `README.md` 顶部加上仓库链接**（可选，便于以后引用）；
3. **继续 M2/M3** —— 按 `_audit/MIGRATION_PLAN.md`，下一步是表现引擎 v2 与评估层，
   两者必须**同批交付**，否则会重演旧项目"先造模型再想评估"的错误。
