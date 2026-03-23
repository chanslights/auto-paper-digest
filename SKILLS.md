# Auto Paper Digest - 抖音自动发布技能指南

## 功能概述

自动从 arXiv 抓取健康/医学论文，上传到 NotebookLM 生成视频 Overview，发布到抖音创作者平台。

## 快速开始

### 1. 安装依赖

```bash
# 安装系统依赖
yum install -y mesa-libgbm alsa-lib

# 安装 Python 依赖
pip install playwright beautifulsoup4 lxml requests click python-dotenv
playwright install chromium
```

### 2. 克隆项目

```bash
git clone https://github.com/chanslights/auto-paper-digest.git
cd auto-paper-digest
pip install -e .
```

### 3. 获取 Cookies（重要！）

#### 3.1 NotebookLM Cookies

1. 在本地 Chrome 登录 `notebooklm.google.com`
2. 安装 **EditThisCookie** 扩展
3. 导出 `notebooklm.google.com` 的 cookies 为 JSON
4. 上传到服务器：`/root/clawd/auto-paper-digest/data/profiles/chrome/Notebook_Cookies.json`

#### 3.2 抖音创作者 Cookies

**方法一：EditThisCookie 导出**
1. 在本地 Chrome 登录 `creator.douyin.com`
2. 导出 `.douyin.com` 和 `.bytedance.com` 的 cookies
3. 上传到服务器

**方法二（推荐）：Playwright 捕获 Session**
```bash
# 在服务器上运行，VNC 打开浏览器
vncserver :1 -geometry 1280x720 -depth 24

# 用 Playwright 启动浏览器让用户登录
cd /root/clawd/auto-paper-digest
DISPLAY=:1 python3 << 'EOF'
from playwright.sync_api import sync_playwright
import json

profile_path = 'data/profiles/default'

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        headless=False,
        viewport={'width': 1280, 'height': 900},
        args=['--no-sandbox']
    )
    
    page = context.new_page()
    page.goto('https://creator.douyin.com/', timeout=60000)
    
    # 用户扫码登录
    import time
    time.sleep(60)  # 等待用户登录
    
    # 保存 session
    cookies = context.cookies()
    with open('data/profiles/chrome/Cookies.json', 'w') as f:
        json.dump(cookies, f)
    
    print(f'Saved {len(cookies)} cookies')
    context.close()
EOF
```

## 使用方法

### 抓取健康论文

```bash
cd /root/clawd/auto-paper-digest
python3 -m apd.cli fetch-health -w 2026-12 -m 5
```

### 上传并生成视频

```bash
# 上传到 NotebookLM 生成视频
DISPLAY=:1 python3 -m apd.cli nblm -w 2026-12 --headful

# 或者用保存的 session（headless 模式）
python3 -m apd.cli nblm -w 2026-12
```

### 添加自定义 Prompt

```bash
# 中文 prompt，生成适合普通观众的视频
DISPLAY=:1 python3 -m apd.cli nblm -w 2026-12 --prompt "用简单的语言解释，适合普通观众，重点介绍实际应用"
```

### 医生科普 Prompt（用于健康/心理类视频）

代码中已内置 `NOTEBOOKLM_PROMPT_MENTAL_HEALTH` 常量（位于 `apd/config.py`）。

```bash
# 方式一：使用内置常量（需要 python 引用）
DISPLAY=:1 python3 -c "
from apd.config import NOTEBOOKLM_PROMPT_MENTAL_HEALTH
import subprocess
subprocess.run(['python3', '-m', 'apd.cli', 'nblm', '-w', '2026-13', '--paper-id', '<论文ID>', '--prompt', NOTEBOOKLM_PROMPT_MENTAL_HEALTH])
"

# 方式二：直接粘贴 prompt
DISPLAY=:1 python3 -m apd.cli nblm -w 2026-13 --paper-id <论文ID> \
  --prompt '你是一位专业的临床医生/医学科普专家，需要为普通大众讲解一篇健康/医疗类学术论文的核心内容。要求：
1. 语音：使用标准普通话，语气专业、温和，符合医生科普的语速（每分钟200字左右），避免生硬机械；
2. 内容：极度简洁，仅保留论文最核心的1-2个结论/发现，剔除专业术语（或用通俗语言解释），总时长控制在60秒内；
3. 风格：纯科普导向，聚焦「普通人能理解、能应用」的知识点，不涉及复杂实验/数据细节；
4. 结构：
   - 开头（10秒）：用生活化的问题引入（如「你知道XX疾病的最新预防方法吗？」）；
   - 核心（40秒）：用1-2句话讲清论文的核心发现（通俗化）；
   - 结尾（10秒）：给出简单的健康建议（如「日常做到XX就能降低风险」）。'
```

**注意：** 使用 `--paper-id` 指定单篇论文，以免覆盖其他已生成的视频。

### 下载视频

