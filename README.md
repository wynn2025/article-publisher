# AI Article Publisher - Markdown多平台文章发布助手

> 一键将Markdown文章发布到CSDN、知乎、小红书等平台。支持Frontmatter、批量发布、格式自动适配。

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 为什么需要这个工具？

写技术文章的人都知道：一篇好文章值得发到多个平台。但每个平台的格式要求不同：
- CSDN标题要够长（至少21字符），标签要选好
- 知乎不支持checkbox，Markdown语法有差异
- 小红书标题限制20字，要加话题标签#，不能有Markdown格式

手动改来改去太累了！这个工具自动处理这些差异，一键多平台发布。

## 功能特点

- **Frontmatter支持** - 在Markdown头部用YAML定义标题、标签、分类
- **平台适配** - 自动转换格式，处理标题长度、标签数量、Markdown语法差异
- **三种发布模式**：
  - API自动发布（CSDN，需Cookie）
  - 浏览器辅助（打开编辑器，自动填好信息）
  - 内容准备（小红书，生成适配文件）
- **批量发布** - 一键发布整个目录的文章
- **文章检查** - 检测代码块、图片链接、字数等常见问题
- **模板生成** - 快速创建标准格式的文章
- **发布日志** - 记录每次发布的详细信息

## 快速开始

### 安装

```bash
pip install requests  # 可选，浏览器模式不需要
```

### 1. 预览文章

```bash
python main.py preview --file my_article.md
```

输出：
```
==================================================
  Article Preview
==================================================
  File:    my_article.md
  Title:   DeepSeek V4 API完全指南
  Tags:    AI, Python, DeepSeek
  Chars:   3,245
  Words:   1,856
  Lines:   89
  Code:    3 blocks
  Images:  2
  Links:   5
==================================================
```

### 2. 发布文章

```bash
# 先用dry-run测试
python main.py publish --file my_article.md --platforms csdn --dry-run

# 正式发布到CSDN
python main.py publish --file my_article.md --platforms csdn

# 同时发布到多个平台
python main.py publish --file my_article.md --platforms csdn,zhihu,xhs
```

### 3. 批量发布

```bash
python main.py batch --dir ./articles/ --platforms csdn,zhihu --dry-run
```

## 使用示例

### 示例1：创建文章模板并发布

```bash
# 1. 生成模板
python main.py template \
  --title "Python异步编程实战" \
  --tags Python,异步,实战 \
  --output my_article.md

# 2. 编辑文章（用你喜欢的编辑器）
code my_article.md

# 3. 检查文章
python main.py check --file my_article.md

# 4. 预览
python main.py preview --file my_article.md

# 5. 发布
python main.py publish --file my_article.md --platforms csdn,zhihu
```

### 示例2：导出平台适配内容

```bash
# 导出小红书格式
python main.py export --file article.md --platform xhs --output xhs_content.txt

# 导出CSDN JSON格式
python main.py export --file article.md --platform csdn --output csdn_data.json
```

### 示例3：CI/CD自动发布

```yaml
# .github/workflows/publish.yml
name: Auto Publish
on:
  push:
    paths: ['articles/**']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Publish to CSDN
        env:
          CSDN_COOKIE: ${{ secrets.CSDN_COOKIE }}
        run: |
          pip install requests
          python main.py batch --dir ./articles/ --platforms csdn
```

## 文章格式

支持标准Markdown + YAML Frontmatter：

```markdown
---
title: "你的文章标题"
tags: [AI, Python, DeepSeek]
category: 技术教程
description: "文章简介"
---

# 你的文章标题

正文内容...

## 章节标题

### 子章节

- 要点1
- 要点2

\`\`\`python
print("Hello!")
\`\`\`
```

## 命令列表

| 命令 | 说明 |
|------|------|
| `preview` | 预览文章信息和统计 |
| `publish` | 发布单篇文章 |
| `batch` | 批量发布目录下所有文章 |
| `check` | 检查文章问题 |
| `template` | 生成文章模板 |
| `export` | 导出为平台适配格式 |

## 平台支持

| 平台 | 自动发布 | 内容适配 | 标签处理 | 说明 |
|------|---------|---------|---------|------|
| CSDN | API+浏览器 | 标题补长 | 最多5个 | 需Cookie或手动发布 |
| 知乎 | 浏览器辅助 | 语法转换 | 最多5个 | 打开编辑器 |
| 小红书 | 内容准备 | 纯文本化 | #话题 | 生成适配文件，需APP发布 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `CSDN_COOKIE` | CSDN登录Cookie（API发布需要） |

## 定价

**个人版**: 免费（基础功能）
**专业版**: 49元（批量发布 + API自动化 + 优先支持）

适合：技术博主、自媒体运营者、SEO从业者、知识付费创作者

## 系统要求

- Python 3.6+
- requests（可选）
- 现代浏览器

## License

MIT License
