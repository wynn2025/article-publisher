#!/usr/bin/env python3
"""
AI Article Publisher v1.0 - Markdown文章多平台发布助手

将Markdown文章自动发布到CSDN、知乎等平台，或生成适配各平台的内容格式。
支持YAML Frontmatter、批量发布、日志记录。

功能：
  - Markdown文章解析（YAML Frontmatter支持）
  - CSDN自动发布（通过API）
  - 知乎文章准备（格式转换）
  - 小红书内容适配（标题限制+话题标签）
  - 文章预览和格式检查
  - 批量发布支持
  - 发布日志记录

依赖：pip install requests
可选：opencli（用于浏览器自动化发布）

Author: AI Tools Workshop
Version: 1.0.0
License: MIT
"""

import os
import sys
import json
import time
import argparse
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# ============================================================
# 配置
# ============================================================

PLATFORMS = {
    "csdn": {
        "name": "CSDN",
        "editor_url": "https://mp.csdn.net/mp_blog/creation/editor",
        "max_tags": 5,
        "title_min_len": 21,
        "api_url": "https://bizapi.csdn.net/blog-console-api/v1/article/save",
    },
    "zhihu": {
        "name": "知乎",
        "editor_url": "https://zhuanlan.zhihu.com/write",
        "max_tags": 5,
    },
    "xhs": {
        "name": "小红书",
        "title_max_len": 20,
    },
}

SUPPORTED_EXT = [".md", ".markdown", ".mdown", ".mkd"]

# ============================================================
# Markdown / Frontmatter 解析
# ============================================================