```bash
DISPLAY=:1 python3 -m apd.cli download-video -w 2026-12 --force
```

### 发布到抖音

```bash
# 确保 DISPLAY 可用
DISPLAY=:1 python3 -m apd.cli publish-douyin -w 2026-12 --headful

# 或者直接用（如果 session 有效）
DISPLAY=:1 python3 -m apd.cli publish-douyin -w 2026-12
```

### 一键运行完整流程

```bash
DISPLAY=:1 python3 -m apd.cli run -w 2026-12 -m 3 --headful
```

## 常见问题

### Q: 提示"需要登录"怎么办？

Session 过期了。需要重新获取 cookies：

**抖音：**
```bash
# 重新登录
rm -f data/profiles/default/SingletonLock
DISPLAY=:1 python3 << 'EOF'
from playwright.sync_api import sync_playwright
import json

profile_path = 'data/profiles/default'

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_path,
        headless=False,
        viewport={'width': 1280, 'height': 900},
        args=['--no-sandbox']
    )
    page = context.new_page()
    page.goto('https://creator.douyin.com/', timeout=60000)
    import time
    time.sleep(120)  # 等用户扫码登录
    cookies = context.cookies()
    with open('data/profiles/chrome/Cookies.json', 'w') as f:
        json.dump(cookies, f)
    context.close()
EOF
```

### Q: Session 能维持多久？

- 抖音 session：通常 2-4 周
- NotebookLM session：通常 1-2 周
- 检测到异常可能提前过期

### Q: 如何设置定时任务？

```bash
# 编辑 crontab
crontab -e

# 每天早上 9 点运行
0 9 * * * cd /root/clawd/auto-paper-digest && DISPLAY=:1 python3 -m apd.cli run -w $(date +\%G-\%V) >> logs/cron.log 2>&1
```

## 目录结构

```
auto-paper-digest/
├── data/
│   ├── profiles/
│   │   ├── chrome/
│   │   │   └── Cookies.json          # EditThisCookie 导出的 cookies
│   │   ├── default/                  # Playwright Chromium profile（包含抖音 session）
│   │   └── nblm_auth/               # NotebookLM profile
│   ├── pdfs/weekly/                 # 下载的 PDF
│   ├── videos/weekly/               # 生成的视频
│   └── apd.db                       # SQLite 数据库
├── apd/
│   ├── health_fetcher.py            # arXiv 健康论文抓取
│   ├── nblm_bot.py                 # NotebookLM 自动化
│   ├── douyin_bot.py               # 抖音发布自动化
│   └── cli.py                      # 命令行工具
└── SKILLS.md                       # 本文件
```

## 视频描述模板

发布时使用的描述模板可在 `apd/cli.py` 中修改：

```python
# 默认模板
description = f"{paper.summary}\n\narXiv: {paper.paper_id}"
```

## Cookies 备份与恢复

Cookies 已备份到 `/root/.config/auto-paper-digest/cookies/`

```bash
# 备份
/root/auto-paper-digest/.devcontainer/backup-cookies.sh backup

# 恢复
/root/auto-paper-digest/.devcontainer/backup-cookies.sh restore
```

**重要**：备份文件包含敏感信息，请妥善保管！

## 技术栈

- **Playwright**: 浏览器自动化
- **arXiv API**: 论文抓取
- **NotebookLM**: AI 视频生成
- **抖音创作者平台**: 视频发布

## Coding Plan / 新服务器部署

### 使用 devcontainer

1. 在 Coding 中创建新项目，启用 DevOps → 代码托管
2. 关联 GitHub 仓库
3. 创建 Devbox（基于 devcontainer）
4. devcontainer 会自动：
   - 安装所有依赖
   - 克隆项目
   - 从备份恢复 cookies

### 部署步骤

```bash
# 1. 克隆项目
cd /root
git clone https://github.com/chanslights/auto-paper-digest.git
cd auto-paper-digest
pip install -e .

# 2. 恢复 cookies（如果之前有备份）
/root/auto-paper-digest/.devcontainer/backup-cookies.sh restore

# 3. 启动 VNC（如需要 headful 模式）
vncserver :1 -geometry 1280x720 -depth 24

# 4. 运行流水线
DISPLAY=:1 python3 -m apd.cli run -w 2026-12
```

### Cookie 位置

```
/root/.config/auto-paper-digest/cookies/
├── Cookies.json              # 抖音 EditThisCookie 格式
├── nblm_auth_storage.json   # NotebookLM storage state
├── default/                  # 抖音 Playwright profile
└── nblm_auth/               # NotebookLM Playwright profile
```

## 注意事项

1. 抖音和 NotebookLM 的 cookies 必须分别获取
2. 使用 VNC 时确保 DISPLAY 环境变量正确
3. 视频生成需要 5-10 分钟，耐心等待
4. 定期检查 cookies 有效性
