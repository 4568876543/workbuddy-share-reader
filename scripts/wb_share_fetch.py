#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wb_share_fetch.py — 读取 WorkBuddy 分享链接的完整内容

## 原理（逆向于 workbuddy.link 分享页）

1. 分享页 URL 形如：
       https://workbuddy.link/p/<pageId>?shareId=<shareId>&ext2=copy_link
   抓该 HTML 后，页面里**直接内嵌**了静态资源基址：
       https://workbuddy-space-static.codebuddy.work/page/<pageId>/<buildHash>/
2. 会话/文档数据以 JSON 形式**公开**托管在该基址下：
       <base>conversation-data.json
   无需 shareId、无需登录即可直接下载。
3. 解析 messages 数组，输出为可读的 Markdown。

## 用法

    python3 wb_share_fetch.py <分享链接或pageId> [--output FILE] [--json]

示例：
    python3 wb_share_fetch.py "https://workbuddy.link/p/QrU0kmqWM79FaeQr6zp3Uk?shareId=xxx&ext2=copy_link"
    python3 wb_share_fetch.py QrU0kmqWM79FaeQr6zp3Uk --output conv.md
    python3 wb_share_fetch.py <url> --json        # 同时导出原始 JSON

仅依赖 Python 标准库，无需 pip 安装。
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error

STATIC_RE = re.compile(
    r"https://workbuddy-space-static\.codebuddy\.work/page/([^/\s\"']+)/([^/\s\"']+)/"
)
PAGEID_RE = re.compile(r"workbuddy\.link/p/([A-Za-z0-9_-]+)")


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def resolve_pageid(arg: str) -> str:
    m = PAGEID_RE.search(arg)
    if m:
        return m.group(1)
    m = re.search(r"[?&]pageId=([A-Za-z0-9_-]+)", arg)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]+", arg.strip()):
        return arg.strip()
    return None


def extract_base(html: str) -> str:
    m = STATIC_RE.search(html)
    if m:
        return m.group(0)
    raise RuntimeError(
        "无法从分享页 HTML 中提取静态资源基址（workbuddy-space-static...）。"
        "可能链接已失效或页面结构已变更。"
    )


def fetch_conversation(base: str) -> dict:
    url = base.rstrip("/") + "/conversation-data.json"
    raw = fetch_text(url)
    return json.loads(raw)


def render_markdown(data: dict) -> str:
    name = data.get("name", "WorkBuddy 分享")
    assistant = data.get("assistantName", "")
    lines = [f"# {name}"]
    if assistant:
        lines.append(f"\n> 助手：{assistant}\n")
    messages = data.get("messages")
    if not isinstance(messages, list):
        # 非会话型分享（如文档）：原样导出顶层字段提示
        keys = list(data.keys())
        lines.append(f"\n> 未识别为会话结构，顶层字段：{keys}\n")
        return "\n".join(lines)
    for i, m in enumerate(messages):
        role = m.get("messageType", "?")
        ct = m.get("createTime", "")
        lines.append(f"\n{'=' * 64}\n[{i}] {role}  {ct}\n{'=' * 64}\n")
        content = m.get("content", [])
        if isinstance(content, str):
            lines.append(content)
            continue
        for c in content:
            if not isinstance(c, dict):
                lines.append(str(c))
                continue
            t = c.get("type")
            if t == "text":
                lines.append(c.get("text", ""))
            elif t == "code":
                code = c.get("text") or c.get("code") or ""
                lang = c.get("language", "")
                lines.append(f"```{lang}\n{code}\n```")
            elif t == "resource_link":
                lines.append(f"[资源链接] {c.get('name', '')} -> {c.get('uri', '')}")
            elif t == "image":
                uri = c.get("uri", "")
                lines.append(f"![图片]({uri})" if uri else "[图片]")
            else:
                lines.append(f"[{t}] {json.dumps(c, ensure_ascii=False)[:300]}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="读取 WorkBuddy 分享链接的完整内容")
    ap.add_argument("target", help="分享链接 URL 或直接给 pageId")
    ap.add_argument("--output", "-o", help="输出 Markdown 文件路径（默认打印到 stdout）")
    ap.add_argument("--json", action="store_true", help="同时把原始 JSON 写到 <output>.json")
    args = ap.parse_args()

    pageid = resolve_pageid(args.target)
    if not pageid:
        sys.exit("✗ 无法从输入中解析 pageId，请传入完整分享链接或 pageId。")

    print(f"→ pageId: {pageid}", file=sys.stderr)

    share_url = f"https://workbuddy.link/p/{pageid}"
    try:
        html = fetch_text(share_url)
    except urllib.error.HTTPError as e:
        sys.exit(f"✗ 抓取分享页失败：HTTP {e.code}")
    except Exception as e:  # noqa
        sys.exit(f"✗ 抓取分享页失败：{e}")

    try:
        base = extract_base(html)
    except RuntimeError as e:
        sys.exit(f"✗ {e}")
    print(f"→ 静态基址: {base}", file=sys.stderr)

    try:
        data = fetch_conversation(base)
    except Exception as e:  # noqa
        sys.exit(f"✗ 抓取会话数据失败：{e}")

    md = render_markdown(data)
    n = len(data.get("messages", [])) if isinstance(data.get("messages"), list) else 0
    print(f"→ 已解析消息 {n} 条", file=sys.stderr)

    if args.json and args.output:
        with open(args.output + ".json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✓ 已写入 {args.output}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