def parse_frontmatter(filepath: str) -> Tuple[Dict, str]:
    """解析Markdown文件的YAML Frontmatter"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    meta = {"title": "", "tags": [], "category": "", "description": ""}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            ytxt, body = parts[1].strip(), parts[2].strip()
            for line in ytxt.split("\n"):
                line = line.strip()
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key == "title":
                    meta["title"] = val
                elif key == "category":
                    meta["category"] = val
                elif key == "description":
                    meta["description"] = val
                elif key == "tags":
                    if val.startswith("["):
                        meta["tags"] = [
                            t.strip().strip('"').strip("'")
                            for t in val.strip("[]").split(",")
                        ]
                    else:
                        meta["tags"] = [val]

    # Fallback: extract title from H1
    if not meta["title"]:
        h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        meta["title"] = (
            h1.group(1).strip() if h1 else Path(filepath).stem.replace("_", " ")
        )

    if not meta["tags"]:
        meta["tags"] = ["AI", "Python"]

    return meta, body


# ============================================================
# 平台格式转换
# ============================================================

def md_to_csdn(meta: Dict, body: str) -> Dict:
    """转换为CSDN发布格式"""
    tags = meta.get("tags", [])[:5]
    title = meta["title"]
    # CSDN标题最少21个字符
    if len(title) < 21:
        title = "2026年" + title + "：技术实战详解"
    return {
        "title": title,
        "content": body,
        "tags": tags,
        "category": meta.get("category", "AI"),
    }


def md_to_zhihu(meta: Dict, body: str) -> Dict:
    """转换为知乎发布格式（去除不支持的Markdown语法）"""
    content = re.sub(r"- \[.\]", "-", body)
    return {
        "title": meta["title"],
        "content": content,
        "tags": meta.get("tags", [])[:5],
        "topic": meta.get("category", "AI"),
    }


def md_to_xhs(meta: Dict, body: str) -> Dict:
    """转换为小红书发布格式（纯文本+话题标签）"""
    content = re.sub(r"^#+\s+", "", body, flags=re.MULTILINE)
    content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
    content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content)
    tags_text = " ".join("#" + t for t in meta.get("tags", [])[:3])
    return {"title": meta["title"][:20], "content": content + "\n\n" + tags_text}


# ============================================================
# 文章检查
# ============================================================

def check_article(filepath: str) -> List[str]:
    """检查文章是否符合发布要求，返回警告列表"""
    warnings = []
    meta, body = parse_frontmatter(filepath)

    if len(body) < 100:
        warnings.append("文章内容过短（< 100字）")

    if len(meta["title"]) < 5:
        warnings.append("标题过短（< 5字）")

    if not meta["tags"]:
        warnings.append("未设置标签")

    code_blocks = re.findall(r"```", body)
    if len(code_blocks) % 2 != 0:
        warnings.append("代码块未正确关闭")

    images = re.findall(r"!\[.*?\]\((.*?)\)", body)
    for img in images:
        if not img.startswith(("http://", "https://")):
            if not os.path.exists(img):
                warnings.append("本地图片不存在: {}".format(img))

    return warnings


def preview_article(filepath: str) -> Dict:
    """预览文章信息"""
    meta, body = parse_frontmatter(filepath)
    char_count = len(body)
    word_count = len(body.split())
    line_count = len(body.splitlines())
    code_blocks = len(re.findall(r"```[\w]*\n", body))
    images = len(re.findall(r"!\[", body))
    links = len(re.findall(r"\[.*?\]\(", body))

    info = {
        "file": filepath,
        "title": meta["title"],
        "tags": meta["tags"],
        "category": meta.get("category", ""),
        "description": meta.get("description", ""),
        "chars": char_count,
        "words": word_count,
        "lines": line_count,
        "code_blocks": code_blocks,
        "images": images,
        "links": links,
        "warnings": check_article(filepath),
    }
    return info


def print_preview(info: Dict):
    """打印文章预览"""
    sep = "=" * 50
    print("\n{}".format(sep))
    print("  Article Preview")
    print(sep)
    print("  File:    {}".format(info["file"]))
    print("  Title:   {}".format(info["title"]))
    print("  Tags:    {}".format(", ".join(info["tags"])))
    print("  Chars:   {:,}".format(info["chars"]))
    print("  Words:   {:,}".format(info["words"]))
    print("  Lines:   {}".format(info["lines"]))
    print("  Code:    {} blocks".format(info["code_blocks"]))
    print("  Images:  {}".format(info["images"]))
    print("  Links:   {}".format(info["links"]))

    if info["warnings"]:
        print("\n  Warnings:")
        for w in info["warnings"]:
            print("    [!] {}".format(w))
    print(sep + "\n")


# ============================================================
# 发布核心
# ============================================================

class ArticlePublisher:
    """文章发布器"""

    def __init__(self, dry_run=False, log_dir="."):
        self.dry_run = dry_run
        self.log_dir = log_dir
        self.log_file = os.path.join(
            log_dir,
            "publish_log_{}.json".format(datetime.now().strftime("%Y%m%d")),
        )
        self.results = []

    def log(self, action, status, detail=""):
        """记录发布日志"""
        entry = {
            "time": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "detail": detail,
        }
        os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.results.append(entry)
        return entry

    def _open_browser(self, url):
        """打开浏览器"""
        import webbrowser
        webbrowser.open(url)

    def _pub_csdn(self, filepath, meta, body):
        """发布到CSDN"""
        formatted = md_to_csdn(meta, body)
        if self.dry_run:
            self.log("csdn", "dry_run", "Title: {}".format(formatted["title"]))
            print("  [DRY-RUN] CSDN: {}".format(formatted["title"]))
            return {"status": "dry_run", "title": formatted["title"]}

        # Try API publish first
        try:
            result = self._csdn_api_publish(formatted)
            if result:
                self.log("csdn", "success", result.get("url", ""))
                return result
        except Exception as e:
            print("  [FALLBACK] API failed: {}, opening browser...".format(e))

        # Fallback: open browser
        self._open_browser(PLATFORMS["csdn"]["editor_url"])
        self.log("csdn", "browser_opened", formatted["title"])
        print("  [BROWSER] CSDN editor opened. Paste your article.")
        print("  Title: {}".format(formatted["title"]))
        print("  Tags: {}".format(", ".join(formatted["tags"])))
        return {"status": "browser", "title": formatted["title"]}

    def _csdn_api_publish(self, formatted):
        """通过API发布到CSDN（需要Cookie）"""
        cookie = os.environ.get("CSDN_COOKIE", "")
        if not cookie:
            return None

        try:
            import requests
        except ImportError:
            return None

        headers = {
            "Content-Type": "application/json",
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0",
        }
        payload = {
            "title": formatted["title"],
            "markdowncontent": formatted["content"],
            "tags": ",".join(formatted["tags"]),
            "category": formatted.get("category", "AI"),
            "type": "original",
        }

        resp = requests.post(
            PLATFORMS["csdn"]["api_url"],
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {"status": "published", "url": data.get("data", {}).get("url", "")}
        return None

    def _pub_zhihu(self, filepath, meta, body):
        """发布到知乎"""
        formatted = md_to_zhihu(meta, body)
        if self.dry_run:
            self.log("zhihu", "dry_run", "Title: {}".format(formatted["title"]))
            print("  [DRY-RUN] Zhihu: {}".format(formatted["title"]))
            return {"status": "dry_run", "title": formatted["title"]}

        self._open_browser(PLATFORMS["zhihu"]["editor_url"])
        self.log("zhihu", "browser_opened", formatted["title"])
        print("  [BROWSER] Zhihu editor opened.")
        print("  Title: {}".format(formatted["title"]))
        print("  Topic: {}".format(formatted["topic"]))
        return {"status": "browser", "title": formatted["title"]}

    def _prep_xhs(self, filepath, meta, body):
        """准备小红书内容"""
        formatted = md_to_xhs(meta, body)
        self.log("xhs", "prepared", formatted["title"])

        # Save adapted content
        out_dir = os.path.join(os.path.dirname(filepath), "xhs_output")
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, Path(filepath).stem + "_xhs.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("Title: {}\n\n{}".format(formatted["title"], formatted["content"]))

        print("  [PREPARED] XHS content saved to: {}".format(out_file))
        print("  Title: {}".format(formatted["title"]))
        return {"status": "prepared", "file": out_file, "title": formatted["title"]}

    def publish_single(self, filepath, platforms):
        """发布单篇文章到指定平台"""
        meta, body = parse_frontmatter(filepath)
        results = {}
        for p in platforms:
            if p == "csdn":
                results["csdn"] = self._pub_csdn(filepath, meta, body)
            elif p == "zhihu":
                results["zhihu"] = self._pub_zhihu(filepath, meta, body)
            elif p == "xhs":
                results["xhs"] = self._prep_xhs(filepath, meta, body)
            else:
                print("  [SKIP] Unknown platform: {}".format(p))
        return results

    def publish_batch(self, directory, platforms, exts=None):
        """批量发布目录下所有文章"""
        if exts is None:
            exts = SUPPORTED_EXT
        files = []
        for root, dirs, filenames in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "xhs_output"]
            for fname in filenames:
                if any(fname.endswith(e) for e in exts):
                    files.append(os.path.join(root, fname))

        if not files:
            print("[WARN] No markdown files found in: {}".format(directory))
            return {}

        print("Found {} articles to publish.".format(len(files)))
        all_results = {}
        for i, f in enumerate(files, 1):
            print("\n--- [{}/{}] {} ---".format(i, len(files), os.path.basename(f)))
            all_results[f] = self.publish_single(f, platforms)
            if i < len(files):
                time.sleep(2)  # Rate limiting

        return all_results


# ============================================================
# 文章模板生成
# ============================================================

def generate_template(title="", tags=None, category="AI"):
    """生成一个示例Markdown文章模板"""
    if tags is None:
        tags = ["AI", "Python", "DeepSeek"]
    tags_str = ", ".join(tags)

    template = """---
