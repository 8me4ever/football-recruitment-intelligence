# GITHUB_SYNC_NOTES — 同步到 GitHub 与换机接续

> 本文档说明如何把这个工作区同步到 GitHub，并在另一台电脑上继续开发。
> 生成于审计与 M1 完成之后。

---

## 0. 当前状态

本地 git 仓库**已准备好**（`F:\Samuel\football recruitment\.git`），含 3 个提交、221 个文件、约 14 MB：

```
c3181ea  docs(audit): 旧项目取证审计与迁移路线图
a686437  chore(archive): 归档原 MSc 项目（移动而非删除）
44d6fc1  feat: M1 clean data layer for Recruitment & Squad Intelligence System
```

**尚未推送** —— 执行环境被沙箱完全断网（连 pypi/baidu 均不可达），
必须在你自己的终端里执行推送。`gh` CLI 已用你的账号登录且 token 有 `repo` 权限，一条命令即可。

---

## ⚠️ 1. 重要：仓库可见性必须先决定

`_audit/DOC_CLAIMS_RAW.md`（163 KB）与 `_audit/EXISTING_PROJECT_AUDIT.md`（59 KB）中，
完整记录了旧 MSc 项目的以下事实：

- 论文第 6 章的统计显著性检验，所依据的"实验数据"由 `np.random.normal()` 生成；
- `Run_Statistical_Tests.py` 的检验结论是硬编码的；
- 论文第 4 章的数据表（球员数、标签分布、完整度）与磁盘数据不一致；
- 泛化测试框架从未真正运行过。

这些是**新系统"诚实化"的依据，不是要隐瞒的内容**。但请注意：

| 仓库可见性 | 后果 |
|---|---|
| **Private（强烈建议）** | 只有你和被邀请的协作者可见。上述内容安全，可完整保留 |
| **Public** | 任何人（包括导师、同学、未来的雇主）都能搜到。**存在实际的学术诚信风险** |

> **建议：建为 private 仓库。** 若将来需要公开展示，先按第 5 节做一份脱敏版本。

---

## 2. 推送步骤（在你自己的终端执行）

`gh` 已登录，以下命令**不要加 `--public`**（`gh repo create` 默认就是 private）：

```powershell
# 进入仓库
cd "F:\Samuel\football recruitment"

# 确认还没有远端
git remote -v

# 创建 private 仓库并推送（一条命令完成）
gh repo create football-recruitment-intelligence --private --source=. --remote=origin --push
```

如果希望**先手动建仓库再推送**：

```powershell
# 1) 在 GitHub 网页上新建一个 private 仓库，例如 football-recruitment-intelligence
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
gh repo view --web     # 在浏览器打开确认是 Private
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

## 5. 如果将来要公开仓库

公开前**必须**处理 `_audit/` 中的敏感内容。可选方案：

| 方案 | 做法 |
|---|---|
| **A. 移到私有仓库** | 把 `_audit/DOC_CLAIMS_RAW.md` 与 `EXISTING_PROJECT_AUDIT.md` 第 6 节移到另一个 private 仓库，公开仓库只留 `MIGRATION_PLAN.md` 与 `GAP_ANALYSIS.md` |
| **B. 脱敏重写** | 保留"旧项目存在方法论缺陷"的结论，去掉"伪造数据"的具体指控与行号 |
| **C. 压缩为教训清单** | 只保留"我们学到的 10 条实施纪律"（MIGRATION_PLAN.md 第 15 节已有），删掉对旧论文的取证细节 |

**建议 A**：公开的是**新系统**，审计细节留在私有侧。这既保护你，也不削弱新系统的价值。

同时，公开前应确认 `archive/` 是否要一起公开 —— 归档里包含旧论文全文与演示 PPT，
如需保留作品集展示，建议只公开 `recruitment-squad-intelligence/` 一个子目录。

---

## 6. 同步状态清单

| 项 | 状态 |
|---|---|
| 本地 git 仓库初始化 | ✅ 完成 |
| 3 个结构化提交 | ✅ 完成 |
| venv 排除（457 MB） | ✅ 完成 |
| `.gitignore` / `.gitattributes` | ✅ 完成 |
| 归档完整性校验（SHA256 清单） | ✅ 171 个文件，无丢失 |
| 新系统在新环境可复现（77 项测试） | ✅ 已验证 |
| **推送到 GitHub** | ⏳ **需你在本地终端执行（见第 2 节）** |
| **仓库可见性决策** | ⏳ **建议 private（见第 1 节）** |
