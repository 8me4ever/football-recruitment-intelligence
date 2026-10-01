# Scrapling 本地离线源码

## 本机副本

- 上游仓库：[D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)
- 固定版本：`v0.4.15`，上游发布标注提交 `333fa22`；它与项目已安装的 Scrapling 版本一致。[官方发布页](https://github.com/D4Vinci/Scrapling/releases/tag/v0.4.15)
- 完整源码：[`vendor/Scrapling-0.4.15`](../vendor/Scrapling-0.4.15)
- 原始压缩包：[`vendor/Scrapling-v0.4.15.zip`](../vendor/Scrapling-v0.4.15.zip)
- ZIP SHA-256：`dd039b2263b14e6791840393c7780a863b74b20413858f9ef044b10eef876dc9`
- 上游许可证：[`vendor/Scrapling-0.4.15/LICENSE`](../vendor/Scrapling-0.4.15/LICENSE)（BSD 3-Clause）

源码、当前 Python 依赖及 Playwright Chromium 均保存在本机。当前项目虚拟环境是 `.venv-scrapling`，其依赖版本在 [`requirements-scrapling.txt`](../requirements-scrapling.txt) 中固定。完成初始化后，Python 会从项目内源码目录导入 Scrapling。

## 初始化与使用

首次下载后运行一次：

```powershell
.\scripts\activate_scrapling_local.ps1
```

脚本只在本地虚拟环境的 `site-packages` 写入一个 `.pth` 路径文件，不安装新包、不访问 GitHub 或 PyPI。之后可直接运行现有采集脚本：

```powershell
.\.venv-scrapling\Scripts\python.exe .\scripts\collect_csl_2026_guoan_scrapling.py --help
```

若电脑已断网，可继续导入 Scrapling 和解析本地 HTML；抓取 Sofascore 等在线页面仍需连接目标网站。下载源码不会改变目标网站要求的登录或人工验证，也不会绕过这些要求。

## 重新建环境时

现有 `.venv-scrapling` 已装齐项目运行所需依赖。若以后需要从头创建新 Python 环境且机器全程离线，还需另行保存相应 Python 版本和平台的依赖 wheel 及 Playwright Chromium 安装包；仅有 Scrapling 源码不能代替这些运行依赖。