title: "{title}"
tags: [{tags}]
category: {category}
description: "Article description here"
---

# {title}

> Brief introduction paragraph.

## Background

Explain the context and motivation.

## Key Points

### Point 1

Detailed explanation with examples.

```python
# Example code
import os
print("Hello, World!")
```

### Point 2

More details and analysis.

## Comparison

| Feature | Option A | Option B |
|---------|----------|----------|
| Speed   | Fast     | Slow     |
| Cost    | Low      | High     |

## Summary

Key takeaways:
- Point 1
- Point 2
- Point 3

## References

- [Link 1](https://example.com)
- [Link 2](https://example.com)

---
*Published with AI Article Publisher*
""".format(title=title or "My Article Title", tags=tags_str, category=category)

    return template


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Article Publisher - Markdown文章多平台发布助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Preview article
  python main.py preview --file article.md

  # Publish to CSDN (dry-run)
  python main.py publish --file article.md --platforms csdn --dry-run

  # Publish to multiple platforms
  python main.py publish --file article.md --platforms csdn,zhihu,xhs

  # Batch publish
  python main.py batch --dir ./articles/ --platforms csdn,zhihu

  # Generate template
  python main.py template --title "My Article" --tags AI,Python

  # Check article
  python main.py check --file article.md
""",
    )

    sub = parser.add_subparsers(dest="command")

    # Preview
    p_preview = sub.add_parser("preview", help="Preview article info")
    p_preview.add_argument("--file", "-f", required=True, help="Markdown file")

    # Publish single
    p_pub = sub.add_parser("publish", help="Publish a single article")
    p_pub.add_argument("--file", "-f", required=True, help="Markdown file")
    p_pub.add_argument("--platforms", "-p", default="csdn",
                       help="Comma-separated platforms: csdn,zhihu,xhs")
    p_pub.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # Batch publish
    p_batch = sub.add_parser("batch", help="Batch publish articles")
    p_batch.add_argument("--dir", "-d", required=True, help="Article directory")
    p_batch.add_argument("--platforms", "-p", default="csdn",
                         help="Comma-separated platforms")
    p_batch.add_argument("--dry-run", action="store_true", help="Dry run mode")

    # Check
    p_check = sub.add_parser("check", help="Check article for issues")
    p_check.add_argument("--file", "-f", required=True, help="Markdown file")

    # Template
    p_tmpl = sub.add_parser("template", help="Generate article template")
    p_tmpl.add_argument("--title", "-t", default="AI技术实战", help="Article title")
    p_tmpl.add_argument("--tags", default="AI,Python", help="Comma-separated tags")
    p_tmpl.add_argument("--category", default="AI", help="Category")
    p_tmpl.add_argument("--output", "-o", help="Output file path")

    # Export
    p_export = sub.add_parser("export", help="Export to platform format")
    p_export.add_argument("--file", "-f", required=True, help="Markdown file")
    p_export.add_argument("--platform", "-p", required=True,
                          choices=["csdn", "zhihu", "xhs"], help="Target platform")
    p_export.add_argument("--output", "-o", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print("AI Article Publisher v1.0.0")
    print("-" * 40)

    if args.command == "preview":
        info = preview_article(args.file)
        print_preview(info)

    elif args.command == "publish":
        platforms = [p.strip() for p in args.platforms.split(",")]
        pub = ArticlePublisher(dry_run=args.dry_run)
        results = pub.publish_single(args.file, platforms)
        print("\nResults:")
        for plat, res in results.items():
            print("  {}: {}".format(plat, res.get("status", "unknown")))

    elif args.command == "batch":
        platforms = [p.strip() for p in args.platforms.split(",")]
        pub = ArticlePublisher(dry_run=args.dry_run)
        pub.publish_batch(args.dir, platforms)

    elif args.command == "check":
        warnings = check_article(args.file)
        if warnings:
            print("Warnings for {}:".format(args.file))
            for w in warnings:
                print("  [!] {}".format(w))
        else:
            print("No issues found in {}".format(args.file))

    elif args.command == "template":
        tags = [t.strip() for t in args.tags.split(",")]
        template = generate_template(
            title=args.title, tags=tags, category=args.category
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(template)
            print("Template saved to: {}".format(args.output))
        else:
            print(template)

    elif args.command == "export":
        meta, body = parse_frontmatter(args.file)
        if args.platform == "csdn":
            data = md_to_csdn(meta, body)
        elif args.platform == "zhihu":
            data = md_to_zhihu(meta, body)
        elif args.platform == "xhs":
            data = md_to_xhs(meta, body)

        output = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print("Exported to: {}".format(args.output))
        else:
            print(output)


if __name__ == "__main__":
    main()
