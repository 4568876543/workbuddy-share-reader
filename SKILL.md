---
name: workbuddy-share-reader
description: 读取 WorkBuddy 分享链接（workbuddy.link/p/xxx）的完整内容。当用户给出 workbuddy.link 分享链接、想要获取该链接背后的完整会话/文档正文、或要把分享对话导出为 Markdown 时使用。触发词：workbuddy 分享链接、分享页内容、读取分享、导出对话、workbuddy.link。
version: "1.0.0"
author: "罗星培 (luodong)"
created: "2026-11-08"
updated: "2026-11-08"
---

# WorkBuddy 分享链接读取器

把一条 `https://workbuddy.link/p/xxx` 分享链接，还原成**完整、可读的会话/文档正文**。
WorkBuddy 的分享页是一个前端 SPA，浏览器里只能"看"、不能直接复制全文或抓取；本 skill 逆向其静态资源托管规律，把内容**一键导出为 Markdown**。

## 何时使用

- 用户发来一个 `workbuddy.link/p/...` 链接，想要里面的全部内容（全文、配置、密钥说明、脚本等）。
- 需要把分享的对话/文档导出成 `.md` 存档或二次处理。
- WebFetch 抓取分享页只拿到"正在加载"占位时。

## 核心原理（3 步）

1. **抓分享页 HTML**：`https://workbuddy.link/p/<pageId>?shareId=...&ext2=copy_link`
   页面 HTML 里**直接内嵌**了静态资源基址：
   `https://workbuddy-space-static.codebuddy.work/page/<pageId>/<buildHash>/`
   （`<buildHash>` 每次可能不同，但一定写在该 HTML 中，动态提取即可，无需硬编码。）
2. **抓会话数据**：上面的基址下公开托管着
   `<base>conversation-data.json`
   这是一个**完整、无需登录、无需 shareId** 的 JSON（含全部 messages）。
3. **解析成 Markdown**：遍历 `messages[]`，把 `type=text/code/resource_link/image` 渲染成可读文本。

> 关键洞察：分享内容走的是**公开静态 CDN**，不是需要鉴权的 API。所以只要拿到底层 pageId 和 buildHash，就能直接拉全文。

## 使用方法

```bash
# 给定完整分享链接，直接打印到终端
python3 scripts/wb_share_fetch.py "https://workbuddy.link/p/QrU0kmqWM79FaeQr6zp3Uk?shareId=xxx&ext2=copy_link"

# 只给 pageId，导出为文件
python3 scripts/wb_share_fetch.py QrU0kmqWM79FaeQr6zp3Uk --output 对话全文.md

# 同时保留原始 JSON（便于二次处理）
python3 scripts/wb_share_fetch.py <url> --output out --json
```

仅依赖 Python 标准库，无需 `pip install`。

## 注意事项

- 内容依赖**公开静态 CDN**，因此只适用于"已分享/可公开访问"的链接；私密、已撤回或已删除的分享无法读取。
- 若 WorkBuddy 改版导致静态基址命名规则变化，`extract_base()` 中的正则需相应调整——脚本会给出明确报错而非静默失败。
- 导出的图片 `type=image` 的 `uri` 可能是资源占位而非可直接打开的 URL，需结合平台另行处理。
- 尊重内容版权与隐私：导出的内容仅用于本人存档或获授权后的用途。
