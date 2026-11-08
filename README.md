# workbuddy-share-reader

把一条 WorkBuddy 分享链接（`https://workbuddy.link/p/xxx`）一键还原成**完整、可读的会话/文档正文（Markdown）**。

WorkBuddy 的分享页是一个前端 SPA，浏览器里只能"在线看"，不能直接复制全文或抓取。本工具逆向其静态资源托管规律，把分享背后的全部内容（对话、配置、脚本、说明）直接导出为 Markdown，**无需登录、无需 shareId**。

## 为什么需要它

- 分享页 WebFetch / 爬虫只能拿到"正在加载"的占位 HTML；
- 想存档、二次处理、或把 AI 对话转成文档时，只能手动逐条复制；
- 本工具一行命令搞定全文导出。

## 原理（3 步）

1. 抓 `https://workbuddy.link/p/<pageId>` 的 HTML —— 里面**内嵌**了公开静态基址
   `https://workbuddy-space-static.codebuddy.work/page/<pageId>/<buildHash>/`
2. 基址下公开托管着 `conversation-data.json`（完整会话 JSON）
3. 解析 `messages[]` 渲染成 Markdown

核心洞察：分享内容走的是**公开静态 CDN**，不是需要鉴权的 API。

## 安装（作为 CodeBuddy / WorkBuddy Skill）

```bash
git clone https://github.com/4568876543/workbuddy-share-reader.git
mkdir -p ~/.codebuddy/skills/
ln -s "$(pwd)/workbuddy-share-reader" ~/.codebuddy/skills/workbuddy-share-reader
```

## 用法

```bash
python3 scripts/wb_share_fetch.py "<分享链接或 pageId>" [--output FILE] [--json]

# 示例
python3 scripts/wb_share_fetch.py "https://workbuddy.link/p/QrU0kmqWM79FaeQr6zp3Uk?shareId=xxx&ext2=copy_link"
python3 scripts/wb_share_fetch.py QrU0kmqWM79FaeQr6zp3Uk --output 对话全文.md
python3 scripts/wb_share_fetch.py <url> --output out --json   # 同时导出原始 JSON
```

仅依赖 Python 标准库，无需 `pip install`。

## License

MIT-0
